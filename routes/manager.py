"""
Manager/GSM Portal — Executive Business Intelligence Dashboard.

Separate from the auditor interface. Designed for management presentations,
revenue optimization analysis, and strategic decision-making.
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, timedelta, date
from database.models import (db, DailyJourMetrics, DailyReconciliation,
                              JournalEntry, DepositVariance, TipDistribution,
                              HPDepartmentSales, DueBack, DepartmentLabor)
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

manager_bp = Blueprint('manager', __name__)


def manager_required(f):
    """Access control for manager portal."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            from flask import redirect, url_for
            return redirect(url_for('auth_v2.login'))
        return f(*args, **kwargs)
    return decorated_function


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _get_historical(start=None, end=None):
    """Get HistoricalAnalytics for a date range."""
    from utils.analytics import HistoricalAnalytics

    if not start or not end:
        max_date = db.session.query(func.max(DailyJourMetrics.date)).scalar()
        if not max_date:
            return None
        min_date = db.session.query(func.min(DailyJourMetrics.date)).scalar()
        start = start or min_date
        end = end or max_date

    h = HistoricalAnalytics(start, end)
    return h if h.has_data() else None


# ==============================================================================
# PAGES
# ==============================================================================

@manager_bp.route('/manager')
@manager_required
def manager_page():
    return render_template('manager.html')


# ==============================================================================
# API — All data for the executive dashboard
# ==============================================================================

@manager_bp.route('/api/manager/overview')
@manager_required
def overview():
    """
    Complete executive overview — single API call that returns everything
    the dashboard needs, organized by section.
    """
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))

    h = _get_historical(start, end)
    if not h:
        return jsonify({'has_data': False})

    # Get all analytics
    kpis = h.get_executive_kpis()
    advanced = h.get_advanced_kpis()
    dow = h.get_dow_analysis()
    opps = h.get_revenue_opportunities()
    trend = h.get_revenue_trend()
    fb = h.get_fb_analytics()
    rooms = h.get_room_analytics()
    payments = h.get_payment_analytics()

    # Monthly summary
    monthly = h.get_monthly_summary() if hasattr(h, 'get_monthly_summary') else []

    # YoY comparison
    yoy = None
    if hasattr(h, 'get_yoy_comparison'):
        try:
            yoy = h.get_yoy_comparison()
        except Exception:
            pass

    # Data status
    from utils.jour_importer import JourImporter
    data_status = JourImporter.get_data_status()

    # Deep insights
    from utils.insights_engine import InsightsEngine
    insights = InsightsEngine(h.metrics).get_all_insights()

    return jsonify({
        'has_data': True,
        'period': {
            'start': h.start_date.isoformat(),
            'end': h.end_date.isoformat(),
            'days': kpis.get('days_count', 0),
        },
        'kpis': kpis,
        'advanced': advanced,
        'dow': dow,
        'opportunities': opps,
        'trend': trend,
        'fb': fb,
        'rooms': rooms,
        'payments': payments,
        'monthly': monthly,
        'yoy': yoy,
        'data_status': data_status,
        'insights': insights,
    })


@manager_bp.route('/api/manager/yearly-comparison')
@manager_required
def yearly_comparison():
    """Year-over-year comparison for all available years."""
    years_data = db.session.query(
        DailyJourMetrics.year,
        func.count(DailyJourMetrics.id).label('days'),
        func.avg(DailyJourMetrics.adr).label('avg_adr'),
        func.avg(DailyJourMetrics.occupancy_rate).label('avg_occ'),
        func.avg(DailyJourMetrics.revpar).label('avg_revpar'),
        func.sum(DailyJourMetrics.total_revenue).label('total_rev'),
        func.sum(DailyJourMetrics.room_revenue).label('room_rev'),
        func.sum(DailyJourMetrics.fb_revenue).label('fb_rev'),
        func.sum(DailyJourMetrics.total_rooms_sold).label('rooms_sold'),
        func.sum(DailyJourMetrics.nb_clients).label('guests'),
        func.avg(DailyJourMetrics.trevpar).label('avg_trevpar'),
        func.sum(DailyJourMetrics.total_cards).label('card_payments'),
        func.sum(DailyJourMetrics.rooms_hors_usage).label('oos_rooms'),
        func.sum(DailyJourMetrics.rooms_comp).label('comp_rooms'),
    ).group_by(DailyJourMetrics.year).order_by(DailyJourMetrics.year).all()

    result = []
    for y in years_data:
        fb_per_guest = y.fb_rev / y.guests if y.guests > 0 else 0
        result.append({
            'year': y.year,
            'days': y.days,
            'avg_adr': round(y.avg_adr, 2),
            'avg_occ': round(y.avg_occ, 1),
            'avg_revpar': round(y.avg_revpar, 2),
            'avg_trevpar': round(y.avg_trevpar, 2),
            'total_revenue': round(y.total_rev, 0),
            'room_revenue': round(y.room_rev, 0),
            'fb_revenue': round(y.fb_rev, 0),
            'rooms_sold': int(y.rooms_sold),
            'guests': int(y.guests),
            'fb_per_guest': round(fb_per_guest, 2),
            'card_payments': round(y.card_payments, 0),
            'oos_rooms': int(y.oos_rooms),
            'comp_rooms': int(y.comp_rooms),
        })

    return jsonify({'years': result})


