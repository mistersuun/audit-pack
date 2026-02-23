"""
RJ Quasimodo blueprint - handles auto card reconciliation.
"""

from flask import Blueprint, request, jsonify, session
from routes.checklist import login_required
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
