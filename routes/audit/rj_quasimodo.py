"""
RJ Quasimodo blueprint - handles auto card reconciliation.
"""

from flask import Blueprint, request, jsonify, session
from utils.auth_decorators import login_required
from .rj_core import RJ_FILES, get_session_id


rj_quasimodo_bp = Blueprint('rj_quasimodo', __name__)


@rj_quasimodo_bp.route('/api/rj/quasimodo', methods=['POST'])
@login_required
def quasimodo_reconcile():
    """
    Auto-calculate Quasimodo card reconciliation from current RJ file.
    Reads transelect + geac_ux and compares terminal vs bank by card type.
    """
    from utils.quasimodo import QuasimodoReconciler

    session_id = get_session_id()
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ chargé'}), 400

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)

        reconciler = QuasimodoReconciler()
        reconciler.load_from_rj(file_bytes)
        result = reconciler.reconcile()

        return jsonify({
            'success': True,
            'reconciliation': result,
            'message_fr': reconciler.get_status_message_fr(),
            'report_text': reconciler.to_printable_report()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_quasimodo_bp.route('/api/rj/quasimodo/file', methods=['POST'])
@login_required
def quasimodo_from_file():
    """
    Parse an uploaded Quasimodo .xls file (Moneris/POS report) and reconcile
    against the GEAC bank settlements from the current RJ.

    Returns the H19 balance check first (formatted to 2 decimals per Excel format),
    then per-card reconciliation vs GEAC cash out.
    """
    from utils.quasimodo import QuasimodoReconciler

    q_file = request.files.get('file')
    if not q_file:
        return jsonify({'success': False, 'error': 'Fichier Quasimodo (.xls) requis'}), 400

    session_id = get_session_id()
    has_rj = session_id in RJ_FILES

    try:
        reconciler = QuasimodoReconciler()
        q_result = reconciler.load_from_quasimodo_file(q_file.read())

        if 'error' in q_result:
            return jsonify({'success': False, 'error': q_result['error']}), 400

        response = {
            'success': True,
            'h19_balanced': q_result.get('h19_balanced'),
            'h19_rounded': q_result.get('h19_rounded'),
            'h19_raw': q_result.get('h19_raw'),
            'h19_message_fr': (
                '✓ Quasimodo balancé (H19 = $0.00)'
                if q_result.get('h19_balanced')
                else f'⚠ Quasimodo NON balancé — H19 = ${q_result.get("h19_rounded", 0):.2f}'
            ),
            'terminal_totals': q_result.get('card_totals'),
            'by_source': q_result.get('by_source'),
            'date': q_result.get('date'),
        }

        # If RJ is loaded, also run reconciliation vs GEAC
        if has_rj:
            file_bytes = RJ_FILES[session_id]
            file_bytes.seek(0)
            from utils.rj_reader import RJReader
            reader = RJReader(file_bytes)
            reconciler.bank_data = reader.read_geac_cash_out()
            recon = reconciler.reconcile()
            response['reconciliation'] = recon
            response['message_fr'] = reconciler.get_status_message_fr()

        return jsonify(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@rj_quasimodo_bp.route('/api/rj/quasimodo/manual', methods=['POST'])
@login_required
def quasimodo_manual():
    """
    Calculate Quasimodo from manually provided data.

    Expected JSON:
    {
        "terminal": {"visa": 5000, "mastercard": 3000, "amex": 2000, "debit": 1000, "discover": 500},
        "bank": {"visa": 5000, "mastercard": 3000, "amex": 2000, "debit": 0, "discover": 500}
    }
    """
    from utils.quasimodo import QuasimodoReconciler

    data = request.get_json()
    if not data or 'terminal' not in data or 'bank' not in data:
        return jsonify({'success': False, 'error': 'Données terminal et banque requises'}), 400

    try:
        reconciler = QuasimodoReconciler()
        reconciler.load_manual(data['terminal'], data['bank'])
        result = reconciler.reconcile()

        return jsonify({
            'success': True,
            'reconciliation': result,
            'message_fr': reconciler.get_status_message_fr(),
            'report_text': reconciler.to_printable_report()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
