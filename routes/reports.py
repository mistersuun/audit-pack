"""
Blueprint for Reports - Analytics and reporting functionality.
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, timedelta
from database.models import db, DailyReport, VarianceRecord
from routes.checklist import login_required

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def reports_page():
    """Display the Reports page."""
    return render_template('reports.html')


# ==============================================================================
# DAILY SUMMARY
# ==============================================================================

@reports_bp.route('/api/reports/daily-summary')
@login_required
def daily_summary():
    """
    Get summary for current day from RJ file or database.

    Returns:
        {
            'date': '2026-01-18',
            'revenue': { 'comptant': 0, 'cartes': 0, 'cheques': 0, 'total': 0 },
            'deposits': { 'cdn': 0, 'us': 0, 'total': 0 },
            'variance': 0,
            'dueback_total': 0
        }
    """
    # Try to get from RJ file first
    from routes.rj import RJ_FILES
    from utils.rj_reader import RJReader

    session_id = session.get('user_session_id', 'default')

    if session_id in RJ_FILES:
        try:
            file_bytes = RJ_FILES[session_id]
            file_bytes.seek(0)
            reader = RJReader(file_bytes)

            # Read data from various sheets
            controle = reader.read_controle()
            recap = reader.read_recap() if hasattr(reader, 'read_recap') else {}

            current_day = controle.get('jour', datetime.now().day)

            return jsonify({
                'success': True,
                'source': 'rj_file',
                'date': f"{controle.get('annee', 2026)}-{controle.get('mois', 1):02d}-{current_day:02d}",
                'day': current_day,
                'revenue': {
                    'comptant': recap.get('comptant_total', 0) or 0,
                    'cartes': recap.get('cartes_total', 0) or 0,
                    'cheques': recap.get('cheque_total', 0) or 0,
                    'total': recap.get('total', 0) or 0,
                },
                'deposits': {
                    'cdn': recap.get('depot_cdn', 0) or 0,
                    'us': recap.get('depot_us', 0) or 0,
                    'total': (recap.get('depot_cdn', 0) or 0) + (recap.get('depot_us', 0) or 0),
                },
                'variance': recap.get('variance', 0) or 0,
                'dueback_total': recap.get('dueback', 0) or 0,
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
            **report.to_dict()
        })

    # No data available
    return jsonify({
        'success': True,
        'source': 'none',
        'date': today.isoformat(),
        'revenue': {'comptant': 0, 'cartes': 0, 'cheques': 0, 'total': 0},
        'deposits': {'cdn': 0, 'us': 0, 'total': 0},
        'variance': 0,
        'dueback_total': 0,
    })


@reports_bp.route('/api/reports/daily-comparison')
@login_required
def daily_comparison():
    """
    Compare today vs yesterday.

    Returns:
        {
            'today': {...},
            'yesterday': {...},
            'changes': {
                'revenue': { 'value': 100, 'percent': 5.2 },
                'deposits': { 'value': -50, 'percent': -2.1 }
            }
        }
    """
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    today_report = DailyReport.query.filter_by(date=today).first()
    yesterday_report = DailyReport.query.filter_by(date=yesterday).first()

    def calc_change(current, previous):
        if previous and previous != 0:
            return {
                'value': current - previous,
                'percent': ((current - previous) / abs(previous)) * 100
            }
        return {'value': current, 'percent': 0}

    today_data = today_report.to_dict() if today_report else None
    yesterday_data = yesterday_report.to_dict() if yesterday_report else None

    changes = {}
    if today_data and yesterday_data:
        changes = {
            'revenue': calc_change(
                today_data['revenue']['total'],
                yesterday_data['revenue']['total']
            ),
            'deposits': calc_change(
                today_data['deposits']['total'],
                yesterday_data['deposits']['total']
            ),
            'variance': calc_change(
                today_data['variance'],
                yesterday_data['variance']
            ),
        }

    return jsonify({
        'success': True,
        'today': today_data,
        'yesterday': yesterday_data,
        'changes': changes
    })


# ==============================================================================
# TRENDS
# ==============================================================================

@reports_bp.route('/api/reports/trends')
@login_required
def get_trends():
    """
    Get trend data for charts.

    Query params:
        period: 7 or 30 (days)

    Returns:
        {
            'labels': ['01/01', '02/01', ...],
            'datasets': {
                'revenue': [100, 150, ...],
                'deposits': [80, 120, ...],
                'variance': [0, -5, ...],
                'dueback': [50, 30, ...]
            }
        }
    """
    period = request.args.get('period', '7', type=int)
    if period not in [7, 30]:
        period = 7

    start_date = datetime.now().date() - timedelta(days=period)

    reports = DailyReport.query.filter(
        DailyReport.date >= start_date
    ).order_by(DailyReport.date).all()

    return jsonify({
        'success': True,
        'period': period,
        'labels': [r.date.strftime('%d/%m') for r in reports],
        'datasets': {
            'revenue': [r.revenue_total for r in reports],
            'deposits': [r.deposit_cdn + r.deposit_us for r in reports],
            'variance': [r.variance for r in reports],
            'dueback': [r.dueback_total for r in reports],
        }
    })


# ==============================================================================
# VARIANCES
# ==============================================================================

@reports_bp.route('/api/reports/variances')
@login_required
def get_variances():
    """
    Get variance records with filters.

    Query params:
        start: start date (YYYY-MM-DD)
        end: end date (YYYY-MM-DD)
        receptionist: filter by receptionist name

    Returns:
        {
            'records': [...],
            'summary': {
                'total_variance': 0,
                'alert_count': 0,
                'by_receptionist': {...}
            }
        }
    """
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    receptionist = request.args.get('receptionist')

    query = VarianceRecord.query

    if start_date:
        query = query.filter(VarianceRecord.date >= start_date)
    if end_date:
        query = query.filter(VarianceRecord.date <= end_date)
    if receptionist:
        query = query.filter(VarianceRecord.receptionist == receptionist)

    records = query.order_by(VarianceRecord.date.desc()).limit(100).all()

    # Calculate summary
    total_variance = sum(r.variance for r in records)
    alert_count = sum(1 for r in records if r.is_alert)

    # Group by receptionist
    by_receptionist = {}
    for r in records:
        if r.receptionist not in by_receptionist:
            by_receptionist[r.receptionist] = {'count': 0, 'total': 0}
        by_receptionist[r.receptionist]['count'] += 1
        by_receptionist[r.receptionist]['total'] += r.variance

    return jsonify({
        'success': True,
        'records': [r.to_dict() for r in records],
        'summary': {
            'total_variance': total_variance,
            'alert_count': alert_count,
            'by_receptionist': by_receptionist
        }
    })


@reports_bp.route('/api/reports/variances/by-receptionist')
@login_required
def variances_by_receptionist():
    """Get variance summary grouped by receptionist."""
    from sqlalchemy import func

    results = db.session.query(
        VarianceRecord.receptionist,
        func.count(VarianceRecord.id).label('count'),
        func.sum(VarianceRecord.variance).label('total'),
        func.avg(VarianceRecord.variance).label('average')
    ).group_by(VarianceRecord.receptionist).all()

    return jsonify({
        'success': True,
        'data': [{
            'name': r.receptionist,
            'count': r.count,
            'total': float(r.total) if r.total else 0,
            'average': float(r.average) if r.average else 0
        } for r in results]
    })


# ==============================================================================
# CREDIT CARDS
# ==============================================================================

@reports_bp.route('/api/reports/credit-cards')
@login_required
def credit_card_report():
    """
    Get credit card breakdown from current RJ.

    Returns:
        {
            'by_type': { 'visa': 0, 'mastercard': 0, 'amex': 0, 'debit': 0 },
            'by_source': { 'terminal': 0, 'fusebox': 0, 'positouch': 0 },
            'reconciliation': { 'difference': 0, 'is_balanced': true }
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

        transelect = reader.read_transelect() if hasattr(reader, 'read_transelect') else {}

        # Calculate totals by card type
        visa_total = transelect.get('visa_total', 0) or 0
        master_total = transelect.get('master_total', 0) or 0
        amex_total = transelect.get('amex_total', 0) or 0
        debit_total = transelect.get('debit_total', 0) or 0

        terminal_total = transelect.get('terminal_total', 0) or 0
        fusebox_total = transelect.get('fusebox_total', 0) or 0

        return jsonify({
            'success': True,
            'by_type': {
                'visa': visa_total,
                'mastercard': master_total,
                'amex': amex_total,
                'debit': debit_total,
            },
            'by_source': {
                'terminal': terminal_total,
                'fusebox': fusebox_total,
                'positouch': transelect.get('positouch_total', 0) or 0,
            },
            'reconciliation': {
                'terminal_total': terminal_total,
                'fusebox_total': fusebox_total,
                'difference': terminal_total - fusebox_total,
                'is_balanced': abs(terminal_total - fusebox_total) < 0.01
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==============================================================================
# SAVE DAILY REPORT
# ==============================================================================

@reports_bp.route('/api/reports/save-daily', methods=['POST'])
@login_required
def save_daily_report():
    """
    Save current day's data to database for historical tracking.

    Request body (optional - will read from RJ if not provided):
        {
            'date': '2026-01-18',
            'revenue_comptant': 0,
            'revenue_cartes': 0,
            'revenue_cheques': 0,
            'deposit_cdn': 0,
            'deposit_us': 0,
            'variance': 0,
            'dueback_total': 0,
            'notes': ''
        }
    """
    data = request.get_json() or {}

    # Determine date
    if 'date' in data:
        report_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    else:
        report_date = datetime.now().date()

    # Check if report exists
    report = DailyReport.query.filter_by(date=report_date).first()

    if not report:
        report = DailyReport(date=report_date)
        db.session.add(report)

    # Update fields
    if 'revenue_comptant' in data:
        report.revenue_comptant = data['revenue_comptant']
    if 'revenue_cartes' in data:
        report.revenue_cartes = data['revenue_cartes']
    if 'revenue_cheques' in data:
        report.revenue_cheques = data['revenue_cheques']
    if 'deposit_cdn' in data:
        report.deposit_cdn = data['deposit_cdn']
    if 'deposit_us' in data:
        report.deposit_us = data['deposit_us']
    if 'variance' in data:
        report.variance = data['variance']
    if 'dueback_total' in data:
        report.dueback_total = data['dueback_total']
    if 'notes' in data:
        report.notes = data['notes']

    # Calculate total
    report.revenue_total = (
        (report.revenue_comptant or 0) +
        (report.revenue_cartes or 0) +
        (report.revenue_cheques or 0)
    )

    # Set auditor
    report.auditor_name = session.get('user_name', 'Unknown')

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Rapport du {report_date} sauvegardé',
        'report': report.to_dict()
    })


# ==============================================================================
# RECEPTIONIST LIST (for dropdowns)
# ==============================================================================

@reports_bp.route('/api/reports/receptionists')
@login_required
def get_receptionists():
    """Get list of unique receptionists from variance records."""
    receptionists = db.session.query(
        VarianceRecord.receptionist
    ).distinct().all()

    return jsonify({
        'success': True,
        'receptionists': [r.receptionist for r in receptionists]
    })
