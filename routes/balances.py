"""
Blueprint for Balances - Account balances and reconciliation tools.
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, timedelta
from database.models import db, DailyReport, CashReconciliation, MonthEndChecklist
from routes.checklist import login_required

balances_bp = Blueprint('balances', __name__)


@balances_bp.route('/balances')
@login_required
def balances_page():
    """Display the Balances page."""
    return render_template('balances.html')


# ==============================================================================
# DAILY BALANCE
# ==============================================================================

@balances_bp.route('/api/balances/daily')
@login_required
def daily_balance():
    """
    Get current day's balance information.

    Returns:
        {
            'accounts': {
                'ar_balance': 0,
                'ar_previous': 0,
                'guest_ledger': 0,
                'city_ledger': 0
            },
            'verification': {
                'expected': 0,
                'actual': 0,
                'difference': 0,
                'is_balanced': true
            }
        }
    """
    from routes.rj import RJ_FILES
    from utils.rj_reader import RJReader

    session_id = session.get('user_session_id', 'default')

    if session_id in RJ_FILES:
        try:
            file_bytes = RJ_FILES[session_id]
            file_bytes.seek(0)
            reader = RJReader(file_bytes)

            # Read GEAC data
            geac = reader.read_geac_ux() if hasattr(reader, 'read_geac_ux') else {}

            ar_balance = geac.get('balance_today', 0) or 0
            ar_previous = geac.get('balance_previous', 0) or 0
            guest_ledger = geac.get('balance_today_guest', 0) or 0
            new_balance = geac.get('new_balance', 0) or 0

            # Calculate expected balance
            expected = ar_previous + (geac.get('daily_charges', 0) or 0) - (geac.get('daily_payments', 0) or 0)

            return jsonify({
                'success': True,
                'source': 'rj_file',
                'accounts': {
                    'ar_balance': ar_balance,
                    'ar_previous': ar_previous,
                    'guest_ledger': guest_ledger,
                    'city_ledger': geac.get('city_ledger', 0) or 0,
                },
                'verification': {
                    'expected': expected,
                    'actual': new_balance,
                    'difference': expected - new_balance,
                    'is_balanced': abs(expected - new_balance) < 0.01
                }
            })
        except Exception as e:
            pass  # Fall through to database

    # Fall back to database
    today = datetime.now().date()
    report = DailyReport.query.filter_by(date=today).first()

    if report:
        return jsonify({
            'success': True,
            'source': 'database',
            'accounts': {
                'ar_balance': report.ar_balance,
                'ar_previous': 0,
                'guest_ledger': report.guest_ledger,
                'city_ledger': report.city_ledger,
            },
            'verification': {
                'expected': 0,
                'actual': report.ar_balance,
                'difference': 0,
                'is_balanced': True
            }
        })

    return jsonify({
        'success': True,
        'source': 'none',
        'accounts': {
            'ar_balance': 0,
            'ar_previous': 0,
            'guest_ledger': 0,
            'city_ledger': 0,
        },
        'verification': {
            'expected': 0,
            'actual': 0,
            'difference': 0,
            'is_balanced': True
        }
    })


# ==============================================================================
# CASH RECONCILIATION
# ==============================================================================

@balances_bp.route('/api/balances/reconciliation/cash')
@login_required
def cash_reconciliation():
    """
    Get cash reconciliation data.

    Returns:
        {
            'system': { 'lightspeed': 0, 'positouch': 0, 'total': 0 },
            'counted': null,
            'variance': null,
            'status': 'pending'
        }
    """
    from routes.rj import RJ_FILES
    from utils.rj_reader import RJReader

    session_id = session.get('user_session_id', 'default')

    system_data = {'lightspeed': 0, 'positouch': 0, 'total': 0}

    if session_id in RJ_FILES:
        try:
            file_bytes = RJ_FILES[session_id]
            file_bytes.seek(0)
            reader = RJReader(file_bytes)

            recap = reader.read_recap() if hasattr(reader, 'read_recap') else {}

            system_data = {
                'lightspeed': recap.get('comptant_lightspeed', 0) or 0,
                'positouch': recap.get('comptant_positouch', 0) or 0,
                'total': recap.get('comptant_total', 0) or 0,
            }
        except:
            pass

    # Check if there's already a reconciliation for today
    today = datetime.now().date()
    existing = CashReconciliation.query.filter_by(date=today).order_by(
        CashReconciliation.created_at.desc()
    ).first()

    if existing:
        return jsonify({
            'success': True,
            'system': system_data,
            'counted': existing.counted_total,
            'variance': existing.variance,
            'status': 'balanced' if abs(existing.variance) < 0.01 else 'variance',
            'record_id': existing.id
        })

    return jsonify({
        'success': True,
        'system': system_data,
        'counted': None,
        'variance': None,
        'status': 'pending'
    })


@balances_bp.route('/api/balances/reconciliation/cash', methods=['POST'])
@login_required
def submit_cash_count():
    """
    Submit cash count for reconciliation.

    Request body:
        {
            'counted': 1234.56,
            'notes': 'optional notes'
        }

    Returns:
        {
            'success': true,
            'system': 1200.00,
            'counted': 1234.56,
            'variance': 34.56,
            'is_balanced': false
        }
    """
    data = request.get_json() or {}
    counted = data.get('counted', 0)
    notes = data.get('notes', '')

    # Get system total
    from routes.rj import RJ_FILES
    from utils.rj_reader import RJReader

    session_id = session.get('user_session_id', 'default')
    system_total = 0

    if session_id in RJ_FILES:
        try:
            file_bytes = RJ_FILES[session_id]
            file_bytes.seek(0)
            reader = RJReader(file_bytes)
            recap = reader.read_recap() if hasattr(reader, 'read_recap') else {}
            system_total = recap.get('comptant_total', 0) or 0
        except:
            pass

    variance = counted - system_total

    # Save reconciliation record
    record = CashReconciliation(
        date=datetime.now().date(),
        system_total=system_total,
        counted_total=counted,
        variance=variance,
        auditor=session.get('user_name', 'Unknown'),
        notes=notes
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'success': True,
        'system': system_total,
        'counted': counted,
        'variance': variance,
        'is_balanced': abs(variance) < 0.01,
        'record_id': record.id
    })


# ==============================================================================
# CASH CALCULATOR (just returns denominations config)
# ==============================================================================

@balances_bp.route('/api/balances/denominations')
@login_required
def get_denominations():
    """Get Canadian denominations for cash calculator."""
    return jsonify({
        'success': True,
        'denominations': {
            'bills': [
                {'value': 100, 'label': '$100'},
                {'value': 50, 'label': '$50'},
                {'value': 20, 'label': '$20'},
                {'value': 10, 'label': '$10'},
                {'value': 5, 'label': '$5'},
            ],
            'coins': [
                {'value': 2, 'label': '$2 (Toonie)'},
                {'value': 1, 'label': '$1 (Loonie)'},
                {'value': 0.25, 'label': '$0.25'},
                {'value': 0.10, 'label': '$0.10'},
                {'value': 0.05, 'label': '$0.05'},
            ]
        }
    })


# ==============================================================================
# X20 / MASTER BALANCE
# ==============================================================================

@balances_bp.route('/api/balances/x20')
@login_required
def x20_balance():
    """
    Get X20/Master Balance data from jour sheet.

    Returns:
        {
            'day': 18,
            'master_balance': {...},
            'x20': { 'debit': 0, 'credit': 0, 'balance': 0 },
            'is_balanced': true
        }
    """
    from routes.rj import RJ_FILES
    from utils.rj_reader import RJReader

    session_id = session.get('user_session_id', 'default')

    if session_id not in RJ_FILES:
        return jsonify({
            'success': False,
            'error': 'No RJ file uploaded'
        }), 400

    try:
        file_bytes = RJ_FILES[session_id]
        file_bytes.seek(0)
        reader = RJReader(file_bytes)

        controle = reader.read_controle()
        current_day = controle.get('jour', datetime.now().day)

        # Read jour sheet if available
        # This would need to be implemented in RJReader
        jour_data = {}

        return jsonify({
            'success': True,
            'day': current_day,
            'master_balance': {
                'rooms': jour_data.get('rooms', 0),
                'fb': jour_data.get('fb', 0),
                'other': jour_data.get('other', 0),
                'total': jour_data.get('total', 0),
            },
            'x20': {
                'debit': jour_data.get('x20_debit', 0),
                'credit': jour_data.get('x20_credit', 0),
                'balance': jour_data.get('x20_balance', 0),
            },
            'is_balanced': abs(jour_data.get('x20_balance', 0)) < 0.01
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==============================================================================
# MONTH END
# ==============================================================================

@balances_bp.route('/api/balances/month-end')
@login_required
def month_end_summary():
    """
    Get month-end summary and checklist.

    Returns:
        {
            'month': 'January 2026',
            'days_completed': 18,
            'days_remaining': 13,
            'totals': {...},
            'averages': {...},
            'checklist': [...]
        }
    """
    today = datetime.now()
    first_day = today.replace(day=1)

    # Calculate last day of month
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # Get reports for current month
    reports = DailyReport.query.filter(
        DailyReport.date >= first_day,
        DailyReport.date <= today
    ).all()

    # Calculate totals
    total_revenue = sum(r.revenue_total for r in reports)
    total_deposits = sum((r.deposit_cdn or 0) + (r.deposit_us or 0) for r in reports)
    total_variance = sum(r.variance or 0 for r in reports)

    # Get or create checklist items
    checklist = MonthEndChecklist.query.filter_by(
        year=today.year,
        month=today.month
    ).all()

    if not checklist:
        # Create default checklist items
        default_tasks = [
            'Vérifier toutes les variances du mois',
            'Réconcilier les dépôts bancaires',
            'Vérifier les balances AR',
            'Exporter le rapport mensuel',
            'Archiver les fichiers RJ',
        ]
        for task in default_tasks:
            item = MonthEndChecklist(
                year=today.year,
                month=today.month,
                task_name=task
            )
            db.session.add(item)
        db.session.commit()

        checklist = MonthEndChecklist.query.filter_by(
            year=today.year,
            month=today.month
        ).all()

    return jsonify({
        'success': True,
        'month': today.strftime('%B %Y'),
        'year': today.year,
        'month_num': today.month,
        'days_completed': len(reports),
        'days_remaining': last_day.day - today.day,
        'totals': {
            'revenue': total_revenue,
            'deposits': total_deposits,
            'variance': total_variance,
        },
        'averages': {
            'daily_revenue': total_revenue / len(reports) if reports else 0,
            'daily_deposits': total_deposits / len(reports) if reports else 0,
        },
        'checklist': [item.to_dict() for item in checklist]
    })


@balances_bp.route('/api/balances/month-end/checklist/<int:item_id>', methods=['POST'])
@login_required
def update_checklist_item(item_id):
    """
    Update a month-end checklist item.

    Request body:
        {
            'completed': true,
            'notes': 'optional notes'
        }
    """
    data = request.get_json() or {}

    item = MonthEndChecklist.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'error': 'Item not found'}), 404

    item.completed = data.get('completed', False)
    item.notes = data.get('notes', item.notes)

    if item.completed:
        item.completed_at = datetime.utcnow()
        item.completed_by = session.get('user_name', 'Unknown')
    else:
        item.completed_at = None
        item.completed_by = None

    db.session.commit()

    return jsonify({
        'success': True,
        'item': item.to_dict()
    })


# ==============================================================================
# RECONCILIATION HISTORY
# ==============================================================================

@balances_bp.route('/api/balances/reconciliation/history')
@login_required
def reconciliation_history():
    """
    Get reconciliation history.

    Query params:
        days: number of days to look back (default 30)

    Returns:
        {
            'records': [...]
        }
    """
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now().date() - timedelta(days=days)

    records = CashReconciliation.query.filter(
        CashReconciliation.date >= start_date
    ).order_by(CashReconciliation.date.desc()).all()

    return jsonify({
        'success': True,
        'records': [r.to_dict() for r in records]
    })
