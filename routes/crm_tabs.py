"""
CRM Tabs Blueprint — API endpoints for the 6 new CRM sub-tabs.

Provides specialized analytics endpoints for:
1. Revenue Management (ADR, RevPAR, occupancy trends)
2. F&B Intelligence (outlet trends, tips, food vs beverage)
3. Labour (staffing costs, hours, ratios)
4. Cash & Reconciliation (auditor stats, deposit trends)
5. Payments (card mix, discount costs, transaction counts)
6. P&L & Budget (variance analysis, profit margin, expense breakdown)

All endpoints support ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD params.
Default to last 12 months if no params provided.
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from datetime import datetime, timedelta, date
from database.models import (
    db, DailyJourMetrics, DailyLaborMetrics, DailyTipMetrics,
    MonthlyBudget, DailyCashRecon, DailyCardMetrics, MonthlyExpense, DepartmentLabor
)
from sqlalchemy import func, desc
import json

crm_tabs_bp = Blueprint('crm_tabs', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            from flask import redirect, url_for
            return redirect(url_for('auth_v2.login'))
        return f(*args, **kwargs)
    return decorated_function


def _parse_date(s):
    """Parse YYYY-MM-DD string to date, or None."""
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _get_date_range():
    """
    Parse start_date & end_date from request params.
    Default to last 12 months if not provided.
    Returns (start_date, end_date) tuple.
    """
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))

    if start and end:
        return start, end

    # Default: last 12 months
    end = date.today()
    start = end - timedelta(days=365)
    return start, end


def _round2(val):
    """Round to 2 decimals safely."""
    if val is None or val == '':
        return 0.0
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return 0.0


# ==============================================================================
# 1. REVENUE MANAGEMENT TAB
# ==============================================================================

@crm_tabs_bp.route('/api/crm/tabs/revenue-mgmt')
@login_required
def revenue_management():
    """
    Revenue Management analytics.
    Returns ADR by DoW, ADR by month, RevPAR trend, occupancy vs ADR scatter,
    budget vs actual, and yearly summary.
    """
    start, end = _get_date_range()

    # Query DailyJourMetrics for the period
    metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(start, end)
    ).all()

    if not metrics:
        return jsonify({
            'success': True,
            'has_data': False,
            'message': 'No data available for the selected period'
        })

    # 1. ADR by Day of Week (Mon=0, Sun=6)
    adr_by_dow = {i: {'day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][i],
                      'adr': 0, 'count': 0} for i in range(7)}
    for m in metrics:
        dow = m.date.weekday()
        adr_by_dow[dow]['adr'] += m.adr or 0
        adr_by_dow[dow]['count'] += 1

    for i in range(7):
        if adr_by_dow[i]['count'] > 0:
            adr_by_dow[i]['adr'] = _round2(adr_by_dow[i]['adr'] / adr_by_dow[i]['count'])
        del adr_by_dow[i]['count']

    # 2. ADR by Month (aggregated across years)
    adr_by_month = {i: {'month': i, 'adr': 0, 'count': 0} for i in range(1, 13)}
    for m in metrics:
        adr_by_month[m.month]['adr'] += m.adr or 0
        adr_by_month[m.month]['count'] += 1

    for i in range(1, 13):
        if adr_by_month[i]['count'] > 0:
            adr_by_month[i]['adr'] = _round2(adr_by_month[i]['adr'] / adr_by_month[i]['count'])
        del adr_by_month[i]['count']

    # 3. RevPAR Trend Monthly (last 5 years)
    revpar_trend = {}
    for m in metrics:
        key = f"{m.year}-{m.month:02d}"
        if key not in revpar_trend:
            revpar_trend[key] = {'revpar': 0, 'count': 0}
        revpar_trend[key]['revpar'] += m.revpar or 0
        revpar_trend[key]['count'] += 1

    revpar_monthly = []
    for key in sorted(revpar_trend.keys()):
        if revpar_trend[key]['count'] > 0:
            revpar_monthly.append({
                'period': key,
                'revpar': _round2(revpar_trend[key]['revpar'] / revpar_trend[key]['count'])
            })

    # 4. Occupancy vs ADR scatter plot
    occ_vs_adr = [{
        'occupancy': _round2(m.occupancy_rate),
        'adr': _round2(m.adr),
        'date': m.date.isoformat()
    } for m in metrics]

    # 5. Budget vs Actual
    budget_vs_actual = []
    budget_map = {}

    # Fetch all budgets for the date range
    budgets = MonthlyBudget.query.filter(
        db.and_(
            MonthlyBudget.year >= start.year,
            db.or_(
                MonthlyBudget.year < end.year,
                db.and_(MonthlyBudget.year == end.year, MonthlyBudget.month <= end.month)
            )
        )
    ).all()

    for b in budgets:
        key = (b.year, b.month)
        budget_map[key] = b

    # Aggregate actuals by year-month
    actuals = {}
    for m in metrics:
        key = (m.year, m.month)
        if key not in actuals:
            actuals[key] = {'room_rev': 0, 'adr': 0, 'occ': 0, 'count': 0}
        actuals[key]['room_rev'] += m.room_revenue or 0
        actuals[key]['adr'] += m.adr or 0
        actuals[key]['occ'] += m.occupancy_rate or 0
        actuals[key]['count'] += 1

    for key in sorted(set(list(budget_map.keys()) + list(actuals.keys()))):
        year, month = key
        budget = budget_map.get(key)
        actual = actuals.get(key)

        room_rev_actual = _round2((actual['room_rev'] if actual else 0))
        adr_actual = _round2((actual['adr'] / actual['count'] if actual and actual['count'] > 0 else 0))
        occ_actual = _round2((actual['occ'] / actual['count'] if actual and actual['count'] > 0 else 0))

        budget_vs_actual.append({
            'year': year,
            'month': month,
            'room_rev_actual': room_rev_actual,
            'room_rev_budget': _round2(budget.room_revenue_budget if budget else 0),
            'adr_actual': adr_actual,
            'adr_budget': _round2(budget.adr_budget if budget else 0),
            'occ_actual': occ_actual,
            'occ_budget': _round2(budget.occupancy_budget if budget else 0),
        })

    # 6. Yearly Summary
    yearly_summary = {}
    for m in metrics:
        year = m.year
        if year not in yearly_summary:
            yearly_summary[year] = {'revenue': 0, 'adr': 0, 'revpar': 0, 'occ': 0, 'count': 0}
        yearly_summary[year]['revenue'] += m.room_revenue or 0
        yearly_summary[year]['adr'] += m.adr or 0
        yearly_summary[year]['revpar'] += m.revpar or 0
        yearly_summary[year]['occ'] += m.occupancy_rate or 0
        yearly_summary[year]['count'] += 1

    yearly = []
    for year in sorted(yearly_summary.keys()):
        y = yearly_summary[year]
        yearly.append({
            'year': year,
            'revenue': _round2(y['revenue']),
            'adr': _round2(y['adr'] / y['count']),
            'revpar': _round2(y['revpar'] / y['count']),
            'occ_pct': _round2(y['occ'] / y['count']),
        })

    return jsonify({
        'success': True,
        'has_data': True,
        'adr_by_dow': list(adr_by_dow.values()),
        'adr_by_month': list(adr_by_month.values()),
        'revpar_trend_monthly': revpar_monthly,
        'occ_vs_adr_scatter': occ_vs_adr,
        'budget_vs_actual': budget_vs_actual,
        'yearly_summary': yearly,
    })


# ==============================================================================
# 2. F&B INTELLIGENCE TAB
# ==============================================================================

@crm_tabs_bp.route('/api/crm/tabs/fb-intel')
@login_required
def fb_intelligence():
    """
    F&B Intelligence analytics.
    Returns outlet trends, F&B per client, tips by department,
    and food vs beverage evolution.
    """
    start, end = _get_date_range()

    # Query DailyJourMetrics
    metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(start, end)
    ).all()

    # Query DailyTipMetrics
    tips = DailyTipMetrics.query.filter(
        DailyTipMetrics.date.between(start, end)
    ).all()

    if not metrics:
        return jsonify({'success': True, 'has_data': False})

    # 1. Outlet trend monthly
    outlets = ['cafe_link', 'piazza', 'spesa', 'room_svc', 'banquet']
    outlet_trend = {}

    for m in metrics:
        key = f"{m.year}-{m.month:02d}"
        if key not in outlet_trend:
            outlet_trend[key] = {o: 0 for o in outlets}
        outlet_trend[key]['cafe_link'] += m.cafe_link_total or 0
        outlet_trend[key]['piazza'] += m.piazza_total or 0
        outlet_trend[key]['spesa'] += m.spesa_total or 0
        outlet_trend[key]['room_svc'] += m.room_svc_total or 0
        outlet_trend[key]['banquet'] += m.banquet_total or 0

    outlet_trend_monthly = []
    for key in sorted(outlet_trend.keys()):
        outlet_trend_monthly.append({
            'period': key,
            **{o: _round2(outlet_trend[key][o]) for o in outlets}
        })

    # 2. F&B per client monthly
    fb_per_client = {}
    for m in metrics:
        key = f"{m.year}-{m.month:02d}"
        if key not in fb_per_client:
            fb_per_client[key] = {'fb': 0, 'clients': 0, 'count': 0}
        fb_per_client[key]['fb'] += m.fb_revenue or 0
        fb_per_client[key]['clients'] += m.nb_clients or 0
        fb_per_client[key]['count'] += 1

    fb_per_client_trend = []
    for key in sorted(fb_per_client.keys()):
        if fb_per_client[key]['clients'] > 0:
            per_client = _round2(fb_per_client[key]['fb'] / fb_per_client[key]['clients'])
        else:
            per_client = 0
        fb_per_client_trend.append({
            'period': key,
            'fb_per_client': per_client
        })

    # 3. Tips by department monthly
    tip_by_dept = {}
    for t in tips:
        key = f"{t.year}-{t.month:02d}-{t.department}"
        if key not in tip_by_dept:
            tip_by_dept[key] = {'brut': 0, 'net': 0, 'count': 0}
        tip_by_dept[key]['brut'] += t.tips_brut or 0
        tip_by_dept[key]['net'] += t.tips_net or 0
        tip_by_dept[key]['count'] += 1

    # Aggregate by period & department
    tip_trend = {}
    for key in tip_by_dept:
        parts = key.split('-')
        period = f"{parts[0]}-{parts[1]}"
        dept = parts[2]

        if period not in tip_trend:
            tip_trend[period] = {}

        brut = _round2(tip_by_dept[key]['brut'] / tip_by_dept[key]['count'])
        net = _round2(tip_by_dept[key]['net'] / tip_by_dept[key]['count'])

        if dept not in tip_trend[period]:
            tip_trend[period][dept] = {'brut': 0, 'net': 0}

        tip_trend[period][dept]['brut'] = brut
        tip_trend[period][dept]['net'] = net

    tip_trend_monthly = []
    for period in sorted(tip_trend.keys()):
        tip_trend_monthly.append({
            'period': period,
            'by_dept': tip_trend[period]
        })

    # 4. Food vs Beverage monthly
    food_bev = {}
    for m in metrics:
        key = f"{m.year}-{m.month:02d}"
        if key not in food_bev:
            food_bev[key] = {'food': 0, 'bev': 0}
        food_bev[key]['food'] += m.total_nourriture or 0
        food_bev[key]['bev'] += (m.total_boisson or 0) + (m.total_bieres or 0) + (m.total_vins or 0) + (m.total_mineraux or 0)

    food_vs_bev = []
    for key in sorted(food_bev.keys()):
        total = food_bev[key]['food'] + food_bev[key]['bev']
        if total > 0:
            food_pct = _round2(food_bev[key]['food'] / total * 100)
            bev_pct = _round2(food_bev[key]['bev'] / total * 100)
        else:
            food_pct = bev_pct = 0

        food_vs_bev.append({
            'period': key,
            'food_pct': food_pct,
            'bev_pct': bev_pct,
            'food_revenue': _round2(food_bev[key]['food']),
            'bev_revenue': _round2(food_bev[key]['bev']),
        })

    return jsonify({
        'success': True,
        'has_data': True,
        'outlet_trend_monthly': outlet_trend_monthly,
        'fb_per_client_trend': fb_per_client_trend,
        'tip_trend_monthly': tip_trend_monthly,
        'food_vs_bev_monthly': food_vs_bev,
    })


# ==============================================================================
# 3. LABOUR TAB
# ==============================================================================

@crm_tabs_bp.route('/api/crm/tabs/labor')
@login_required
def labor_analytics():
    """
    Main-d'oeuvre (Labour) analytics.
    Returns labour costs by department, hours, labour % of revenue,
    revenue per hour, overtime trends, headcount trends, and department summary.
    """
    start, end = _get_date_range()

    # Query DepartmentLabor, DailyLaborMetrics, DailyJourMetrics
    dept_labor = DepartmentLabor.query.filter(
        db.and_(
            DepartmentLabor.year >= start.year,
            db.or_(
                DepartmentLabor.year < end.year,
                db.and_(DepartmentLabor.year == end.year, DepartmentLabor.month <= end.month)
            )
        )
    ).all()

    metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(start, end)
    ).all()

    if not dept_labor:
        return jsonify({'success': True, 'has_data': False})

    # 1. Labor by department monthly
    labor_by_dept = {}
    departments = {}

    for dl in dept_labor:
        key = f"{dl.year}-{dl.month:02d}"
        dept = dl.department

        if key not in labor_by_dept:
            labor_by_dept[key] = {}

        labor_by_dept[key][dept] = _round2(dl.total_labor_cost)
        departments[dept] = True

    labor_by_dept_monthly = []
    for key in sorted(labor_by_dept.keys()):
        labor_by_dept_monthly.append({
            'period': key,
            'by_dept': labor_by_dept[key]
        })

    # 2. Labor hours by department monthly
    hours_by_dept = {}
    for dl in dept_labor:
        key = f"{dl.year}-{dl.month:02d}"
        dept = dl.department

        if key not in hours_by_dept:
            hours_by_dept[key] = {}

        hours_by_dept[key][dept] = _round2(dl.total_hours)

    labor_hours_by_dept = []
    for key in sorted(hours_by_dept.keys()):
        labor_hours_by_dept.append({
            'period': key,
            'by_dept': hours_by_dept[key]
        })

    # 3. Labor % of Revenue monthly
    revenue_by_period = {}
    labor_cost_total_by_period = {}

    for m in metrics:
        key = f"{m.year}-{m.month:02d}"
        if key not in revenue_by_period:
            revenue_by_period[key] = 0
        revenue_by_period[key] += m.total_revenue or 0

    for dl in dept_labor:
        key = f"{dl.year}-{dl.month:02d}"
        if key not in labor_cost_total_by_period:
            labor_cost_total_by_period[key] = 0
        labor_cost_total_by_period[key] += dl.total_labor_cost or 0

    labor_pct_of_revenue = []
    for key in sorted(set(list(revenue_by_period.keys()) + list(labor_cost_total_by_period.keys()))):
        rev = revenue_by_period.get(key, 0)
        lab = labor_cost_total_by_period.get(key, 0)

        if rev > 0:
            pct = _round2(lab / rev * 100)
        else:
            pct = 0

        labor_pct_of_revenue.append({
            'period': key,
            'labor_pct': pct,
            'labor_cost': _round2(lab),
            'revenue': _round2(rev),
        })

    # 4. Revenue per labor hour
    revenue_per_labor_hour = []
    for key in sorted(set(list(revenue_by_period.keys()) + list(labor_cost_total_by_period.keys()))):
        total_hours = sum(dl.total_hours or 0 for dl in dept_labor if f"{dl.year}-{dl.month:02d}" == key)
        rev = revenue_by_period.get(key, 0)

        if total_hours > 0:
            rev_per_hour = _round2(rev / total_hours)
        else:
            rev_per_hour = 0

        revenue_per_labor_hour.append({
            'period': key,
            'revenue_per_hour': rev_per_hour,
            'total_hours': _round2(total_hours),
            'revenue': _round2(rev),
        })

    # 5. Overtime trend
    overtime_by_dept = {}
    for dl in dept_labor:
        key = f"{dl.year}-{dl.month:02d}"
        dept = dl.department

        if key not in overtime_by_dept:
            overtime_by_dept[key] = {}

        overtime_by_dept[key][dept] = _round2(dl.overtime_hours)

    overtime_trend = []
    for key in sorted(overtime_by_dept.keys()):
        overtime_trend.append({
            'period': key,
            'by_dept': overtime_by_dept[key]
        })

    # 6. Headcount trend
    headcount_by_dept = {}
    for dl in dept_labor:
        key = f"{dl.year}-{dl.month:02d}"
        dept = dl.department

        if key not in headcount_by_dept:
            headcount_by_dept[key] = {}

        headcount_by_dept[key][dept] = dl.headcount

    headcount_trend = []
    for key in sorted(headcount_by_dept.keys()):
        headcount_trend.append({
            'period': key,
            'by_dept': headcount_by_dept[key]
        })

    # 7. Department summary (all time in the range)
    dept_summary = {}
    for dl in dept_labor:
        dept = dl.department
        if dept not in dept_summary:
            dept_summary[dept] = {
                'total_cost': 0,
                'total_hours': 0,
                'headcount': 0,
                'count': 0,
                'overtime_hours': 0,
            }

        dept_summary[dept]['total_cost'] += dl.total_labor_cost or 0
        dept_summary[dept]['total_hours'] += dl.total_hours or 0
        dept_summary[dept]['headcount'] = dl.headcount or 0
        dept_summary[dept]['overtime_hours'] += dl.overtime_hours or 0
        dept_summary[dept]['count'] += 1

    dept_stats = []
    for dept in sorted(dept_summary.keys()):
        d = dept_summary[dept]
        if d['total_hours'] > 0:
            avg_hourly = _round2(d['total_cost'] / d['total_hours'])
        else:
            avg_hourly = 0

        if d['total_hours'] > 0:
            overtime_pct = _round2(d['overtime_hours'] / d['total_hours'] * 100)
        else:
            overtime_pct = 0

        dept_stats.append({
            'department': dept,
            'total_cost': _round2(d['total_cost']),
            'total_hours': _round2(d['total_hours']),
            'avg_hourly_rate': avg_hourly,
            'overtime_pct': overtime_pct,
            'headcount': d['headcount'],
        })

    return jsonify({
        'success': True,
        'has_data': True,
        'labor_by_dept_monthly': labor_by_dept_monthly,
        'labor_hours_by_dept': labor_hours_by_dept,
        'labor_pct_of_revenue': labor_pct_of_revenue,
        'revenue_per_labor_hour': revenue_per_labor_hour,
        'overtime_trend': overtime_trend,
        'headcount_trend': headcount_trend,
        'dept_summary': dept_stats,
    })


# ==============================================================================
# 4. CASH & RECONCILIATION TAB
# ==============================================================================

@crm_tabs_bp.route('/api/crm/tabs/cash-recon')
@login_required
def cash_reconciliation():
    """
    Cash & Reconciliation analytics.
    Returns trends and auditor statistics.
    """
    start, end = _get_date_range()

    # Query DailyCashRecon
    recon = DailyCashRecon.query.filter(
        DailyCashRecon.date.between(start, end)
    ).order_by(DailyCashRecon.date).all()

    if not recon:
        return jsonify({'success': True, 'has_data': False})

    # 1. Surplus/deficit trend (aggregate by week if >90 days)
    days_span = (end - start).days
    aggregate_by_week = days_span > 90

    surplus_deficit_trend = []
    if aggregate_by_week:
        # Aggregate by week
        weekly = {}
        for r in recon:
            week_start = r.date - timedelta(days=r.date.weekday())
            week_key = week_start.isoformat()

            if week_key not in weekly:
                weekly[week_key] = {'total': 0, 'count': 0}

            weekly[week_key]['total'] += r.surplus_deficit or 0
            weekly[week_key]['count'] += 1

        for week_key in sorted(weekly.keys()):
            avg = _round2(weekly[week_key]['total'] / weekly[week_key]['count'])
            surplus_deficit_trend.append({
                'week': week_key,
                'surplus_deficit': avg
            })
    else:
        # Daily data
        for r in recon:
            surplus_deficit_trend.append({
                'date': r.date.isoformat(),
                'surplus_deficit': _round2(r.surplus_deficit)
            })

    # 2. Quasimodo variance trend
    quasimodo_trend = []
    if aggregate_by_week:
        weekly_q = {}
        for r in recon:
            week_start = r.date - timedelta(days=r.date.weekday())
            week_key = week_start.isoformat()

            if week_key not in weekly_q:
                weekly_q[week_key] = {'total': 0, 'count': 0}

            weekly_q[week_key]['total'] += r.quasimodo_variance or 0
            weekly_q[week_key]['count'] += 1

        for week_key in sorted(weekly_q.keys()):
            avg = _round2(weekly_q[week_key]['total'] / weekly_q[week_key]['count'])
            quasimodo_trend.append({
                'week': week_key,
                'quasimodo_variance': avg
            })
    else:
        for r in recon:
            quasimodo_trend.append({
                'date': r.date.isoformat(),
                'quasimodo_variance': _round2(r.quasimodo_variance)
            })

    # 3. Diff caisse trend
    diff_caisse_trend = []
    if aggregate_by_week:
        weekly_dc = {}
        for r in recon:
            week_start = r.date - timedelta(days=r.date.weekday())
            week_key = week_start.isoformat()

            if week_key not in weekly_dc:
                weekly_dc[week_key] = {'total': 0, 'count': 0}

            weekly_dc[week_key]['total'] += r.diff_caisse or 0
            weekly_dc[week_key]['count'] += 1

        for week_key in sorted(weekly_dc.keys()):
            avg = _round2(weekly_dc[week_key]['total'] / weekly_dc[week_key]['count'])
            diff_caisse_trend.append({
                'week': week_key,
                'diff_caisse': avg
            })
    else:
        for r in recon:
            diff_caisse_trend.append({
                'date': r.date.isoformat(),
                'diff_caisse': _round2(r.diff_caisse)
            })

    # 4. Auditor stats
    auditor_stats = {}
    for r in recon:
        auditor = r.auditor_name or 'Unknown'

        if auditor not in auditor_stats:
            auditor_stats[auditor] = {
                'surplus': 0,
                'quasimodo': 0,
                'count': 0,
                'abs_variance': 0,
            }

        auditor_stats[auditor]['surplus'] += r.surplus_deficit or 0
        auditor_stats[auditor]['quasimodo'] += r.quasimodo_variance or 0
        auditor_stats[auditor]['count'] += 1
        auditor_stats[auditor]['abs_variance'] += abs(r.quasimodo_variance or 0)

    auditor_list = []
    for auditor in sorted(auditor_stats.keys()):
        a = auditor_stats[auditor]
        auditor_list.append({
            'name': auditor,
            'avg_surplus': _round2(a['surplus'] / a['count']),
            'avg_quasimodo': _round2(a['quasimodo'] / a['count']),
            'total_audits': a['count'],
            'avg_absolute_variance': _round2(a['abs_variance'] / a['count']),
        })

    # 5. Cash deposit trend monthly
    deposit_by_month = {}
    for r in recon:
        key = f"{r.year}-{r.month:02d}"
        if key not in deposit_by_month:
            deposit_by_month[key] = {'cdn': 0, 'usd': 0}

        deposit_by_month[key]['cdn'] += r.deposit_cdn or 0
        deposit_by_month[key]['usd'] += r.deposit_usd or 0

    deposit_trend = []
    for key in sorted(deposit_by_month.keys()):
        deposit_trend.append({
            'period': key,
            'deposit_cdn': _round2(deposit_by_month[key]['cdn']),
            'deposit_usd': _round2(deposit_by_month[key]['usd']),
            'deposit_total': _round2(deposit_by_month[key]['cdn'] + deposit_by_month[key]['usd']),
        })

    # 6. Recon quality monthly
    threshold = 5  # ±$5
    recon_quality = {}
    for r in recon:
        key = f"{r.year}-{r.month:02d}"
        if key not in recon_quality:
            recon_quality[key] = {'quasimodo': 0, 'surplus': 0, 'within': 0, 'count': 0}

        recon_quality[key]['quasimodo'] += abs(r.quasimodo_variance or 0)
        recon_quality[key]['surplus'] += abs(r.surplus_deficit or 0)
        if abs(r.quasimodo_variance or 0) <= threshold:
            recon_quality[key]['within'] += 1
        recon_quality[key]['count'] += 1

    quality_monthly = []
    for key in sorted(recon_quality.keys()):
        q = recon_quality[key]
        pct_within = _round2(q['within'] / q['count'] * 100) if q['count'] > 0 else 0

        quality_monthly.append({
            'period': key,
            'avg_quasimodo': _round2(q['quasimodo'] / q['count']),
            'avg_surplus': _round2(q['surplus'] / q['count']),
            'pct_within_threshold': pct_within,
        })

    return jsonify({
        'success': True,
        'has_data': True,
        'surplus_deficit_trend': surplus_deficit_trend,
        'quasimodo_trend': quasimodo_trend,
        'diff_caisse_trend': diff_caisse_trend,
        'auditor_stats': auditor_list,
        'cash_deposit_trend': deposit_trend,
        'recon_quality_monthly': quality_monthly,
    })


# ==============================================================================
# 5. PAYMENTS & FEES TAB
# ==============================================================================

@crm_tabs_bp.route('/api/crm/tabs/payments')
@login_required
def payment_analytics():
    """
    Paiements & Frais (Payments & Fees) analytics.
    Returns card mix, volumes, discount costs, net vs gross,
    transaction counts, and average ticket sizes.
    """
    start, end = _get_date_range()

    # Query DailyCardMetrics
    cards = DailyCardMetrics.query.filter(
        DailyCardMetrics.date.between(start, end)
    ).all()

    if not cards:
        return jsonify({'success': True, 'has_data': False})

    # 1. Card mix monthly (as % of total)
    card_mix = {}
    for c in cards:
        key = f"{c.year}-{c.month:02d}"
        if key not in card_mix:
            card_mix[key] = {'VISA': 0, 'MC': 0, 'AMEX': 0, 'DEBIT': 0, 'DISCOVER': 0, 'total': 0}

        card_mix[key][c.card_type] = (card_mix[key].get(c.card_type, 0) or 0) + c.pos_total
        card_mix[key]['total'] += c.pos_total

    card_mix_monthly = []
    for key in sorted(card_mix.keys()):
        total = card_mix[key]['total'] or 1  # Avoid division by zero
        card_mix_monthly.append({
            'period': key,
            'visa_pct': _round2(card_mix[key]['VISA'] / total * 100),
            'mc_pct': _round2(card_mix[key]['MC'] / total * 100),
            'amex_pct': _round2(card_mix[key]['AMEX'] / total * 100),
            'debit_pct': _round2(card_mix[key]['DEBIT'] / total * 100),
            'discover_pct': _round2(card_mix[key]['DISCOVER'] / total * 100),
        })

    # 2. Card volume monthly
    card_volume = {}
    for c in cards:
        key = f"{c.year}-{c.month:02d}"
        if key not in card_volume:
            card_volume[key] = {}

        if c.card_type not in card_volume[key]:
            card_volume[key][c.card_type] = 0

        card_volume[key][c.card_type] += c.pos_total

    card_volume_monthly = []
    for key in sorted(card_volume.keys()):
        card_volume_monthly.append({
            'period': key,
            'by_card': {ct: _round2(card_volume[key].get(ct, 0)) for ct in ['VISA', 'MC', 'AMEX', 'DEBIT', 'DISCOVER']}
        })

    # 3. Discount cost monthly
    discount_cost = {}
    for c in cards:
        key = f"{c.year}-{c.month:02d}"
        if key not in discount_cost:
            discount_cost[key] = {}

        if c.card_type not in discount_cost[key]:
            discount_cost[key][c.card_type] = 0

        discount_cost[key][c.card_type] += c.discount_amount or 0

    discount_cost_monthly = []
    for key in sorted(discount_cost.keys()):
        discount_cost_monthly.append({
            'period': key,
            'by_card': {ct: _round2(discount_cost[key].get(ct, 0)) for ct in ['VISA', 'MC', 'AMEX', 'DEBIT', 'DISCOVER']}
        })

    # 4. Discount total trend (monthly total + blended rate)
    discount_total = {}
    for c in cards:
        key = f"{c.year}-{c.month:02d}"
        if key not in discount_total:
            discount_total[key] = {'discount': 0, 'volume': 0}

        discount_total[key]['discount'] += c.discount_amount or 0
        discount_total[key]['volume'] += c.pos_total

    discount_total_trend = []
    for key in sorted(discount_total.keys()):
        dt = discount_total[key]
        if dt['volume'] > 0:
            blended_rate = _round2(dt['discount'] / dt['volume'] * 100)
        else:
            blended_rate = 0

        discount_total_trend.append({
            'period': key,
            'total_discount': _round2(dt['discount']),
            'blended_rate_pct': blended_rate,
        })

    # 5. Net vs gross monthly
    net_vs_gross = {}
    for c in cards:
        key = f"{c.year}-{c.month:02d}"
        if key not in net_vs_gross:
            net_vs_gross[key] = {'pos': 0, 'net': 0}

        net_vs_gross[key]['pos'] += c.pos_total
        net_vs_gross[key]['net'] += c.net_amount

    net_vs_gross_monthly = []
    for key in sorted(net_vs_gross.keys()):
        net_vs_gross_monthly.append({
            'period': key,
            'pos_total': _round2(net_vs_gross[key]['pos']),
            'net_amount': _round2(net_vs_gross[key]['net']),
        })

    # 6. Transaction count monthly
    transaction_count = {}
    for c in cards:
        key = f"{c.year}-{c.month:02d}"
        if key not in transaction_count:
            transaction_count[key] = {}

        if c.card_type not in transaction_count[key]:
            transaction_count[key][c.card_type] = 0

        transaction_count[key][c.card_type] += c.transaction_count or 0

    transaction_count_monthly = []
    for key in sorted(transaction_count.keys()):
        transaction_count_monthly.append({
            'period': key,
            'by_card': {ct: transaction_count[key].get(ct, 0) for ct in ['VISA', 'MC', 'AMEX', 'DEBIT', 'DISCOVER']}
        })

    # 7. Average ticket monthly
    avg_ticket = {}
    for c in cards:
        key = f"{c.year}-{c.month:02d}"
        if key not in avg_ticket:
            avg_ticket[key] = {}

        if c.card_type not in avg_ticket[key]:
            avg_ticket[key][c.card_type] = {'volume': 0, 'count': 0}

        avg_ticket[key][c.card_type]['volume'] += c.pos_total
        avg_ticket[key][c.card_type]['count'] += c.transaction_count or 0

    avg_ticket_monthly = []
    for key in sorted(avg_ticket.keys()):
        by_card = {}
        for ct in ['VISA', 'MC', 'AMEX', 'DEBIT', 'DISCOVER']:
            if ct in avg_ticket[key] and avg_ticket[key][ct]['count'] > 0:
                by_card[ct] = _round2(avg_ticket[key][ct]['volume'] / avg_ticket[key][ct]['count'])
            else:
                by_card[ct] = 0

        avg_ticket_monthly.append({
            'period': key,
            'by_card': by_card
        })

    return jsonify({
        'success': True,
        'has_data': True,
        'card_mix_monthly': card_mix_monthly,
        'card_volume_monthly': card_volume_monthly,
        'discount_cost_monthly': discount_cost_monthly,
        'discount_total_trend': discount_total_trend,
        'net_vs_gross_monthly': net_vs_gross_monthly,
        'transaction_count_monthly': transaction_count_monthly,
        'avg_ticket_monthly': avg_ticket_monthly,
    })


# ==============================================================================
# 6. P&L & BUDGET TAB
# ==============================================================================

@crm_tabs_bp.route('/api/crm/tabs/pnl-budget')
@login_required
def pnl_budget():
    """
    P&L & Budget analytics.
    Returns budget variance, expense breakdown, profit margin,
    labour ratio, franchise fees, utilities, and annual P&L.
    """
    start, end = _get_date_range()

    # Query all needed models
    budgets = MonthlyBudget.query.filter(
        db.and_(
            MonthlyBudget.year >= start.year,
            db.or_(
                MonthlyBudget.year < end.year,
                db.and_(MonthlyBudget.year == end.year, MonthlyBudget.month <= end.month)
            )
        )
    ).all()

    expenses = MonthlyExpense.query.filter(
        db.and_(
            MonthlyExpense.year >= start.year,
            db.or_(
                MonthlyExpense.year < end.year,
                db.and_(MonthlyExpense.year == end.year, MonthlyExpense.month <= end.month)
            )
        )
    ).all()

    metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(start, end)
    ).all()

    dept_labor = DepartmentLabor.query.filter(
        db.and_(
            DepartmentLabor.year >= start.year,
            db.or_(
                DepartmentLabor.year < end.year,
                db.and_(DepartmentLabor.year == end.year, DepartmentLabor.month <= end.month)
            )
        )
    ).all()

    if not budgets and not expenses and not metrics:
        return jsonify({'success': True, 'has_data': False})

    # 1. Budget variance monthly
    budget_map = {(b.year, b.month): b for b in budgets}

    revenue_by_period = {}
    for m in metrics:
        key = (m.year, m.month)
        if key not in revenue_by_period:
            revenue_by_period[key] = 0
        revenue_by_period[key] += m.total_revenue or 0

    budget_variance = []
    for key in sorted(set(list(budget_map.keys()) + list(revenue_by_period.keys()))):
        year, month = key
        budget = budget_map.get(key)
        actual_rev = revenue_by_period.get(key, 0)
        budget_rev = budget.total_revenue_budget if budget else 0

        variance = actual_rev - budget_rev
        variance_pct = _round2((variance / budget_rev * 100) if budget_rev > 0 else 0)

        budget_variance.append({
            'year': year,
            'month': month,
            'revenue_actual': _round2(actual_rev),
            'revenue_budget': _round2(budget_rev),
            'variance': _round2(variance),
            'variance_pct': variance_pct,
        })

    # 2. Expense breakdown monthly
    expense_breakdown = []
    for exp in sorted(expenses, key=lambda e: (e.year, e.month)):
        expense_breakdown.append({
            'year': exp.year,
            'month': exp.month,
            'labor_rooms': _round2(exp.labor_rooms),
            'labor_fb': _round2(exp.labor_fb),
            'labor_admin': _round2(exp.labor_admin),
            'utilities': _round2(exp.utilities),
            'franchise_fees': _round2(exp.franchise_fees),
            'total_expenses': _round2(exp.total_expenses),
        })

    # 3. Profit margin monthly
    profit_margin_monthly = []
    expense_map = {(e.year, e.month): e for e in expenses}

    for key in sorted(revenue_by_period.keys()):
        year, month = key
        revenue = revenue_by_period[key]
        expense = expense_map.get(key)
        exp_total = expense.total_expenses if expense else 0

        gross_profit = revenue - exp_total
        margin = _round2((gross_profit / revenue * 100) if revenue > 0 else 0)

        profit_margin_monthly.append({
            'year': year,
            'month': month,
            'revenue': _round2(revenue),
            'expenses': _round2(exp_total),
            'gross_profit': _round2(gross_profit),
            'margin_pct': margin,
        })

    # 4. Labor ratio monthly
    labor_ratio = {}
    for dl in dept_labor:
        key = (dl.year, dl.month)
        if key not in labor_ratio:
            labor_ratio[key] = 0
        labor_ratio[key] += dl.total_labor_cost or 0

    labor_ratio_monthly = []
    for key in sorted(set(list(revenue_by_period.keys()) + list(labor_ratio.keys()))):
        year, month = key
        revenue = revenue_by_period.get(key, 0)
        lab = labor_ratio.get(key, 0)

        ratio = _round2((lab / revenue * 100) if revenue > 0 else 0)

        labor_ratio_monthly.append({
            'year': year,
            'month': month,
            'labor_cost': _round2(lab),
            'revenue': _round2(revenue),
            'labor_ratio_pct': ratio,
        })

    # 5. Franchise fee trend
    franchise_trend = []
    for exp in sorted(expenses, key=lambda e: (e.year, e.month)):
        franchise_trend.append({
            'year': exp.year,
            'month': exp.month,
            'franchise_fees': _round2(exp.franchise_fees),
        })

    # 6. Utility trend
    utility_trend = []
    for exp in sorted(expenses, key=lambda e: (e.year, e.month)):
        utility_trend.append({
            'year': exp.year,
            'month': exp.month,
            'utilities': _round2(exp.utilities),
        })

    # 7. Annual P&L summary
    annual_pnl = {}
    for m in metrics:
        year = m.year
        if year not in annual_pnl:
            annual_pnl[year] = {'revenue': 0, 'expenses': 0, 'labor': 0}
        annual_pnl[year]['revenue'] += m.total_revenue or 0

    for exp in expenses:
        year = exp.year
        if year not in annual_pnl:
            annual_pnl[year] = {'revenue': 0, 'expenses': 0, 'labor': 0}
        annual_pnl[year]['expenses'] += exp.total_expenses or 0
        annual_pnl[year]['labor'] += exp.labor_total or 0

    for dl in dept_labor:
        year = dl.year
        if year not in annual_pnl:
            annual_pnl[year] = {'revenue': 0, 'expenses': 0, 'labor': 0}
        annual_pnl[year]['labor'] += dl.total_labor_cost or 0

    annual = []
    for year in sorted(annual_pnl.keys()):
        a = annual_pnl[year]
        gross_profit = a['revenue'] - a['expenses']
        labor_pct = _round2((a['labor'] / a['revenue'] * 100) if a['revenue'] > 0 else 0)
        franchise_pct = _round2(((a['expenses'] * 0.05) / a['revenue'] * 100) if a['revenue'] > 0 else 0)  # Assume 5%

        annual.append({
            'year': year,
            'total_revenue': _round2(a['revenue']),
            'total_expenses': _round2(a['expenses']),
            'gross_profit': _round2(gross_profit),
            'labor_pct': labor_pct,
            'franchise_pct': franchise_pct,
        })

    return jsonify({
        'success': True,
        'has_data': True,
        'budget_variance_monthly': budget_variance,
        'expense_breakdown_monthly': expense_breakdown,
        'profit_margin_monthly': profit_margin_monthly,
        'labor_ratio_monthly': labor_ratio_monthly,
        'franchise_fee_trend': franchise_trend,
        'utility_trend': utility_trend,
        'annual_pnl': annual,
    })
