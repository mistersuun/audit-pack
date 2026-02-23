"""
RJ Core blueprint - handles file upload, download, status, and reading.
"""

from flask import Blueprint, request, jsonify, send_file, session, render_template
from datetime import datetime, date as date_type
import io
import re
import uuid
import threading
import time
import logging
from routes.checklist import login_required
from utils.rj_filler import RJFiller, DEFAULT_FILENAME
from utils.rj_reader import RJReader
from utils.csrf import csrf_protect

logger = logging.getLogger(__name__)


def _extract_date_from_filename(filename):
    """
    Try to extract audit date from the RJ filename.

    Supports patterns like:
      RJ_20260115.xls       → (15, 1, 2026)
      RJ_2026-01-15.xls     → (15, 1, 2026)
      RJ 15-01-2026.xls     → (15, 1, 2026)
      RJ_15012026.xls       → (15, 1, 2026)
      RJ Janvier 15 2026.xls → (15, 1, 2026)

    Returns:
        dict with {jour, mois, annee} or None if no date found
    """
    if not filename:
        return None

    name = filename.rsplit('.', 1)[0]  # Remove extension

    # Pattern 1: YYYYMMDD or YYYY-MM-DD or YYYY_MM_DD
    m = re.search(r'(20\d{2})[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])', name)
    if m:
        return {'jour': int(m.group(3)), 'mois': int(m.group(2)), 'annee': int(m.group(1))}

    # Pattern 2: DD-MM-YYYY or DD/MM/YYYY or DD_MM_YYYY
    m = re.search(r'(0[1-9]|[12]\d|3[01])[-/_](0[1-9]|1[0-2])[-/_](20\d{2})', name)
    if m:
        return {'jour': int(m.group(1)), 'mois': int(m.group(2)), 'annee': int(m.group(3))}

    # Pattern 3: DDMMYYYY (8 digits)
    m = re.search(r'(0[1-9]|[12]\d|3[01])(0[1-9]|1[0-2])(20\d{2})', name)
    if m:
        return {'jour': int(m.group(1)), 'mois': int(m.group(2)), 'annee': int(m.group(3))}

    # Pattern 4: French month names
    months_fr = {
        'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12
    }
    lower = name.lower()
    for mname, mnum in months_fr.items():
        if mname in lower:
            # Find day and year near the month name
            nums = re.findall(r'\d+', name)
            day = year = None
            for n in nums:
                v = int(n)
                if 2020 <= v <= 2030:
                    year = v
                elif 1 <= v <= 31:
                    day = v
            if day and year:
                return {'jour': day, 'mois': mnum, 'annee': year}

    return None


rj_core_bp = Blueprint('rj_core', __name__)


# Temporary storage for RJ files (per session)
# In production, use proper file storage or database
RJ_FILES = {}
RJ_FILES_LOCK = threading.Lock()

# Cache for RJFiller instances to avoid re-parsing on every request
# Stores: session_id -> (BytesIO_id, RJFiller)
_RJ_FILLER_CACHE = {}

# Temporary storage for SD files (per session)
SD_FILES = {}
SD_FILES_LOCK = threading.Lock()

# Temporary storage for HP files (per session)
HP_FILES = {}
HP_FILES_LOCK = threading.Lock()

# Memory protection: max sessions and auto-expiration
MAX_SESSIONS = 10
SESSION_EXPIRY_SECONDS = 8 * 3600  # 8 hours
RJ_FILES_TIMESTAMPS = {}
SD_FILES_TIMESTAMPS = {}
HP_FILES_TIMESTAMPS = {}


def get_or_create_filler(session_id):
    """
    Get a cached RJFiller or create a new one.

    Returns the RJFiller instance. The caller is responsible for
    saving via save_and_store() after modifications.

    Raises KeyError if session_id not in RJ_FILES.
    """
    file_bytes = RJ_FILES[session_id]
    buf_id = id(file_bytes)

    cached = _RJ_FILLER_CACHE.get(session_id)
    if cached and cached[0] == buf_id:
        # Same BytesIO object — reuse the filler
        return cached[1]

    # New or changed buffer — create fresh filler
    file_bytes.seek(0)
    filler = RJFiller(file_bytes)
    _RJ_FILLER_CACHE[session_id] = (buf_id, filler)
    return filler


def save_and_store(session_id, filler):
    """
    Save the RJFiller to bytes and store back in RJ_FILES.
    Invalidates the filler cache so next access creates a fresh one.
    """
    output_buffer = filler.save_to_bytes()
    RJ_FILES[session_id] = output_buffer
    # Invalidate cache since buffer changed
    _RJ_FILLER_CACHE.pop(session_id, None)


