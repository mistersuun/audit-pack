"""
Direction Reports — Daily reports for GM/GSM (Rapp_p1, p2, p3, État rev).

Replicates the 4 Excel Direction report sheets with data from:
- DailyJourMetrics (revenue, occupancy, payments)
- NightAuditSession (detailed F&B breakdown)
- DepartmentLabor (hours, wages by department)
- MonthlyExpense (fixed costs)
- MonthlyBudget (targets)
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, date, timedelta
from database.models import (db, DailyJourMetrics, NightAuditSession,
                              DepartmentLabor, MonthlyExpense, MonthlyBudget,
                              JournalEntry, DailyLaborMetrics)
from sqlalchemy import func, text
import logging

logger = logging.getLogger(__name__)

direction_bp = Blueprint('direction', __name__)

TOTAL_ROOMS = 340

# Budget ratios from Excel Budget sheet (#34) — used when no MonthlyBudget exists
DEFAULT_BUDGET = {
    'rooms_available_month': 7056,      # 340 * ~20.75 avg days
    'rooms_target_month': 5925,         # 83.97% occ
    'adr_target': 221.41,
    'room_revenue_month': 1311825,
    'location_salle_month': 215000,
    'piazza_month': 185000,             # Piazza + Bar
    'banquet_month': 310000,
    'spesa_month': 29000,
    'giotto_month': 9500,               # estimated
    'cupola_month': 7250,
    'total_revenue_month': 2347579,
    # Cost ratios (% of revenue)
    'cost_nourriture': 0.38,
    'cost_alcool': 0.194,
    'cost_biere': 0.3175,
    'cost_vin': 0.345,
    'cost_mineraux': 0.23,
    # Benefits ratios (% of salary)
    'benefits_hebergement': 0.43,
    'benefits_restauration': 0.445,
    'benefits_autres': 0.475,
    # Fixed costs (annual)
    'marketing_annual': 33204,
    'admin_annual': 157633,
    'entretien_annual': 58134,
    'energie_annual': 59790,
    'taxes_assurances_annual': 77204,
    'amortissement_annual': 58333,
    'interet_annual': 56083,
    'loyer_annual': 180000,
    # Variable cost ratio for rooms
    'cost_variable_chambres': 0.112,
    'cost_variable_banquet': 0.061,
    'cost_variable_resto': 0.354,
    'cost_autres_resto': 0.065,
    'cost_av': 0.90,
    'cost_autres_revenus': 0.368,
}


def direction_required(f):
    """Access control for direction portal."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            from flask import redirect, url_for
            return redirect(url_for('auth_v2.login'))
        role = session.get('user_role_type', '')
        if role not in ('admin', 'gm', 'gsm', 'accounting'):
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# PAGE
# ==============================================================================

@direction_bp.route('/direction')
@direction_required
def direction_page():
    return render_template('direction_portal.html')


# ==============================================================================
# API — Dashboard KPIs
# ==============================================================================

@direction_bp.route('/api/direction/dashboard')
@direction_required
def dashboard_kpis():
    """KPI summary for the Direction dashboard."""
    import calendar
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date requise'}), 400

    try:
        target = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Date invalide'}), 400

    daily = DailyJourMetrics.query.filter_by(date=target).first()
    if not daily:
        return jsonify({'error': 'Aucune donnée', 'has_data': False}), 404

    year, month = target.year, target.month
    days_in_month = calendar.monthrange(year, month)[1]

    # MTD
    mtd_start = date(year, month, 1)
    mtd_metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date >= mtd_start,
        DailyJourMetrics.date <= target
    ).all()
    mtd = _aggregate_mtd(mtd_metrics)
    days_in_period = len(mtd_metrics)

    # Budget
    budget = _get_budget(year, month, target.day, days_in_period)

    # KPIs
    rooms_avail = daily.rooms_available or TOTAL_ROOMS
    occ = (daily.total_rooms_sold or 0) / rooms_avail if rooms_avail else 0
    adr = daily.adr or 0
    revpar = (daily.room_revenue or 0) / rooms_avail if rooms_avail else 0
    rev_jour = daily.total_revenue or 0

    # Budget comparisons
    budget_adr = budget.get('adr', 0)
    budget_occ = budget.get('rooms_day', 0) / TOTAL_ROOMS if budget.get('rooms_day') else 0
    budget_rev_day = budget.get('total_revenue_day', 0)
    budget_revpar = budget_adr * budget_occ if budget_adr and budget_occ else 0

    # Recent audits — pull from DailyJourMetrics (real RJ data) + NightAuditSession for auditor info
    try:
        days_param = min(int(request.args.get('days', 30)), 365)
    except (ValueError, TypeError):
        days_param = 30
    if days_param > 0:
        cutoff = target - timedelta(days=days_param)
        recent_metrics = DailyJourMetrics.query.filter(
            DailyJourMetrics.date >= cutoff,
            DailyJourMetrics.date <= target
        ).order_by(DailyJourMetrics.date.desc()).all()
    else:
        recent_metrics = DailyJourMetrics.query.order_by(
            DailyJourMetrics.date.desc()
        ).limit(60).all()

    # Build lookup of NightAuditSession by date for auditor names
    rj_dates = [m.date for m in recent_metrics]
    rj_sessions = {
        s.audit_date: s for s in NightAuditSession.query.filter(
            NightAuditSession.audit_date.in_(rj_dates)
        ).all()
    } if rj_dates else {}

    recent_audits = []
    for m in recent_metrics:
        sess = rj_sessions.get(m.date)
        recent_audits.append({
            'date': m.date.strftime('%d/%m/%Y'),
            'revenue': round(m.total_revenue, 0),
            'occ': round(m.occupancy_rate, 1),
            'adr': round(m.adr, 2),
            'rooms_sold': m.total_rooms_sold,
            'auditor': sess.auditor_name if sess else None,
            'status': sess.status if sess else 'imported',
        })

    return jsonify({
        'revpar': round(revpar, 2),
        'revpar_budget_var': round(revpar - budget_revpar, 2) if budget_revpar else None,
        'adr': round(adr, 2),
        'adr_budget_var': round(adr - budget_adr, 2) if budget_adr else None,
        'occupation': round(occ, 4),
        'occupation_budget_var': round(occ - budget_occ, 4) if budget_occ else None,
        'revenus_jour': round(rev_jour, 2),
        'revenus_jour_budget_var': round(rev_jour - budget_rev_day, 2) if budget_rev_day else None,
        'revenus_mois': round(mtd['total_revenue'], 2),
        'recent_audits': recent_audits,
    })


# ==============================================================================
# API — RJ Summary (read-only)
# ==============================================================================

