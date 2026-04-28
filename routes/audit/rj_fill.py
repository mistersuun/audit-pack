"""
RJ Fill blueprint - handles sheet filling and DueBack operations.
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import io
import math
import os
import tempfile
import logging
from utils.auth_decorators import login_required
from utils.rj_filler import RJFiller
from utils.rj_reader import RJReader
from utils.rj_mapper import CELL_MAPPINGS
from utils.csrf import csrf_protect
from .rj_core import RJ_FILES, RJ_FILES_LOCK, get_session_id, get_or_create_filler, save_and_store, invalidate_rj_cache

logger = logging.getLogger(__name__)


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

    data = request.get_json() or {}

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

        # Column Z has a SUM formula — never overwrite it.
        # The formula auto-computes the total from per-receptionist cells.
        total_z = total_previous + total_current

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
        date_parts = [f"{vjour:02d}"]
        if mois:
            date_parts.append(f"{mois:02d}")
        if annee:
            date_parts.append(str(annee))
        date_str = "/".join(date_parts)

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


@rj_fill_bp.route('/api/rj/fill-all', methods=['POST'])
@login_required
@csrf_protect
def fill_all():
    """
    Fill GEAC, Transelect, and Jour sheets in one COM session.

    JSON body:
        parsed_data: {
            'daily_revenue': { ... },   # from DailyRevenueParser
            'sales_journal': { ... },    # from SalesJournalParser
            'ar_summary': { ... },       # from ARSummaryParser
            'hp_excel': { ... },         # from HPExcelParser
        }
        manual_values: { 'g4': float, 'club_lounge': float, 'deposit_on_hand': float }
        adjustments: [ { 'department': str, 'amount': float } ]
        day: int (optional, reads from controle if missing)

    Returns:
        {
            'success': true,
            'geac_cells': N,
            'transelect_cells': N,
            'jour_cells': N,
            'dc_value': float,
            'dc_balanced': bool,
            'day': int,
            'jour_values': { col_letter: value },
            'summary': { warnings, errors }
        }
    """
    from utils.geac_filler import compute_geac_data
    from utils.transelect_filler import compute_transelect_data
    from utils.jour_mapper import JourMapper
    from utils.daily_rev_jour_mapping import col_index_to_letter

    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 400

    data = request.get_json(silent=True) or {}
    parsed_data = data.get('parsed_data', {})
    manual_values = data.get('manual_values', {})
    adjustments = data.get('adjustments', [])
    day = data.get('day')
    if day is not None:
        try:
            day = int(day)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': f'Jour invalide: {day}'}), 400

    tmp_path = None
    try:
        # ---- Copy RJ bytes under lock, then release before COM work ----
        with RJ_FILES_LOCK:
            rj_bytes = RJ_FILES[session_id]
            rj_bytes.seek(0)
            raw_bytes = rj_bytes.read()
        tmp = tempfile.NamedTemporaryFile(suffix='.xls', delete=False)
        tmp.write(raw_bytes)
        tmp.close()
        tmp_path = tmp.name

        # ---- Get audit day ----
        if day is not None and (day < 1 or day > 31):
            return jsonify({'success': False, 'error': f'Jour invalide: {day}'}), 400
        if not day:
            reader = RJReader(io.BytesIO(raw_bytes))
            day = reader.get_current_audit_day()
        if not day:
            return jsonify({'success': False, 'error': f'Jour invalide: {day}'}), 400

        # ---- Compute data (pure Python, no COM) ----
        dr = parsed_data.get('daily_revenue', {})
        sj = parsed_data.get('sales_journal', {})
        ar = parsed_data.get('ar_summary', {})

        geac_data = compute_geac_data(dr, ar)
        transelect_data = compute_transelect_data(sj, dr)

        mapper = JourMapper(
            daily_rev_data=dr,
            sales_journal_data=sj,
            ar_summary_data=ar,
            hp_data=parsed_data.get('hp_excel', {}),
            market_segment_data=parsed_data.get('market_segment', {}),
            dbrs_data=parsed_data.get('dbrs', {}),
            manual_values=manual_values,
            adjustments=adjustments,
        )
        jour_values_0based = mapper.compute_all()
        summary = mapper.get_summary()

        # Convert JourMapper 0-based col indices to 1-based for COM
        jour_values_1based = {col + 1: val for col, val in jour_values_0based.items()}

        # ---- Write via COM ----
        from utils.rj_filler_com import RJFillerCOM

        with RJFillerCOM(tmp_path) as filler:
            filler.write_geac(geac_data)
            filler.write_transelect(transelect_data)

            # Force recalc so Transelect row 38 formula totals update before we read
            filler.excel.Calculate()
            import time as _time
            _time.sleep(0.3)

            # calcul_carte equivalent: read Transelect row 38 (1-based) cols A-F
            # and write to Jour BI:BN (1-based cols 61-66).
            # Transelect col → Jour col: A→BI, B→BJ, C→BK, D→BL, E→BM, F→BN
            ts = filler.wb.Sheets('transelect')
            for trans_col in range(1, 7):
                v = ts.Cells(38, trans_col).Value
                if v is not None and isinstance(v, (int, float)):
                    jour_values_1based[60 + trans_col] = v

            filler.write_jour_row(day, jour_values_1based)

            # ---- BJ auto-compensation ----
            # Transelect X24 (row 20, col 24) holds the restaurant card carry-down
            # variance. BJ (Jour col 62) carries the Discover total from
            # Transelect (row 38, col 2, written above) AND absorbs X24 to drive
            # DC toward $0. We must PRESERVE the Discover total — write the
            # formula as `={discover}+{x24}` instead of overwriting BJ.
            # Sign heuristic: pick whichever of +X24 / -X24 minimises |DC| after
            # the write. Because we preserve Discover (the only change is +chosen),
            # the actual post-write DC equals dc_before_bj + chosen_x24.
            # PANNE LIEN HOTEL is intentionally excluded — it lands in AK via DR
            # chambres and must never be double-compensated here.
            js = filler.wb.Sheets('jour')
            jour_row = day + 2  # Day 1 → row 3
            x24 = ts.Cells(20, 24).Value or 0.0
            filler.excel.Calculate()
            _time.sleep(0.2)
            dc_before_bj = float(js.Cells(jour_row, 3).Value or 0.0)
            existing_bj = float(js.Cells(jour_row, 62).Value or 0.0)
            logger.info(
                'fill_all BJ: X24=%.2f  DC_before=%.2f  Discover_in_BJ=%.2f',
                x24, dc_before_bj, existing_bj,
            )

            if x24:
                if abs(dc_before_bj + x24) < abs(dc_before_bj - x24):
                    chosen_x24 = x24
                else:
                    chosen_x24 = -x24
                if chosen_x24 >= 0:
                    bj_formula = f'={existing_bj:.2f}+{chosen_x24:.2f}'
                else:
                    bj_formula = f'={existing_bj:.2f}-{abs(chosen_x24):.2f}'
                logger.info(
                    'fill_all BJ: writing col62 formula %s (chosen X24=%.2f, preserves Discover=%.2f)',
                    bj_formula, chosen_x24, existing_bj,
                )
                js.Cells(jour_row, 62).Formula = bj_formula
                filler.excel.Calculate()
                _time.sleep(0.2)

            dc_value = float(js.Cells(jour_row, 3).Value or 0.0)

        # ---- Read file back to memory ----
        # Note: concurrent fill_all calls for the same session could race here.
        # This is safe in practice (single-auditor workflow, Flask dev server is
        # single-threaded). For production WSGI with threads, consider per-session locks.
        with open(tmp_path, 'rb') as f:
            output = io.BytesIO(f.read())
        with RJ_FILES_LOCK:
            RJ_FILES[session_id] = output
        invalidate_rj_cache(session_id)

        # ---- Build display values ----
        values_display = {}
        for col_idx, val in jour_values_0based.items():
            letter = col_index_to_letter(int(col_idx))
            values_display[letter] = round(val, 2) if isinstance(val, (int, float)) else val

        return jsonify({
            'success': True,
            'geac_cells': len(geac_data),
            'transelect_cells': len(transelect_data),
            'jour_cells': len(jour_values_1based),
            'dc_value': round(dc_value, 2),
            'dc_balanced': abs(dc_value) < 0.01,
            'day': day,
            'jour_values': values_display,
            'summary': summary,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        # Clean up temp files
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            backup_path = tmp_path + '.bak.xls'
            try:
                os.unlink(backup_path)
            except OSError:
                pass


@rj_fill_bp.route('/api/rj/autofill-recap-from-docs', methods=['POST'])
@login_required
@csrf_protect
def autofill_recap_from_docs():
    """Parse House Totals + Débourse 90.2 + (optional) Cashier Cashout,
    fill the Recap sheet, then run envoie_dans_jour so BU:CA land in Jour.

    Multipart form fields (all optional but at least one must be present):
        house_totals:   HOUSE_TOTALS.txt  -> B7 (Comptant Positouch), B11 (Remb Gratuité)
        debourse:       90_2.pdf          -> B12 (Remb Client), B16 (Due Back Réception)
        cashier_cashout CASHIER_CASHOUT.pdf (currently informational only)

    Optional form fields:
        day:              target day 1-31 (read from controle if missing)
        surplus_deficit:  manual B19 value (physical cash vs expected)
        argent_recu:      manual B24 value (cash actually in the box)

    Returns the values pushed to Jour BU:CA and the resulting DC.
    """
    from utils.parsers.house_totals_parser import HouseTotalsParser
    from utils.parsers.debourse_parser import DebourseParser
    from utils.rj_filler_com import RJFillerCOM

    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 400

    # --- Gather files from multipart form ---
    ht_file = request.files.get('house_totals')
    deb_file = request.files.get('debourse')
    _ = request.files.get('cashier_cashout')  # parsed upstream for GEAC; unused here

    dr_file_present = request.files.get('daily_revenue')
    if not ht_file and not deb_file and not dr_file_present:
        return jsonify({
            'success': False,
            'error': 'Au moins un fichier requis (house_totals, debourse ou daily_revenue)'
        }), 400

    # --- Parse inputs ---
    recap_inputs = {}
    parsed_summary = []

    if ht_file:
        ht = HouseTotalsParser(ht_file.read(), filename=ht_file.filename)
        ht.parse()
        if not ht.extracted_data:
            return jsonify({'success': False, 'error': 'House Totals parsing failed'}), 400
        comptant = ht.extracted_data.get('comptant_positouch')
        remb_grat = ht.extracted_data.get('remb_gratuite')
        if comptant is not None:
            recap_inputs['B7'] = float(comptant)
            parsed_summary.append(f'Comptant Positouch (B7)={comptant:.2f}')
        if remb_grat is not None:
            recap_inputs['B11'] = float(remb_grat)  # parser returns signed (negative)
            parsed_summary.append(f'Remb Gratuité (B11)={remb_grat:.2f}')

    if deb_file:
        deb = DebourseParser(deb_file.read(), filename=deb_file.filename)
        deb.parse()
        if not deb.extracted_data:
            return jsonify({'success': False, 'error': 'Débourse 90.2 parsing failed'}), 400
        deb_total = deb.extracted_data.get('debourse_total')
        if deb_total is not None:
            # B12 (Remb Client) is entered as NEGATIVE — it reduces the total.
            # B16 (Due Back Réception) is entered as POSITIVE because E16=-D16
            # inverts the sign so L19 ends up negative.
            # B17 (Due Back N/B) is sourced from DR `due_back_nourriture` (below),
            # NOT from the débourse total.
            neg_val = -abs(float(deb_total))
            pos_val = abs(float(deb_total))
            recap_inputs['B12'] = neg_val
            recap_inputs['B16'] = pos_val   # E16==-D16 inverts → L19 negative
            parsed_summary.append(
                f'Remb Client (B12)={neg_val:.2f}  Due Back Réception (B16)={pos_val:.2f}'
            )

    # B17 Due Back N/B comes from Daily Revenue — comptabilite_nonrev.due_back_nourriture
    # DR stores it as negative (e.g. -519.30); B17 needs the positive magnitude
    # (Recap E17=-D17 will invert it back to negative for L19).
    dr_file = request.files.get('daily_revenue')
    if dr_file:
        from utils.parsers.daily_revenue_parser import DailyRevenueParser
        dr = DailyRevenueParser(dr_file.read(), filename=dr_file.filename)
        dr.parse()
        dbn = (dr.extracted_data or {}).get('non_revenue', {}) \
            .get('comptabilite_nonrev', {}).get('due_back_nourriture')
        if dbn is not None and abs(float(dbn)) > 0.005:
            b17_val = abs(float(dbn))
            recap_inputs['B17'] = b17_val
            parsed_summary.append(f'Due Back N/B (B17)={b17_val:.2f} (from DR)')

    # --- Optional manual values ---
    sd = request.form.get('surplus_deficit')
    if sd not in (None, ''):
        try:
            # B19 (Surplus/déficit) is signed: négatif = surplus, positif = déficit
            # (matches the UI hint and rj_native.py:1002).
            sd_val = float(sd)
            recap_inputs['B19'] = sd_val
            parsed_summary.append(f'Surplus/Déficit (B19)={sd_val:.2f}')
        except ValueError:
            return jsonify({'success': False, 'error': 'surplus_deficit invalide'}), 400

    ar_recu_raw = request.form.get('argent_recu')
    # Defer the argent_recu back-solve until after we open the workbook — it
    # needs the existing B6 (LightSpeed cash) and B8 (Chèque A/R) values, which
    # may have been written by the rj_native pipeline on a prior request.
    if ar_recu_raw not in (None, ''):
        try:
            ar_recu = float(ar_recu_raw)
        except ValueError:
            return jsonify({'success': False, 'error': 'argent_recu invalide'}), 400
    else:
        ar_recu = None

    # --- Determine target day ---
    day = request.form.get('day')
    if day:
        try:
            day = int(day)
        except ValueError:
            return jsonify({'success': False, 'error': f'Jour invalide: {day}'}), 400
    else:
        day = None

    # --- Copy RJ bytes under lock, then release before COM ---
    tmp_path = None
    try:
        with RJ_FILES_LOCK:
            rj_bytes = RJ_FILES[session_id]
            rj_bytes.seek(0)
            raw_bytes = rj_bytes.read()

        if not day:
            reader = RJReader(io.BytesIO(raw_bytes))
            day = reader.get_current_audit_day()
        if not day or day < 1 or day > 31:
            return jsonify({'success': False, 'error': f'Jour invalide: {day}'}), 400

        tmp = tempfile.NamedTemporaryFile(suffix='.xls', delete=False)
        tmp.write(raw_bytes)
        tmp.close()
        tmp_path = tmp.name

        # --- Write to Recap, run envoie_dans_jour equivalent, return DC ---
        with RJFillerCOM(tmp_path) as filler:
            recap_sheet = filler.wb.Sheets('Recap')

            # If argent_recu was provided, back-solve B9 (Chèque Daily Revenu).
            # B24 is `=SUM(D10,E22)` and cannot be written directly. Solve:
            #   B24 = D10 + E22 = (B6+B7+B8+B9) + (B16+B17+B19)
            #   → B9 = argent_recu - B6 - B7 - B8 - (B16+B17+B19)
            # B6 (LightSpeed cash) and B8 (Chèque A/R) may already be non-zero
            # from the rj_native pipeline (rj_native.py:993-997). Reading them
            # from the workbook prevents silent overshoot by exactly B6+B8.
            if ar_recu is not None:
                # Use recap_inputs values when present (about to be written),
                # otherwise read existing workbook values. Avoid the .get(default)
                # idiom — its default expression evaluates eagerly, which would
                # do unnecessary COM reads.
                b6 = float(recap_sheet.Cells(6, 2).Value or 0)
                b7 = (recap_inputs['B7'] if 'B7' in recap_inputs
                      else float(recap_sheet.Cells(7, 2).Value or 0))
                b8 = float(recap_sheet.Cells(8, 2).Value or 0)
                b16 = (recap_inputs['B16'] if 'B16' in recap_inputs
                       else float(recap_sheet.Cells(16, 2).Value or 0))
                b17 = float(recap_sheet.Cells(17, 2).Value or 0)  # always manual
                b19 = (recap_inputs['B19'] if 'B19' in recap_inputs
                       else float(recap_sheet.Cells(19, 2).Value or 0))
                e22_contribution = b16 + b17 + b19
                b9 = ar_recu - b6 - b7 - b8 - e22_contribution
                if abs(b9) > 0.005:
                    recap_inputs['B9'] = round(b9, 2)
                    parsed_summary.append(
                        f'Chèque Daily Rev (B9)={b9:.2f}  '
                        f'[ar_recu={ar_recu:.2f} - B6={b6:.2f} - B7={b7:.2f} '
                        f'- B8={b8:.2f} - E22={e22_contribution:.2f}]'
                    )
                parsed_summary.append(
                    f'argent_recu={ar_recu:.2f} → B24 formula will compute to {ar_recu:.2f}'
                )

            # 1. Fill Recap cells (HasFormula guard protects existing formulas)
            for cell_ref, value in recap_inputs.items():
                # Parse B7 -> row=7 col=2, B11 -> row=11 col=2, etc.
                col_letter = cell_ref[0]  # always B in our map
                row_num = int(cell_ref[1:])
                col_num = ord(col_letter.upper()) - ord('A') + 1
                filler.write_sheet_cell('Recap', row_num, col_num, value)

            # 2. Force recalc so Recap formulas update H19:N19
            filler.excel.Calculate()
            import time as _time
            _time.sleep(0.3)

            # 3. Read Recap H19:N19 (1-based: row 19, cols 8-14)
            recap_row_values = []
            for col_1based in range(8, 15):  # H=8, I=9, J=10, K=11, L=12, M=13, N=14
                v = recap_sheet.Cells(19, col_1based).Value
                recap_row_values.append(v if isinstance(v, (int, float)) else 0)

            # 4. Write to Jour BU:CA (1-based cols 73-79) for target day
            jour_row = day + 2  # Jour day=1 -> row 3, day=23 -> row 25
            jour_sheet = filler.wb.Sheets('jour')
            for offset, val in enumerate(recap_row_values):
                jour_col = 73 + offset  # BU=73, BV=74, ..., CA=79
                cell = jour_sheet.Cells(jour_row, jour_col)
                if not cell.HasFormula:
                    cell.Value = val

            # 5. Recalc, read DC
            filler.excel.Calculate()
            _time.sleep(0.3)
            dc_value = jour_sheet.Cells(jour_row, 3).Value

        # --- Save back to in-memory store ---
        # Same race caveat as fill_all (rj_fill.py:993-995): RJ_FILES_LOCK is
        # released for the COM session, so two concurrent calls on the same
        # session race here (last writer wins). Safe in practice (single-auditor
        # workflow, Flask dev server is single-threaded). For production WSGI
        # with threads, wrap the copy/COM/readback block with a per-session lock.
        with open(tmp_path, 'rb') as f:
            output = io.BytesIO(f.read())
        with RJ_FILES_LOCK:
            RJ_FILES[session_id] = output
        invalidate_rj_cache(session_id)

        return jsonify({
            'success': True,
            'day': day,
            'recap_filled': recap_inputs,
            'recap_h19_n19': recap_row_values,
            'jour_bu_ca_row': jour_row,
            'dc_value': round(dc_value, 2) if isinstance(dc_value, (int, float)) else None,
            # Match fill_all's threshold so the UI banner verdict is consistent
            # whether or not the recap-side chain runs.
            'dc_balanced': isinstance(dc_value, (int, float)) and abs(dc_value) < 0.01,
            'parsed': parsed_summary,
        })

    except Exception as e:
        import traceback
        logger.exception('autofill_recap_from_docs failed')
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            # RJFillerCOM.__enter__ creates a sibling .bak.xls; its __exit__
            # never deletes it, so we must clean up here (mirror fill_all).
            backup_path = tmp_path + '.bak.xls'
            try:
                os.unlink(backup_path)
            except OSError:
                pass
