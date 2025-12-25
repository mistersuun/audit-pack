"""
Blueprint for RJ (Revenue Journal) management.
Allows uploading RJ file and filling it with form data.
"""

from flask import Blueprint, request, jsonify, send_file, session, render_template
from functools import wraps
from datetime import datetime
import io
import os
from routes.checklist import login_required
from utils.rj_filler import RJFiller
from utils.rj_reader import RJReader


rj_bp = Blueprint('rj', __name__)


# Temporary storage for RJ files (per session)
# In production, use proper file storage or database
RJ_FILES = {}


@rj_bp.route('/rj')
@login_required
def rj_page():
    """Display the RJ management page."""
    return render_template('rj.html')


@rj_bp.route('/api/rj/upload', methods=['POST'])
@login_required
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

        # Store in session-based storage
        session_id = session.get('user_session_id', 'default')
        RJ_FILES[session_id] = file_bytes

        return jsonify({
            'success': True,
            'message': 'Fichier RJ uploadé avec succès',
            'file_info': {
                'filename': file.filename,
                'size': len(file_bytes.getvalue())
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_bp.route('/api/rj/dueback/names', methods=['GET'])
@login_required
def get_dueback_names():
    """
    Return receptionist columns and optional values for a given day.
    """
    session_id = session.get('user_session_id', 'default')
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400
    day = request.args.get('day', type=int)
    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        reader = RJReader(file_bytes)
        data = reader.read_dueback(day=day)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_bp.route('/api/rj/dueback/bulk', methods=['POST'])
@login_required
def fill_dueback_bulk():
    """
    Fill multiple DueBack entries (previous/nouveau) using column letters.
    Expects JSON: { day: int, items: [ { col_letter: 'C', line_type: 'previous'|'nouveau', amount: float } ] }
    """
    session_id = session.get('user_session_id', 'default')
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400
    data = request.get_json() or {}
    day = data.get('day')
    items = data.get('items', [])
    if not day or not items:
        return jsonify({'success': False, 'error': 'Missing day or items'}), 400
    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        filler = RJFiller(file_bytes)
        filled = 0
        for item in items:
            col = item.get('col_letter')
            line_type = item.get('line_type', 'nouveau')
            amount = item.get('amount')
            if col and amount is not None:
                filler.fill_dueback_by_col(day, col, amount, line_type=line_type)
                filled += 1
        output_buffer = filler.save_to_bytes()
        RJ_FILES[session_id] = output_buffer
        return jsonify({'success': True, 'message': f'{filled} entrées DueBack enregistrées', 'filled': filled})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_bp.route('/api/rj/fill/<sheet_name>', methods=['POST'])
@login_required
def fill_rj_sheet(sheet_name):
    """
    Fill a specific sheet in the RJ file with form data.

    Args:
        sheet_name: Name of the sheet (e.g., 'recap', 'transelect', 'geac', 'controle')

    Expects JSON:
        - Form data matching the sheet's field names

    Returns:
        - success: True/False
        - cells_filled: Number of cells that were filled
    """
    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded. Please upload file first.'}), 400

    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    try:
        # Get the RJ file
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        # Create RJ filler
        rj_filler = RJFiller(file_bytes)

        # Map sheet name to actual sheet name in Excel
        sheet_mapping = {
            'recap': 'Recap',
            'transelect': 'transelect',
            'geac': 'geac_ux',
            'controle': 'controle',
        }

        excel_sheet_name = sheet_mapping.get(sheet_name.lower())

        if not excel_sheet_name:
            return jsonify({'success': False, 'error': f'Unknown sheet: {sheet_name}'}), 400

        # Fill the sheet
        cells_filled = rj_filler.fill_sheet(excel_sheet_name, data)

        # Save back to memory
        output_buffer = rj_filler.save_to_bytes()
        RJ_FILES[session_id] = output_buffer

        return jsonify({
            'success': True,
            'message': f'{cells_filled} cellules remplies dans {sheet_name}',
            'cells_filled': cells_filled
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_bp.route('/api/rj/fill/dueback', methods=['POST'])
@login_required
def fill_dueback():
    """
    Fill DueBack sheet with daily data.

    Expects JSON:
        - day: Day number (1-31)
        - receptionist: Receptionist name
        - amount: Amount to enter
    """
    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json()

    required_fields = ['day', 'receptionist', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        rj_filler = RJFiller(file_bytes)

        # Determine which line to fill (previous or nouveau)
        line_type = data.get('line', 'nouveau')

        rj_filler.fill_dueback_day(
            data['day'],
            data['receptionist'],
            data['amount'],
            line_type=line_type
        )

        output_buffer = rj_filler.save_to_bytes()
        RJ_FILES[session_id] = output_buffer

        line_text = 'Previous' if line_type == 'previous' else 'Nouveau'
        return jsonify({
            'success': True,
            'message': f'DueBack {line_text} rempli pour jour {data["day"]}, {data["receptionist"]}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_bp.route('/api/rj/reset', methods=['POST'])
@login_required
def reset_rj_tabs():
    """
    Reset (Clear) specific tabs in the RJ file for a new day.
    """
    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        rj_filler = RJFiller(file_bytes)
        cleared_count = rj_filler.reset_tabs()

        output_buffer = rj_filler.save_to_bytes()
        RJ_FILES[session_id] = output_buffer

        return jsonify({
            'success': True,
            'message': f'Onglets réinitialisés avec succès ({cleared_count} cellules effacées)',
            'cleared_count': cleared_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_bp.route('/api/rj/sync', methods=['POST'])
@login_required
def sync_duback_setd():
    """
    Sync DueBack amounts to SetD for the current day.
    """
    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json() or {}
    day = data.get('day')

    # If day not provided, try to read it from controle tab
    if not day:
        try:
            file_bytes = RJ_FILES[session_id]
            file_bytes.seek(0)
            reader = RJReader(file_bytes)
            controle_data = reader.read_controle()
            if controle_data and 'jour' in controle_data:
                day = int(controle_data['jour'])
        except:
            pass
            
    if not day:
        return jsonify({'success': False, 'error': 'Day could not be determined. Please provide day in request.'}), 400

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        rj_filler = RJFiller(file_bytes)
        updates = rj_filler.sync_duback_to_setd(day)

        output_buffer = rj_filler.save_to_bytes()
        RJ_FILES[session_id] = output_buffer

        return jsonify({
            'success': True,
            'message': f'Sync terminé: {updates} valeurs mises à jour dans SetD pour le jour {day}',
            'updates': updates
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_bp.route('/api/rj/deposit', methods=['POST'])
@login_required
def update_deposit():
    """
    Update the Deposit tab with a verified amount.
    """
    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json()
    amount = data.get('amount')
    date_str = data.get('date') # Optional, will use today if missing

    if not amount:
        return jsonify({'success': False, 'error': 'Amount is required'}), 400

    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        rj_filler = RJFiller(file_bytes)
        success = rj_filler.update_deposit(date_str, amount)

        if success:
            output_buffer = rj_filler.save_to_bytes()
            RJ_FILES[session_id] = output_buffer
            return jsonify({
                'success': True,
                'message': f'Dépôt de {amount}$ ajouté pour le {date_str}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update deposit sheet'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_bp.route('/api/rj/download', methods=['GET'])
@login_required
def download_rj():
    """
    Download the filled RJ file.

    Returns:
        - Excel file download
    """
    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'error': 'No RJ file available'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        # Generate filename with date
        today = datetime.now()
        filename = f'RJ_{today.strftime("%Y-%m-%d")}_filled.xls'

        return send_file(
            file_bytes,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.ms-excel'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rj_bp.route('/api/rj/status', methods=['GET'])
@login_required
def rj_status():
    """
    Check if RJ file is uploaded for current session.

    Returns:
        - uploaded: True/False
        - file_size: Size in bytes (if uploaded)
    """
    session_id = session.get('user_session_id', 'default')

    if session_id in RJ_FILES:
        file_bytes = RJ_FILES[session_id]
        return jsonify({
            'uploaded': True,
            'file_size': len(file_bytes.getvalue())
        })
    else:
        return jsonify({'uploaded': False})


@rj_bp.route('/api/rj/read', methods=['GET'])
@login_required
def read_rj():
    """
    Read and return current RJ data.

    Returns:
        - JSON with all RJ data (controle, dueback, recap, etc.)
    """
    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'error': 'No RJ file uploaded'}), 404

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reader = RJReader(file_bytes)
        data = reader.read_all()

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rj_bp.route('/api/rj/read/<sheet_name>', methods=['GET'])
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
    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'error': 'No RJ file uploaded'}), 404

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
            return jsonify({'error': f'Unknown sheet: {sheet_name}'}), 400

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