@direction_bp.route('/api/direction/rj-summary/<report_date>')
@direction_required
def rj_summary(report_date):
    """Complete read-only NightAuditSession for Direction — all 155 columns."""
    try:
        target = datetime.strptime(report_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Date invalide'}), 400

    nas = NightAuditSession.query.filter_by(audit_date=target).first()
    if not nas:
        return jsonify({'error': 'Aucun RJ pour cette date'}), 404

    # Return ALL data via to_dict() — the complete 14-tab RJ
    d = nas.to_dict() if hasattr(nas, 'to_dict') else {}

    # Ensure date is formatted for display
    d['audit_date_display'] = target.strftime('%d/%m/%Y')
    d['audit_date_iso'] = target.isoformat()

    return jsonify(d)


# ==============================================================================
# API — Trends (30-day)
# ==============================================================================

@direction_bp.route('/api/direction/trends')
@direction_required
def trends_data():
    """Configurable trend data for charts (default 30 days, max 365)."""
    try:
        days = min(int(request.args.get('days', 30)), 365)
    except (ValueError, TypeError):
        days = 30
    metrics = DailyJourMetrics.query.order_by(
        DailyJourMetrics.date.desc()
    ).limit(days).all()

    metrics.reverse()  # oldest first

    months_fr = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
                 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']

    labels, rev_data, occ_data, adr_data = [], [], [], []
    revpar_data, fb_data, room_rev_data = [], [], []

    for m in metrics:
        labels.append(f"{m.date.day} {months_fr[m.date.month - 1]}")
        rev_data.append(round(m.total_revenue or 0, 2))
        occ_data.append(round(m.occupancy_rate or 0, 1))
        adr_data.append(round(m.adr or 0, 2))
        revpar_data.append(round(m.revpar or 0, 2))
        fb_data.append(round(m.fb_revenue or 0, 2))
        room_rev_data.append(round(m.room_revenue or 0, 2))

    return jsonify({
        'revenue': {'labels': labels, 'data': rev_data},
        'occupation': {'labels': labels, 'data': occ_data},
        'adr': {'labels': labels, 'data': adr_data},
        'revpar': {'labels': labels, 'data': revpar_data},
        'fb': {'labels': labels, 'data': fb_data},
        'room_revenue': {'labels': labels, 'data': room_rev_data},
    })


# ==============================================================================
# API — Full Executive Overview (for rich dashboard)
# ==============================================================================

@direction_bp.route('/api/direction/overview')
@direction_required
def direction_overview():
    """
    Complete executive overview — mirrors manager overview but for Direction.
    Returns KPIs, trend, F&B, rooms, payments, monthly, YoY, DOW analysis.
    """
    from utils.analytics import HistoricalAnalytics

    start = request.args.get('start_date')
    end = request.args.get('end_date')

    if start:
        try:
            start = datetime.strptime(start, '%Y-%m-%d').date()
        except ValueError:
            start = None
    if end:
        try:
            end = datetime.strptime(end, '%Y-%m-%d').date()
        except ValueError:
            end = None

    if not start or not end:
        max_date = db.session.query(func.max(DailyJourMetrics.date)).scalar()
        min_date = db.session.query(func.min(DailyJourMetrics.date)).scalar()
        if not max_date:
            return jsonify({'has_data': False})
        start = start or min_date
        end = end or max_date

    h = HistoricalAnalytics(start, end)
    if not h.has_data():
        return jsonify({'has_data': False})

    kpis = h.get_executive_kpis()
    advanced = h.get_advanced_kpis()
    dow = h.get_dow_analysis()
    trend = h.get_revenue_trend()
    fb = h.get_fb_analytics()
    rooms = h.get_room_analytics()
    payments = h.get_payment_analytics()
    monthly = h.get_monthly_summary() if hasattr(h, 'get_monthly_summary') else []

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
        'trend': trend,
        'fb': fb,
        'rooms': rooms,
        'payments': payments,
        'monthly': monthly,
    })


# ==============================================================================
# API — Year-over-Year Comparison
# ==============================================================================

@direction_bp.route('/api/direction/yearly-comparison')
@direction_required
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
    ).group_by(DailyJourMetrics.year).order_by(DailyJourMetrics.year).all()

    result = []
    prev = None
    for y in years_data:
        fb_per_guest = y.fb_rev / y.guests if y.guests and y.guests > 0 else 0
        row = {
            'year': y.year,
            'days': y.days,
            'avg_adr': round(y.avg_adr, 2),
            'avg_occ': round(y.avg_occ, 1),
            'avg_revpar': round(y.avg_revpar, 2),
            'avg_trevpar': round(y.avg_trevpar, 2) if y.avg_trevpar else 0,
            'total_revenue': round(y.total_rev, 0),
            'room_revenue': round(y.room_rev, 0),
            'fb_revenue': round(y.fb_rev, 0),
            'rooms_sold': int(y.rooms_sold),
            'guests': int(y.guests),
            'fb_per_guest': round(fb_per_guest, 2),
        }
        # Compute deltas vs previous year
        if prev:
            row['delta_adr'] = round(row['avg_adr'] - prev['avg_adr'], 2)
            row['delta_occ'] = round(row['avg_occ'] - prev['avg_occ'], 1)
            row['delta_revpar'] = round(row['avg_revpar'] - prev['avg_revpar'], 2)
            row['delta_revenue'] = round(row['total_revenue'] - prev['total_revenue'], 0)
        prev = row
        result.append(row)

    return jsonify({'years': result})


# ==============================================================================
# API — All dates available (full 5-year history)
# ==============================================================================

@direction_bp.route('/api/direction/all-dates')
@direction_required
def all_dates():
    """All available dates grouped by year-month for the full date picker."""
    dates = db.session.query(DailyJourMetrics.date).order_by(
        DailyJourMetrics.date.desc()
    ).all()
    return jsonify({'dates': [d[0].isoformat() for d in dates]})


# ==============================================================================
# API — RJ Sessions list (for NightAuditSession viewer)
# ==============================================================================

@direction_bp.route('/api/direction/rj-sessions')
@direction_required
def rj_sessions():
    """List all NightAuditSession records for the RJ viewer."""
    sessions = NightAuditSession.query.order_by(
        NightAuditSession.audit_date.desc()
    ).all()

    result = []
    for s in sessions:
        result.append({
            'date': s.audit_date.isoformat() if s.audit_date else None,
            'date_display': s.audit_date.strftime('%d/%m/%Y') if s.audit_date else '—',
            'auditor': s.auditor_name or '—',
            'status': s.status or 'draft',
        })

    return jsonify({'sessions': result})


# ==============================================================================
# API — Monthly Summary (for bar chart)
# ==============================================================================

