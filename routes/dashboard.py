"""
Dashboard Blueprint — Smart landing page with KPIs, alerts, shift progress & weather.

Features:
1. Tonight's KPIs vs yesterday / last week / last month
2. Intelligent threshold-based alerts & recommendations
3. Shift progress + RJ session status
4. Weather integration (from NightAuditSession)
"""

from flask import Blueprint, request, jsonify, render_template, session
from datetime import datetime, timedelta, date
import calendar
from collections import defaultdict
from database.models import (
    db, DailyJourMetrics, DailyCashRecon, DailyCardMetrics,
    DailyLaborMetrics, DepartmentLabor, MonthlyBudget, NightAuditSession,
    Shift, Task, TaskCompletion, DepositVariance,
    MonthEndChecklist, MonthlyExpense, OTBForecast, STRCompSet, TOTAL_ROOMS
)
from sqlalchemy import func, desc
from utils.auth_decorators import login_required, role_required
import json

dashboard_bp = Blueprint('dashboard', __name__)


def _r2(val):
    """Round to 2 decimals safely."""
    try:
        return round(float(val or 0), 2)
    except (ValueError, TypeError):
        return 0.0


def _parse_date(s):
    """Parse a YYYY-MM-DD string to a date object. Returns None on failure."""
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _audit_date_default():
    """
    Resolve the default audit date for night-shift endpoints.
    Night auditors work ~23h-07h. Before 07:00 the active audit night
    is still yesterday, so the midnight boundary does not reset the session.
    """
    now = datetime.now()
    if now.hour < 7:
        return (now - timedelta(days=1)).date()
    return now.date()


# ==============================================================================
# THRESHOLD ENGINE — Configurable rules that generate recommendations
# ==============================================================================

# Thresholds are (metric, operator, value, severity, message_template, action)
# Severity: critical, warning, info, success
# Action: actionable suggestion

THRESHOLDS = {
    'occupation': [
        ('occupancy_rate', '<', 45, 'critical',
         "Occupation critique à {value}% — bien en dessous du seuil rentable",
         "Activer promotions OTA d'urgence, contacter groupes locaux, offrir tarif walk-in agressif"),
        ('occupancy_rate', '<', 60, 'warning',
         "Occupation basse à {value}% (moy. {avg}%)",
         "Considérer pricing walk-in promotionnel, vérifier les OTA, appeler les no-shows potentiels"),
        ('occupancy_rate', '>', 90, 'success',
         "Excellent taux d'occupation à {value}%!",
         "Maximiser l'upsell suites/chambres premium, activer le pricing dynamique à la hausse"),
    ],
    'adr': [
        ('adr', 'below_avg_pct', 15, 'warning',
         "ADR à {value}$ — {gap}% sous la moyenne de {avg}$",
         "Revoir la stratégie de pricing pour ce jour de semaine, vérifier les tarifs corporate"),
        ('adr', 'above_avg_pct', 15, 'success',
         "ADR excellent à {value}$ — {gap}% au-dessus de la moyenne!",
         "Maintenir le positionnement, surveiller l'impact sur l'occupation"),
    ],
    'revpar': [
        ('revpar', 'below_avg_pct', 20, 'warning',
         "RevPAR faible à {value}$ (moy. {avg}$)",
         "Le RevPAR combine ADR et occupation — identifier lequel des deux tire vers le bas"),
    ],
    'fb': [
        ('fb_per_client', '<', 12, 'warning',
         "F&B par client bas à {value}$ (cible >15$)",
         "Revoir le menu, former le personnel sur l'upsell boissons, proposer des combos"),
        ('fb_per_client', '>', 25, 'success',
         "Excellent F&B par client à {value}$!",
         "Analyser quels plats/boissons performent pour répliquer"),
    ],
    'cash': [
        ('quasimodo_variance', 'abs>', 10, 'critical',
         "Variance Quasimodo élevée: {value}$ (seuil ±5$)",
         "Vérifier la réconciliation des cartes, recompter la caisse, chercher transaction manquante"),
        ('quasimodo_variance', 'abs>', 5, 'warning',
         "Variance Quasimodo de {value}$ — au-dessus du seuil normal",
         "Revoir les transactions Transelect, vérifier les annulations de la soirée"),
        ('surplus_deficit', 'abs>', 50, 'critical',
         "Surplus/Déficit de caisse important: {value}$",
         "Recompter la caisse immédiatement, vérifier les remboursements et gratuités"),
        ('surplus_deficit', 'abs>', 20, 'warning',
         "Écart de caisse de {value}$ — supérieur à la normale",
         "Vérifier les transactions cash, les remboursements et les corrections"),
    ],
    'labor': [
        ('labor_pct', '>', 38, 'critical',
         "Ratio main-d'œuvre/revenu à {value}% — très élevé (cible <30%)",
         "Revoir les horaires, identifier les départements en sureffectif, optimiser les shifts"),
        ('labor_pct', '>', 32, 'warning',
         "Ratio main-d'œuvre à {value}% — au-dessus de la cible de 30%",
         "Surveiller les heures supplémentaires, ajuster les horaires pour les prochains jours"),
    ],
    'cards': [
        ('amex_pct', '>', 30, 'info',
         "Part AMEX à {value}% — frais d'escompte élevés",
         "AMEX coûte ~2.65% vs 1.5% Visa/MC. Encourager Visa/MC/Débit au check-in si possible"),
    ],
    'trends': [
        ('occ_trend_3d', '<', -10, 'warning',
         "Occupation en baisse de {value}pts sur 3 jours consécutifs",
         "Tendance baissière — vérifier calendrier événements, ajuster tarifs proactivement"),
        ('adr_trend_7d', '<', -8, 'warning',
         "ADR en baisse de {value}$ sur la dernière semaine",
         "Revoir la stratégie de pricing, comparer avec les tarifs des concurrents"),
        ('fb_trend_7d', '<', -15, 'info',
         "Revenus F&B en baisse de {value}% sur 7 jours",
         "Vérifier heures d'ouverture restaurant, événements spéciaux, promotions"),
    ],
}


def evaluate_thresholds(today_data, avg_data, trend_data, cash_data, labor_data, card_data):
    """
    Evaluate all thresholds against current data.
    Returns list of {severity, category, message, action, metric, value}.
    """
    alerts = []

    def add_alert(severity, category, message, action, metric='', value=0):
        alerts.append({
            'severity': severity,
            'category': category,
            'message': message,
            'action': action,
            'metric': metric,
            'value': value,
        })

    if not today_data:
        return alerts

    # --- Occupation ---
    occ = today_data.get('occupancy_rate', 0)
    occ_avg = avg_data.get('occupancy_rate', 70)
    for _, op, threshold, sev, msg, action in THRESHOLDS['occupation']:
        if op == '<' and occ < threshold:
            add_alert(sev, 'occupation', msg.format(value=_r2(occ), avg=_r2(occ_avg)),
                       action, 'occupancy_rate', occ)
            break
        elif op == '>' and occ > threshold:
            add_alert(sev, 'occupation', msg.format(value=_r2(occ), avg=_r2(occ_avg)),
                       action, 'occupancy_rate', occ)
            break

    # --- ADR ---
    adr = today_data.get('adr', 0)
    adr_avg = avg_data.get('adr', 150)
    if adr_avg > 0:
        gap_pct = _r2(abs(adr - adr_avg) / adr_avg * 100)
        for _, op, threshold, sev, msg, action in THRESHOLDS['adr']:
            if op == 'below_avg_pct' and adr < adr_avg and gap_pct >= threshold:
                add_alert(sev, 'adr', msg.format(value=_r2(adr), avg=_r2(adr_avg), gap=gap_pct),
                           action, 'adr', adr)
                break
            elif op == 'above_avg_pct' and adr > adr_avg and gap_pct >= threshold:
                add_alert(sev, 'adr', msg.format(value=_r2(adr), avg=_r2(adr_avg), gap=gap_pct),
                           action, 'adr', adr)
                break

    # --- RevPAR ---
    revpar = today_data.get('revpar', 0)
    revpar_avg = avg_data.get('revpar', 100)
    if revpar_avg > 0:
        gap_pct = _r2(abs(revpar - revpar_avg) / revpar_avg * 100)
        for _, op, threshold, sev, msg, action in THRESHOLDS['revpar']:
            if op == 'below_avg_pct' and revpar < revpar_avg and gap_pct >= threshold:
                add_alert(sev, 'revpar', msg.format(value=_r2(revpar), avg=_r2(revpar_avg)),
                           action, 'revpar', revpar)
                break

    # --- F&B per client ---
    fb_pc = today_data.get('fb_per_client', 0)
    for _, op, threshold, sev, msg, action in THRESHOLDS['fb']:
        if op == '<' and fb_pc > 0 and fb_pc < threshold:
            add_alert(sev, 'fb', msg.format(value=_r2(fb_pc)), action, 'fb_per_client', fb_pc)
            break
        elif op == '>' and fb_pc > threshold:
            add_alert(sev, 'fb', msg.format(value=_r2(fb_pc)), action, 'fb_per_client', fb_pc)
            break

    # --- Cash/Recon ---
    if cash_data:
        quasi = cash_data.get('quasimodo_variance', 0)
        surplus = cash_data.get('surplus_deficit', 0)
        for _, op, threshold, sev, msg, action in THRESHOLDS['cash']:
            metric_val = quasi if 'quasimodo' in _ else surplus
            if op == 'abs>' and abs(metric_val) > threshold:
                add_alert(sev, 'cash', msg.format(value=_r2(metric_val)),
                           action, _, metric_val)
                break

    # --- Labor ---
    if labor_data:
        labor_pct = labor_data.get('labor_pct', 0)
        for _, op, threshold, sev, msg, action in THRESHOLDS['labor']:
            if op == '>' and labor_pct > threshold:
                add_alert(sev, 'labor', msg.format(value=_r2(labor_pct)),
                           action, 'labor_pct', labor_pct)
                break

    # --- Card mix ---
    if card_data:
        amex_pct = card_data.get('amex_pct', 0)
        for _, op, threshold, sev, msg, action in THRESHOLDS['cards']:
            if op == '>' and amex_pct > threshold:
                add_alert(sev, 'cards', msg.format(value=_r2(amex_pct)),
                           action, 'amex_pct', amex_pct)
                break

    # --- Trend alerts ---
    if trend_data:
        for metric, op, threshold, sev, msg, action in THRESHOLDS['trends']:
            val = trend_data.get(metric, 0)
            if op == '<' and val < threshold:
                add_alert(sev, 'trends', msg.format(value=_r2(val)),
                           action, metric, val)

    return alerts