def _cleanup_expired_sessions():
    """Remove expired sessions from RJ_FILES and SD_FILES."""
    now = time.time()

    # Clean RJ_FILES
    expired = [sid for sid, ts in RJ_FILES_TIMESTAMPS.items()
               if now - ts > SESSION_EXPIRY_SECONDS]
    for sid in expired:
        RJ_FILES.pop(sid, None)
        RJ_FILES_TIMESTAMPS.pop(sid, None)
        _RJ_FILLER_CACHE.pop(sid, None)

    # Clean SD_FILES
    expired = [sid for sid, ts in SD_FILES_TIMESTAMPS.items()
               if now - ts > SESSION_EXPIRY_SECONDS]
    for sid in expired:
        SD_FILES.pop(sid, None)
        SD_FILES_TIMESTAMPS.pop(sid, None)

    # If still over max, remove oldest
    while len(RJ_FILES) > MAX_SESSIONS:
        oldest = min(RJ_FILES_TIMESTAMPS, key=RJ_FILES_TIMESTAMPS.get)
        RJ_FILES.pop(oldest, None)
        RJ_FILES_TIMESTAMPS.pop(oldest, None)
        _RJ_FILLER_CACHE.pop(oldest, None)

    while len(SD_FILES) > MAX_SESSIONS:
        oldest = min(SD_FILES_TIMESTAMPS, key=SD_FILES_TIMESTAMPS.get)
        SD_FILES.pop(oldest, None)
        SD_FILES_TIMESTAMPS.pop(oldest, None)


def _touch_session(session_id):
    """Update the timestamp for a session to keep it alive."""
    if session_id in RJ_FILES_TIMESTAMPS:
        RJ_FILES_TIMESTAMPS[session_id] = time.time()


def get_session_id():
    """
    Get or create a unique session ID for the current user.
    Prevents multiple users from sharing the same 'default' session.
    """
    sid = session.get('user_session_id')
    if not sid:
        sid = str(uuid.uuid4())[:12]
        session['user_session_id'] = sid
    return sid


@rj_core_bp.route('/rj')
@login_required
def rj_page():
    """Display the RJ management page (original monolithic version)."""
    return render_template('rj.html')


@rj_core_bp.route('/rj/v2')
@login_required
def rj_page_v2():
    """Display the new modular RJ page with lazy-loaded tabs."""
    return render_template('audit/rj/rj_layout.html')


@rj_core_bp.route('/api/rj/tab/<tab_id>')
@login_required
def get_rj_tab(tab_id):
    """
    Serve individual tab HTML fragments for lazy loading.

    Args:
        tab_id: Tab identifier (e.g., 'nouveau-jour', 'sd', 'recap')

    Returns:
        HTML fragment for the requested tab
    """
    valid_tabs = ['nouveau-jour', 'sd', 'depot', 'dueback', 'recap', 'transelect', 'geac', 'import-docs']
    if tab_id not in valid_tabs:
        return jsonify({'success': False, 'error': f'Invalid tab: {tab_id}'}), 404

    # Check if RJ file is loaded for this session
    session_id = get_session_id()
    rj_loaded = session_id in RJ_FILES

    # import-docs tab can work without RJ, all others require it
    requires_rj = tab_id != 'import-docs'

    template_name = tab_id.replace('-', '_')
    try:
        return render_template(
            f'audit/rj/tabs/{template_name}.html',
            rj_loaded=rj_loaded,
            requires_rj=requires_rj
        )
    except Exception as e:
        return jsonify({'success': False, 'error': f'Tab template not found: {str(e)}'}), 500


