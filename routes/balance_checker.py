"""
Blueprint for Balance Checker — Upload files and auto-detect/fix imbalances.
"""

from flask import Blueprint, request, jsonify, render_template, session
from routes.checklist import login_required
import logging

logger = logging.getLogger(__name__)
balance_checker_bp = Blueprint('balance_checker', __name__)


@balance_checker_bp.route('/balance-checker')
@login_required
def balance_checker_page():
    """Display the Balance Checker page."""
    return render_template('balance_checker.html')


@balance_checker_bp.route('/api/balance-checker/analyze', methods=['POST'])
@login_required
def analyze_balance():
    """
    Upload files and run all balance checks.

    Accepts multipart form data with:
    - rj_file: The main RJ Excel file (required)
    - quasimodo_file: Quasimodo report (optional)
    - sd_file: SD deposit summary (optional)
    - sd_day: Which day sheet to read from SD (optional, default=1)
    """
    from utils.balance_checker import BalanceChecker

    checker = BalanceChecker()
    files_processed = []
    errors = []

    # Load RJ file (required)
    rj_file = request.files.get('rj_file')
    if rj_file:
        try:
            rj_bytes = rj_file.read()
            if checker.load_rj(rj_bytes):
                files_processed.append('RJ')
            else:
                errors.append('Erreur lors du chargement du fichier RJ')
        except Exception as e:
            errors.append(f'Erreur RJ: {str(e)}')
    else:
        return jsonify({'success': False, 'error': 'Fichier RJ requis'}), 400

    # Load Quasimodo file (optional)
    quasi_file = request.files.get('quasimodo_file')
    if quasi_file:
        try:
            quasi_bytes = quasi_file.read()
            if checker.load_quasimodo(quasi_bytes):
                files_processed.append('Quasimodo')
        except Exception as e:
            errors.append(f'Erreur Quasimodo: {str(e)}')

    # Load SD file (optional)
    sd_file = request.files.get('sd_file')
    if sd_file:
        try:
            sd_bytes = sd_file.read()
            sd_day = request.form.get('sd_day', 1, type=int)
            if checker.load_sd(sd_bytes, day=sd_day):
                files_processed.append('SD')
        except Exception as e:
            errors.append(f'Erreur SD: {str(e)}')

    # Run all checks
    try:
        report = checker.run_all_checks()
        report['files_processed'] = files_processed
        report['errors'] = errors
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        logger.error(f"Balance check error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@balance_checker_bp.route('/api/balance-checker/quick', methods=['POST'])
@login_required
def quick_check():
    """
    Quick balance check using the RJ file currently in memory (from the RJ module).
    No file upload needed — uses the RJ already loaded in the session.
    """
    from utils.balance_checker import BalanceChecker
    from routes.audit.rj_core import RJ_FILES

    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'Aucun fichier RJ en mémoire. Téléversez un RJ d\'abord.'}), 400

    try:
        checker = BalanceChecker()
        file_obj = RJ_FILES[session_id]
        file_obj.seek(0)
        rj_bytes = file_obj.read()
        file_obj.seek(0)

        if checker.load_rj(rj_bytes):
            report = checker.run_all_checks()
            return jsonify({'success': True, 'report': report})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'analyse du fichier RJ'}), 500
    except Exception as e:
        logger.error(f"Quick check error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