# ==============================================================================
# API — Monthly Expenses & GOPPAR
# ==============================================================================

@manager_bp.route('/api/manager/expenses', methods=['GET'])
@manager_required
def get_expenses():
    """Get all monthly expense records."""
    from database.models import MonthlyExpense
    expenses = MonthlyExpense.query.order_by(
        MonthlyExpense.year.desc(), MonthlyExpense.month.desc()
    ).all()
    return jsonify({'expenses': [e.to_dict() for e in expenses]})


@manager_bp.route('/api/manager/expenses', methods=['POST'])
@manager_required
def save_expense():
    """Save or update a monthly expense record."""
    from database.models import MonthlyExpense
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    year = data.get('year')
    month = data.get('month')
    if not year or not month:
        return jsonify({'error': 'year and month required'}), 400

    # Upsert
    exp = MonthlyExpense.query.filter_by(year=year, month=month).first()
    if not exp:
        exp = MonthlyExpense(year=year, month=month)
        db.session.add(exp)

    # Set all fields
    for field in ['labor_rooms', 'labor_fb', 'labor_admin', 'labor_maintenance',
                  'labor_other', 'utilities', 'supplies', 'maintenance_costs',
                  'marketing', 'insurance', 'franchise_fees', 'technology',
                  'other_expenses', 'notes']:
        if field in data:
            setattr(exp, field, data[field])

    exp.calculate_totals()
    db.session.commit()
    return jsonify({'success': True, 'expense': exp.to_dict()})


@manager_bp.route('/api/manager/goppar')
@manager_required
def goppar():
    """
    Calculate GOPPAR and profitability metrics by combining
    revenue data (DailyJourMetrics) with expense data (MonthlyExpense).
    """
    from database.models import MonthlyExpense

    # Get all expenses
    expenses = MonthlyExpense.query.all()
    if not expenses:
        return jsonify({'has_data': False, 'message': 'No expense data entered yet'})

    # Build expense lookup by year-month
    exp_map = {}
    for e in expenses:
        key = (e.year, e.month)
        exp_map[key] = e

    # Get revenue data for matching months
    results = []
    total_revenue = 0
    total_expenses = 0
    total_rooms_available = 0
    total_rooms_sold = 0
    total_days = 0

    for (year, month), exp in sorted(exp_map.items()):
        # Get daily metrics for this month
        metrics = DailyJourMetrics.query.filter(
            DailyJourMetrics.year == year,
            DailyJourMetrics.month == month,
            DailyJourMetrics.total_revenue > 0
        ).all()

        if not metrics:
            continue

        days = len(metrics)
        rev = sum(m.total_revenue for m in metrics)
        room_rev = sum(m.room_revenue for m in metrics)
        fb_rev = sum(m.fb_revenue for m in metrics)
        rooms_avail = sum(m.rooms_available for m in metrics)
        rooms_sold = sum(m.total_rooms_sold for m in metrics)
        avg_occ = sum(m.occupancy_rate for m in metrics) / days
        avg_adr = sum(m.adr for m in metrics) / days

        gop = rev - exp.total_expenses
        goppar = gop / rooms_avail if rooms_avail > 0 else 0
        margin = (gop / rev * 100) if rev > 0 else 0

        # Labor metrics
        lcpor = exp.labor_total / rooms_sold if rooms_sold > 0 else 0
        labor_pct = (exp.labor_total / rev * 100) if rev > 0 else 0

        # Break-even
        # Approximate: fixed costs / (ADR * rooms_available_per_day * (1 - var_cost_ratio))
        # Simplified: break_even_occ = total_expenses / (rev / avg_occ * 100) * 100 if avg_occ > 0
        break_even_occ = (exp.total_expenses / (rev / avg_occ * 100) * 100) if avg_occ > 0 and rev > 0 else 0

        months_fr = {1:'Jan',2:'Fév',3:'Mar',4:'Avr',5:'Mai',6:'Jun',
                     7:'Jul',8:'Aoû',9:'Sep',10:'Oct',11:'Nov',12:'Déc'}

        results.append({
            'year': year, 'month': month,
            'label': f"{months_fr.get(month, month)} {year}",
            'days': days,
            'total_revenue': round(rev, 0),
            'room_revenue': round(room_rev, 0),
            'fb_revenue': round(fb_rev, 0),
            'total_expenses': round(exp.total_expenses, 0),
            'labor_total': round(exp.labor_total, 0),
            'gop': round(gop, 0),
            'goppar': round(goppar, 2),
            'margin_pct': round(margin, 1),
            'avg_occ': round(avg_occ, 1),
            'avg_adr': round(avg_adr, 2),
            'lcpor': round(lcpor, 2),
            'labor_pct_revenue': round(labor_pct, 1),
            'break_even_occ': round(break_even_occ, 1),
            'rooms_sold': rooms_sold,
            'rooms_available': rooms_avail,
        })

        total_revenue += rev
        total_expenses += exp.total_expenses
        total_rooms_available += rooms_avail
        total_rooms_sold += rooms_sold
        total_days += days

    # Summary
    total_gop = total_revenue - total_expenses
    avg_goppar = total_gop / total_rooms_available if total_rooms_available > 0 else 0
    avg_margin = (total_gop / total_revenue * 100) if total_revenue > 0 else 0
    avg_lcpor = sum(r['labor_total'] for r in results) / total_rooms_sold if total_rooms_sold > 0 else 0

    return jsonify({
        'has_data': True,
        'monthly': results,
        'summary': {
            'total_revenue': round(total_revenue, 0),
            'total_expenses': round(total_expenses, 0),
            'total_gop': round(total_gop, 0),
            'avg_goppar': round(avg_goppar, 2),
            'avg_margin_pct': round(avg_margin, 1),
            'avg_lcpor': round(avg_lcpor, 2),
            'months_covered': len(results),
            'total_days': total_days,
        }
    })