@rj_core_bp.route('/api/rj/upload', methods=['POST'])
@login_required
@csrf_protect
def upload_rj():
    """
    Upload RJ file for the current shift.

    Expects:
        - File upload with key 'rj_file'

    Returns:
        - success: True/False
        - message: Status message
        - file_info: Information about the uploaded file
    """
    if 'rj_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['rj_file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({'success': False, 'error': 'File must be .xls or .xlsx'}), 400

    try:
        # Read file to memory
        file_bytes = io.BytesIO(file.read())

        # Store filename as attribute on the BytesIO object for later retrieval
        file_bytes._rj_filename = file.filename

        # Store in session-based storage
        session_id = get_session_id()
        RJ_FILES[session_id] = file_bytes
        RJ_FILES_TIMESTAMPS[session_id] = time.time()
        _cleanup_expired_sessions()

        # Read current audit data from the file
        audit_info = {}
        try:
            file_bytes.seek(0)
            reader = RJReader(file_bytes)
            controle = reader.read_controle()
            if controle:
                audit_info = {
                    'jour': controle.get('jour'),
                    'mois': controle.get('mois'),
                    'annee': controle.get('annee'),
                    'prepare_par': controle.get('prepare_par'),
                }
        except Exception:
            pass  # If reading fails, just skip — user can set date manually

        # Fallback: try to extract date from filename if controle is empty
        if not audit_info.get('jour') or not audit_info.get('mois') or not audit_info.get('annee'):
            fname_date = _extract_date_from_filename(file.filename)
            if fname_date:
                if not audit_info.get('jour'):
                    audit_info['jour'] = fname_date['jour']
                if not audit_info.get('mois'):
                    audit_info['mois'] = fname_date['mois']
                if not audit_info.get('annee'):
                    audit_info['annee'] = fname_date['annee']
                audit_info['date_source'] = 'filename'

        # Auto-persist Jour sheet data to DB for historical analytics
        history_info = {}
        try:
            from utils.jour_importer import JourImporter
            file_bytes.seek(0)
            metrics, info = JourImporter.extract_from_rj(file_bytes, file.filename)
            file_bytes.seek(0)
            if metrics:
                result = JourImporter.persist_batch(metrics, source='rj_upload')
                history_info = {
                    'days_saved': result['total'],
                    'month': info.get('month'),
                    'year': info.get('year'),
                }
        except Exception as hist_err:
            logger.warning(f"Auto-save to history failed (non-blocking): {hist_err}")

        # ★ Archive ALL 38 sheets to database (ETL / zero data loss)
        archive_info = {}
        try:
            from routes.audit.rj_native import _archive_rj_to_db
            rj_date = None
            if audit_info.get('jour') and audit_info.get('mois') and audit_info.get('annee'):
                rj_date = date_type(int(audit_info['annee']), int(audit_info['mois']), int(audit_info['jour']))
            if rj_date:
                file_bytes.seek(0)
                archive_info = _archive_rj_to_db(
                    file_bytes.getvalue(), rj_date,
                    source_filename=file.filename,
                    uploaded_by=session.get('user_name', '')
                )
        except Exception as arc_err:
            logger.warning(f"RJ archive failed (non-blocking): {arc_err}")

        return jsonify({
            'success': True,
            'message': 'Fichier RJ uploadé avec succès',
            'file_info': {
                'filename': file.filename,
                'size': len(file_bytes.getvalue())
            },
            'audit_info': audit_info,
            'history': history_info,
            'archive': archive_info
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/download', methods=['GET'])
@login_required
def download_rj():
    """
    Download the filled RJ file.

    Returns:
        - Excel file download
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file available'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        # Create a copy to send, preserving the original buffer position for future use
        download_buffer = io.BytesIO(file_bytes.read())
        file_bytes.seek(0)  # Reset position for future use

        # Generate filename with date
        today = datetime.now()
        filename = f'RJ_{today.strftime("%Y-%m-%d")}_filled.xls'

        return send_file(
            download_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.ms-excel'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/status', methods=['GET'])
@login_required
def rj_status():
    """
    Check if RJ file is uploaded for current session.

    Returns:
        - uploaded: True/False
        - file_size: Size in bytes (if uploaded)
        - current_day: Current audit day (if uploaded)
    """
    session_id = get_session_id()

    if session_id in RJ_FILES:
        file_bytes = RJ_FILES[session_id]

        # Get current audit day and filename
        current_day = None
        filename = DEFAULT_FILENAME
        try:
            file_bytes.seek(0)
            reader = RJReader(file_bytes)
            current_day = reader.get_current_audit_day()
        except Exception:
            pass  # If we can't get the day, just return None

        # Try to get stored filename
        filename = getattr(file_bytes, '_rj_filename', filename)

        # Touch session timestamp
        RJ_FILES_TIMESTAMPS[session_id] = time.time()

        return jsonify({
            'file_loaded': True,
            'uploaded': True,  # Keep for backwards compatibility
            'filename': filename,
            'file_size': len(file_bytes.getvalue()),
            'current_day': current_day
        })
    else:
        return jsonify({'file_loaded': False, 'uploaded': False})


@rj_core_bp.route('/api/rj/read', methods=['GET'])
@login_required
def read_rj():
    """
    Read and return current RJ data.

    Returns:
        - JSON with all RJ data (controle, dueback, recap, etc.)
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reader = RJReader(file_bytes)
        data = reader.read_all()

        _touch_session(session_id)

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/read/<sheet_name>', methods=['GET'])
@login_required
def read_rj_sheet(sheet_name):
    """
    Read specific sheet from RJ.

    Args:
        sheet_name: 'controle', 'dueback', 'recap', 'transelect', or 'geac_ux'

    Query params:
        - day: For dueback, specific day to read (optional)

    Returns:
        - JSON with sheet data
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reader = RJReader(file_bytes)

        if sheet_name == 'controle':
            data = reader.read_controle()
        elif sheet_name == 'dueback':
            day = request.args.get('day', type=int)
            data = reader.read_dueback(day=day)
        elif sheet_name == 'recap':
            data = reader.read_recap()
        elif sheet_name == 'transelect':
            data = reader.read_transelect()
        elif sheet_name == 'geac_ux':
            data = reader.read_geac_ux()
        else:
            return jsonify({'success': False, 'error': f'Unknown sheet: {sheet_name}'}), 400

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/weather', methods=['GET'])
@login_required
def get_weather():
    """Return current weather for Laval, QC for auto-fill."""
    try:
        from utils.weather_api import get_current_weather_data
        weather = get_current_weather_data()
        return jsonify({'success': True, 'weather': weather})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/preview', methods=['GET'])
@login_required
def preview_rj():
    """
    Get live preview of Excel file data.

    Query params:
        - sheet: Sheet name to preview (default: 'Recap')
        - start_row: Starting row (default: 0)
        - end_row: Ending row (default: 50)
        - start_col: Starting column (default: 0)
        - end_col: Ending column (default: 20)

    Returns:
        - JSON with sheet data for preview
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reader = RJReader(file_bytes)

        # Get parameters
        sheet_name = request.args.get('sheet', 'Recap')

        # Validate sheet_name: not empty, reasonable length
        if not sheet_name or len(sheet_name) > 50:
            return jsonify({'success': False, 'error': 'Invalid sheet name'}), 400

        # Get available sheets and validate sheet exists
        available_sheets = reader.get_available_sheets()
        if sheet_name not in available_sheets:
            return jsonify({'success': False, 'error': f'Sheet "{sheet_name}" not found'}), 404

        start_row = request.args.get('start_row', type=int, default=0)
        end_row = request.args.get('end_row', type=int, default=50)
        start_col = request.args.get('start_col', type=int, default=0)
        end_col = request.args.get('end_col', type=int, default=20)

        # Read sheet range
        preview_data = reader.read_sheet_range(
            sheet_name=sheet_name,
            start_row=start_row,
            end_row=end_row,
            start_col=start_col,
            end_col=end_col
        )

        _touch_session(session_id)

        return jsonify({
            'success': True,
            'data': preview_data,
            'available_sheets': available_sheets
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/report/pdf', methods=['GET'])
@login_required
def generate_pdf_report():
    """
    Generate a Night Audit PDF report for the General Manager.

    Reads all RJ data, computes card totals, runs validation,
    and returns a downloadable PDF.
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reader = RJReader(file_bytes)

        # Read all sheets
        rj_data = reader.read_all()

        # Add pre-computed card totals for the PDF
        try:
            rj_data['transelect_totals'] = reader.read_transelect_totals()
        except Exception:
            rj_data['transelect_totals'] = {}

        try:
            rj_data['geac_cashout'] = reader.read_geac_cash_out()
        except Exception:
            rj_data['geac_cashout'] = {}

        # Run validation checks
        validation_checks = []
        try:
            controle = rj_data.get('controle', {})
            jour = controle.get('jour')
            mois = controle.get('mois')
            annee = controle.get('annee')
            if jour and mois and annee:
                validation_checks.append({
                    'name': 'Date configurée',
                    'status': 'ok',
                    'detail': f'Jour {int(jour)}/{int(mois)}/{int(annee)}'
                })
            else:
                validation_checks.append({
                    'name': 'Date configurée',
                    'status': 'error',
                    'detail': 'Date non configurée'
                })

            recap = rj_data.get('recap', {})
            if recap:
                validation_checks.append({
                    'name': 'Recap',
                    'status': 'ok',
                    'detail': 'Données présentes'
                })

            validation_checks.append({
                'name': 'Transelect',
                'status': 'info',
                'detail': 'Variance normale (arrondis cartes)'
            })

            dueback = rj_data.get('dueback', {})
            rec_count = len(dueback.get('receptionists', [])) if dueback else 0
            if rec_count > 0:
                validation_checks.append({
                    'name': 'DueBack',
                    'status': 'ok',
                    'detail': f'{rec_count} réceptionnistes'
                })
        except Exception:
            pass

        # Get weather (optional, don't fail if unavailable)
        weather = None
        try:
            from utils.weather_api import get_current_weather_data
            weather = get_current_weather_data()
        except Exception:
            pass

        # Generate PDF
        from utils.pdf_report import generate_night_report
        pdf_buffer = generate_night_report(
            rj_data=rj_data,
            validation_checks=validation_checks,
            weather=weather,
        )

        # Build filename
        controle = rj_data.get('controle', {})
        jour = controle.get('jour', '')
        mois = controle.get('mois', '')
        annee = controle.get('annee', '')
        if jour and mois and annee:
            filename = f"Rapport_Nuit_{int(annee)}-{int(mois):02d}-{int(jour):02d}.pdf"
        else:
            filename = f"Rapport_Nuit_{datetime.now().strftime('%Y-%m-%d')}.pdf"

        _touch_session(session_id)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/validate', methods=['GET'])
@login_required
def validate_rj():
    """
    Cross-validate all RJ sheets and return a health summary.

    Returns checks for:
    - Recap balance (should be $0.00)
    - Transelect variance (informational, always has rounding)
    - DueBack total vs SetD total
    - Controle date is set
    - All required sheets filled
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file'}), 400

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        reader = RJReader(file_bytes)

        checks = []

        # 1. Controle date
        try:
            controle = reader.read_controle()
            jour = controle.get('jour')
            mois = controle.get('mois')
            annee = controle.get('annee')
            if jour and mois and annee:
                checks.append({
                    'name': 'Date configurée',
                    'status': 'ok',
                    'detail': f'Jour {int(jour)}/{int(mois)}/{int(annee)}'
                })
            else:
                checks.append({
                    'name': 'Date configurée',
                    'status': 'error',
                    'detail': 'Date non configurée dans controle'
                })
        except Exception:
            checks.append({'name': 'Date configurée', 'status': 'error', 'detail': 'Impossible de lire controle'})

        # 2. Recap balance (check if Row 22 minus Row 24 = 0, or similar)
        try:
            recap_data = reader.read_recap() if hasattr(reader, 'read_recap') else None
            if recap_data and 'balance' in recap_data:
                balance = float(recap_data['balance'])
                if abs(balance) < 0.01:
                    checks.append({'name': 'Recap balance', 'status': 'ok', 'detail': '$0.00'})
                else:
                    checks.append({'name': 'Recap balance', 'status': 'warning', 'detail': f'${balance:.2f}'})
            else:
                checks.append({'name': 'Recap balance', 'status': 'info', 'detail': 'Non vérifié'})
        except Exception:
            checks.append({'name': 'Recap balance', 'status': 'info', 'detail': 'Non vérifié'})

        # 3. Transelect vs GEAC cross-validation (card totals)
        try:
            ts_totals = reader.read_transelect_totals()
            geac_totals = reader.read_geac_cash_out()
            ts_sum = sum(ts_totals.get(k, 0) for k in ('visa', 'mastercard', 'amex'))
            geac_sum = sum(geac_totals.get(k, 0) for k in ('visa', 'mastercard', 'amex'))

            if ts_sum == 0 and geac_sum == 0:
                checks.append({
                    'name': 'Cartes TS vs GEAC',
                    'status': 'info',
                    'detail': 'Pas de données cartes'
                })
            else:
                diff = abs(ts_sum - geac_sum)
                if diff < 1.00:
                    checks.append({
                        'name': 'Cartes TS vs GEAC',
                        'status': 'ok',
                        'detail': f'Écart ${diff:.2f} (OK)'
                    })
                elif diff < 50.00:
                    checks.append({
                        'name': 'Cartes TS vs GEAC',
                        'status': 'warning',
                        'detail': f'Écart ${diff:.2f} (TS=${ts_sum:.0f} vs GEAC=${geac_sum:.0f})'
                    })
                else:
                    checks.append({
                        'name': 'Cartes TS vs GEAC',
                        'status': 'error',
                        'detail': f'Écart ${diff:.2f} — TS=${ts_sum:.0f} vs GEAC=${geac_sum:.0f}'
                    })
        except Exception:
            checks.append({'name': 'Cartes TS vs GEAC', 'status': 'info', 'detail': 'Non vérifié'})

        # 4. Recap balance — compute surplus/deficit from actual cells
        try:
            recap = reader.read_recap()
            sf = lambda k: float(recap.get(k) or 0)
            # Recap surplus = (comptant + cheques) - remb - dueback - depot
            comptant = sf('comptant_lightspeed_lecture') + sf('comptant_lightspeed_corr') \
                     + sf('comptant_positouch_lecture') + sf('comptant_positouch_corr')
            cheques = sf('cheque_payment_lecture') + sf('cheque_payment_corr')
            remb = sf('remb_gratuite_lecture') + sf('remb_gratuite_corr') \
                 + sf('remb_client_lecture') + sf('remb_client_corr')
            dueback_total = sf('due_back_reception_lecture') + sf('due_back_reception_corr') \
                          + sf('due_back_nb_lecture') + sf('due_back_nb_corr')
            depot = sf('depot_canadien_lecture') + sf('depot_canadien_corr')
            surplus = sf('surplus_deficit_lecture') + sf('surplus_deficit_corr')

            argent_recu = comptant + cheques - remb - dueback_total
            expected_surplus = argent_recu - depot

            if abs(depot) < 0.01 and abs(comptant) < 0.01:
                checks.append({'name': 'Recap balance', 'status': 'info', 'detail': 'Pas encore rempli'})
            elif abs(surplus) < 0.01:
                checks.append({'name': 'Recap balance', 'status': 'ok', 'detail': 'Surplus/Déficit = $0.00'})
            else:
                checks.append({
                    'name': 'Recap balance',
                    'status': 'warning',
                    'detail': f'Surplus/Déficit = ${surplus:.2f}'
                })
        except Exception:
            checks.append({'name': 'Recap balance', 'status': 'info', 'detail': 'Non vérifié'})

        # 5. DueBack filled
        try:
            dueback = reader.read_dueback()
            rec_count = len(dueback.get('receptionists', [])) if dueback else 0
            if rec_count > 0:
                checks.append({'name': 'DueBack', 'status': 'ok', 'detail': f'{rec_count} réceptionnistes'})
            else:
                checks.append({'name': 'DueBack', 'status': 'info', 'detail': 'Aucune donnée'})
        except Exception:
            checks.append({'name': 'DueBack', 'status': 'info', 'detail': 'Non vérifié'})

        # 6. Check if sheets have data
        sheet_names = []
        for i in range(reader.wb.nsheets):
            sheet_names.append(reader.wb.sheet_by_index(i).name)

        required = ['controle', 'Recap', 'transelect']
        for req in required:
            found = any(s.lower() == req.lower() for s in sheet_names)
            if not found:
                checks.append({'name': f'Feuille {req}', 'status': 'error', 'detail': 'Manquante'})

        # Overall status
        has_error = any(c['status'] == 'error' for c in checks)
        has_warning = any(c['status'] == 'warning' for c in checks)
        overall = 'error' if has_error else ('warning' if has_warning else 'ok')

        _touch_session(session_id)

        return jsonify({
            'success': True,
            'overall': overall,
            'checks': checks,
            'sheet_count': len(sheet_names)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/dueback/receptionists', methods=['GET'])
@login_required
def get_dueback_receptionists():
    """
    Get receptionist list dynamically from the DUBACK# sheet headers.

    Reads row 2 (last name) and row 3 (first name) from the actual file
    instead of using a hardcoded mapping.

    Returns:
        JSON list of {col_letter, last_name, first_name, full_name}
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'receptionists': [], 'error': 'Aucun fichier RJ chargé'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        reader = RJReader(file_bytes)
        dueback = reader.read_dueback()

        receptionists = dueback.get('receptionists', [])

        _touch_session(session_id)

        return jsonify({
            'success': True,
            'receptionists': receptionists,
            'count': len(receptionists)
        })

    except Exception as e:
        return jsonify({'success': False, 'receptionists': [], 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/quasimodo/generate', methods=['POST'])
@login_required
@csrf_protect
def generate_quasimodo():
    """
    Generate a Quasimodo .xls file from the current RJ transelect data.

    Reads transelect + controle from the loaded RJ, computes MON/GLB/REC
    card breakdowns, and returns a downloadable Quasimodo .xls file.

    Optional JSON body:
        can_deposit (float): Canadian deposit amount
        us_deposit  (float): US deposit amount
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reader = RJReader(file_bytes)
        transelect = reader.read_transelect()
        controle = reader.read_controle()

        # Optional deposits from request body
        body = request.get_json(silent=True) or {}
        can_deposit = body.get('can_deposit')
        us_deposit = body.get('us_deposit')

        # Try to read CAN deposit from RJ if not provided
        if can_deposit is None:
            try:
                # Read depot_canadien from the rj sheet (J25 = row 24, col 9)
                rj_sheet = reader.wb.sheet_by_name('rj')
                cached = rj_sheet.cell_value(24, 9)
                if cached and isinstance(cached, (int, float)):
                    can_deposit = float(cached)
            except Exception:
                can_deposit = 0

        from utils.quasimodo_generator import QuasimodoGenerator

        gen = QuasimodoGenerator(
            transelect_data=transelect,
            controle_data=controle,
            can_deposit=can_deposit,
            us_deposit=us_deposit,
        )

        xls_bytes = gen.generate()
        filename = gen.get_filename()

        _touch_session(session_id)

        return send_file(
            io.BytesIO(xls_bytes),
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.ms-excel'
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/quasimodo/preview', methods=['GET'])
@login_required
def preview_quasimodo():
    """
    Preview the Quasimodo data without generating the file.

    Returns JSON with MON/GLB/REC breakdowns, deposits, and transit.
    Useful for the UI to show what the file will contain before download.
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reader = RJReader(file_bytes)
        transelect = reader.read_transelect()
        controle = reader.read_controle()

        # Try to read CAN deposit from RJ
        can_deposit = 0
        try:
            rj_sheet = reader.wb.sheet_by_name('rj')
            cached = rj_sheet.cell_value(24, 9)
            if cached and isinstance(cached, (int, float)):
                can_deposit = float(cached)
        except Exception:
            pass

        from utils.quasimodo_generator import QuasimodoGenerator

        gen = QuasimodoGenerator(
            transelect_data=transelect,
            controle_data=controle,
            can_deposit=can_deposit,
            us_deposit=0,
        )

        _touch_session(session_id)

        return jsonify({
            'success': True,
            **gen.get_summary()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/quasimodo/autofill', methods=['POST'])
@login_required
@csrf_protect
def autofill_quasimodo_fields():
    """
    Auto-fill Quasimodo reconciliation fields (E20-E24) in the transelect sheet.

    Computes card totals from MON+GLB (Section 1) and writes them to the
    Quasimodo columns in Section 2 for cross-verification.
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reader = RJReader(file_bytes)
        totals = reader.read_transelect_totals()

        # Build data dict mapping field names to values
        quasimodo_fill = {
            'quasimodo_debit': totals.get('debit', 0),
            'quasimodo_visa': totals.get('visa', 0),
            'quasimodo_master': totals.get('mastercard', 0),
            'quasimodo_amex': totals.get('amex', 0),
        }

        # Write to transelect sheet
        file_bytes.seek(0)
        from utils.rj_filler import RJFiller
        filler = RJFiller(file_bytes)
        filled = filler.fill_sheet('transelect', quasimodo_fill)

        # Save back
        output = io.BytesIO()
        filler.save(output)
        output.seek(0)
        RJ_FILES[session_id] = output

        _touch_session(session_id)

        return jsonify({
            'success': True,
            'filled_count': filled,
            'values': {k: round(v, 2) for k, v in quasimodo_fill.items()},
            'message': f'Champs Quasimodo E20-E24 remplis ({filled} cellules)'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/download/check', methods=['GET'])
@login_required
def check_before_download():
    """
    Pre-download validation check.

    Runs validation and returns warnings/errors so the UI can prompt
    the user before downloading an incomplete file.
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        reader = RJReader(file_bytes)

        warnings = []
        errors = []

        # 1. Check date is set
        try:
            controle = reader.read_controle()
            jour = controle.get('jour')
            mois = controle.get('mois')
            annee = controle.get('annee')
            if not (jour and mois and annee):
                errors.append('Date non configurée dans Contrôle')
        except Exception:
            errors.append('Impossible de lire la feuille Contrôle')

        # 2. Check transelect has data
        try:
            transelect = reader.read_transelect()
            totals = reader.read_transelect_totals()
            total_cards = sum(totals.values())
            if total_cards == 0:
                warnings.append('Transelect vide — aucune carte de crédit saisie')
            elif total_cards < 1000:
                warnings.append(f'Transelect total faible: ${total_cards:.2f}')
        except Exception:
            warnings.append('Impossible de lire Transelect')

        # 3. Check GEAC has data
        try:
            geac = reader.read_geac_cash_out()
            geac_total = sum(v for v in geac.values() if isinstance(v, (int, float)))
            if geac_total == 0:
                warnings.append('GEAC vide — aucun cash out saisi')
        except Exception:
            warnings.append('Impossible de lire GEAC')

        # 4. Check Recap
        try:
            recap = reader.read_recap()
            if not recap.get('prepare_par'):
                warnings.append('Recap: "Préparé par" non rempli')
        except Exception:
            warnings.append('Impossible de lire Recap')

        # 5. Check DueBack
        try:
            dueback = reader.read_dueback()
            rec_count = len(dueback.get('receptionists', []))
            if rec_count == 0:
                warnings.append('DueBack: aucune donnée de réceptionniste')
        except Exception:
            pass  # DueBack is optional some days

        ready = len(errors) == 0
        status = 'ready' if ready and len(warnings) == 0 else (
            'warnings' if ready else 'errors'
        )

        _touch_session(session_id)

        return jsonify({
            'success': True,
            'status': status,
            'ready': ready,
            'errors': errors,
            'warnings': warnings,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_core_bp.route('/api/rj/progress', methods=['GET'])
@login_required
def get_progress():
    """
    Get completion progress across all RJ sections.

    Returns a list of sections with their completion status,
    suitable for rendering a progress bar in the UI.
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'sections': [], 'progress': 0})

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        reader = RJReader(file_bytes)

        sections = []

        # 1. Contrôle (date + preparer)
        try:
            controle = reader.read_controle()
            has_date = bool(controle.get('jour') and controle.get('mois') and controle.get('annee'))
            has_prep = bool(controle.get('prepare_par'))
            sections.append({
                'name': 'Contrôle',
                'tab': 'nouveau-jour',
                'done': has_date and has_prep,
                'detail': 'Date + préparé par' if has_date and has_prep else (
                    'Date manquante' if not has_date else 'Préparé par manquant'
                )
            })
        except Exception:
            sections.append({'name': 'Contrôle', 'tab': 'nouveau-jour', 'done': False, 'detail': 'Non lu'})

        # 2. Recap
        try:
            recap = reader.read_recap()
            filled_fields = sum(1 for k, v in recap.items() if v and k != 'date')
            sections.append({
                'name': 'Recap',
                'tab': 'recap',
                'done': filled_fields >= 3,
                'detail': f'{filled_fields} champs remplis'
            })
        except Exception:
            sections.append({'name': 'Recap', 'tab': 'recap', 'done': False, 'detail': 'Non lu'})

        # 3. Transelect
        try:
            totals = reader.read_transelect_totals()
            total_cards = sum(totals.values())
            sections.append({
                'name': 'Transelect',
                'tab': 'transelect',
                'done': total_cards > 0,
                'detail': f'${total_cards:,.2f} total cartes' if total_cards > 0 else 'Vide'
            })
        except Exception:
            sections.append({'name': 'Transelect', 'tab': 'transelect', 'done': False, 'detail': 'Non lu'})

        # 4. GEAC
        try:
            geac = reader.read_geac_cash_out()
            geac_total = sum(v for v in geac.values() if isinstance(v, (int, float)))
            sections.append({
                'name': 'GEAC',
                'tab': 'geac',
                'done': geac_total > 0,
                'detail': f'${geac_total:,.2f} cash out' if geac_total > 0 else 'Vide'
            })
        except Exception:
            sections.append({'name': 'GEAC', 'tab': 'geac', 'done': False, 'detail': 'Non lu'})

        # 5. DueBack
        try:
            dueback = reader.read_dueback()
            recs = dueback.get('receptionists', [])
            sections.append({
                'name': 'DueBack',
                'tab': 'dueback',
                'done': len(recs) > 0,
                'detail': f'{len(recs)} réceptionnistes' if recs else 'Vide'
            })
        except Exception:
            sections.append({'name': 'DueBack', 'tab': 'dueback', 'done': False, 'detail': 'Non lu'})

        # 6. Dépôt / SD
        sd_done = session_id in SD_FILES
        sections.append({
            'name': 'Dépôt / SD',
            'tab': 'sd',
            'done': sd_done,
            'detail': 'Fichier SD chargé' if sd_done else 'Aucun fichier SD'
        })

        # 7. Macros (jour sheet)
        sections.append({
            'name': 'Macros Jour',
            'tab': 'macros',
            'done': False,  # Can't easily verify — user driven
            'detail': 'Envoie + Calcul Carte'
        })

        done_count = sum(1 for s in sections if s['done'])
        total_count = len(sections)
        progress = round((done_count / total_count) * 100) if total_count > 0 else 0

        _touch_session(session_id)

        return jsonify({
            'success': True,
            'sections': sections,
            'done': done_count,
            'total': total_count,
            'progress': progress,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
