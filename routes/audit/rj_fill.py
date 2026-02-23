"""
RJ Fill blueprint - handles sheet filling and DueBack operations.
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import io
import math
from routes.checklist import login_required
from utils.rj_filler import RJFiller
from utils.rj_reader import RJReader
from utils.rj_mapper import CELL_MAPPINGS
from utils.csrf import csrf_protect
from .rj_core import RJ_FILES, get_session_id, get_or_create_filler, save_and_store, _RJ_FILLER_CACHE


# Configuration constants
MAX_FINANCIAL_AMOUNT = 10_000_000  # Maximum absolute value for financial amounts


def validate_amount(value, field_name='amount', max_val=MAX_FINANCIAL_AMOUNT):
    """
    Validate a financial amount value.

    Args:
        value: Value to validate (can be str, int, float, or None)
        field_name: Name of the field for error messages (default 'amount')
        max_val: Maximum absolute value allowed (default 10,000,000)

    Returns:
        Tuple of (float_value, error_message)
        - On success: (float_value, None)
        - On failure: (None, error_message_string)
    """
    # Handle None
    if value is None:
        return None, f"{field_name} cannot be None"

    # Try to convert to float
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        return None, f"{field_name} must be a valid number, got '{value}'"

    # Check for NaN or Infinity
    if not math.isfinite(float_value):
        if math.isnan(float_value):
            return None, f"{field_name} cannot be NaN"
        else:
            return None, f"{field_name} cannot be Infinity"

    # Check absolute value bounds
    if abs(float_value) > max_val:
        return None, f"{field_name} must not exceed {max_val:,.0f} in absolute value"

    return float_value, None


rj_fill_bp = Blueprint('rj_fill', __name__)


@rj_fill_bp.route('/api/rj/fill/<sheet_name>', methods=['POST'])
@login_required
@csrf_protect
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
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded. Please upload file first.'}), 400

    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    try:
        # Map sheet name to actual sheet name in Excel
        sheet_mapping = {
            'recap': 'Recap',
            'transelect': 'transelect',
            'geac': 'geac_ux',
            'controle': 'controle',
            'depot': 'depot',
            'daily': 'daily',
        }

        excel_sheet_name = sheet_mapping.get(sheet_name.lower())

        if not excel_sheet_name:
            return jsonify({'success': False, 'error': f'Unknown sheet: {sheet_name}'}), 400

        # Validate that sheet has mappings defined
        if excel_sheet_name not in CELL_MAPPINGS:
            return jsonify({'success': False, 'error': f'Sheet "{excel_sheet_name}" is not supported'}), 400

        # Get or create RJ filler
        rj_filler = get_or_create_filler(session_id)

        # Fill the sheet
        cells_filled = rj_filler.fill_sheet(excel_sheet_name, data)

        # Save back to memory
        save_and_store(session_id, rj_filler)

        return jsonify({
            'success': True,
            'message': f'{cells_filled} cellules remplies dans {sheet_name}',
            'cells_filled': cells_filled
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/fill/dueback', methods=['POST'])
@login_required
@csrf_protect
def fill_dueback():
    """
    Fill DueBack sheet with daily data.

    Expects JSON:
        - day: Day number (1-31)
        - receptionist: Receptionist name
        - amount: Amount to enter
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json()

    required_fields = ['day', 'receptionist', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    # Validate amount
    amount_val, err = validate_amount(data.get('amount'))
    if err:
        return jsonify({'success': False, 'error': err}), 400

    try:
        rj_filler = get_or_create_filler(session_id)

        # Determine which line to fill (previous or nouveau)
        line_type = data.get('line', 'nouveau')

        rj_filler.fill_dueback_day(
            data['day'],
            data['receptionist'],
            amount_val,
            line_type=line_type
        )

        save_and_store(session_id, rj_filler)

        line_text = 'Previous' if line_type == 'previous' else 'Nouveau'
        return jsonify({
            'success': True,
            'message': f'DueBack {line_text} rempli pour jour {data["day"]}, {data["receptionist"]}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/dueback/names', methods=['GET'])
@login_required
def get_dueback_names():
    """
    Return receptionist columns and optional values for a given day.
    """
    session_id = get_session_id()
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


@rj_fill_bp.route('/api/rj/dueback/total', methods=['GET'])
@login_required
def get_dueback_total():
    """
    Get the total from column Z for a specific day in DueBack sheet.

    Query params:
        day (int): Day number (1-31)

    Returns:
        {
            'success': bool,
            'total': float,
            'day': int
        }
    """
    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    day = request.args.get('day', type=int, default=1)

    # Validate day
    if not 1 <= day <= 31:
        return jsonify({'success': False, 'error': 'Day must be between 1 and 31'}), 400

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        reader = RJReader(file_bytes)

        # Get total from column Z
        total = reader.get_dueback_day_total(day)

        return jsonify({
            'success': True,
            'total': total,
            'day': day
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/dueback/column-b', methods=['GET'])
@login_required
def get_dueback_column_b():
    """
    Get Column B (R/J) values for the current audit day in DueBack sheet.

    Column B contains a reference to the 'jour' sheet (=+jour!BY[row])
    and is READ-ONLY - it cannot be calculated from receptionist entries.

    Query params:
        day (int, optional): Day number (1-31). If not provided, uses current audit day.

    Returns:
        {
            'success': bool,
            'data': {
                'previous': float,
                'current': float,
                'net': float
            },
            'day': int
        }
    """
    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        reader = RJReader(file_bytes)

        # Get day from query param or use current audit day
        day = request.args.get('day', type=int)
        if not day:
            # Get current audit day from RJ file
            day = reader.get_current_audit_day()

        # Validate day
        if not 1 <= day <= 31:
            return jsonify({'success': False, 'error': 'Day must be between 1 and 31'}), 400

        # Get Column B values
        column_b_data = reader.get_dueback_column_b(day)

        return jsonify({
            'success': True,
            'data': column_b_data,
            'day': day
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/dueback/bulk', methods=['POST'])
@login_required
@csrf_protect
def fill_dueback_bulk():
    """
    Fill multiple DueBack entries (previous/nouveau) using column letters.
    Expects JSON: { day: int, items: [ { col_letter: 'C', line_type: 'previous'|'nouveau', amount: float } ] }
    """
    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400
    data = request.get_json() or {}
    day = data.get('day')
    items = data.get('items', [])
    if not day or not items:
        return jsonify({'success': False, 'error': 'Missing day or items'}), 400
    try:
        filler = get_or_create_filler(session_id)
        filled = 0
        for item in items:
            col = item.get('col_letter')
            line_type = item.get('line_type', 'nouveau')
            amount = item.get('amount')
            if col and amount is not None:
                # Validate amount
                amount_val, err = validate_amount(amount, field_name=f'amount ({col})')
                if err:
                    return jsonify({'success': False, 'error': err}), 400
                filler.fill_dueback_by_col(day, col, amount_val, line_type=line_type)
                filled += 1
        save_and_store(session_id, filler)
        return jsonify({'success': True, 'message': f'{filled} entrées DueBack enregistrées', 'filled': filled})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/dueback/save', methods=['POST'])
@login_required
@csrf_protect
def save_dueback_simple():
    """
    Save DueBack data for current audit day using simplified workflow.
    Expects JSON: { 'C': { previous: float, current: float }, 'D': { previous: float, current: float }, ... }

    Previous values are entered as positive in UI but stored as negative in Excel.
    Current values are stored as positive.
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json() or {}

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    try:
        # Get the RJ file
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        # Create a bytes copy to avoid shared buffer issues between RJFiller and RJReader
        raw_bytes = file_bytes.read()
        file_bytes.seek(0)

        # Create RJ reader to get current audit day
        reader = RJReader(io.BytesIO(raw_bytes))
        current_day = reader.get_current_audit_day()

        if not current_day:
            return jsonify({'success': False, 'error': 'Could not determine current audit day'}), 400

        # Get or create filler (will reuse if same buffer)
        filler = get_or_create_filler(session_id)

        # Fill all receptionist columns
        filled_count = 0
        total_previous = 0
        total_current = 0

        for col_letter, values in data.items():
            previous = values.get('previous', 0)  # Already negative from frontend
            current = values.get('current', 0)

            # Validate previous amount
            prev_val, err = validate_amount(previous, field_name=f'previous ({col_letter})')
            if err:
                return jsonify({'success': False, 'error': err}), 400

            # Validate current amount
            curr_val, err = validate_amount(current, field_name=f'current ({col_letter})')
            if err:
                return jsonify({'success': False, 'error': err}), 400

            # Fill previous (balance row) - already negative
            if prev_val != 0:
                filler.fill_dueback_by_col(current_day, col_letter, prev_val, line_type='previous')
                total_previous += prev_val
                filled_count += 1

            # Fill current (operations row) - positive
            if curr_val != 0:
                filler.fill_dueback_by_col(current_day, col_letter, curr_val, line_type='nouveau')
                total_current += curr_val
                filled_count += 1

        # Calculate and fill Total Z (column Z)
        total_z = total_previous + total_current
        filler.fill_dueback_by_col(current_day, 'Z', total_previous, line_type='previous')
        filler.fill_dueback_by_col(current_day, 'Z', total_current, line_type='nouveau')

        # Save back to memory
        save_and_store(session_id, filler)

        return jsonify({
            'success': True,
            'message': 'DueBack sauvegardé avec succès',
            'day': current_day,
            'filled_count': filled_count,
            'total_z': total_z
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/autofill-cashout', methods=['POST'])
@login_required
@csrf_protect
def autofill_geac_cashout():
    """
    Auto-fill GEAC/UX Row 6 (Daily Cash Out) + Row 12 (Daily Revenue) + Transelect fusebox rows
    from Daily Revenue card totals.

    Since FreedomPay bank settlements = Daily Revenue system totals
    (variance should be $0.00), we can copy DR card amounts directly to both rows.

    Expects JSON:
        cards: {visa: float, mastercard: float, amex: float, diners: float, discover: float}

    Fills:
        - geac_ux sheet Row 6: B6 (amex), E6 (diners), G6 (mc), J6 (visa), K6 (discover)
        - geac_ux sheet Row 12: B12 (amex), E12 (diners), G12 (mc), J12 (visa), K12 (discover)
        - transelect sheet: B21 (visa), B22 (mc), B24 (amex)
    """
    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 400

    data = request.get_json() or {}
    cards = data.get('cards', {})

    if not cards:
        return jsonify({'success': False, 'error': 'Aucun montant par carte fourni'}), 400

    try:
        from utils.parsers.freedompay_parser import FreedomPayParser

        # Create parser in auto-fill mode
        parser = FreedomPayParser(daily_revenue_cards=cards)
        result = parser.get_result()

        if not result['success']:
            return jsonify(result), 400

        # Get fillable data for all sheets and rows
        geac_fill = parser.get_geac_fillable()
        daily_rev_fill = parser.get_daily_revenue_fillable()
        transelect_fill = parser.get_transelect_fillable()

        rj_filler = get_or_create_filler(session_id)
        cells_filled = 0

        # Fill GEAC/UX Row 6 (Daily Cash Out)
        if geac_fill:
            cells_filled += rj_filler.fill_sheet('geac_ux', {
                k: v for k, v in result['data'].items()
                if k in parser.FIELD_MAPPINGS
            })

        # Fill GEAC/UX Row 12 (Daily Revenue)
        if daily_rev_fill:
            cells_filled += rj_filler.fill_sheet('geac_ux', {
                k: v for k, v in result['data'].items()
                if k in parser.DAILY_REV_MAPPINGS
            })

        # Fill Transelect fusebox rows
        if transelect_fill:
            cells_filled += rj_filler.fill_sheet('transelect', {
                k: v for k, v in result['data'].items()
                if k in parser.TRANSELECT_MAPPINGS
            })

        save_and_store(session_id, rj_filler)

        return jsonify({
            'success': True,
            'cells_filled': cells_filled,
            'geac_filled': list(geac_fill.keys()),
            'daily_rev_filled': list(daily_rev_fill.keys()),
            'transelect_filled': list(transelect_fill.keys()),
            'source': result['data'].get('source', 'unknown'),
            'message': f'Cash Out auto-rempli: {cells_filled} cellules (GEAC/UX Rows 6 & 12 + Transelect)'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/controle', methods=['POST'])
@login_required
@csrf_protect
def update_controle():
    """
    Update the controle sheet with new day/date values for a new audit day.

    Expected JSON body:
    {
        "vjour": 23,      // Day number (1-31)
        "mois": 1,        // Month (1-12)
        "annee": 2026,    // Year
        "prepare_par": "Auditor Name"  // Optional - prepared by
    }
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json() or {}
    vjour = data.get('vjour')
    mois = data.get('mois')
    annee = data.get('annee')
    prepare_par = data.get('prepare_par')

    if not vjour:
        return jsonify({'success': False, 'error': 'vjour (jour) est requis'}), 400

    # Validate day
    try:
        vjour = int(vjour)
        if vjour < 1 or vjour > 31:
            return jsonify({'success': False, 'error': 'vjour doit être entre 1 et 31'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'vjour doit être un nombre'}), 400

    # Validate month if provided
    if mois:
        try:
            mois = int(mois)
            if mois < 1 or mois > 12:
                return jsonify({'success': False, 'error': 'mois doit être entre 1 et 12'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'mois doit être un nombre'}), 400

    # Validate year if provided
    if annee:
        try:
            annee = int(annee)
            if annee < 2000 or annee > 2100:
                return jsonify({'success': False, 'error': 'annee doit être entre 2000 et 2100'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'annee doit être un nombre'}), 400

    try:
        rj_filler = get_or_create_filler(session_id)
        updated = rj_filler.update_controle(vjour=vjour, mois=mois, annee=annee)

        # Fill prepare_par if provided
        if prepare_par:
            fill_data = {'prepare_par': prepare_par}
            rj_filler.fill_sheet('controle', fill_data)

        save_and_store(session_id, rj_filler)

        # Format date for message
        date_str = f"{vjour:02d}"
        if mois:
            date_str = f"{vjour:02d}/{mois:02d}"
        if annee:
            date_str = f"{vjour:02d}/{annee}"

        msg = f'Contrôle mis à jour: Jour {date_str}'
        if prepare_par:
            msg += f', préparé par {prepare_par}'

        return jsonify({
            'success': True,
            'message': msg,
            'updated': updated
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/autofill-controle', methods=['POST'])
@login_required
@csrf_protect
def autofill_controle():
    """
    Auto-fill Controle sheet with auditor name (from session) and current date.

    Expected JSON body (optional):
    {
        "vjour": 23,      // Day number (1-31) - if not provided, uses current audit day
        "mois": 1,        // Month (1-12) - if not provided, uses current month
        "annee": 2026     // Year - if not provided, uses current year
    }

    Auto-fills:
    - prepare_par: from session['user_name'] (logged-in auditor)
    - vjour, mois, annee: from provided date or current audit date
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 400

    # Get auditor name from session
    prepare_par = session.get('user_name', 'Auditor')
    if not prepare_par:
        return jsonify({'success': False, 'error': 'User information not available in session'}), 400

    data = request.get_json() or {}
    vjour = data.get('vjour')
    mois = data.get('mois')
    annee = data.get('annee')

    # If date not provided, try to get from current audit day in RJ file
    if not vjour or not mois or not annee:
        try:
            file_bytes = RJ_FILES[session_id]
            file_bytes.seek(0)
            reader = RJReader(file_bytes)

            if not vjour:
                current_day = reader.get_current_audit_day()
                vjour = current_day if current_day else 1

            if not mois:
                # Get current month
                mois = datetime.now().month

            if not annee:
                # Get current year
                annee = datetime.now().year
        except Exception as e:
            # Fall back to current date
            now = datetime.now()
            if not vjour:
                vjour = now.day
            if not mois:
                mois = now.month
            if not annee:
                annee = now.year

    # Validate day
    try:
        vjour = int(vjour)
        if vjour < 1 or vjour > 31:
            return jsonify({'success': False, 'error': 'vjour doit être entre 1 et 31'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'vjour doit être un nombre'}), 400

    # Validate month
    try:
        mois = int(mois)
        if mois < 1 or mois > 12:
            return jsonify({'success': False, 'error': 'mois doit être entre 1 et 12'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'mois doit être un nombre'}), 400

    # Validate year
    try:
        annee = int(annee)
        if annee < 2000 or annee > 2100:
            return jsonify({'success': False, 'error': 'annee doit être entre 2000 et 2100'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'annee doit être un nombre'}), 400

    try:
        rj_filler = get_or_create_filler(session_id)

        # Update date fields
        updated = rj_filler.update_controle(vjour=vjour, mois=mois, annee=annee)

        # Fill prepare_par with auditor name
        fill_data = {'prepare_par': prepare_par}
        cells_filled = rj_filler.fill_sheet('controle', fill_data)

        save_and_store(session_id, rj_filler)

        return jsonify({
            'success': True,
            'message': f'Contrôle auto-rempli: Jour {vjour:02d}/{mois:02d}/{annee}, préparé par {prepare_par}',
            'day': vjour,
            'month': mois,
            'year': annee,
            'prepare_par': prepare_par,
            'cells_filled': cells_filled,
            'updated': updated
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/autofill-recap', methods=['POST'])
@login_required
@csrf_protect
def autofill_recap():
    """
    Auto-fill Recap sheet fields from Daily Revenue parser results.

    Expected JSON body:
    {
        "daily_revenue_data": {
            "settlements": { "cheque": value, ... },
            "balance": { "today": value, ... },
            ...
        }
    }

    Fills:
    - cheque_daily_revenu_lecture: from settlements.cheque
    - prepare_par: from session['user_name'] (logged-in auditor)
    - date: from current audit date or provided date
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 400

    data = request.get_json() or {}
    dr_data = data.get('daily_revenue_data', {})

    if not dr_data:
        return jsonify({'success': False, 'error': 'daily_revenue_data est requis'}), 400

    # Get auditor name from session
    prepare_par = session.get('user_name', 'Auditor')

    try:
        rj_filler = get_or_create_filler(session_id)
        recap_fill_data = {}

        # Extract cheque from settlements if available
        settlements = dr_data.get('settlements', {})
        if 'cheque' in settlements:
            cheque_value = settlements['cheque']
            # Convert to absolute value for display
            recap_fill_data['cheque_daily_revenu_lecture'] = abs(float(cheque_value)) if cheque_value else 0

        # Add auditor name
        recap_fill_data['prepare_par'] = prepare_par

        # Add date (Excel serial or current date)
        # For now, use current date; the RJFiller will convert to Excel serial if needed
        recap_fill_data['date'] = datetime.now().strftime('%Y-%m-%d')

        # Fill the Recap sheet
        cells_filled = rj_filler.fill_sheet('Recap', recap_fill_data)

        save_and_store(session_id, rj_filler)

        filled_fields = []
        if 'cheque_daily_revenu_lecture' in recap_fill_data:
            filled_fields.append(f"Cheque: ${recap_fill_data['cheque_daily_revenu_lecture']:.2f}")
        if 'prepare_par' in recap_fill_data:
            filled_fields.append(f"Préparé par: {recap_fill_data['prepare_par']}")
        if 'date' in recap_fill_data:
            filled_fields.append(f"Date: {recap_fill_data['date']}")

        return jsonify({
            'success': True,
            'message': f'Recap auto-rempli: {len(filled_fields)} champ(s)',
            'cells_filled': cells_filled,
            'filled_fields': filled_fields,
            'data': recap_fill_data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_fill_bp.route('/api/rj/deposit', methods=['POST'])
@login_required
@csrf_protect
def update_deposit():
    """
    Update the Deposit tab with a verified amount.
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json()
    amount = data.get('amount')
    date_str = data.get('date')  # Optional, will use today if missing

    if not amount:
        return jsonify({'success': False, 'error': 'Amount is required'}), 400

    # Validate amount
    amount_val, err = validate_amount(amount)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')

    try:
        rj_filler = get_or_create_filler(session_id)
        success = rj_filler.update_deposit(date_str, amount_val)

        if success:
            save_and_store(session_id, rj_filler)
            return jsonify({
                'success': True,
                'message': f'Dépôt de {amount_val}$ ajouté pour le {date_str}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update deposit sheet'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