# ==============================================================================
# API — Labor Analytics
# ==============================================================================

@manager_bp.route('/api/manager/labor', methods=['GET'])
@manager_required
def get_labor():
    """
    Get all labor data, optionally filtered by year.
    Returns department-level labor costs with budget analysis.
    """
    from database.models import DepartmentLabor

    year = request.args.get('year', type=int)

    query = DepartmentLabor.query
    if year:
        query = query.filter_by(year=year)

    labor_records = query.order_by(
        DepartmentLabor.year.desc(),
        DepartmentLabor.month.desc(),
        DepartmentLabor.department
    ).all()

    if not labor_records:
        return jsonify({'has_data': False, 'message': 'No labor data available'})

    # Group by year-month for monthly summaries
    monthly_summaries = {}
    for record in labor_records:
        key = (record.year, record.month)
        if key not in monthly_summaries:
            monthly_summaries[key] = {
                'year': record.year,
                'month': record.month,
                'total_labor_cost': 0,
                'total_hours': 0,
                'headcount': 0,
                'departments': []
            }
        monthly_summaries[key]['total_labor_cost'] += record.total_labor_cost
        monthly_summaries[key]['total_hours'] += record.total_hours
        monthly_summaries[key]['headcount'] += record.headcount
        monthly_summaries[key]['departments'].append(record.to_dict())

    # Calculate LCPOR (Labor Cost Per Occupied Room)
    results = []
    for (yr, mo), summary in sorted(monthly_summaries.items(), reverse=True):
        # Get rooms sold for this month from DailyJourMetrics
        metrics = db.session.query(
            func.sum(DailyJourMetrics.total_rooms_sold).label('rooms_sold'),
            func.sum(DailyJourMetrics.total_revenue).label('revenue')
        ).filter(
            DailyJourMetrics.year == yr,
            DailyJourMetrics.month == mo
        ).first()

        rooms_sold = metrics.rooms_sold or 0
        revenue = metrics.revenue or 0
        lcpor = summary['total_labor_cost'] / rooms_sold if rooms_sold > 0 else 0
        labor_pct = (summary['total_labor_cost'] / revenue * 100) if revenue > 0 else 0

        results.append({
            'year': yr,
            'month': mo,
            'total_labor_cost': round(summary['total_labor_cost'], 2),
            'total_hours': round(summary['total_hours'], 1),
            'headcount': summary['headcount'],
            'rooms_sold': int(rooms_sold),
            'revenue': round(revenue, 2),
            'lcpor': round(lcpor, 2),
            'labor_pct_revenue': round(labor_pct, 1),
            'departments': summary['departments']
        })

    return jsonify({'has_data': True, 'monthly': results})