@direction_bp.route('/api/direction/monthly-summary')
@direction_required
def monthly_summary():
    """Monthly aggregated revenue/occ/ADR for historical charts."""
    months_fr = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
                 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']

    data = db.session.query(
        DailyJourMetrics.year,
        DailyJourMetrics.month,
        func.count(DailyJourMetrics.id).label('days'),
        func.sum(DailyJourMetrics.total_revenue).label('total_rev'),
        func.sum(DailyJourMetrics.room_revenue).label('room_rev'),
        func.sum(DailyJourMetrics.fb_revenue).label('fb_rev'),
        func.avg(DailyJourMetrics.adr).label('avg_adr'),
        func.avg(DailyJourMetrics.occupancy_rate).label('avg_occ'),
        func.avg(DailyJourMetrics.revpar).label('avg_revpar'),
        func.sum(DailyJourMetrics.total_rooms_sold).label('rooms_sold'),
        func.sum(DailyJourMetrics.nb_clients).label('guests'),
    ).group_by(
        DailyJourMetrics.year, DailyJourMetrics.month
    ).order_by(
        DailyJourMetrics.year, DailyJourMetrics.month
    ).all()

    result = []
    for m in data:
        result.append({
            'year': m.year,
            'month': m.month,
            'label': f"{months_fr[m.month - 1]} {m.year}",
            'days': m.days,
            'total_revenue': round(m.total_rev, 0),
            'room_revenue': round(m.room_rev, 0),
            'fb_revenue': round(m.fb_rev, 0),
            'avg_adr': round(m.avg_adr, 2),
            'avg_occ': round(m.avg_occ, 1),
            'avg_revpar': round(m.avg_revpar, 2),
            'rooms_sold': int(m.rooms_sold),
            'guests': int(m.guests),
        })

    return jsonify({'months': result})


# ==============================================================================
# API — Daily Direction Report
# ==============================================================================