# ==============================================================================
# PAGE ROUTE
# ==============================================================================

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html')


@dashboard_bp.route('/dashboard/gm')
@login_required
@role_required('gm', 'gsm', 'admin')
def gm_briefing_page():
    """GM Morning Briefing — role-restricted dashboard page."""
    return render_template('dashboard/gm_briefing.html')


@dashboard_bp.route('/dashboard/accounting')
@login_required
@role_required('accounting', 'gm', 'admin')
def accounting_page():
    """Accounting Month-End Dashboard — role-restricted page."""
    return render_template('dashboard/accounting.html')


# ==============================================================================
# API ENDPOINT
# ==============================================================================

@dashboard_bp.route('/api/dashboard/smart')
@login_required
def smart_dashboard():
    """
    Smart dashboard endpoint — returns KPIs, comparisons, alerts,
    shift progress, and weather for the landing page.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)

    # =========================================================================
    # 1. TONIGHT'S KPIs (most recent day with data)
    # =========================================================================
    latest = DailyJourMetrics.query.order_by(desc(DailyJourMetrics.date)).first()
    if not latest:
        return jsonify({'success': True, 'has_data': False})

    latest_date = latest.date
    today_data = {
        'date': latest_date.isoformat(),
        'occupancy_rate': _r2(latest.occupancy_rate),
        'adr': _r2(latest.adr),
        'revpar': _r2(latest.revpar),
        'room_revenue': _r2(latest.room_revenue),
        'fb_revenue': _r2(latest.fb_revenue),
        'total_revenue': _r2(latest.total_revenue),
        'nb_clients': latest.nb_clients or 0,
        'rooms_sold': (latest.rooms_simple or 0) + (latest.rooms_double or 0) +
                      (latest.rooms_suite or 0) + (latest.rooms_comp or 0),
        'rooms_comp': latest.rooms_comp or 0,
        'hors_usage': latest.rooms_hors_usage or 0,
    }

    # F&B per client
    if today_data['nb_clients'] > 0:
        today_data['fb_per_client'] = _r2(today_data['fb_revenue'] / today_data['nb_clients'])
    else:
        today_data['fb_per_client'] = 0

    # =========================================================================
    # 2. COMPARISON DATA (yesterday, last week same DOW, last month avg)
    # =========================================================================
    def get_day_data(target_date):
        m = DailyJourMetrics.query.filter_by(date=target_date).first()
        if not m:
            return None
        return {
            'date': m.date.isoformat(),
            'occupancy_rate': _r2(m.occupancy_rate),
            'adr': _r2(m.adr),
            'revpar': _r2(m.revpar),
            'room_revenue': _r2(m.room_revenue),
            'fb_revenue': _r2(m.fb_revenue),
            'total_revenue': _r2(m.total_revenue),
            'nb_clients': m.nb_clients or 0,
        }

    yesterday_data = get_day_data(latest_date - timedelta(days=1))
    last_week_data = get_day_data(latest_date - timedelta(days=7))

    # Last 30 days average
    thirty_days_ago = latest_date - timedelta(days=30)
    avg_metrics = db.session.query(
        func.avg(DailyJourMetrics.occupancy_rate),
        func.avg(DailyJourMetrics.adr),
        func.avg(DailyJourMetrics.revpar),
        func.avg(DailyJourMetrics.room_revenue),
        func.avg(DailyJourMetrics.fb_revenue),
        func.avg(DailyJourMetrics.total_revenue),
        func.avg(DailyJourMetrics.nb_clients),
    ).filter(DailyJourMetrics.date.between(thirty_days_ago, latest_date)).first()

    avg_data = {
        'occupancy_rate': _r2(avg_metrics[0]),
        'adr': _r2(avg_metrics[1]),
        'revpar': _r2(avg_metrics[2]),
        'room_revenue': _r2(avg_metrics[3]),
        'fb_revenue': _r2(avg_metrics[4]),
        'total_revenue': _r2(avg_metrics[5]),
        'nb_clients': _r2(avg_metrics[6]),
    }

    # Compute deltas
    def compute_deltas(current, compare, label):
        if not compare:
            return None
        deltas = {}
        for key in ['occupancy_rate', 'adr', 'revpar', 'room_revenue', 'fb_revenue', 'total_revenue']:
            curr = current.get(key, 0)
            prev = compare.get(key, 0)
            if prev and prev != 0:
                deltas[key] = _r2((curr - prev) / abs(prev) * 100)
            else:
                deltas[key] = 0
        return {'label': label, 'data': compare, 'deltas': deltas}

    comparisons = {
        'yesterday': compute_deltas(today_data, yesterday_data, 'vs Hier'),
        'last_week': compute_deltas(today_data, last_week_data, 'vs Sem. passée'),
        'avg_30d': compute_deltas(today_data, avg_data, 'vs Moy. 30j'),
    }

    # =========================================================================
    # 3. TREND DATA (for threshold engine)
    # =========================================================================
    recent_7 = DailyJourMetrics.query.filter(
        DailyJourMetrics.date.between(latest_date - timedelta(days=7), latest_date)
    ).order_by(DailyJourMetrics.date).all()

    trend_data = {}
    if len(recent_7) >= 3:
        last3_occ = [m.occupancy_rate or 0 for m in recent_7[-3:]]
        trend_data['occ_trend_3d'] = _r2(last3_occ[-1] - last3_occ[0])

    if len(recent_7) >= 2:
        trend_data['adr_trend_7d'] = _r2((recent_7[-1].adr or 0) - (recent_7[0].adr or 0))
        fb_first = recent_7[0].fb_revenue or 0
        fb_last = recent_7[-1].fb_revenue or 0
        if fb_first > 0:
            trend_data['fb_trend_7d'] = _r2((fb_last - fb_first) / fb_first * 100)

    # Mini sparkline data (last 7 days)
    sparklines = {
        'occupancy': [_r2(m.occupancy_rate) for m in recent_7],
        'adr': [_r2(m.adr) for m in recent_7],
        'revpar': [_r2(m.revpar) for m in recent_7],
        'revenue': [_r2(m.total_revenue) for m in recent_7],
        'dates': [m.date.isoformat() for m in recent_7],
    }

    # =========================================================================
    # 4. CASH/RECON DATA (latest)
    # =========================================================================
    cash_rec = DailyCashRecon.query.order_by(desc(DailyCashRecon.date)).first()
    cash_data = None
    if cash_rec:
        cash_data = {
            'date': cash_rec.date.isoformat(),
            'quasimodo_variance': _r2(cash_rec.quasimodo_variance),
            'surplus_deficit': _r2(cash_rec.surplus_deficit),
            'deposit_cdn': _r2(cash_rec.deposit_cdn),
            'deposit_usd': _r2(cash_rec.deposit_usd),
            'auditor_name': cash_rec.auditor_name,
        }

    # =========================================================================
    # 5. LABOR DATA (latest month)
    # =========================================================================
    labor_data = None
    latest_labor = DepartmentLabor.query.order_by(
        desc(DepartmentLabor.year), desc(DepartmentLabor.month)
    ).first()
    if latest_labor:
        latest_y, latest_m = latest_labor.year, latest_labor.month
        all_labor = DepartmentLabor.query.filter_by(year=latest_y, month=latest_m).all()
        total_labor_cost = sum(dl.total_labor_cost or 0 for dl in all_labor)

        # Get revenue for same month
        month_rev = db.session.query(func.sum(DailyJourMetrics.total_revenue)).filter(
            DailyJourMetrics.year == latest_y,
            DailyJourMetrics.month == latest_m
        ).scalar() or 0

        # Prorate labor cost when the labor month is the current partial month.
        # DepartmentLabor stores full-month budgeted/posted cost, but if we are
        # mid-month we only have partial revenue — prorating prevents a misleadingly
        # high ratio (e.g. full month labor vs. 15 days of revenue).
        days_in_month = calendar.monthrange(latest_y, latest_m)[1]
        days_with_revenue = db.session.query(func.count(DailyJourMetrics.id)).filter(
            DailyJourMetrics.year == latest_y,
            DailyJourMetrics.month == latest_m
        ).scalar() or 0

        is_partial_month = (
            latest_y == today.year
            and latest_m == today.month
            and days_with_revenue < days_in_month
        )

        if is_partial_month and days_in_month > 0:
            prorated_labor_cost = total_labor_cost * (days_with_revenue / days_in_month)
        else:
            prorated_labor_cost = total_labor_cost

        labor_pct = _r2(prorated_labor_cost / month_rev * 100) if month_rev > 0 else 0
        labor_data = {
            'month': f"{latest_y}-{latest_m:02d}",
            'total_cost': _r2(total_labor_cost),
            'prorated_cost': _r2(prorated_labor_cost),
            'revenue': _r2(month_rev),
            'labor_pct': labor_pct,
            'is_partial_month': is_partial_month,
            'days_elapsed': days_with_revenue,
            'days_in_month': days_in_month,
        }

    # =========================================================================
    # 6. CARD MIX DATA (latest day)
    # =========================================================================
    card_data = None
    latest_cards = DailyCardMetrics.query.filter_by(date=latest_date).all()
    if latest_cards:
        total_vol = sum(c.pos_total or 0 for c in latest_cards)
        amex_vol = sum(c.pos_total or 0 for c in latest_cards if c.card_type == 'AMEX')
        card_data = {
            'total_volume': _r2(total_vol),
            'amex_pct': _r2(amex_vol / total_vol * 100) if total_vol > 0 else 0,
        }

    # =========================================================================
    # 7. THRESHOLD ALERTS
    # =========================================================================
    alerts = evaluate_thresholds(today_data, avg_data, trend_data, cash_data, labor_data, card_data)

    # Sort: critical first, then warning, info, success
    severity_order = {'critical': 0, 'warning': 1, 'info': 2, 'success': 3}
    alerts.sort(key=lambda a: severity_order.get(a['severity'], 9))

    # =========================================================================
    # 8. SHIFT PROGRESS
    # =========================================================================
    shift_data = None
    try:
        current_shift = Shift.query.filter_by(
            date=today
        ).order_by(desc(Shift.id)).first()

        if current_shift:
            total_tasks = Task.query.count()
            completed = TaskCompletion.query.filter_by(shift_id=current_shift.id).count()
            shift_data = {
                'id': current_shift.id,
                'date': current_shift.date.isoformat(),
                'total_tasks': total_tasks,
                'completed_tasks': completed,
                'progress_pct': _r2(completed / total_tasks * 100) if total_tasks > 0 else 0,
                'status': 'completed' if completed >= total_tasks else 'in_progress',
            }
    except Exception:
        pass

    # =========================================================================
    # 9. RJ SESSION STATUS
    # =========================================================================
    rj_data = None
    try:
        rj_session = NightAuditSession.query.filter_by(
            audit_date=today
        ).first()
        if not rj_session:
            rj_session = NightAuditSession.query.filter_by(
                audit_date=yesterday
            ).first()

        if rj_session:
            rj_data = {
                'date': rj_session.audit_date.isoformat(),
                'status': rj_session.status,
                'auditor': rj_session.auditor_name,
            }
    except Exception:
        pass

    # =========================================================================
    # 10. WEATHER (from latest NightAuditSession)
    # =========================================================================
    weather_data = None
    try:
        weather_session = NightAuditSession.query.filter(
            NightAuditSession.temperature.isnot(None)
        ).order_by(desc(NightAuditSession.audit_date)).first()
        if weather_session:
            weather_data = {
                'temperature': weather_session.temperature,
                'condition': weather_session.weather_condition,
                'date': weather_session.audit_date.isoformat(),
            }
    except Exception:
        pass

    # =========================================================================
    # 11. QUICK STATS (for context)
    # =========================================================================
    total_days = DailyJourMetrics.query.count()
    date_range = db.session.query(
        func.min(DailyJourMetrics.date),
        func.max(DailyJourMetrics.date)
    ).first()

    # This month performance
    month_start = latest_date.replace(day=1)
    mtd_metrics = db.session.query(
        func.avg(DailyJourMetrics.occupancy_rate),
        func.avg(DailyJourMetrics.adr),
        func.sum(DailyJourMetrics.total_revenue),
        func.count(DailyJourMetrics.id),
    ).filter(DailyJourMetrics.date.between(month_start, latest_date)).first()

    mtd_data = {
        'avg_occ': _r2(mtd_metrics[0]),
        'avg_adr': _r2(mtd_metrics[1]),
        'total_revenue': _r2(mtd_metrics[2]),
        'days': mtd_metrics[3] or 0,
    }

    # Budget comparison for this month
    budget = MonthlyBudget.query.filter_by(
        year=latest_date.year, month=latest_date.month
    ).first()
    budget_data = None
    if budget and mtd_data['total_revenue'] > 0:
        days_in_month = calendar.monthrange(latest_date.year, latest_date.month)[1]
        days_elapsed = mtd_data['days']
        prorated_budget = (budget.total_revenue or 0) * (days_elapsed / days_in_month)
        variance = mtd_data['total_revenue'] - prorated_budget
        budget_data = {
            'prorated_budget': _r2(prorated_budget),
            'variance': _r2(variance),
            'variance_pct': _r2(variance / prorated_budget * 100) if prorated_budget > 0 else 0,
            'on_track': variance >= 0,
        }

    return jsonify({
        'success': True,
        'has_data': True,
        'today': today_data,
        'comparisons': comparisons,
        'sparklines': sparklines,
        'alerts': alerts,
        'shift': shift_data,
        'rj': rj_data,
        'weather': weather_data,
        'cash': cash_data,
        'labor': labor_data,
        'mtd': mtd_data,
        'budget': budget_data,
        'meta': {
            'total_days': total_days,
            'date_from': date_range[0].isoformat() if date_range[0] else None,
            'date_to': date_range[1].isoformat() if date_range[1] else None,
        }
    })


# ==============================================================================
# AUDITOR PANEL ENDPOINT
# ==============================================================================

@dashboard_bp.route('/api/dashboard/auditor-panel')
@login_required
def auditor_panel():
    """
    Night Auditor Error Detection Panel.

    Returns three sections:
      1. balance_grid      — Recap / Transelect / AR / Quasimodo balance status
      2. outstanding_items — Sorted list of issues that require attention
      3. variance_alerts   — Contextual variance data with 7-day rolling average

    Query param:
      ?date=YYYY-MM-DD   Override audit date (defaults to tonight's audit date,
                         i.e. yesterday when called before 07:00).
    """
    # ------------------------------------------------------------------
    # Resolve audit date
    # ------------------------------------------------------------------
    audit_date = _parse_date(request.args.get('date')) or _audit_date_default()

    # ------------------------------------------------------------------
    # Primary data: tonight's NightAuditSession
    # ------------------------------------------------------------------
    nas = NightAuditSession.query.filter_by(audit_date=audit_date).first()

    # Prior night session (for fallback_notes)
    prior_date = audit_date - timedelta(days=1)
    prior_nas = NightAuditSession.query.filter_by(audit_date=prior_date).first()

    # 7-day rolling Quasimodo average (excludes tonight — context only)
    seven_days_back = audit_date - timedelta(days=7)
    recent_cash = DailyCashRecon.query.filter(
        DailyCashRecon.date.between(seven_days_back, audit_date - timedelta(days=1))
    ).all()
    avg_quasi_7d = (
        sum(abs(r.quasimodo_variance or 0) for r in recent_cash) / len(recent_cash)
        if recent_cash else None
    )

    # ------------------------------------------------------------------
    # Section 1 — Balance Status Grid
    # ------------------------------------------------------------------
    def _balance_check(is_balanced, value, threshold, label):
        """
        Produce a single balance-check dict.
        status is 'green' when balanced, 'red' when unbalanced, 'pending'
        when no session data exists yet (is_balanced is None).
        """
        if is_balanced is None:
            return {'label': label, 'status': 'pending', 'value': None,
                    'threshold': threshold, 'is_ok': None}
        return {
            'label':     label,
            'status':    'green' if is_balanced else 'red',
            'value':     _r2(value),
            'threshold': threshold,
            'is_ok':     bool(is_balanced),
        }

    if nas:
        recap_check = _balance_check(
            nas.is_recap_balanced,
            abs(nas.recap_balance or 0),
            0.02,
            'Récap',
        )
        transelect_check = _balance_check(
            nas.is_transelect_balanced,
            abs(nas.transelect_variance or 0),
            1.00,
            'Transelect',
        )
        ar_check = _balance_check(
            nas.is_ar_balanced,
            abs(nas.geac_ar_variance or 0),
            0.02,
            'AR (GEAC)',
        )
        # Quasimodo uses a numeric threshold (±5$), not the boolean flag pattern
        quasi_var = nas.quasi_variance or 0
        quasi_check = {
            'label':     'Quasimodo',
            'status':    'green' if abs(quasi_var) <= 5.0 else 'red',
            'value':     _r2(quasi_var),
            'threshold': 5.00,
            'is_ok':     abs(quasi_var) <= 5.00,
        }
        overall_balanced = nas.is_fully_balanced
    else:
        _pending = {'status': 'pending', 'value': None, 'is_ok': None}
        recap_check      = dict(_pending, label='Récap',      threshold=0.02)
        transelect_check = dict(_pending, label='Transelect', threshold=1.00)
        ar_check         = dict(_pending, label='AR (GEAC)',  threshold=0.02)
        quasi_check      = dict(_pending, label='Quasimodo',  threshold=5.00)
        overall_balanced = None

    balance_grid = {
        'overall_balanced': overall_balanced,
        'checks': {
            'recap':      recap_check,
            'transelect': transelect_check,
            'ar_geac':    ar_check,
            'quasimodo':  quasi_check,
        },
    }

    # ------------------------------------------------------------------
    # Section 2 — Outstanding Items
    # ------------------------------------------------------------------
    outstanding = []

    if nas:
        # Locked sessions are read-only — suppress actionable suggestions
        is_locked = nas.status == 'locked'

        def _action(text):
            return '' if is_locked else text

        # Recap balance
        if not nas.is_recap_balanced:
            outstanding.append({
                'priority': 'high',
                'category': 'RECAP',
                'issue':    f"Récap non balancé — variance: {nas.recap_balance or 0:+.2f}$",
                'action':   _action("Vérifier les lectures Lightspeed et POS, recompter les dépôts."),
                'value':    _r2(nas.recap_balance),
            })

        # Transelect balance
        if not nas.is_transelect_balanced:
            outstanding.append({
                'priority': 'high',
                'category': 'TRANSELECT',
                'issue':    f"Transelect non balancé — variance: {nas.transelect_variance or 0:+.2f}$",
                'action':   _action("Comparer terminaux restaurant vs réception, vérifier Daily Rev FreedomPay."),
                'value':    _r2(nas.transelect_variance),
            })

        # AR balance
        if not nas.is_ar_balanced:
            outstanding.append({
                'priority': 'high',
                'category': 'AR_GEAC',
                'issue':    f"AR GEAC non balancé — variance: {nas.geac_ar_variance or 0:+.2f}$",
                'action':   _action("Vérifier solde précédent, charges et paiements du jour."),
                'value':    _r2(nas.geac_ar_variance),
            })

        # Quasimodo variance
        quasi_var = nas.quasi_variance or 0
        if abs(quasi_var) > 5.0:
            outstanding.append({
                'priority': 'critical' if abs(quasi_var) > 10.0 else 'high',
                'category': 'QUASIMODO',
                'issue':    f"Variance Quasimodo: {quasi_var:+.2f}$ (seuil ±5$)",
                'action':   _action(
                    "Revoir les cartes par terminal (Débit/Visa/MC/Amex), chercher transaction manquante."
                ),
                'value':    _r2(quasi_var),
            })

        # GL 101100 suspense
        if abs(nas.gl_101100_variance or 0) > 0.02:
            outstanding.append({
                'priority': 'medium',
                'category': 'GL_101100',
                'issue':    f"Compte GL 101100 — variance non résolue: {nas.gl_101100_variance or 0:+.2f}$",
                'action':   _action("Vérifier les entrées du journal EJ et réconcilier le solde."),
                'value':    _r2(nas.gl_101100_variance),
            })

        # GL 100401 suspense
        if abs(nas.gl_100401_variance or 0) > 0.02:
            outstanding.append({
                'priority': 'medium',
                'category': 'GL_100401',
                'issue':    f"Compte GL 100401 — variance: {nas.gl_100401_variance or 0:+.2f}$",
                'action':   _action("Vérifier le compte bancaire vs dépôt net Récap."),
                'value':    _r2(nas.gl_100401_variance),
            })

        # Internet variance (Lightspeed 36.1 vs 36.5)
        if abs(nas.internet_variance or 0) > 0.02:
            outstanding.append({
                'priority': 'medium',
                'category': 'INTERNET',
                'issue':    f"Variance Internet: {nas.internet_variance or 0:+.2f}$ (LS 36.1 vs 36.5)",
                'action':   _action("Comparer Cashier Detail 36.1 et 36.5, ajuster si nécessaire."),
                'value':    _r2(nas.internet_variance),
            })

        # Sonifi variance (CD 35.2 vs courriel)
        if abs(nas.sonifi_variance or 0) > 0.02:
            outstanding.append({
                'priority': 'medium',
                'category': 'SONIFI',
                'issue':    f"Variance Sonifi: {nas.sonifi_variance or 0:+.2f}$ (CD 35.2 vs courriel)",
                'action':   _action("Vérifier montant courriel Sonifi 03h00 vs Cashier Detail 35.2."),
                'value':    _r2(nas.sonifi_variance),
            })

        # Session not yet submitted
        if nas.status in ('draft', 'in_progress'):
            outstanding.append({
                'priority': 'info',
                'category': 'SUBMISSION',
                'issue':    f"RJ en statut '{nas.status}' — non soumis",
                'action':   "Compléter toutes les sections et soumettre avant 06h00.",
                'value':    None,
            })

    # Sort: critical > high > medium > info
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'info': 3}
    outstanding.sort(key=lambda x: priority_order.get(x['priority'], 9))

    # ------------------------------------------------------------------
    # Section 3 — Variance Alerts (with 7-day context)
    # ------------------------------------------------------------------
    variance_alerts = []

    if nas:
        quasi_var = nas.quasi_variance or 0

        # Quasimodo — with rolling 7-day average for context
        variance_alerts.append({
            'metric':             'quasimodo_variance',
            'label':              'Variance Quasimodo',
            'current':            _r2(quasi_var),
            'threshold':          5.00,
            'threshold_critical': 10.00,
            'avg_7d':             round(avg_quasi_7d, 2) if avg_quasi_7d is not None else None,
            'status':             (
                'ok'      if abs(quasi_var) <= 5.0  else
                'warning' if abs(quasi_var) <= 10.0 else
                'critical'
            ),
            'context': (
                f"Moy. 7 jours: \u00b1{avg_quasi_7d:.2f}$"
                if avg_quasi_7d is not None
                else "Pas de donn\u00e9es de comparaison"
            ),
        })

        # Surplus / Deficit — recap_balance is the surplus/deficit equivalent
        surplus = nas.recap_balance or 0
        variance_alerts.append({
            'metric':             'surplus_deficit',
            'label':              'Surplus / D\u00e9ficit caisse',
            'current':            _r2(surplus),
            'threshold':          20.00,
            'threshold_critical': 50.00,
            'avg_7d':             None,
            'status':             (
                'ok'      if abs(surplus) <= 20.0 else
                'warning' if abs(surplus) <= 50.0 else
                'critical'
            ),
            'context': "Diff\u00e9rence entre encaisse compt\u00e9e et syst\u00e8me",
        })

        # AR variance
        ar_var = nas.geac_ar_variance or 0
        variance_alerts.append({
            'metric':    'ar_variance',
            'label':     'Variance AR GEAC',
            'current':   _r2(ar_var),
            'threshold': 0.02,
            'avg_7d':    None,
            'status':    'ok' if abs(ar_var) <= 0.02 else 'critical',
            'context':   "Doit \u00eatre \u00b10.02$ pour fermeture propre",
        })

    # ------------------------------------------------------------------
    # Build and return response
    # ------------------------------------------------------------------
    session_exists = nas is not None
    is_locked = session_exists and nas.status == 'locked'

    return jsonify({
        'success':        True,
        'audit_date':     audit_date.isoformat(),
        'session_exists': session_exists,
        'session_status': nas.status if nas else None,
        'session_locked': is_locked,
        'auditor':        nas.auditor_name if nas else None,
        'generated_at':   datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),

        'balance_grid':      balance_grid,
        'outstanding_items': outstanding,
        'variance_alerts':   variance_alerts,

        'fallback_notes': {
            'session_found':      session_exists,
            'prior_night_found':  prior_nas is not None,
            'avg_7d_data_points': len(recent_cash),
        },
    })


# ==============================================================================
# GM MORNING BRIEFING
# ==============================================================================

@dashboard_bp.route('/api/dashboard/gm-briefing')
@login_required
@role_required('gm', 'gsm', 'admin')
def gm_briefing():
    """
    GM Morning Briefing — four-panel summary of last night's performance,
    operational status, forward OTB look, and trend context.

    Query param:
        date (YYYY-MM-DD): briefing date; defaults to most recent DJM row.
    """

    # =========================================================================
    # Resolve briefing date
    # =========================================================================
    target_date = _parse_date(request.args.get('date'))
    if not target_date:
        latest_djm = DailyJourMetrics.query.order_by(desc(DailyJourMetrics.date)).first()
        if not latest_djm:
            return jsonify({'success': True, 'has_data': False, 'reason': 'no_djm_data'})
        target_date = latest_djm.date

    # =========================================================================
    # Helper: variance dict {value, pct, direction}.
    # Returns all-null when reference is missing or zero.
    # =========================================================================
    def _variance(actual, reference):
        if reference is None or reference == 0:
            return {'value': None, 'pct': None, 'direction': 'unknown'}
        diff = _r2(actual - reference)
        pct  = _r2(diff / abs(reference) * 100)
        return {
            'value':     diff,
            'pct':       pct,
            'direction': 'above' if diff >= 0 else 'below',
        }

    # =========================================================================
    # PANEL 1 — Last Night Performance
    # =========================================================================
    night = DailyJourMetrics.query.filter_by(date=target_date).first()
    if not night:
        return jsonify({
            'success':  True,
            'has_data': False,
            'reason':   'no_djm_for_date',
            'briefing_date': target_date.isoformat(),
        })

    # Computed KPIs
    rooms_sold     = night.total_rooms_sold or 0
    oos_rooms_djm  = night.rooms_hors_usage or 0
    avail_adjusted = TOTAL_ROOMS - oos_rooms_djm
    occ_adjusted   = (
        rooms_sold / avail_adjusted * 100
        if avail_adjusted > 0
        else (night.occupancy_rate or 0)
    )
    rooms_paid    = rooms_sold - (night.rooms_comp or 0)
    effective_adr = (
        night.room_revenue / rooms_paid
        if rooms_paid > 0
        else (night.adr or 0)
    )
    comp_pct = _r2(night.rooms_comp / rooms_sold * 100) if rooms_sold > 0 else 0

    # Budget prorated to one day
    budget = MonthlyBudget.query.filter_by(
        year=target_date.year, month=target_date.month
    ).first()
    days_in_month      = calendar.monthrange(target_date.year, target_date.month)[1]
    budget_occ_daily   = (
        _r2(budget.rooms_target / TOTAL_ROOMS / days_in_month * 100)
        if budget and TOTAL_ROOMS > 0 else None
    )
    budget_adr_daily   = _r2(budget.adr_target)   if budget else None
    budget_room_rev_d  = _r2(budget.room_revenue / days_in_month) if budget else None
    budget_total_rev_d = _r2(budget.total_revenue / days_in_month) if budget else None
    budget_revpar_daily = (
        _r2(budget_room_rev_d / TOTAL_ROOMS)
        if budget_room_rev_d is not None and TOTAL_ROOMS > 0
        else None
    )

    # LY same date — fallback: 364 days back (same DOW)
    ly_fallback_applied = False
    ly_date  = None
    ly_night = None
    try:
        ly_date  = target_date.replace(year=target_date.year - 1)
        ly_night = DailyJourMetrics.query.filter_by(date=ly_date).first()
    except ValueError:
        pass  # e.g. Feb 29 in non-leap year — no exact LY date

    if not ly_night:
        ly_date_fallback = target_date - timedelta(days=364)
        ly_night         = DailyJourMetrics.query.filter_by(date=ly_date_fallback).first()
        if ly_night:
            ly_date             = ly_date_fallback
            ly_fallback_applied = True

    # 7-day rolling average (days -8 through -1 relative to target, excluding target itself)
    week_start = target_date - timedelta(days=8)
    week_end   = target_date - timedelta(days=1)
    avg7_row   = db.session.query(
        func.avg(DailyJourMetrics.occupancy_rate),
        func.avg(DailyJourMetrics.adr),
        func.avg(DailyJourMetrics.revpar),
        func.avg(DailyJourMetrics.room_revenue),
        func.avg(DailyJourMetrics.fb_revenue),
        func.avg(DailyJourMetrics.total_revenue),
        func.count(DailyJourMetrics.id),
    ).filter(
        DailyJourMetrics.date.between(week_start, week_end)
    ).first()

    avg7_count     = avg7_row[6] or 0
    avg7_occ       = avg7_row[0]
    avg7_adr       = avg7_row[1]
    avg7_revpar    = avg7_row[2]
    avg7_room_rev  = avg7_row[3]
    avg7_total_rev = avg7_row[5]
    avg7_low_sample = avg7_count < 3

    vs_budget = {
        'occupancy':     _variance(_r2(night.occupancy_rate), budget_occ_daily),
        'adr':           _variance(_r2(night.adr),            budget_adr_daily),
        'revpar':        _variance(_r2(night.revpar),         budget_revpar_daily),
        'room_revenue':  _variance(_r2(night.room_revenue),   budget_room_rev_d),
        'total_revenue': _variance(_r2(night.total_revenue),  budget_total_rev_d),
    }

    if ly_night:
        vs_ly = {
            'date_used':     ly_date.isoformat() if ly_date else None,
            'occupancy':     _variance(_r2(night.occupancy_rate), _r2(ly_night.occupancy_rate)),
            'adr':           _variance(_r2(night.adr),            _r2(ly_night.adr)),
            'revpar':        _variance(_r2(night.revpar),         _r2(ly_night.revpar)),
            'room_revenue':  _variance(_r2(night.room_revenue),   _r2(ly_night.room_revenue)),
            'total_revenue': _variance(_r2(night.total_revenue),  _r2(ly_night.total_revenue)),
        }
    else:
        null_v = {'value': None, 'pct': None, 'direction': 'unknown'}
        vs_ly = {
            'date_used':     None,
            'occupancy':     null_v, 'adr': null_v, 'revpar': null_v,
            'room_revenue':  null_v, 'total_revenue': null_v,
        }

    vs_7day_avg = {
        'occupancy':     _variance(_r2(night.occupancy_rate), _r2(avg7_occ)       if avg7_occ       is not None else None),
        'adr':           _variance(_r2(night.adr),            _r2(avg7_adr)       if avg7_adr       is not None else None),
        'revpar':        _variance(_r2(night.revpar),         _r2(avg7_revpar)    if avg7_revpar    is not None else None),
        'room_revenue':  _variance(_r2(night.room_revenue),   _r2(avg7_room_rev)  if avg7_room_rev  is not None else None),
        'total_revenue': _variance(_r2(night.total_revenue),  _r2(avg7_total_rev) if avg7_total_rev is not None else None),
    }
    if avg7_low_sample:
        vs_7day_avg['low_sample'] = True

    panel1 = {
        'date': target_date.isoformat(),
        'kpis': {
            'occupancy_pct':          _r2(night.occupancy_rate),
            'occupancy_adjusted_pct': _r2(occ_adjusted),
            'adr':                    _r2(night.adr),
            'effective_adr':          _r2(effective_adr),
            'revpar':                 _r2(night.revpar),
            'room_revenue':           _r2(night.room_revenue),
            'fb_revenue':             _r2(night.fb_revenue),
            'total_revenue':          _r2(night.total_revenue),
            'rooms_sold':             rooms_sold,
            'rooms_comp':             night.rooms_comp or 0,
            'comp_pct':               comp_pct,
            'oos_rooms':              oos_rooms_djm,
        },
        'vs_budget':   vs_budget,
        'vs_ly':       vs_ly,
        'vs_7day_avg': vs_7day_avg,
        'fallback_notes': {
            'budget_available':    budget is not None,
            'ly_data_available':   ly_night is not None,
            'ly_date_used':        ly_date.isoformat() if ly_date else None,
            'ly_fallback_applied': ly_fallback_applied,
            '7day_sample_count':   avg7_count,
        },
    }

    # =========================================================================
    # PANEL 2 — Operational Status
    # =========================================================================
    rj   = NightAuditSession.query.filter_by(audit_date=target_date).first()
    cash = DailyCashRecon.query.filter_by(date=target_date).first()

    # OOS RevPAR impact: out-of-service room count × last night's ADR.
    # Prefer the NAS value when available (explicit audit entry); 0 is a valid count.
    if rj and rj.jour_rooms_hors_usage is not None:
        panel2_oos = rj.jour_rooms_hors_usage
    else:
        panel2_oos = oos_rooms_djm
    revpar_impact = _r2(panel2_oos * (night.adr or 0))

    # Consecutive balanced-night streak from target_date back, up to 30 days
    recent_sessions = NightAuditSession.query.filter(
        NightAuditSession.audit_date <= target_date,
        NightAuditSession.audit_date >= target_date - timedelta(days=30),
    ).order_by(desc(NightAuditSession.audit_date)).all()

    streak = 0
    for s in recent_sessions:
        if s.is_fully_balanced:
            streak += 1
        else:
            break

    if rj:
        balance_grid = {
            'recap':      {'balanced': rj.is_recap_balanced,     'value': _r2(rj.recap_balance),       'threshold': 0.02},
            'transelect': {'balanced': rj.is_transelect_balanced, 'value': _r2(rj.transelect_variance), 'threshold': 1.00},
            'ar':         {'balanced': rj.is_ar_balanced,         'value': _r2(rj.geac_ar_variance),    'threshold': 0.02},
            'is_fully_balanced': rj.is_fully_balanced,
        }
        gl_suspense = {
            'gl_101100_balance':  _r2(rj.gl_101100_new_balance),
            'gl_101100_variance': _r2(rj.gl_101100_variance),
            'gl_100401_balance':  _r2(rj.gl_100401_new_balance),
            'gl_100401_variance': _r2(rj.gl_100401_variance),
            'notes':              rj.gl_101100_notes or '',
        }
        rj_block = {
            'exists':       True,
            'auditor':      rj.auditor_name,
            'status':       rj.status,
            'submitted_at': rj.completed_at.isoformat() if rj.completed_at else None,
            'is_submitted': rj.status in ('submitted', 'locked'),
        }
    else:
        null_grid_row = {'balanced': None, 'value': None}
        balance_grid = {
            'recap':      dict(null_grid_row, threshold=0.02),
            'transelect': dict(null_grid_row, threshold=1.00),
            'ar':         dict(null_grid_row, threshold=0.02),
            'is_fully_balanced': None,
        }
        gl_suspense = {
            'gl_101100_balance': None, 'gl_101100_variance': None,
            'gl_100401_balance': None, 'gl_100401_variance': None,
            'notes': '',
        }
        rj_block = {
            'exists': False, 'auditor': None, 'status': None,
            'submitted_at': None, 'is_submitted': False,
        }

    if cash:
        quasimodo_block = {
            'variance':        _r2(cash.quasimodo_variance),
            'threshold':       5.00,
            'status':          'ok' if abs(cash.quasimodo_variance or 0) <= 5 else 'warning',
            'surplus_deficit': _r2(cash.surplus_deficit),
        }
    else:
        quasimodo_block = {
            'variance': None, 'threshold': 5.00, 'status': 'no_data', 'surplus_deficit': None,
        }

    panel2 = {
        'rj_session':   rj_block,
        'balance_grid': balance_grid,
        'quasimodo':    quasimodo_block,
        'oos_rooms': {
            'count':         panel2_oos,
            'revpar_impact': revpar_impact,
            'note': "Revenus non générés si les chambres OOS avaient été vendues au tarif ADR de la nuit",
        },
        'gl_suspense':                 gl_suspense,
        'consecutive_balanced_streak': streak,
        'fallback_notes': {
            'rj_session_found': rj is not None,
            'cash_recon_found': cash is not None,
        },
    }

    # =========================================================================
    # PANEL 3 — Forward Look (OTB next 7 + next 30 days)
    # =========================================================================
    today = date.today()

    latest_snap   = db.session.query(func.max(OTBForecast.snapshot_date)).scalar()
    otb_available = latest_snap is not None

    if otb_available:
        snap_age_days = (today - latest_snap).days
        data_is_stale = snap_age_days > 3

        next7_end  = today + timedelta(days=7)
        next30_end = today + timedelta(days=30)

        next7_rows = OTBForecast.query.filter(
            OTBForecast.snapshot_date == latest_snap,
            OTBForecast.target_date   >  today,
            OTBForecast.target_date   <= next7_end,
        ).order_by(OTBForecast.target_date).all()

        next30_rows = OTBForecast.query.filter(
            OTBForecast.snapshot_date == latest_snap,
            OTBForecast.target_date   >  today,
            OTBForecast.target_date   <= next30_end,
        ).order_by(OTBForecast.target_date).all()

        next7_daily = []
        for r in next7_rows:
            ly_r = r.ly_rooms
            ly_v = r.ly_revenue
            next7_daily.append({
                'target_date':    r.target_date.isoformat(),
                'day_of_week':    r.target_date.strftime('%A'),
                'rooms_otb':      r.rooms_otb or 0,
                'occ_otb_pct':    _r2((r.rooms_otb or 0) / TOTAL_ROOMS * 100) if TOTAL_ROOMS else 0,
                'adr_otb':        _r2(r.adr_otb),
                'revenue_otb':    _r2(r.revenue_otb),
                'group_rooms':    r.group_rooms or 0,
                'transient_rooms': r.transient_rooms or 0,
                'ly_rooms':       ly_r,
                'ly_occ_pct':     _r2(ly_r / TOTAL_ROOMS * 100) if ly_r is not None else None,
                'ly_revenue':     _r2(ly_v) if ly_v is not None else None,
                'vs_ly_rooms':    _variance(r.rooms_otb or 0, ly_r),
                'vs_ly_revenue':  _variance(_r2(r.revenue_otb), _r2(ly_v) if ly_v is not None else None),
            })

        # Aggregate next-30 totals
        next30_rooms_otb   = sum(r.rooms_otb   or 0 for r in next30_rows)
        next30_revenue_otb = sum(r.revenue_otb  or 0 for r in next30_rows)
        next30_ly_rooms    = sum(r.ly_rooms   or 0 for r in next30_rows if r.ly_rooms   is not None)
        next30_ly_revenue  = sum(r.ly_revenue or 0 for r in next30_rows if r.ly_revenue is not None)
        next30_days_ly     = sum(1 for r in next30_rows if r.ly_rooms is not None)
        ly_coverage_str    = f"{next30_days_ly} of {len(next30_rows)} days have LY data"

        avg_daily_occ_otb = (
            _r2(sum((r.rooms_otb or 0) / TOTAL_ROOMS * 100 for r in next30_rows) / len(next30_rows))
            if next30_rows and TOTAL_ROOMS else None
        )
        avg_daily_adr_otb = (
            _r2(next30_revenue_otb / next30_rooms_otb)
            if next30_rooms_otb > 0 else None
        )

        next30_pace = {
            'total_rooms_otb':    next30_rooms_otb,
            'total_revenue_otb':  _r2(next30_revenue_otb),
            'total_ly_rooms':     next30_ly_rooms,
            'total_ly_revenue':   _r2(next30_ly_revenue),
            'vs_ly_rooms_pct':    _r2((next30_rooms_otb - next30_ly_rooms) / next30_ly_rooms * 100)
                                  if next30_ly_rooms > 0 else None,
            'vs_ly_revenue_pct':  _r2((next30_revenue_otb - next30_ly_revenue) / next30_ly_revenue * 100)
                                  if next30_ly_revenue > 0 else None,
            'avg_daily_occ_otb':  avg_daily_occ_otb,
            'avg_daily_adr_otb':  avg_daily_adr_otb,
        }

        panel3 = {
            'snapshot_date':     latest_snap.isoformat(),
            'snapshot_age_days': snap_age_days,
            'data_is_stale':     data_is_stale,
            'next_7_days':       next7_daily,
            'next_30_days_pace': next30_pace,
            'fallback_notes': {
                'otb_data_available':     True,
                'ly_comparison_coverage': ly_coverage_str,
                'stale_warning': "Données OTB vieilles de plus de 3 jours" if data_is_stale else None,
            },
        }
    else:
        null_pace = {
            'total_rooms_otb': None, 'total_revenue_otb': None,
            'total_ly_rooms':  None, 'total_ly_revenue':  None,
            'vs_ly_rooms_pct': None, 'vs_ly_revenue_pct': None,
            'avg_daily_occ_otb': None, 'avg_daily_adr_otb': None,
        }
        panel3 = {
            'snapshot_date': None, 'snapshot_age_days': None, 'data_is_stale': None,
            'next_7_days': [], 'next_30_days_pace': null_pace,
            'fallback_notes': {'otb_data_available': False, 'ly_comparison_coverage': None},
        }

    # =========================================================================
    # PANEL 4 — Trend Context
    # =========================================================================

    # Latest STR RevPAR index (most recent daily record)
    latest_str = STRCompSet.query.filter_by(
        period_type='daily'
    ).order_by(desc(STRCompSet.report_date)).first()

    if latest_str:
        str_block = {
            'report_date':   latest_str.report_date.isoformat(),
            'my_revpar':     _r2(latest_str.my_revpar) if latest_str.my_revpar is not None else None,
            'comp_revpar':   _r2(latest_str.comp_revpar) if latest_str.comp_revpar is not None else None,
            'revpar_index':  _r2(latest_str.revpar_index) if latest_str.revpar_index is not None else None,
            'revpar_rank':   latest_str.revpar_rank,
            'comp_set_size': latest_str.comp_set_size,
            'my_occ':        _r2(latest_str.my_occ) if latest_str.my_occ is not None else None,
            'comp_occ':      _r2(latest_str.comp_occ) if latest_str.comp_occ is not None else None,
            'occ_index':     _r2(latest_str.occ_index) if latest_str.occ_index is not None else None,
            'my_adr':        _r2(latest_str.my_adr) if latest_str.my_adr is not None else None,
            'comp_adr':      _r2(latest_str.comp_adr) if latest_str.comp_adr is not None else None,
            'adr_index':     _r2(latest_str.adr_index) if latest_str.adr_index is not None else None,
            'data_available': True,
        }
    else:
        str_block = {'data_available': False}

    # Labor % of revenue — last 3 full calendar months before target_date's month.
    # We step back month by month three times from the start of target_date's month.
    target_month_start = target_date.replace(day=1)
    three_months_ago_start = target_month_start
    for _ in range(3):
        three_months_ago_start = (three_months_ago_start - timedelta(days=1)).replace(day=1)

    labor_rows = DepartmentLabor.query.filter(
        db.or_(
            DepartmentLabor.year > three_months_ago_start.year,
            db.and_(
                DepartmentLabor.year  == three_months_ago_start.year,
                DepartmentLabor.month >= three_months_ago_start.month,
            )
        ),
        db.or_(
            DepartmentLabor.year < target_date.year,
            db.and_(
                DepartmentLabor.year  == target_date.year,
                DepartmentLabor.month <  target_date.month,
            )
        ),
    ).all()

    labor_by_period = defaultdict(float)
    for dl in labor_rows:
        labor_by_period[f"{dl.year}-{dl.month:02d}"] += dl.total_labor_cost or 0

    rev_rows_p4 = db.session.query(
        DailyJourMetrics.year,
        DailyJourMetrics.month,
        func.sum(DailyJourMetrics.total_revenue).label('total_rev'),
    ).filter(
        db.or_(
            DailyJourMetrics.year > three_months_ago_start.year,
            db.and_(
                DailyJourMetrics.year  == three_months_ago_start.year,
                DailyJourMetrics.month >= three_months_ago_start.month,
            )
        ),
        db.or_(
            DailyJourMetrics.year < target_date.year,
            db.and_(
                DailyJourMetrics.year  == target_date.year,
                DailyJourMetrics.month <  target_date.month,
            )
        ),
    ).group_by(DailyJourMetrics.year, DailyJourMetrics.month).all()

    rev_by_period = {f"{r.year}-{r.month:02d}": r.total_rev or 0 for r in rev_rows_p4}

    def _labor_status(pct):
        if pct > 38:
            return 'critical'
        if pct >= 30:
            return 'warning'
        return 'ok'

    labor_pct_trend = []
    for period in sorted(labor_by_period.keys()):
        labor_cost = labor_by_period[period]
        revenue    = rev_by_period.get(period, 0)
        labor_pct  = _r2(labor_cost / revenue * 100) if revenue > 0 else None
        labor_pct_trend.append({
            'period':     period,
            'labor_cost': _r2(labor_cost),
            'revenue':    _r2(revenue),
            'labor_pct':  labor_pct,
            'status':     _labor_status(labor_pct) if labor_pct is not None else 'no_data',
        })

    # Top active alert — re-use existing threshold engine with last night's data
    night_kpi_for_alerts = {
        'occupancy_rate': _r2(night.occupancy_rate),
        'adr':            _r2(night.adr),
        'revpar':         _r2(night.revpar),
        'room_revenue':   _r2(night.room_revenue),
        'total_revenue':  _r2(night.total_revenue),
        'fb_per_client':  0,
    }
    if (night.nb_clients or 0) > 0:
        night_kpi_for_alerts['fb_per_client'] = _r2((night.fb_revenue or 0) / night.nb_clients)

    thirty_ago   = target_date - timedelta(days=30)
    avg_row_p4   = db.session.query(
        func.avg(DailyJourMetrics.occupancy_rate),
        func.avg(DailyJourMetrics.adr),
        func.avg(DailyJourMetrics.revpar),
    ).filter(
        DailyJourMetrics.date.between(thirty_ago, target_date - timedelta(days=1))
    ).first()

    avg_data_p4 = {
        'occupancy_rate': _r2(avg_row_p4[0]) if avg_row_p4[0] else 70,
        'adr':            _r2(avg_row_p4[1]) if avg_row_p4[1] else 150,
        'revpar':         _r2(avg_row_p4[2]) if avg_row_p4[2] else 100,
    }

    cash_p4 = {
        'quasimodo_variance': _r2(cash.quasimodo_variance),
        'surplus_deficit':    _r2(cash.surplus_deficit),
    } if cash else None

    labor_p4 = None
    if labor_pct_trend:
        last_labor_period = labor_pct_trend[-1]
        if last_labor_period['labor_pct'] is not None:
            labor_p4 = {'labor_pct': last_labor_period['labor_pct']}

    all_alerts = evaluate_thresholds(
        night_kpi_for_alerts, avg_data_p4, {}, cash_p4, labor_p4, None
    )
    severity_order = {'critical': 0, 'warning': 1, 'info': 2, 'success': 3}
    all_alerts.sort(key=lambda a: severity_order.get(a['severity'], 9))
    top_alert = all_alerts[0] if all_alerts else None

    panel4 = {
        'str_index':       str_block,
        'labor_pct_trend': labor_pct_trend,
        'top_alert':       top_alert,
    }

    # =========================================================================
    # Assemble full response envelope
    # =========================================================================
    return jsonify({
        'success':        True,
        'has_data':       True,
        'generated_at':   datetime.utcnow().isoformat(),
        'briefing_date':  target_date.isoformat(),
        'last_night':          panel1,
        'operational_status':  panel2,
        'forward_look':        panel3,
        'trend_context':       panel4,
    })


# ==============================================================================
# ACCOUNTING MONTH-END DASHBOARD
# ==============================================================================

@dashboard_bp.route('/api/dashboard/accounting')
@login_required
@role_required('accounting', 'gm', 'admin')
def accounting_dashboard():
    """
    Accounting month-end dashboard — seven sections covering checklist progress,
    revenue verification, data gaps, GL suspense, deposit variances,
    card discount costs, and data quality warnings.

    Query params:
        year  (int): year of the period; defaults to current year.
        month (int): month of the period (1-12); defaults to current month.
    """
    year  = request.args.get('year',  date.today().year,  type=int)
    month = request.args.get('month', date.today().month, type=int)

    if not (1 <= month <= 12):
        return jsonify({'success': False, 'error': 'Mois invalide (1-12)'}), 400

    days_in_month = calendar.monthrange(year, month)[1]
    month_start   = date(year, month, 1)
    month_end     = date(year, month, days_in_month)
    today         = date.today()

    # Future dates within the current/future month are never "missing" — cap at today.
    # For fully future months, effective_end will be before month_start — guard against that.
    effective_end = min(month_end, today)
    days_in_window = max(0, (effective_end - month_start).days + 1)

    # =========================================================================
    # A — MonthEndChecklist progress
    # =========================================================================
    tasks           = MonthEndChecklist.query.filter_by(year=year, month=month).all()
    total_tasks     = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.completed)
    pending_tasks   = [t.task_name for t in tasks if not t.completed]
    checklist_pct   = _r2(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    if total_tasks == 0:
        checklist_status = 'no_tasks'
    elif completed_tasks >= total_tasks:
        checklist_status = 'complete'
    else:
        checklist_status = 'in_progress'

    # =========================================================================
    # B — Revenue verification
    # =========================================================================
    djm_agg = db.session.query(
        func.sum(DailyJourMetrics.total_revenue),
        func.sum(DailyJourMetrics.room_revenue),
        func.sum(DailyJourMetrics.fb_revenue),
        func.count(DailyJourMetrics.id),
    ).filter(
        DailyJourMetrics.date.between(month_start, month_end)
    ).first()

    djm_total_rev    = _r2(djm_agg[0])
    djm_room_rev     = _r2(djm_agg[1])
    djm_fb_rev       = _r2(djm_agg[2])
    days_with_djm    = djm_agg[3] or 0
    days_missing_rev = max(0, days_in_window - days_with_djm)

    budget = MonthlyBudget.query.filter_by(year=year, month=month).first()
    budget_total_rev = _r2(budget.total_revenue) if budget else None
    vs_budget_pct    = (
        _r2((djm_total_rev - budget_total_rev) / budget_total_rev * 100)
        if budget_total_rev and budget_total_rev != 0
        else None
    )

    note_rev = None
    if days_with_djm < days_in_month:
        note_rev = f"Seulement {days_with_djm} sur {days_in_month} jours ont des données. Mois incomplet."

    revenue_verification = {
        'djm_total_revenue':    djm_total_rev,
        'djm_room_revenue':     djm_room_rev,
        'djm_fb_revenue':       djm_fb_rev,
        'days_with_djm':        days_with_djm,
        'days_expected':        days_in_window,
        'days_missing':         days_missing_rev,
        'budget_total_revenue': budget_total_rev,
        'vs_budget_pct':        vs_budget_pct,
        'note':                 note_rev,
    }

    # =========================================================================
    # C — Missing data detection (only for dates that have passed)
    # =========================================================================
    # days_in_window already computed above after effective_end
    all_dates_in_window = {
        month_start + timedelta(days=i)
        for i in range(days_in_window)
    }

    djm_present = {
        r.date for r in DailyJourMetrics.query.filter(
            DailyJourMetrics.date.between(month_start, effective_end)
        ).with_entities(DailyJourMetrics.date).all()
    }
    nas_present = {
        r.audit_date for r in NightAuditSession.query.filter(
            NightAuditSession.audit_date.between(month_start, effective_end)
        ).with_entities(NightAuditSession.audit_date).all()
    }

    missing_djm_dates = sorted(all_dates_in_window - djm_present)
    missing_rj_dates  = sorted(all_dates_in_window - nas_present)

    djm_coverage_pct = _r2(len(djm_present) / days_in_window * 100) if days_in_window > 0 else 0
    rj_coverage_pct  = _r2(len(nas_present) / days_in_window * 100) if days_in_window > 0 else 0

    missing_data = {
        'djm_missing_dates': [d.isoformat() for d in missing_djm_dates],
        'rj_missing_dates':  [d.isoformat() for d in missing_rj_dates],
        'djm_coverage_pct':  djm_coverage_pct,
        'rj_coverage_pct':   rj_coverage_pct,
    }

    # =========================================================================
    # D — GL Suspense (from most recent NightAuditSession in month)
    # =========================================================================
    latest_nas = NightAuditSession.query.filter(
        NightAuditSession.audit_date.between(month_start, month_end)
    ).order_by(desc(NightAuditSession.audit_date)).first()

    if latest_nas:
        gl_suspense = {
            'as_of_date': latest_nas.audit_date.isoformat(),
            'gl_101100': {
                'previous_balance': _r2(latest_nas.gl_101100_previous),
                'additions':        _r2(latest_nas.gl_101100_additions),
                'deductions':       _r2(latest_nas.gl_101100_deductions),
                'new_balance':      _r2(latest_nas.gl_101100_new_balance),
                'variance':         _r2(latest_nas.gl_101100_variance),
                'notes':            latest_nas.gl_101100_notes or '',
            },
            'gl_100401': {
                'previous_balance': _r2(latest_nas.gl_100401_previous),
                'additions':        _r2(latest_nas.gl_100401_additions),
                'deductions':       _r2(latest_nas.gl_100401_deductions),
                'new_balance':      _r2(latest_nas.gl_100401_new_balance),
                'variance':         _r2(latest_nas.gl_100401_variance),
                'notes':            latest_nas.gl_100401_notes or '',
            },
        }
    else:
        gl_suspense = {'as_of_date': None, 'gl_101100': None, 'gl_100401': None}

    # =========================================================================
    # E — Deposit variance leaderboard by employee
    # =========================================================================
    dep_var_rows = db.session.query(
        DepositVariance.employee_name,
        DepositVariance.department,
        func.count(DepositVariance.id).label('occurrences'),
        func.sum(DepositVariance.variance).label('total_variance'),
        func.sum(func.abs(DepositVariance.variance)).label('abs_total'),
        func.avg(DepositVariance.variance).label('avg_variance'),
    ).filter(
        DepositVariance.audit_date.between(month_start, month_end)
    ).group_by(
        DepositVariance.employee_name,
        DepositVariance.department,
    ).order_by(
        func.sum(func.abs(DepositVariance.variance)).desc()
    ).all()

    deposit_leaderboard = []
    for r in dep_var_rows:
        abs_total = _r2(r.abs_total or 0)
        flag = 'critical' if abs_total >= 50 else ('review' if abs_total >= 20 else 'ok')
        deposit_leaderboard.append({
            'employee':       r.employee_name,
            'department':     r.department,
            'occurrences':    r.occurrences,
            'total_variance': _r2(r.total_variance or 0),
            'abs_total':      abs_total,
            'avg_variance':   _r2(r.avg_variance or 0),
            'flag':           flag,
        })

    # =========================================================================
    # F — Card discount costs by type
    # =========================================================================
    card_cost_rows = db.session.query(
        DailyCardMetrics.card_type,
        func.sum(DailyCardMetrics.pos_total).label('total_volume'),
        func.sum(DailyCardMetrics.discount_amount).label('total_discount'),
        func.sum(DailyCardMetrics.net_amount).label('net_amount'),
        func.sum(DailyCardMetrics.transaction_count).label('total_txn'),
    ).filter(
        DailyCardMetrics.date.between(month_start, month_end)
    ).group_by(DailyCardMetrics.card_type).all()

    card_by_type  = []
    total_vol_all = 0.0
    total_disc_all = 0.0
    total_net_all  = 0.0
    total_txn_all  = 0

    for r in card_cost_rows:
        vol  = _r2(r.total_volume   or 0)
        disc = _r2(r.total_discount or 0)
        net  = _r2(r.net_amount     or 0)
        txn  = r.total_txn or 0
        rate_pct = _r2(disc / vol * 100) if vol > 0 else 0
        card_by_type.append({
            'card_type':    r.card_type,
            'volume':       vol,
            'discount':     disc,
            'rate_pct':     rate_pct,
            'transactions': txn,
            'net':          net,
        })
        total_vol_all  += vol
        total_disc_all += disc
        total_net_all  += net
        total_txn_all  += txn

    blended_rate = _r2(total_disc_all / total_vol_all * 100) if total_vol_all > 0 else 0

    card_discount_costs = {
        'by_type': card_by_type,
        'totals': {
            'total_volume':       _r2(total_vol_all),
            'total_discount':     _r2(total_disc_all),
            'blended_rate_pct':   blended_rate,
            'total_net':          _r2(total_net_all),
            'total_transactions': total_txn_all,
        },
    }

    # =========================================================================
    # G — Data quality warnings
    # =========================================================================
    warnings = []

    # 1. MonthlyExpense missing
    exp = MonthlyExpense.query.filter_by(year=year, month=month).first()
    if not exp:
        warnings.append({
            'code':     'MISSING_MONTHLY_EXPENSE',
            'severity': 'warning',
            'message':  f"MonthlyExpense non saisi pour {year}-{month:02d}. Les calculs P&L et GOPPAR seront incomplets.",
            'action':   "Saisir les dépenses dans l'onglet P&L avant de clôturer le mois.",
        })

    # 2. MonthlyBudget missing
    if not budget:
        warnings.append({
            'code':     'MISSING_MONTHLY_BUDGET',
            'severity': 'warning',
            'message':  f"Aucun budget trouvé pour {year}-{month:02d}.",
            'action':   "Saisir le budget dans la configuration Revenue Management.",
        })

    # 3. DJM gaps (dates that have passed without a row)
    if missing_djm_dates:
        severity = 'critical' if len(missing_djm_dates) > 3 else 'warning'
        warnings.append({
            'code':     'MISSING_DJM_DATES',
            'severity': severity,
            'message':  f"{len(missing_djm_dates)} date(s) sans ligne DailyJourMetrics.",
            'dates':    [d.isoformat() for d in missing_djm_dates],
            'action':   "Téléverser les fichiers RJ manquants ou vérifier la sortie du parseur.",
        })

    # 4. Missing NightAuditSession
    if missing_rj_dates:
        warnings.append({
            'code':     'MISSING_RJ_SESSIONS',
            'severity': 'warning',
            'message':  f"{len(missing_rj_dates)} date(s) sans NightAuditSession.",
            'dates':    [d.isoformat() for d in missing_rj_dates],
            'action':   "Vérifier les soumissions d'audit de nuit pour ces dates.",
        })

    # 5. DepartmentLabor missing entirely for this period
    dl_count = DepartmentLabor.query.filter_by(year=year, month=month).count()
    if dl_count == 0:
        warnings.append({
            'code':     'MISSING_DEPARTMENT_LABOR',
            'severity': 'warning',
            'message':  "Aucune entrée DepartmentLabor pour cette période. Les ratios de main-d'œuvre ne peuvent pas être calculés.",
            'action':   "Importer les données de paie ou les saisir manuellement dans l'onglet Main-d'œuvre.",
        })

    # =========================================================================
    # Build period label and return
    # =========================================================================
    try:
        month_label = date(year, month, 1).strftime('%B %Y')
    except Exception:
        month_label = f"{year}-{month:02d}"

    return jsonify({
        'success': True,
        'period': {
            'year':          year,
            'month':         month,
            'label':         month_label,
            'days_in_month': days_in_month,
        },
        'checklist': {
            'total_tasks':     total_tasks,
            'completed_tasks': completed_tasks,
            'progress_pct':    checklist_pct,
            'pending_tasks':   pending_tasks,
            'status':          checklist_status,
        },
        'revenue_verification':          revenue_verification,
        'missing_data':                  missing_data,
        'gl_suspense':                   gl_suspense,
        'deposit_variance_leaderboard':  deposit_leaderboard,
        'card_discount_costs':           card_discount_costs,
        'data_quality_warnings':         warnings,
    })
