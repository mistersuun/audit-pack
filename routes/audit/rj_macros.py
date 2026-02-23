"""
RJ Macros blueprint - handles reset, sync, and macro operations.
"""

from flask import Blueprint, request, jsonify, session
import io
import logging
from routes.checklist import login_required
from utils.rj_filler import RJFiller
from utils.rj_reader import RJReader
from .rj_core import RJ_FILES, get_session_id, get_or_create_filler, save_and_store, _RJ_FILLER_CACHE


from utils.csrf import csrf_protect

logger = logging.getLogger(__name__)
rj_macros_bp = Blueprint('rj_macros', __name__)


@rj_macros_bp.route('/api/rj/reset', methods=['POST'])
@login_required
@csrf_protect
def reset_rj_tabs():
    """
    Reset (Clear) specific tabs in the RJ file for a new day.
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    try:
        rj_filler = get_or_create_filler(session_id)
        cleared_count = rj_filler.reset_tabs()

        save_and_store(session_id, rj_filler)

        return jsonify({
            'success': True,
            'message': f'Onglets réinitialisés avec succès ({cleared_count} cellules effacées)',
            'cleared_count': cleared_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_macros_bp.route('/api/rj/reset/<sheet_name>', methods=['POST'])
@login_required
@csrf_protect
def reset_single_sheet(sheet_name):
    """
    Reset (Clear) a single sheet in the RJ file.

    Args:
        sheet_name: Name of sheet to reset ('Recap', 'transelect', 'geac_ux', 'depot')
    """
    session_id = get_session_id()

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    # Map friendly names to actual sheet names
    sheet_name_map = {
        'recap': 'Recap',
        'transelect': 'transelect',
        'geac': 'geac_ux',
        'geac_ux': 'geac_ux',
        'depot': 'depot',
        'daily': 'daily',
    }

    actual_sheet_name = sheet_name_map.get(sheet_name.lower())
    if not actual_sheet_name:
        return jsonify({
            'success': False,
            'error': f'Unknown sheet: {sheet_name}. Valid sheets: recap, transelect, geac, depot'
        }), 400

    try:
        rj_filler = get_or_create_filler(session_id)
        cleared_count = rj_filler.reset_single_tab(actual_sheet_name)

        save_and_store(session_id, rj_filler)

        # Friendly names for messages
        friendly_names = {
            'Recap': 'Recap',
            'transelect': 'Transelect',
            'geac_ux': 'GEAC',
            'depot': 'Dépôt',
            'daily': 'Daily'
        }

        return jsonify({
            'success': True,
            'message': f'{friendly_names.get(actual_sheet_name, actual_sheet_name)} effacé ({cleared_count} cellules)',
            'sheet': actual_sheet_name,
            'cleared_count': cleared_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_macros_bp.route('/api/rj/sync', methods=['POST'])
@login_required
@csrf_protect
def sync_duback_setd():
    """
    Sync DueBack amounts to SetD for the current day.
    """
    session_id = get_session_id()

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
        except Exception as e:
            logger.warning(f"Could not read day from controle: {e}")

    if not day:
        return jsonify({'success': False, 'error': 'Day could not be determined. Please provide day in request.'}), 400

    try:
        rj_filler = get_or_create_filler(session_id)
        updates = rj_filler.sync_duback_to_setd(day)

        save_and_store(session_id, rj_filler)

        return jsonify({
            'success': True,
            'message': f'Sync terminé: {updates} valeurs mises à jour dans SetD pour le jour {day}',
            'updates': updates
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_macros_bp.route('/api/rj/macro/envoie-jour', methods=['POST'])
@login_required
@csrf_protect
def macro_envoie_dans_jour():
    """
    Execute envoie_dans_jour macro - Copy Recap H19:N19 to jour ar_[day].

    Request body (optional):
        {
            "day": 23  # Day of the month (1-31). If not provided, reads from controle.
        }

    Returns:
        {
            "success": true,
            "message": "Recap envoyé dans jour pour le jour 23",
            "data": { "day": 23, "recap_values": [...], "target_row": 26, "columns": "BU:CA" }
        }
    """
    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json() or {}
    day = data.get('day')

    try:
        rj_filler = get_or_create_filler(session_id)
        result = rj_filler.envoie_dans_jour(day=day)

        save_and_store(session_id, rj_filler)

        return jsonify({
            'success': True,
            'message': f"Recap envoyé dans jour pour le jour {result['day']}",
            'data': result
        })

    except Exception as e:
        logger.exception(f"Error executing envoie_dans_jour macro")
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_macros_bp.route('/api/rj/macro/calcul-carte', methods=['POST'])
@login_required
@csrf_protect
def macro_calcul_carte():
    """
    Execute calcul_carte macro - Copy transelect card totals to jour CC_[day].

    Request body (optional):
        {
            "day": 23  # Day of the month (1-31). If not provided, reads from controle.
        }

    Returns:
        {
            "success": true,
            "message": "Cartes calculées pour le jour 23",
            "data": { "day": 23, "card_totals": [...], "target_row": 26, "start_column": "BF" }
        }
    """
    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json() or {}
    day = data.get('day')

    try:
        rj_filler = get_or_create_filler(session_id)
        result = rj_filler.calcul_carte(day=day)

        save_and_store(session_id, rj_filler)

        return jsonify({
            'success': True,
            'message': f"Cartes calculées pour le jour {result['day']}",
            'data': result
        })

    except Exception as e:
        logger.exception(f"Error executing calcul_carte macro")
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_macros_bp.route('/api/rj/recap/send-to-jour', methods=['POST'])
@login_required
@csrf_protect
def send_recap_to_jour():
    """
    Copy Recap summary (row 19, columns H-N) to 'jour' sheet for a specific day.

    Request body:
        {
            "day": 23  # Day of the month (1-31)
        }

    Returns:
        {
            "success": true,
            "message": "Recap envoyé dans RJ pour le jour 23",
            "recap_data": {...},  # Data that was copied
            "jour_data": {...}    # Resulting data in jour
        }
    """
    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json() or {}
    try:
        day = int(data.get('day', 0))
    except (ValueError, TypeError):
        day = 0

    if not day or not 1 <= day <= 31:
        return jsonify({'success': False, 'error': 'Day must be between 1-31'}), 400

    try:
        from utils.rj_writer import copy_recap_to_jour, get_recap_summary, get_jour_day_data

        # Get current RJ
        rj_bytes = RJ_FILES[session_id]

        # Get recap data before copy (for display)
        recap_data = get_recap_summary(rj_bytes)

        # Copy Recap to jour
        updated_rj = copy_recap_to_jour(rj_bytes, day)

        # Get jour data after copy (for verification)
        jour_data = get_jour_day_data(updated_rj, day)

        # Update in session and invalidate cache
        RJ_FILES[session_id] = updated_rj
        _RJ_FILLER_CACHE.pop(session_id, None)

        return jsonify({
            'success': True,
            'message': f'Recap envoyé dans RJ pour le jour {day}',
            'recap_data': recap_data,
            'jour_data': jour_data,
            'day': day
        })

    except Exception as e:
        logger.exception(f"Error sending recap to jour")
        return jsonify({'success': False, 'error': str(e)}), 500
