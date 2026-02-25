"""
Blueprint for Balances - Account balances and reconciliation tools.

Note: Legacy RJ file-based lookups (routes.rj / RJ_FILES) have been removed.
All data now comes from NightAuditSession in the database.
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, timedelta
from database.models import db, DailyReport, CashReconciliation, MonthEndChecklist, NightAuditSession
from routes.checklist import login_required

balances_bp = Blueprint('balances', __name__)


def _get_today_session():
    """Get today's NightAuditSession from the database (if any)."""
    today = datetime.now().date()
    return NightAuditSession.query.filter_by(audit_date=today).first()


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
    """Get current day's balance information from NightAuditSession or DailyReport."""
    nas = _get_today_session()

    if nas:
        # Pull from NightAuditSession (new system)
        data = nas.to_dict()
        ar_balance = data.get('geac_daily_rev', {}).get('balance_today', 0) or 0
        return jsonify({
            'success': True,
            'source': 'night_audit_session',
            'accounts': {
                'ar_balance': ar_balance,
                'ar_previous': 0,
                'guest_ledger': 0,
                'city_ledger': 0,
            },
            'verification': {
                'expected': 0,
                'actual': ar_balance,
                'difference': 0,
                'is_balanced': True
            }
        })

    # Fall back to DailyReport
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
            'ar_balance': 0, 'ar_previous': 0,
            'guest_ledger': 0, 'city_ledger': 0,
        },
        'verification': {
            'expected': 0, 'actual': 0, 'difference': 0, 'is_balanced': True
        }
    })


# ==============================================================================
# CASH RECONCILIATION
# ==============================================================================

@balances_bp.route('/api/balances/reconciliation/cash')
@login_required
def cash_reconciliation():
    """Get cash reconciliation data from NightAuditSession."""
    nas = _get_today_session()
    system_data = {'lightspeed': 0, 'positouch': 0, 'total': 0}

    if nas:
        system_data = {
            'lightspeed': nas.cash_ls_lecture or 0,
            'positouch': nas.cash_pos_lecture or 0,
            'total': (nas.deposit_cdn or 0),
        }

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
    """Submit cash count for reconciliation."""
    data = request.get_json() or {}
    counted = data.get('counted', 0)
    notes = data.get('notes', '')

    # Get system total from NightAuditSession
    nas = _get_today_session()
    system_total = (nas.deposit_cdn or 0) if nas else 0

    variance = counted - system_total

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
    """Get X20/Master Balance data from NightAuditSession jour fields."""
    nas = _get_today_session()

    if not nas:
        return jsonify({
            'success': False,
            'error': 'Aucune session RJ pour aujourd\'hui'
        }), 400

    data = nas.to_dict()
    rooms = data.get('jour_room_revenue', 0) or 0
    fb = data.get('jour_total_fb', 0) or 0
    other = data.get('jour_total_other', 0) or 0
    total = rooms + fb + other

    return jsonify({
        'success': True,
        'day': nas.audit_date.day if nas.audit_date else datetime.now().day,
        'master_balance': {
            'rooms': rooms,
            'fb': fb,
            'other': other,
            'total': total,
        },
        'x20': {
            'debit': 0,
            'credit': 0,
            'balance': 0,
        },
        'is_balanced': True
    })


# ==============================================================================
# MONTH END
# ==============================================================================

@balances_bp.route('/api/balances/month-end')
@login_required
def month_end_summary():
    """Get month-end summary and checklist."""
    today = datetime.now()
    first_day = today.replace(day=1)

    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    reports = DailyReport.query.filter(
        DailyReport.date >= first_day,
        DailyReport.date <= today
    ).all()

    total_revenue = sum(r.revenue_total for r in reports)
    total_deposits = sum((r.deposit_cdn or 0) + (r.deposit_us or 0) for r in reports)
    total_variance = sum(r.variance or 0 for r in reports)

    checklist = MonthEndChecklist.query.filter_by(
        year=today.year, month=today.month
    ).all()

    if not checklist:
        default_tasks = [
            'Vérifier toutes les variances du mois',
            'Réconcilier les dépôts bancaires',
            'Vérifier les balances AR',
            'Exporter le rapport mensuel',
            'Archiver les fichiers RJ',
        ]
        for task in default_tasks:
            item = MonthEndChecklist(
                year=today.year, month=today.month, task_name=task
            )
            db.session.add(item)
        db.session.commit()
        checklist = MonthEndChecklist.query.filter_by(
            year=today.year, month=today.month
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
    """Update a month-end checklist item."""
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
    """Get reconciliation history."""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now().date() - timedelta(days=days)

    records = CashReconciliation.query.filter(
        CashReconciliation.date >= start_date
    ).order_by(CashReconciliation.date.desc()).all()

    return jsonify({
        'success': True,
        'records': [r.to_dict() for r in records]
    })