@manager_bp.route('/api/manager/labor', methods=['POST'])
@manager_required
def save_labor():
    """
    Upsert a department labor record (year, month, department as unique key).
    """
    from database.models import DepartmentLabor

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    year = data.get('year')
    month = data.get('month')
    department = data.get('department')
    if not all([year, month, department]):
        return jsonify({'error': 'year, month, and department required'}), 400

    # Upsert
    labor = DepartmentLabor.query.filter_by(
        year=year, month=month, department=department
    ).first()
    if not labor:
        labor = DepartmentLabor(year=year, month=month, department=department)
        db.session.add(labor)

    # Set all fields
    for field in ['regular_hours', 'overtime_hours', 'regular_wages', 'overtime_wages',
                  'benefits', 'headcount', 'tips_collected', 'tips_distributed',
                  'budget_hours', 'budget_cost', 'notes']:
        if field in data:
            setattr(labor, field, data[field])

    labor.calculate_totals()
    db.session.commit()
    return jsonify({'success': True, 'labor': labor.to_dict()})


@manager_bp.route('/api/manager/labor-analytics', methods=['GET'])
@manager_required
def labor_analytics():
    """
    Comprehensive labor analytics dashboard combining labor data with revenue/occupancy data.
    Returns complete department efficiency analysis, monthly trends, and staffing patterns.
    """
    from database.models import DepartmentLabor

    year = request.args.get('year', type=int)

    query = DepartmentLabor.query
    if year:
        query = query.filter_by(year=year)

    labor_records = query.order_by(
        DepartmentLabor.year.desc(),
        DepartmentLabor.month.desc(),
        DepartmentLabor.department
    ).all()

    if not labor_records:
        return jsonify({'has_data': False, 'message': 'No labor data available'})

    # ───── DEPARTMENT-LEVEL AGGREGATION ─────
    dept_stats = {}
    monthly_by_dept = {}  # For trending

    for record in labor_records:
        dept = record.department
        key = (record.year, record.month)

        if dept not in dept_stats:
            dept_stats[dept] = {
                'department': dept,
                'total_cost': 0,
                'total_hours': 0,
                'regular_hours': 0,
                'overtime_hours': 0,
                'total_headcount': 0,
                'total_tips': 0,
                'months_count': 0,
                'budget_cost': 0,
                'budget_hours': 0,
                'records': []
            }

        if (dept, key) not in monthly_by_dept:
            monthly_by_dept[(dept, key)] = {
                'year': record.year,
                'month': record.month,
                'department': dept,
                'hours': 0,
                'cost': 0,
                'ot_hours': 0,
                'ot_cost': 0,
            }

        # Aggregate
        dept_stats[dept]['total_cost'] += record.total_labor_cost
        dept_stats[dept]['total_hours'] += record.total_hours
        dept_stats[dept]['regular_hours'] += record.regular_hours
        dept_stats[dept]['overtime_hours'] += record.overtime_hours
        dept_stats[dept]['total_headcount'] += record.headcount
        dept_stats[dept]['total_tips'] += record.tips_collected + record.tips_distributed
        dept_stats[dept]['budget_cost'] += record.budget_cost
        dept_stats[dept]['budget_hours'] += record.budget_hours
        dept_stats[dept]['months_count'] += 1
        dept_stats[dept]['records'].append(record.to_dict())

        # Monthly detail
        monthly_by_dept[(dept, key)]['hours'] += record.total_hours
        monthly_by_dept[(dept, key)]['cost'] += record.total_labor_cost
        monthly_by_dept[(dept, key)]['ot_hours'] += record.overtime_hours
        monthly_by_dept[(dept, key)]['ot_cost'] += record.overtime_wages

    # ───── DEPARTMENT EFFICIENCY METRICS ─────
    # Determine the years covered by labor records to scope revenue query
    labor_years = set(r.year for r in labor_records)

    analytics = []
    for dept, stats in sorted(dept_stats.items()):
        # Get revenue for the same period as labor data
        revenue_metrics = db.session.query(
            func.sum(DailyJourMetrics.total_revenue).label('revenue'),
            func.sum(DailyJourMetrics.total_rooms_sold).label('rooms_sold')
        )

        if year:
            revenue_metrics = revenue_metrics.filter(DailyJourMetrics.year == year)
        elif labor_years:
            revenue_metrics = revenue_metrics.filter(DailyJourMetrics.year.in_(labor_years))

        rev_data = revenue_metrics.first()
        total_revenue = rev_data.revenue or 0
        total_rooms_sold = rev_data.rooms_sold or 0

        # Key metrics
        revenue_per_hour = total_revenue / stats['total_hours'] if stats['total_hours'] > 0 else 0
        avg_hourly_rate = stats['total_cost'] / stats['total_hours'] if stats['total_hours'] > 0 else 0
        revenue_per_employee = total_revenue / (stats['total_headcount'] / stats['months_count']) if stats['months_count'] > 0 and stats['total_headcount'] > 0 else 0

        # Overtime analysis
        overtime_pct = (stats['overtime_hours'] / stats['total_hours'] * 100) if stats['total_hours'] > 0 else 0
        overtime_cost_pct = (stats['overtime_hours'] * avg_hourly_rate * 1.5 / stats['total_cost'] * 100) if stats['total_cost'] > 0 else 0

        # Tips
        total_comp = stats['total_cost'] + stats['total_tips']
        tips_pct = (stats['total_tips'] / total_comp * 100) if total_comp > 0 else 0

        # Budget variance
        budget_var = stats['total_cost'] - stats['budget_cost']
        budget_var_pct = (budget_var / stats['budget_cost'] * 100) if stats['budget_cost'] > 0 else 0
        budget_hours_var = stats['total_hours'] - stats['budget_hours']

        # Avg headcount
        avg_headcount = stats['total_headcount'] / stats['months_count'] if stats['months_count'] > 0 else 0

        analytics.append({
            'department': dept,
            'total_labor_cost': round(stats['total_cost'], 2),
            'total_hours': round(stats['total_hours'], 1),
            'regular_hours': round(stats['regular_hours'], 1),
            'overtime_hours': round(stats['overtime_hours'], 1),
            'avg_headcount': round(avg_headcount, 1),
            'avg_hourly_rate': round(avg_hourly_rate, 2),
            'revenue_per_labor_hour': round(revenue_per_hour, 2),
            'revenue_per_employee': round(revenue_per_employee, 0),
            'overtime_pct': round(overtime_pct, 1),
            'overtime_cost_pct': round(overtime_cost_pct, 1),
            'tips_total': round(stats['total_tips'], 2),
            'tips_pct_compensation': round(tips_pct, 1),
            'budget_variance': round(budget_var, 2),
            'budget_variance_pct': round(budget_var_pct, 1),
            'budget_hours_variance': round(budget_hours_var, 1),
            'months_analyzed': stats['months_count'],
        })

    # Rank by efficiency (revenue per labor hour)
    analytics_sorted = sorted(analytics, key=lambda x: x['revenue_per_labor_hour'], reverse=True)

    # Calculate rankings
    for i, item in enumerate(analytics_sorted, 1):
        item['efficiency_rank'] = i

    # ───── MONTHLY TRENDS ─────
    monthly_summary = []
    months_fr = {1:'Jan',2:'Fév',3:'Mar',4:'Avr',5:'Mai',6:'Jun',
                 7:'Jul',8:'Aoû',9:'Sep',10:'Oct',11:'Nov',12:'Déc'}

    for (dept, (yr, mo)), data in sorted(monthly_by_dept.items()):
        rev_metrics = db.session.query(
            func.sum(DailyJourMetrics.total_revenue).label('revenue'),
            func.sum(DailyJourMetrics.total_rooms_sold).label('rooms_sold')
        ).filter(
            DailyJourMetrics.year == yr,
            DailyJourMetrics.month == mo
        ).first()

        month_revenue = rev_metrics.revenue or 0
        month_rooms = rev_metrics.rooms_sold or 0

        monthly_summary.append({
            'year': yr,
            'month': mo,
            'label': f"{months_fr.get(mo, mo)} {yr}",
            'department': dept,
            'hours': round(data['hours'], 1),
            'cost': round(data['cost'], 2),
            'ot_hours': round(data['ot_hours'], 1),
            'ot_cost': round(data['ot_cost'], 2),
            'revenue': round(month_revenue, 2),
            'rooms_sold': month_rooms,
            'labor_pct_revenue': round((data['cost'] / month_revenue * 100) if month_revenue > 0 else 0, 1),
            'lcpor': round((data['cost'] / month_rooms) if month_rooms > 0 else 0, 2),
        })

    # ───── STAFFING PATTERNS (overstaffed/understaffed) ─────
    staffing_analysis = []
    for dept in sorted(dept_stats.keys()):
        monthly_costs = []
        monthly_revenues = []

        for (d, (yr, mo)), mdata in sorted(monthly_by_dept.items()):
            if d == dept:
                monthly_costs.append(mdata['cost'])

        # Get corresponding revenues
        for (d, (yr, mo)), mdata in sorted(monthly_by_dept.items()):
            if d == dept:
                rev_m = db.session.query(
                    func.sum(DailyJourMetrics.total_revenue).label('revenue')
                ).filter(
                    DailyJourMetrics.year == yr,
                    DailyJourMetrics.month == mo
                ).first()
                monthly_revenues.append(rev_m.revenue or 0)

        # Correlation: do labor costs track with revenue?
        if len(monthly_costs) > 2 and len(monthly_revenues) > 2:
            import statistics
            if all(v > 0 for v in monthly_revenues) and all(c > 0 for c in monthly_costs):
                # Simple correlation check: cost_trend vs revenue_trend
                staffing_analysis.append({
                    'department': dept,
                    'staffing_pattern': 'flexible' if len(monthly_costs) > 1 else 'insufficient_data',
                    'avg_cost': round(sum(monthly_costs) / len(monthly_costs), 2),
                    'cost_volatility': round(statistics.stdev(monthly_costs) if len(monthly_costs) > 1 else 0, 2),
                })

    # ───── OVERALL SUMMARY ─────
    total_labor_cost = sum(a['total_labor_cost'] for a in analytics)
    total_hours = sum(a['total_hours'] for a in analytics)

    # Scope revenue queries to same years as labor data
    rooms_q = db.session.query(func.sum(DailyJourMetrics.total_rooms_sold))
    rev_q = db.session.query(func.sum(DailyJourMetrics.total_revenue))
    if year:
        rooms_q = rooms_q.filter(DailyJourMetrics.year == year)
        rev_q = rev_q.filter(DailyJourMetrics.year == year)
    elif labor_years:
        rooms_q = rooms_q.filter(DailyJourMetrics.year.in_(labor_years))
        rev_q = rev_q.filter(DailyJourMetrics.year.in_(labor_years))
    total_rooms_sold = rooms_q.first()[0] or 0
    total_revenue = rev_q.first()[0] or 0

    summary = {
        'total_departments': len(analytics),
        'total_labor_cost': round(total_labor_cost, 2),
        'total_hours': round(total_hours, 1),
        'avg_hourly_rate': round(sum(a['avg_hourly_rate'] for a in analytics) / len(analytics) if analytics else 0, 2),
        'labor_pct_revenue': round((total_labor_cost / total_revenue * 100) if total_revenue > 0 else 0, 1),
        'lcpor': round((total_labor_cost / total_rooms_sold) if total_rooms_sold > 0 else 0, 2),
        'total_overtime_hours': round(sum(a['overtime_hours'] for a in analytics), 1),
        'avg_overtime_pct': round(sum(a['overtime_pct'] for a in analytics) / len(analytics) if analytics else 0, 1),
    }

    return jsonify({
        'has_data': True,
        'analytics': analytics_sorted,
        'monthly': monthly_summary,
        'staffing': staffing_analysis,
        'summary': summary,
    })