@direction_bp.route('/api/direction/daily-report/<report_date>')
@direction_required
def daily_report(report_date):
    """
    Returns all 4 Direction reports for a given date.
    Aggregates daily + MTD data + budget comparisons.
    """
    try:
        target = datetime.strptime(report_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Date invalide'}), 400

    year = target.year
    month = target.month
    day = target.day

    # --- Get daily metrics for the target date ---
    daily = DailyJourMetrics.query.filter_by(date=target).first()
    if not daily:
        return jsonify({'error': 'Aucune donnée pour cette date', 'has_data': False}), 404

    # --- Get MTD (month to date) aggregates ---
    mtd_start = date(year, month, 1)
    mtd_metrics = DailyJourMetrics.query.filter(
        DailyJourMetrics.date >= mtd_start,
        DailyJourMetrics.date <= target
    ).all()

    mtd = _aggregate_mtd(mtd_metrics)
    days_in_period = len(mtd_metrics)

    # --- Get NightAuditSession for detailed F&B (if available) ---
    nas = NightAuditSession.query.filter_by(audit_date=target).first()

    # --- Get budget ---
    budget = _get_budget(year, month, day, days_in_period)

    # --- Get labor data ---
    labor = _get_labor_data(year, month, day, days_in_period)

    # --- Get fixed costs ---
    fixed_costs = _get_fixed_costs(year, month, days_in_period)

    # --- Build reports ---
    result = {
        'has_data': True,
        'date': target.isoformat(),
        'day': day,
        'days_in_period': days_in_period,
        'auditor': nas.auditor_name if nas else '',
        'rapp_p1': _build_rapp_p1(daily, mtd, budget, labor),
        'rapp_p2': _build_rapp_p2(labor, mtd, days_in_period),
        'rapp_p3': _build_rapp_p3(daily, mtd, budget, labor, days_in_period),
        'etat_rev': _build_etat_rev(daily, mtd, budget, labor, fixed_costs, days_in_period),
    }

    return jsonify(result)


@direction_bp.route('/api/direction/dates')
@direction_required
def available_dates():
    """Returns list of dates with data for the date picker."""
    dates = db.session.query(DailyJourMetrics.date).order_by(
        DailyJourMetrics.date.desc()
    ).limit(90).all()
    return jsonify({'dates': [d[0].isoformat() for d in dates]})


# ==============================================================================
# HELPER — MTD Aggregation
# ==============================================================================

def _aggregate_mtd(metrics):
    """Aggregate a list of DailyJourMetrics into MTD totals."""
    mtd = {
        'room_revenue': 0, 'fb_revenue': 0, 'total_revenue': 0,
        'piazza_total': 0, 'spesa_total': 0, 'banquet_total': 0,
        'cafe_link_total': 0, 'room_svc_total': 0, 'tabagie_total': 0,
        'other_revenue': 0, 'tips_total': 0,
        'total_nourriture': 0, 'total_boisson': 0, 'total_bieres': 0,
        'total_vins': 0, 'total_mineraux': 0,
        'rooms_sold': 0, 'rooms_simple': 0, 'rooms_double': 0,
        'rooms_suite': 0, 'rooms_comp': 0, 'nb_clients': 0,
        'rooms_available': 0, 'rooms_hors_usage': 0,
        'total_cards': 0, 'visa_total': 0, 'mastercard_total': 0,
        'amex_elavon_total': 0, 'debit_total': 0, 'discover_total': 0,
        'tps_total': 0, 'tvq_total': 0, 'tvh_total': 0,
    }
    for m in metrics:
        for k in mtd:
            field = k if k != 'rooms_sold' else 'total_rooms_sold'
            mtd[k] += getattr(m, field, 0) or 0
    # Computed MTD KPIs
    mtd['adr'] = mtd['room_revenue'] / mtd['rooms_sold'] if mtd['rooms_sold'] else 0
    mtd['occupancy'] = (mtd['rooms_sold'] / mtd['rooms_available'] * 100) if mtd['rooms_available'] else 0
    mtd['revpar'] = mtd['room_revenue'] / mtd['rooms_available'] if mtd['rooms_available'] else 0
    return mtd


# ==============================================================================
# HELPER — Budget
# ==============================================================================

def _get_budget(year, month, day, days_in_period):
    """Get budget for the period. Falls back to DEFAULT_BUDGET."""
    b = MonthlyBudget.query.filter_by(year=year, month=month).first()

    if b:
        return b.to_dict()

    # Use default budget prorated to period
    db_ = DEFAULT_BUDGET
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    ratio_day = 1 / days_in_month
    ratio_mtd = days_in_period / days_in_month

    return {
        'rooms_day': round(db_['rooms_target_month'] * ratio_day),
        'rooms_mtd': round(db_['rooms_target_month'] * ratio_mtd),
        'adr': db_['adr_target'],
        'room_revenue_day': db_['room_revenue_month'] * ratio_day,
        'room_revenue_mtd': db_['room_revenue_month'] * ratio_mtd,
        'location_day': db_['location_salle_month'] * ratio_day,
        'location_mtd': db_['location_salle_month'] * ratio_mtd,
        'piazza_day': db_['piazza_month'] * ratio_day,
        'piazza_mtd': db_['piazza_month'] * ratio_mtd,
        'banquet_day': db_['banquet_month'] * ratio_day,
        'banquet_mtd': db_['banquet_month'] * ratio_mtd,
        'total_revenue_day': db_['total_revenue_month'] * ratio_day,
        'total_revenue_mtd': db_['total_revenue_month'] * ratio_mtd,
        'giotto_day': db_['giotto_month'] * ratio_day,
        'giotto_mtd': db_['giotto_month'] * ratio_mtd,
        'cupola_day': db_['cupola_month'] * ratio_day,
        'cupola_mtd': db_['cupola_month'] * ratio_mtd,
        'spesa_day': db_['spesa_month'] * ratio_day,
        'spesa_mtd': db_['spesa_month'] * ratio_mtd,
        'cost_variable_chambres': db_['cost_variable_chambres'],
        'cost_variable_banquet': db_['cost_variable_banquet'],
        'cost_variable_resto': db_['cost_variable_resto'],
        'cost_autres_resto': db_['cost_autres_resto'],
        'cost_av': db_['cost_av'],
        'cost_autres_revenus': db_['cost_autres_revenus'],
        'benefits_hebergement': db_['benefits_hebergement'],
        'benefits_restauration': db_['benefits_restauration'],
        'benefits_autres': db_['benefits_autres'],
    }


# ==============================================================================
# HELPER — Labor
# ==============================================================================

def _get_labor_data(year, month, day, days_in_period):
    """Get labor data organized by department."""
    records = DepartmentLabor.query.filter_by(year=year, month=month).all()

    labor = {}
    for r in records:
        labor[r.department] = r.to_dict()

    return labor


# ==============================================================================
# HELPER — Fixed Costs
# ==============================================================================

def _get_fixed_costs(year, month, days_in_period):
    """Get monthly expense data or use defaults."""
    expense = MonthlyExpense.query.filter_by(year=year, month=month).first()

    if expense:
        return expense.to_dict()

    # Default annual costs prorated to month
    db_ = DEFAULT_BUDGET
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    ratio_month = 1 / 12

    return {
        'marketing': db_['marketing_annual'] * ratio_month,
        'admin': db_['admin_annual'] * ratio_month,
        'entretien': db_['entretien_annual'] * ratio_month,
        'energie': db_['energie_annual'] * ratio_month,
        'taxes_assurances': db_['taxes_assurances_annual'] * ratio_month,
        'amortissement': db_['amortissement_annual'] * ratio_month,
        'interet': db_['interet_annual'] * ratio_month,
        'loyer': db_['loyer_annual'] * ratio_month,
    }


# ==============================================================================
# REPORT BUILDERS
# ==============================================================================

def _build_rapp_p1(daily, mtd, budget, labor):
    """Sommaire des Revenus — Rapp_p1"""

    # Revenue section
    d = daily
    piazza_day = (d.piazza_total or 0)
    cupola_day = 0  # Cupola is part of piazza in our data
    giotto_day = (d.cafe_link_total or 0)  # Giotto = Café Link area
    location_day = 0  # Location salle — not tracked separately in DailyJourMetrics yet
    banquet_day = (d.banquet_total or 0)
    banquet_ii_day = 0  # Audio-visual — separate in Excel
    resto_day = piazza_day + cupola_day + giotto_day + banquet_day + banquet_ii_day
    minibar_day = 0
    telephone_day = 0
    autres_day = (d.other_revenue or 0) + (d.tabagie_total or 0)

    rooms_sold_day = d.total_rooms_sold or 0
    adr_day = d.adr or 0
    room_rev_day = d.room_revenue or 0
    total_day = d.total_revenue or 0

    # Food & Beverage totals
    nourriture_day = d.total_nourriture or 0
    boisson_day = (d.total_boisson or 0) + (d.total_bieres or 0) + (d.total_vins or 0) + (d.total_mineraux or 0)

    return {
        'revenus': {
            'chambres_louees': {'jour': rooms_sold_day, 'mois': mtd['rooms_sold'],
                                'budget_jour': budget.get('rooms_day', 0), 'budget_mois': budget.get('rooms_mtd', 0)},
            'taux_moyen': {'jour': round(adr_day, 2), 'mois': round(mtd['adr'], 2),
                           'budget_mois': budget.get('adr', 0)},
            'total_chambres': {'jour': round(room_rev_day, 2), 'mois': round(mtd['room_revenue'], 2),
                               'budget_jour': round(budget.get('room_revenue_day', 0), 2),
                               'budget_mois': round(budget.get('room_revenue_mtd', 0), 2)},
            'location_salle': {'jour': round(location_day, 2), 'mois': round(mtd.get('location', 0), 2),
                               'budget_jour': round(budget.get('location_day', 0), 2),
                               'budget_mois': round(budget.get('location_mtd', 0), 2)},
            'giotto': {'jour': round(giotto_day, 2), 'mois': round(mtd['cafe_link_total'], 2),
                       'budget_jour': round(budget.get('giotto_day', 0), 2),
                       'budget_mois': round(budget.get('giotto_mtd', 0), 2)},
            'piazza': {'jour': round(piazza_day, 2), 'mois': round(mtd['piazza_total'], 2),
                       'budget_jour': round(budget.get('piazza_day', 0), 2),
                       'budget_mois': round(budget.get('piazza_mtd', 0), 2)},
            'cupola': {'jour': round(cupola_day, 2), 'mois': 0},
            'banquets': {'jour': round(banquet_day, 2), 'mois': round(mtd['banquet_total'], 2),
                         'budget_jour': round(budget.get('banquet_day', 0), 2),
                         'budget_mois': round(budget.get('banquet_mtd', 0), 2)},
            'banquets_ii': {'jour': round(banquet_ii_day, 2), 'mois': 0},
            'total_restauration': {'jour': round(resto_day, 2), 'mois': round(mtd['fb_revenue'], 2)},
            'minibar': {'jour': round(minibar_day, 2), 'mois': 0},
            'telephone': {'jour': 0, 'mois': 0},
            'autres_revenus': {'jour': round(autres_day, 2), 'mois': round(mtd['other_revenue'] + mtd['tabagie_total'], 2)},
            'recettes_total': {'jour': round(total_day, 2), 'mois': round(mtd['total_revenue'], 2)},
            'recettes_nourriture': {'jour': round(nourriture_day, 2), 'mois': round(mtd['total_nourriture'], 2)},
            'recettes_boisson': {'jour': round(boisson_day, 2), 'mois': round(
                mtd['total_boisson'] + mtd['total_bieres'] + mtd['total_vins'] + mtd['total_mineraux'], 2)},
        },
        'main_oeuvre': _build_labor_summary(labor, mtd),
    }


def _build_labor_summary(labor, mtd):
    """Build labor cost summary for Rapp_p1."""
    depts_hebergement = ['RECEPTION', 'ROOMS', 'HOUSEKEEPING']
    depts_restauration = ['KITCHEN', 'RESTAURANT', 'BAR', 'BANQUET']

    def _dept_cost(dept_name):
        d = labor.get(dept_name, {})
        return {
            'mois': round(d.get('total_labor_cost', 0), 2),
            'pct_mois': 0,
            'budget_mois': round(d.get('budget_cost', 0), 2),
        }

    hebergement = {
        'reception': _dept_cost('RECEPTION'),
        'femme_chambre': _dept_cost('ROOMS'),
        'equipier': _dept_cost('HOUSEKEEPING'),
        'gouvernante': {'mois': 0, 'pct_mois': 0, 'budget_mois': 0},
        'buanderie': {'mois': 0, 'pct_mois': 0, 'budget_mois': 0},
    }

    restauration = {
        'giotto': {'mois': 0, 'pct_mois': 0, 'budget_mois': 0},
        'piazza': _dept_cost('RESTAURANT'),
        'cupola': {'mois': 0, 'pct_mois': 0, 'budget_mois': 0},
        'banquets': _dept_cost('BANQUET'),
        'banquets_ii': {'mois': 0, 'pct_mois': 0, 'budget_mois': 0},
        'cuisine': _dept_cost('KITCHEN'),
    }

    autres = {
        'adm_generale': _dept_cost('ADMINISTRATION'),
        'marketing': _dept_cost('SALES'),
        'entretien': _dept_cost('MAINTENANCE'),
    }

    # Totals
    total_heb = sum(v['mois'] for v in hebergement.values())
    total_rest = sum(v['mois'] for v in restauration.values())
    total_autres = sum(v['mois'] for v in autres.values())
    total_sal = total_heb + total_rest + total_autres

    # Calculate percentages
    total_rev = mtd.get('total_revenue', 1)
    if total_rev > 0:
        for dept in hebergement.values():
            dept['pct_mois'] = round(dept['mois'] / total_rev, 4) if dept['mois'] else 0
        for dept in restauration.values():
            dept['pct_mois'] = round(dept['mois'] / total_rev, 4) if dept['mois'] else 0
        for dept in autres.values():
            dept['pct_mois'] = round(dept['mois'] / total_rev, 4) if dept['mois'] else 0

    return {
        'hebergement': hebergement,
        'total_hebergement': {'mois': round(total_heb, 2)},
        'restauration': restauration,
        'total_restauration': {'mois': round(total_rest, 2)},
        'autres': autres,
        'total_salaires': {'mois': round(total_sal, 2)},
    }


def _build_rapp_p2(labor, mtd, days_in_period):
    """Sommaire Heures & Employés — Rapp_p2"""
    def _dept_hours(dept_name):
        d = labor.get(dept_name, {})
        total_h = d.get('total_hours', 0)
        return {
            'heures_mois': round(total_h, 1),
            'employes_mois': round(total_h / (days_in_period * 8), 2) if days_in_period else 0,
        }

    rooms_sold = mtd.get('rooms_sold', 0)
    femme_chambre = _dept_hours('ROOMS')

    return {
        'hebergement': {
            'reception': _dept_hours('RECEPTION'),
            'femme_chambre': femme_chambre,
            'equipier': _dept_hours('HOUSEKEEPING'),
            'gouvernante': {'heures_mois': 0, 'employes_mois': 0},
            'buanderie': {'heures_mois': 0, 'employes_mois': 0},
        },
        'restauration': {
            'piazza': _dept_hours('RESTAURANT'),
            'cupola': {'heures_mois': 0, 'employes_mois': 0},
            'banquets': _dept_hours('BANQUET'),
            'banquets_ii': {'heures_mois': 0, 'employes_mois': 0},
            'cuisine': _dept_hours('KITCHEN'),
        },
        'autres': {
            'adm_generale': _dept_hours('ADMINISTRATION'),
            'marketing': _dept_hours('SALES'),
            'entretien': _dept_hours('MAINTENANCE'),
        },
        'femme_chambre_stats': {
            'employes_mois': femme_chambre['employes_mois'],
            'moy_chambre_emp': round(rooms_sold / (femme_chambre['employes_mois'] * days_in_period), 1)
                if femme_chambre['employes_mois'] > 0 and days_in_period > 0 else 0,
        },
    }


def _build_rapp_p3(daily, mtd, budget, labor, days_in_period):
    """Analyse Détaillée — Rapp_p3 (simplified to department level)"""
    d = daily
    total_rev_day = d.total_revenue or 0
    total_rev_mtd = mtd['total_revenue']

    def _section(label, rev_day, rev_mtd, rev_budget, labor_dept_names):
        total_hours = 0
        total_cost = 0
        budget_cost = 0
        for dept in labor_dept_names:
            lb = labor.get(dept, {})
            total_hours += lb.get('total_hours', 0)
            total_cost += lb.get('total_labor_cost', 0)
            budget_cost += lb.get('budget_cost', 0)

        emp_mtd = round(total_hours / (days_in_period * 8), 1) if days_in_period else 0
        pct = round(total_cost / rev_mtd, 4) if rev_mtd else 0
        pct_budget = round(budget_cost / rev_budget, 4) if rev_budget else 0

        return {
            'label': label,
            'revenus': {'jour': round(rev_day, 2), 'mois': round(rev_mtd, 2),
                        'budget': round(rev_budget, 2), 'ecart': round(rev_mtd - rev_budget, 2)},
            'heures_mois': round(total_hours, 1),
            'employes_mois': emp_mtd,
            'salaires_mois': round(total_cost, 2),
            'pct_mois': pct,
            'budget_salaires': round(budget_cost, 2),
            'pct_budget': pct_budget,
            'ecart_salaires': round(total_cost - budget_cost, 2),
        }

    return {
        'chambres': _section('CHAMBRES', d.room_revenue or 0, mtd['room_revenue'],
                             budget.get('room_revenue_mtd', 0),
                             ['RECEPTION', 'ROOMS', 'HOUSEKEEPING']),
        'nourriture': _section('NOURRITURE', d.total_nourriture or 0, mtd['total_nourriture'],
                               budget.get('banquet_mtd', 0) + budget.get('spesa_mtd', 0),
                               ['KITCHEN']),
        'piazza': _section('PIAZZA', d.piazza_total or 0, mtd['piazza_total'],
                           budget.get('piazza_mtd', 0), ['RESTAURANT']),
        'banquet': _section('BANQUET NOURRITURE', d.banquet_total or 0, mtd['banquet_total'],
                            budget.get('banquet_mtd', 0), ['BANQUET']),
        'boisson': _section('BOISSON', (d.total_boisson or 0) + (d.total_bieres or 0),
                            mtd['total_boisson'] + mtd['total_bieres'],
                            budget.get('piazza_mtd', 0) * 0.3, ['BAR']),
        'location': _section('LOCATION SALLE', 0, 0, budget.get('location_mtd', 0), []),
        'buanderie': _section('BUANDERIE', 0, 0, 0, []),
        'entretien': _section('ENTRETIEN', 0, 0, 0, ['MAINTENANCE']),
        'total': {
            'revenus': {'jour': round(total_rev_day, 2), 'mois': round(total_rev_mtd, 2),
                        'budget': round(budget.get('total_revenue_mtd', 0), 2)},
        },
    }


def _build_etat_rev(daily, mtd, budget, labor, fixed_costs, days_in_period):
    """État des Revenus et Dépenses — P&L quotidien"""
    d = daily
    import calendar

    year = d.date.year
    month = d.date.month
    days_in_month = calendar.monthrange(year, month)[1]
    ratio_day = 1 / days_in_month
    ratio_mtd = days_in_period / days_in_month

    b = DEFAULT_BUDGET
    total_rev_day = d.total_revenue or 0
    total_rev_mtd = mtd['total_revenue']

    # --- CHAMBRES ---
    room_rev_day = d.room_revenue or 0
    room_rev_mtd = mtd['room_revenue']
    rooms_sold_day = d.total_rooms_sold or 0
    rooms_sold_mtd = mtd['rooms_sold']
    occ_day = (d.occupancy_rate or 0) / 100

    # Labor chambres (MTD only from DepartmentLabor)
    sal_chambres_mtd = sum(labor.get(dept, {}).get('total_labor_cost', 0)
                           for dept in ['RECEPTION', 'ROOMS', 'HOUSEKEEPING'])
    ben_chambres_mtd = sal_chambres_mtd * b['benefits_hebergement']
    cost_var_chambres_day = room_rev_day * b['cost_variable_chambres']
    cost_var_chambres_mtd = room_rev_mtd * b['cost_variable_chambres']

    # --- BANQUETS II / LOCATION ---
    location_day = 0  # Would come from NAS if tracked
    location_mtd = 0
    sal_banquet_ii_mtd = 0
    ben_banquet_ii_mtd = 0
    cost_var_bqt_day = location_day * b['cost_variable_banquet']
    cost_var_bqt_mtd = location_mtd * b['cost_variable_banquet']

    # --- RESTAURATION ---
    fb_day = d.fb_revenue or 0
    fb_mtd = mtd['fb_revenue']
    sal_resto_mtd = sum(labor.get(dept, {}).get('total_labor_cost', 0)
                        for dept in ['KITCHEN', 'RESTAURANT', 'BAR', 'BANQUET'])
    ben_resto_mtd = sal_resto_mtd * b['benefits_restauration']
    cost_var_resto_day = fb_day * b['cost_variable_resto']
    cost_var_resto_mtd = fb_mtd * b['cost_variable_resto']
    cost_autres_resto_day = fb_day * b['cost_autres_resto']
    cost_autres_resto_mtd = fb_mtd * b['cost_autres_resto']

    # --- AUTRES ---
    autres_rev_day = (d.other_revenue or 0) + (d.tabagie_total or 0)
    autres_rev_mtd = mtd['other_revenue'] + mtd['tabagie_total']
    internet_day = 0  # Tracked separately in NAS
    av_day = 0
    av_mtd = 0

    # --- AUTRES SALAIRES ---
    sal_autres_mtd = sum(labor.get(dept, {}).get('total_labor_cost', 0)
                         for dept in ['ADMINISTRATION', 'SALES', 'MAINTENANCE'])
    ben_autres_mtd = sal_autres_mtd * b['benefits_autres']

    # --- PROFIT CALCULATION ---
    total_sal_mtd = sal_chambres_mtd + sal_resto_mtd + sal_autres_mtd
    total_ben_mtd = ben_chambres_mtd + ben_resto_mtd + ben_autres_mtd
    total_sal_charges_mtd = total_sal_mtd + total_ben_mtd

    # Fixed costs (prorated to MTD)
    fc = fixed_costs
    fc_marketing = fc.get('marketing', 0) * ratio_mtd
    fc_admin = fc.get('admin', 0) * ratio_mtd
    fc_entretien = fc.get('entretien', 0) * ratio_mtd
    fc_energie = fc.get('energie', 0) * ratio_mtd
    fc_taxes = fc.get('taxes_assurances', 0) * ratio_mtd
    fc_amort = fc.get('amortissement', 0) * ratio_mtd
    fc_interet = fc.get('interet', 0) * ratio_mtd
    fc_loyer = fc.get('loyer', 0) * ratio_mtd
    total_fixed = fc_marketing + fc_admin + fc_entretien + fc_energie + fc_taxes + fc_amort + fc_interet

    # Profit
    profit_avant_fixes_day = total_rev_day - cost_var_chambres_day - cost_var_resto_day - cost_autres_resto_day - cost_var_bqt_day
    profit_avant_fixes_mtd = total_rev_mtd - total_sal_charges_mtd - cost_var_chambres_mtd - cost_var_resto_mtd - cost_autres_resto_mtd - cost_var_bqt_mtd
    profit_avant_loyer = profit_avant_fixes_mtd - total_fixed
    benefice_net = profit_avant_loyer - fc_loyer

    # Stats sidebar
    nb_clients_day = d.nb_clients or 0
    revcd = room_rev_day / nb_clients_day if nb_clients_day else 0
    rooms_avail_day = d.rooms_available or TOTAL_ROOMS
    revpar = room_rev_day / rooms_avail_day if rooms_avail_day else 0

    return {
        'chambres': {
            'louees_jour': rooms_sold_day, 'occ_jour': round(occ_day, 4),
            'ventes_jour': round(room_rev_day, 2), 'ventes_mois': round(room_rev_mtd, 2),
            'salaires_mois': round(sal_chambres_mtd, 2), 'pct_sal': round(sal_chambres_mtd / room_rev_mtd, 4) if room_rev_mtd else 0,
            'ben_marg_mois': round(ben_chambres_mtd, 2), 'pct_ben': round(b['benefits_hebergement'], 4),
            'cost_var_jour': round(cost_var_chambres_day, 2), 'cost_var_mois': round(cost_var_chambres_mtd, 2),
            'pct_var': round(b['cost_variable_chambres'], 4),
            'marge_jour': round(room_rev_day - cost_var_chambres_day, 2),
            'marge_mois': round(room_rev_mtd - sal_chambres_mtd - ben_chambres_mtd - cost_var_chambres_mtd, 2),
        },
        'banquets_ii': {
            'location_jour': round(location_day, 2), 'location_mois': round(location_mtd, 2),
            'sal_mois': round(sal_banquet_ii_mtd + ben_banquet_ii_mtd, 2),
            'cost_var_jour': round(cost_var_bqt_day, 2), 'cost_var_mois': round(cost_var_bqt_mtd, 2),
        },
        'restauration': {
            'ventes_jour': round(fb_day, 2), 'ventes_mois': round(fb_mtd, 2),
            'pct_ventes': round(fb_day / total_rev_day, 4) if total_rev_day else 0,
            'salaires_mois': round(sal_resto_mtd, 2), 'pct_sal': round(sal_resto_mtd / fb_mtd, 4) if fb_mtd else 0,
            'ben_marg_mois': round(ben_resto_mtd, 2),
            'cost_var_jour': round(cost_var_resto_day, 2), 'cost_var_mois': round(cost_var_resto_mtd, 2),
            'pct_var': round(b['cost_variable_resto'], 4),
            'cost_autres_jour': round(cost_autres_resto_day, 2), 'cost_autres_mois': round(cost_autres_resto_mtd, 2),
            'pct_autres': round(b['cost_autres_resto'], 4),
            'marge_jour': round(fb_day - cost_var_resto_day - cost_autres_resto_day, 2),
            'marge_mois': round(fb_mtd - sal_resto_mtd - ben_resto_mtd - cost_var_resto_mtd - cost_autres_resto_mtd, 2),
        },
        'autres': {
            'revenus_jour': round(autres_rev_day, 2), 'revenus_mois': round(autres_rev_mtd, 2),
            'av_mois': round(av_mtd, 2),
            'internet_jour': round(internet_day, 2),
        },
        'salaires': {
            'autres_sal_mois': round(sal_autres_mtd, 2),
            'ben_marg_mois': round(ben_autres_mtd, 2),
            'total_sal_mois': round(total_sal_mtd, 2),
            'total_sal_charges_mois': round(total_sal_charges_mtd, 2),
        },
        'profit': {
            'avant_fixes_jour': round(profit_avant_fixes_day, 2),
            'avant_fixes_mois': round(profit_avant_fixes_mtd, 2),
            'pct_fixes_jour': round(profit_avant_fixes_day / total_rev_day, 4) if total_rev_day else 0,
            'pct_fixes_mois': round(profit_avant_fixes_mtd / total_rev_mtd, 4) if total_rev_mtd else 0,
        },
        'couts_fixes': {
            'marketing': round(fc_marketing, 2),
            'admin': round(fc_admin, 2),
            'entretien': round(fc_entretien, 2),
            'energie': round(fc_energie, 2),
            'taxes': round(fc_taxes, 2),
            'amortissement': round(fc_amort, 2),
            'interet': round(fc_interet, 2),
            'total': round(total_fixed, 2),
            'loyer': round(fc_loyer, 2),
        },
        'resultat': {
            'profit_avant_loyer': round(profit_avant_loyer, 2),
            'pct_avant_loyer': round(profit_avant_loyer / total_rev_mtd, 4) if total_rev_mtd else 0,
            'benefice_net': round(benefice_net, 2),
            'pct_net': round(benefice_net / total_rev_mtd, 4) if total_rev_mtd else 0,
        },
        'stats': {
            'ventes_jour': round(total_rev_day, 2),
            'ventes_mois': round(total_rev_mtd, 2),
            'sal_jour': round(total_sal_mtd / days_in_period, 2) if days_in_period else 0,
            'sal_pct': round(total_sal_charges_mtd / total_rev_mtd, 4) if total_rev_mtd else 0,
            'tarif_moyen_jour': round(d.adr or 0, 2),
            'tarif_moyen_mois': round(mtd['adr'], 2),
            'nb_clients': nb_clients_day,
            'moy_client': round(total_rev_day / nb_clients_day, 2) if nb_clients_day else 0,
            'revcd': round(revcd, 2),
            'revpar': round(revpar, 2),
            'occ_disponible': d.rooms_available or TOTAL_ROOMS,
            'occ_simple': d.rooms_simple or 0,
            'occ_double': d.rooms_double or 0,
            'occ_suite': d.rooms_suite or 0,
            'pct_simple': round((d.rooms_simple or 0) / rooms_avail_day, 4) if rooms_avail_day else 0,
            'pct_suite': round((d.rooms_suite or 0) / rooms_avail_day, 4) if rooms_avail_day else 0,
        },
    }


# ==============================================================================
# CROSS-ANALYSIS APIs — JOINs across all 38 sheets
# ==============================================================================

@direction_bp.route('/api/direction/labor-analysis')
@direction_required
def labor_analysis():
    """Labour cost % by department — JOIN DailyLaborMetrics × DailyJourMetrics."""
    try:
        days = min(int(request.args.get('days', 30)), 365)
    except (ValueError, TypeError):
        days = 30
    end = date.today()
    start = end - timedelta(days=days)

    # Get labor data grouped by date
    labor_by_date = db.session.query(
        DailyLaborMetrics.date,
        DailyLaborMetrics.department,
        func.sum(DailyLaborMetrics.regular_hours).label('hours'),
        func.sum(DailyLaborMetrics.labor_cost).label('cost')
    ).filter(
        DailyLaborMetrics.date.between(start, end)
    ).group_by(DailyLaborMetrics.date, DailyLaborMetrics.department).all()

    # Get revenue data
    revenue_by_date = {d.date: d for d in DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(start, end)
    ).all()}

    # Build response: daily labor cost % + department breakdown
    daily = {}
    dept_totals = {}
    for row in labor_by_date:
        dt = row.date.isoformat()
        if dt not in daily:
            rev = revenue_by_date.get(row.date)
            daily[dt] = {
                'date': dt,
                'total_revenue': rev.total_revenue if rev else 0,
                'room_revenue': rev.room_revenue if rev else 0,
                'total_labor': 0, 'total_hours': 0, 'departments': {}
            }
        daily[dt]['total_labor'] += row.cost or 0
        daily[dt]['total_hours'] += row.hours or 0
        daily[dt]['departments'][row.department] = {
            'hours': round(row.hours or 0, 1), 'cost': round(row.cost or 0, 2)
        }
        dept_totals[row.department] = dept_totals.get(row.department, 0) + (row.cost or 0)

    # Calculate labor %
    for d in daily.values():
        rev = d['total_revenue'] or 0
        d['labor_pct'] = round(d['total_labor'] / rev * 100, 1) if rev > 0 else 0
        d['total_labor'] = round(d['total_labor'], 2)

    # Sort departments by total cost
    dept_sorted = sorted(dept_totals.items(), key=lambda x: -x[1])
    top_depts = [{'name': d, 'total_cost': round(c, 2)} for d, c in dept_sorted[:12]]

    return jsonify({
        'daily': sorted(daily.values(), key=lambda x: x['date']),
        'departments': top_depts,
        'summary': {
            'total_labor': round(sum(d['total_labor'] for d in daily.values()), 2),
            'total_revenue': round(sum(d['total_revenue'] for d in daily.values()), 2),
            'avg_labor_pct': round(
                sum(d['labor_pct'] for d in daily.values()) / len(daily) if daily else 0, 1),
            'days_analyzed': len(daily)
        }
    })


