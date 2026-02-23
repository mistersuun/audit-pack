"""
Dashboard Blueprint — Smart landing page with KPIs, alerts, shift progress & weather.

Features:
1. Tonight's KPIs vs yesterday / last week / last month
2. Intelligent threshold-based alerts & recommendations
3. Shift progress + RJ session status
4. Weather integration (from NightAuditSession)
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, timedelta, date
from database.models import (
    db, DailyJourMetrics, DailyCashRecon, DailyCardMetrics,
    DailyLaborMetrics, DepartmentLabor, MonthlyBudget, NightAuditSession,
    Shift, Task, TaskCompletion
)
from sqlalchemy import func, desc
import json

dashboard_bp = Blueprint('dashboard', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            from flask import redirect, url_for
            return redirect(url_for('auth_v2.login'))
        return f(*args, **kwargs)
    return decorated_function


def _r2(val):
    """Round to 2 decimals safely."""
    try:
        return round(float(val or 0), 2)
    except (ValueError, TypeError):
        return 0.0


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

        labor_pct = _r2(total_labor_cost / month_rev * 100) if month_rev > 0 else 0
        labor_data = {
            'month': f"{latest_y}-{latest_m:02d}",
            'total_cost': _r2(total_labor_cost),
            'revenue': _r2(month_rev),
            'labor_pct': labor_pct,
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
        days_in_month = 30  # Approximate
        days_elapsed = mtd_data['days']
        prorated_budget = (budget.total_revenue_budget or 0) * (days_elapsed / days_in_month)
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