@manager_bp.route('/api/manager/labor/efficiency', methods=['GET'])
@manager_required
def labor_efficiency():
    """
    Deep efficiency analysis: labor intensity, productivity metrics, seasonal patterns.
    Compares labor cost trends with revenue trends to identify overstaffed/understaffed periods.
    """
    from database.models import DepartmentLabor

    labor_records = DepartmentLabor.query.order_by(
        DepartmentLabor.year.desc(),
        DepartmentLabor.month.desc()
    ).all()

    if not labor_records:
        return jsonify({'has_data': False})

    # Build monthly consolidated view
    months_data = {}
    for record in labor_records:
        key = (record.year, record.month)
        if key not in months_data:
            months_data[key] = {
                'year': record.year,
                'month': record.month,
                'total_cost': 0,
                'total_hours': 0,
                'total_headcount': 0,
                'budget_cost': 0,
            }
        months_data[key]['total_cost'] += record.total_labor_cost
        months_data[key]['total_hours'] += record.total_hours
        months_data[key]['total_headcount'] += record.headcount
        months_data[key]['budget_cost'] += record.budget_cost

    # Join with revenue data
    months_fr = {1:'Jan',2:'Fév',3:'Mar',4:'Avr',5:'Mai',6:'Jun',
                 7:'Jul',8:'Aoû',9:'Sep',10:'Oct',11:'Nov',12:'Déc'}
    efficiency_data = []

    for (yr, mo), labor_data in sorted(months_data.items(), reverse=True):
        rev_metrics = db.session.query(
            func.sum(DailyJourMetrics.total_revenue).label('revenue'),
            func.sum(DailyJourMetrics.total_rooms_sold).label('rooms_sold'),
            func.count(DailyJourMetrics.id).label('days')
        ).filter(
            DailyJourMetrics.year == yr,
            DailyJourMetrics.month == mo
        ).first()

        revenue = rev_metrics.revenue or 0
        rooms_sold = rev_metrics.rooms_sold or 0
        days = rev_metrics.days or 0

        # Calculate efficiency metrics
        labor_intensity = (labor_data['total_cost'] / revenue * 100) if revenue > 0 else 0
        revenue_per_labor_hour = revenue / labor_data['total_hours'] if labor_data['total_hours'] > 0 else 0
        revenue_per_employee = revenue / labor_data['total_headcount'] if labor_data['total_headcount'] > 0 else 0
        labor_cost_per_room = labor_data['total_cost'] / rooms_sold if rooms_sold > 0 else 0

        # Budget variance
        budget_variance_pct = ((labor_data['total_cost'] - labor_data['budget_cost']) / labor_data['budget_cost'] * 100) if labor_data['budget_cost'] > 0 else 0

        # Determine staffing status
        if budget_variance_pct > 10:
            staffing_status = 'OVERSTAFFED'
        elif budget_variance_pct < -10:
            staffing_status = 'UNDERSTAFFED'
        else:
            staffing_status = 'OPTIMAL'

        efficiency_data.append({
            'year': yr,
            'month': mo,
            'label': f"{months_fr.get(mo, mo)} {yr}",
            'revenue': round(revenue, 2),
            'labor_cost': round(labor_data['total_cost'], 2),
            'labor_hours': round(labor_data['total_hours'], 1),
            'headcount': labor_data['total_headcount'],
            'labor_intensity': round(labor_intensity, 1),
            'revenue_per_labor_hour': round(revenue_per_labor_hour, 2),
            'revenue_per_employee': round(revenue_per_employee, 0),
            'labor_cost_per_room': round(labor_cost_per_room, 2),
            'budget_variance_pct': round(budget_variance_pct, 1),
            'staffing_status': staffing_status,
            'days': days,
        })

    # Calculate season patterns (high/low labor seasons)
    seasonal_data = {}
    for data in efficiency_data:
        mo = data['month']
        if mo not in seasonal_data:
            seasonal_data[mo] = []
        seasonal_data[mo].append(data)

    season_summary = []
    for month, entries in sorted(seasonal_data.items()):
        avg_intensity = sum(e['labor_intensity'] for e in entries) / len(entries)
        avg_revenue = sum(e['revenue'] for e in entries) / len(entries)

        season_summary.append({
            'month': months_fr.get(month, month),
            'avg_labor_intensity': round(avg_intensity, 1),
            'avg_revenue': round(avg_revenue, 0),
            'season_type': 'HIGH' if avg_intensity > 35 else 'LOW' if avg_intensity < 25 else 'NORMAL'
        })

    return jsonify({
        'has_data': True,
        'monthly': efficiency_data,
        'seasonal': season_summary,
        'summary': {
            'avg_labor_intensity': round(sum(e['labor_intensity'] for e in efficiency_data) / len(efficiency_data) if efficiency_data else 0, 1),
            'months_overstaffed': len([e for e in efficiency_data if e['staffing_status'] == 'OVERSTAFFED']),
            'months_understaffed': len([e for e in efficiency_data if e['staffing_status'] == 'UNDERSTAFFED']),
        }
    })