@direction_bp.route('/api/direction/gl-reconciliation')
@direction_required
def gl_reconciliation():
    """GL journal entries vs RJ data — JOIN JournalEntry × NightAuditSession."""
    target_date = request.args.get('date')

    if target_date:
        # Single date: detailed GL breakdown
        try:
            dt = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date'}), 400

        entries = JournalEntry.query.filter_by(audit_date=dt).order_by(
            JournalEntry.amount.desc()).all()
        nas = NightAuditSession.query.filter_by(audit_date=dt).first()

        gl_total = sum(e.amount or 0 for e in entries)
        rj_total = nas.jour_total_revenue if nas else 0

        # Group by category
        categories = {}
        for e in entries:
            code = e.gl_code or 'UNKNOWN'
            prefix = code[:3]  # Group by first 3 digits
            cat_name = {
                '075': 'Revenus & Coûts opérationnels',
                '100': 'Comptes bancaires',
                '101': 'Comptes transitoires',
                '442': 'Déductions syndicales',
                '935': 'Abonnements',
            }.get(prefix, f'GL {prefix}xxx')
            if cat_name not in categories:
                categories[cat_name] = {'entries': [], 'total': 0}
            categories[cat_name]['entries'].append(e.to_dict())
            categories[cat_name]['total'] += e.amount or 0

        for c in categories.values():
            c['total'] = round(c['total'], 2)

        return jsonify({
            'date': target_date,
            'gl_total': round(gl_total, 2),
            'rj_total': round(rj_total, 2),
            'variance': round(gl_total - rj_total, 2),
            'entry_count': len(entries),
            'categories': categories,
            'has_nas': nas is not None
        })
    else:
        # All dates with GL data
        dates = db.session.query(
            JournalEntry.audit_date,
            func.count(JournalEntry.id).label('entries'),
            func.sum(JournalEntry.amount).label('gl_total')
        ).group_by(JournalEntry.audit_date).order_by(JournalEntry.audit_date.desc()).all()

        result = []
        for d in dates:
            nas = NightAuditSession.query.filter_by(audit_date=d.audit_date).first()
            rj_total = nas.jour_total_revenue if nas else 0
            result.append({
                'date': d.audit_date.isoformat(),
                'entries': d.entries,
                'gl_total': round(d.gl_total or 0, 2),
                'rj_total': round(rj_total, 2),
                'variance': round((d.gl_total or 0) - rj_total, 2)
            })

        return jsonify({'dates': result})


@direction_bp.route('/api/direction/labor-by-department')
@direction_required
def labor_by_department():
    """Detailed labor breakdown by department for a specific period."""
    try:
        days = min(int(request.args.get('days', 30)), 365)
    except (ValueError, TypeError):
        days = 30
    end = date.today()
    start = end - timedelta(days=days)

    result = db.session.query(
        DailyLaborMetrics.department,
        func.sum(DailyLaborMetrics.regular_hours).label('total_hours'),
        func.sum(DailyLaborMetrics.overtime_hours).label('ot_hours'),
        func.sum(DailyLaborMetrics.labor_cost).label('total_cost'),
        func.avg(DailyLaborMetrics.labor_cost).label('avg_daily_cost'),
        func.count(func.distinct(DailyLaborMetrics.date)).label('days')
    ).filter(
        DailyLaborMetrics.date.between(start, end),
        DailyLaborMetrics.labor_cost > 0
    ).group_by(DailyLaborMetrics.department).order_by(
        func.sum(DailyLaborMetrics.labor_cost).desc()
    ).all()

    # Get total revenue for the period
    rev = db.session.query(
        func.sum(DailyJourMetrics.total_revenue)
    ).filter(DailyJourMetrics.date.between(start, end)).scalar() or 0

    departments = []
    for r in result:
        departments.append({
            'department': r.department,
            'total_hours': round(r.total_hours or 0, 1),
            'ot_hours': round(r.ot_hours or 0, 1),
            'total_cost': round(r.total_cost or 0, 2),
            'avg_daily_cost': round(r.avg_daily_cost or 0, 2),
            'days': r.days,
            'cost_pct_revenue': round((r.total_cost or 0) / rev * 100, 2) if rev > 0 else 0
        })

    return jsonify({
        'departments': departments,
        'period_revenue': round(rev, 2),
        'period_days': days,
        'total_labor_cost': round(sum(d['total_cost'] for d in departments), 2)
    })