# ==============================================================================
# AUTOMATION ANALYTICS — New data sources dashboard
# ==============================================================================

@manager_bp.route('/api/manager/automation-stats')
@manager_required
def automation_stats():
    """Return comprehensive stats on all imported data sources + automation %."""
    from database.models import (DailyReconciliation, JournalEntry,
                                 DepositVariance, TipDistribution,
                                 HPDepartmentSales, DueBack, MonthlyExpense)
    try:
        counts = {
            'daily_metrics': DailyJourMetrics.query.count(),
            'reconciliations': DailyReconciliation.query.count(),
            'journal_entries': JournalEntry.query.count(),
            'deposit_variances': DepositVariance.query.count(),
            'tip_distributions': TipDistribution.query.count(),
            'hp_sales': HPDepartmentSales.query.count(),
            'due_backs': DueBack.query.count(),
            'labor_records': DepartmentLabor.query.count(),
            'expenses': MonthlyExpense.query.count(),
        }

        total_records = sum(counts.values())

        # Automation percentage calculation (46 tasks)
        automated_tasks = {
            'checklist_digital': True,           # Task 1: Digital checklist
            'rj_navigation': True,               # Task 2: RJ form navigation
            'kpi_extraction': True,              # Task 3: Auto KPI from jour
            'quasimodo_reconciliation': True,     # Task 4: Card reconciliation
            'quasimodo_file_gen': True,           # Task 5: Quasimodo .xls generation
            'ar_balance_check': True,             # Task 6: AR balance verification
            'autofill_controle': True,            # Task 7: Date/preparer autofill
            'autofill_cashout': True,             # Task 8: GEAC cashout from DR
            'autofill_recap': True,               # Task 9: Recap cheque + date
            'dueback_sync': True,                 # Task 10: DueBack → SetD sync
            'macro_envoie_jour': True,            # Task 11: Recap → jour macro
            'macro_calcul_carte': True,           # Task 12: Card → jour macro
            'bi_dashboard': True,                 # Task 13: Executive BI dashboard
            'insights_engine': True,              # Task 14: 29 analytics modules
            'narrative_story': True,              # Task 15: Data storytelling
            'staffing_optimization': True,        # Task 16: Staffing by regime
            'balance_checker': True,              # Task 17: Auto-balance correction
            'sd_import': counts['deposit_variances'] > 0,  # Task 18: SD import
            'pourboire_import': counts['tip_distributions'] > 0,  # Task 19: Tips
            'hp_import': counts['hp_sales'] > 0,  # Task 20: HP F&B
            'gl_import': counts['journal_entries'] > 0,  # Task 21: GL entries
            'recon_import': counts['reconciliations'] > 0,  # Task 22: Recon
            'labor_import': counts['labor_records'] > 0,  # Task 23: Labor
        }

        total_automatable = 46  # Total checklist tasks
        automated_count = sum(1 for v in automated_tasks.values() if v)

        # Reconciliation health
        recon_data = DailyReconciliation.query.order_by(
            DailyReconciliation.audit_date.desc()).limit(30).all()
        balanced_days = sum(1 for r in recon_data if r.is_balanced)
        recon_health = round(balanced_days / len(recon_data) * 100, 1) if recon_data else 0

        # Deposit variance summary
        from sqlalchemy import func as sqlfunc
        deposit_stats = db.session.query(
            sqlfunc.count(DepositVariance.id),
            sqlfunc.sum(sqlfunc.abs(DepositVariance.variance)),
            sqlfunc.avg(sqlfunc.abs(DepositVariance.variance))
        ).filter(DepositVariance.variance != 0).first()

        # Top tip earners
        top_tips = db.session.query(
            TipDistribution.employee_name,
            sqlfunc.sum(TipDistribution.total_sales).label('total')
        ).group_by(TipDistribution.employee_name).order_by(
            sqlfunc.sum(TipDistribution.total_sales).desc()
        ).limit(10).all()

        # HP monthly trend
        hp_monthly = db.session.query(
            HPDepartmentSales.year, HPDepartmentSales.month,
            sqlfunc.sum(HPDepartmentSales.total_sales).label('total')
        ).group_by(HPDepartmentSales.year, HPDepartmentSales.month).order_by(
            HPDepartmentSales.year, HPDepartmentSales.month
        ).all()

        # GL top accounts
        gl_top = db.session.query(
            JournalEntry.gl_code, JournalEntry.description_1,
            sqlfunc.sum(JournalEntry.amount).label('total'),
            sqlfunc.count(JournalEntry.id).label('entries')
        ).group_by(JournalEntry.gl_code, JournalEntry.description_1).order_by(
            sqlfunc.sum(JournalEntry.amount).desc()
        ).limit(15).all()

        return jsonify({
            'has_data': True,
            'data_counts': counts,
            'total_records': total_records,
            'automation': {
                'total_tasks': total_automatable,
                'automated_count': automated_count,
                'automation_pct': round(automated_count / total_automatable * 100, 1),
                'tasks': {k: v for k, v in automated_tasks.items()},
            },
            'reconciliation_health': {
                'last_30_days': len(recon_data),
                'balanced_days': balanced_days,
                'health_pct': recon_health,
            },
            'deposit_variances': {
                'total_with_variance': deposit_stats[0] or 0,
                'total_variance_amount': round(deposit_stats[1] or 0, 2),
                'avg_variance': round(deposit_stats[2] or 0, 2),
            },
            'top_tip_earners': [{'name': t[0], 'total_sales': round(t[1], 2)} for t in top_tips],
            'hp_monthly': [{'year': h[0], 'month': h[1], 'total': round(h[2], 2)} for h in hp_monthly],
            'gl_top_accounts': [{'code': g[0], 'desc': g[1], 'total': round(g[2], 2), 'entries': g[3]} for g in gl_top],
        })
    except Exception as e:
        logger.error(f"Automation stats error: {e}", exc_info=True)
        return jsonify({'has_data': False, 'error': str(e)})