@direction_bp.route('/api/direction/gl-top-accounts')
@direction_required
def gl_top_accounts():
    """Top GL accounts by total amount — for the Direction GL overview."""
    target_date = request.args.get('date')
    filters = [JournalEntry.amount != 0]
    if target_date:
        try:
            dt = datetime.strptime(target_date, '%Y-%m-%d').date()
            filters.append(JournalEntry.audit_date == dt)
        except ValueError:
            pass

    result = db.session.query(
        JournalEntry.gl_code,
        JournalEntry.description_1,
        func.sum(JournalEntry.amount).label('total'),
        func.count(JournalEntry.id).label('count')
    ).filter(*filters).group_by(
        JournalEntry.gl_code, JournalEntry.description_1
    ).order_by(func.sum(JournalEntry.amount).desc()).limit(20).all()

    return jsonify({
        'accounts': [{
            'gl_code': r.gl_code,
            'description': r.description_1,
            'total': round(r.total or 0, 2),
            'count': r.count
        } for r in result],
        'date': target_date or 'all'
    })


@direction_bp.route('/api/direction/cross-analysis')
@direction_required
def cross_analysis():
    """Complete cross-sheet analysis — combines all data sources for a date range."""
    try:
        days = min(int(request.args.get('days', 30)), 365)
    except (ValueError, TypeError):
        days = 30
    end = date.today()
    start = end - timedelta(days=days)

    # Revenue data
    revenue = DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(start, end)
    ).order_by(DailyJourMetrics.date).all()

    # Labor data aggregated by date
    labor_q = db.session.query(
        DailyLaborMetrics.date,
        func.sum(DailyLaborMetrics.labor_cost).label('total_cost'),
        func.sum(DailyLaborMetrics.regular_hours).label('total_hours')
    ).filter(
        DailyLaborMetrics.date.between(start, end)
    ).group_by(DailyLaborMetrics.date).all()
    labor_map = {r.date: {'cost': r.total_cost or 0, 'hours': r.total_hours or 0} for r in labor_q}

    # GL data aggregated by date
    gl_q = db.session.query(
        JournalEntry.audit_date,
        func.sum(JournalEntry.amount).label('gl_total'),
        func.count(JournalEntry.id).label('gl_count')
    ).filter(
        JournalEntry.audit_date.between(start, end)
    ).group_by(JournalEntry.audit_date).all()
    gl_map = {r.audit_date: {'total': r.gl_total or 0, 'count': r.gl_count} for r in gl_q}

    # NAS data
    nas_q = NightAuditSession.query.filter(
        NightAuditSession.audit_date.between(start, end)
    ).all()
    nas_map = {n.audit_date: n for n in nas_q}

    # Build combined daily view
    daily = []
    for rev in revenue:
        dt = rev.date
        lab = labor_map.get(dt, {'cost': 0, 'hours': 0})
        gl = gl_map.get(dt, {'total': 0, 'count': 0})
        nas = nas_map.get(dt)

        daily.append({
            'date': dt.isoformat(),
            'revenue': round(rev.total_revenue or 0, 2),
            'room_revenue': round(rev.room_revenue or 0, 2),
            'fb_revenue': round(rev.fb_revenue or 0, 2),
            'adr': round(rev.adr or 0, 2),
            'occupancy': round(rev.occupancy_rate or 0, 1),
            'labor_cost': round(lab['cost'], 2),
            'labor_hours': round(lab['hours'], 1),
            'labor_pct': round(lab['cost'] / rev.total_revenue * 100, 1) if rev.total_revenue else 0,
            'gl_total': round(gl['total'], 2),
            'gl_entries': gl['count'],
            'has_rj': nas is not None,
            'rj_status': nas.status if nas else None,
            'quasi_variance': round(nas.quasi_variance or 0, 2) if nas else None,
            'recap_balance': round(nas.recap_balance or 0, 2) if nas else None,
        })

    return jsonify({
        'daily': daily,
        'summary': {
            'total_revenue': round(sum(d['revenue'] for d in daily), 2),
            'total_labor': round(sum(d['labor_cost'] for d in daily), 2),
            'avg_labor_pct': round(
                sum(d['labor_pct'] for d in daily) / len(daily), 1) if daily else 0,
            'days_with_gl': sum(1 for d in daily if d['gl_entries'] > 0),
            'days_with_rj': sum(1 for d in daily if d['has_rj']),
            'total_days': len(daily)
        }
    })
