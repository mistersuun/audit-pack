"""
RJ Correction Module — Unlock, diagnose & correct locked audit sessions.

Provides:
- Correction page with variance diagnostic
- Unlock/relock endpoints with audit trail
- Field-level change logging
- Diagnostic engine that explains each variance
"""

from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, date
from database.models import db, NightAuditSession, SessionEditLog
import json
import logging

logger = logging.getLogger(__name__)

rj_correction_bp = Blueprint('rj_correction', __name__)


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            from flask import redirect, url_for
            return redirect(url_for('auth_v2.login'))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════
# PAGE — Correction UI
# ═══════════════════════════════════════

@rj_correction_bp.route('/rj/correction')
@auth_required
def correction_page():
    """Render the correction diagnostic page."""
    return render_template('audit/rj/rj_correction.html')


# ═══════════════════════════════════════
# API — SESSION LIST (locked/submitted)
# ═══════════════════════════════════════

@rj_correction_bp.route('/api/rj/correction/sessions')
@auth_required
def list_correction_sessions():
    """List all sessions that have been locked or are being corrected."""
    sessions = NightAuditSession.query.filter(
        NightAuditSession.status.in_(['locked', 'correcting', 'submitted'])
    ).order_by(NightAuditSession.audit_date.desc()).limit(60).all()

    result = []
    for nas in sessions:
        # Quick variance summary
        result.append({
            'audit_date': nas.audit_date.isoformat(),
            'auditor_name': nas.auditor_name or '—',
            'status': nas.status,
            'completed_at': nas.completed_at.isoformat() if nas.completed_at else None,
            'correction_count': nas.correction_count or 0,
            'last_corrected_by': nas.last_corrected_by,
            'last_corrected_at': nas.last_corrected_at.isoformat() if nas.last_corrected_at else None,
            'recap_balance': nas.recap_balance or 0,
            'transelect_variance': nas.transelect_variance or 0,
            'quasi_variance': nas.quasi_variance or 0,
            'diff_caisse_formula': nas.diff_caisse_formula or 0,
        })
    return jsonify({'sessions': result})


# ═══════════════════════════════════════
# API — DIAGNOSTIC (variance breakdown)
# ═══════════════════════════════════════

@rj_correction_bp.route('/api/rj/correction/diagnostic/<audit_date>')
@auth_required
def get_diagnostic(audit_date):
    """Generate a full variance diagnostic for a session."""
    try:
        d = datetime.strptime(audit_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400

    nas = NightAuditSession.query.filter_by(audit_date=d).first()
    if not nas:
        return jsonify({'error': 'Session non trouvée'}), 404

    # Run calculate_all to refresh all values
    nas.calculate_all()
    db.session.commit()

    diagnostic = _build_diagnostic(nas)
    return jsonify({
        'audit_date': nas.audit_date.isoformat(),
        'auditor_name': nas.auditor_name,
        'status': nas.status,
        'correction_count': nas.correction_count or 0,
        'correction_reason': nas.correction_reason,
        'diagnostic': diagnostic,
        'session': nas.to_dict(),
    })


def _build_diagnostic(nas):
    """Build a section-by-section diagnostic with variance explanations."""
    sections = []

    # 1. RECAP — Cash balance
    recap_bal = nas.recap_balance or 0
    recap_items = []
    for line_name, lec_field, corr_field in [
        ('Cash LS', 'cash_ls_lecture', 'cash_ls_corr'),
        ('Cash POS', 'cash_pos_lecture', 'cash_pos_corr'),
        ('Chèque AR', 'cheque_ar_lecture', 'cheque_ar_corr'),
        ('Chèque DR', 'cheque_dr_lecture', 'cheque_dr_corr'),
        ('Remb. Gratuite', 'remb_gratuite_lecture', 'remb_gratuite_corr'),
        ('Remb. Client', 'remb_client_lecture', 'remb_client_corr'),
        ('DueBack Réception', 'dueback_reception_lecture', 'dueback_reception_corr'),
        ('DueBack NB', 'dueback_nb_lecture', 'dueback_nb_corr'),
    ]:
        lec = getattr(nas, lec_field, 0) or 0
        corr = getattr(nas, corr_field, 0) or 0
        net = round(lec + corr, 2)
        if lec != 0 or corr != 0:
            recap_items.append({
                'label': line_name, 'lecture': lec, 'correction': corr, 'net': net
            })
    sections.append({
        'id': 'recap', 'title': 'Recap (Comptant)',
        'variance': round(recap_bal, 2),
        'tolerance': 0.02,
        'status': 'ok' if abs(recap_bal) < 0.02 else 'error',
        'items': recap_items,
        'explanation': _explain_recap(recap_bal, recap_items),
    })

    # 2. TRANSELECT — Card variance
    trans_var = nas.transelect_variance or 0
    trans_items = []
    trans_rest = nas.get_json('transelect_restaurant') if hasattr(nas, 'get_json') else {}
    trans_rec = nas.get_json('transelect_reception') if hasattr(nas, 'get_json') else {}
    rest_total = 0
    if isinstance(trans_rest, dict):
        for term, cards in trans_rest.items():
            if isinstance(cards, dict):
                term_total = sum(v or 0 for v in cards.values() if isinstance(v, (int, float)))
                rest_total += term_total
                trans_items.append({'label': f'Restaurant {term}', 'value': round(term_total, 2)})
    rec_total = 0
    if isinstance(trans_rec, dict):
        for card, terms in trans_rec.items():
            if isinstance(terms, dict):
                card_total = sum(v or 0 for v in terms.values() if isinstance(v, (int, float)))
                rec_total += card_total
                trans_items.append({'label': f'Réception {card}', 'value': round(card_total, 2)})
    sections.append({
        'id': 'transelect', 'title': 'Transelect (Cartes)',
        'variance': round(trans_var, 2),
        'tolerance': 1.00,
        'status': 'ok' if abs(trans_var) < 1.00 else ('warning' if abs(trans_var) < 5.00 else 'error'),
        'items': trans_items,
        'explanation': f'Restaurant POS: ${rest_total:,.2f} | Réception Bank: ${rec_total:,.2f} | Écart: ${trans_var:+,.2f}. Note: le Transelect ne balance jamais à $0 exactement.',
    })

    # 3. GEAC — Card balance
    geac_var = nas.geac_ar_variance or 0
    geac_cashout = nas.get_json('geac_cashout') if hasattr(nas, 'get_json') else {}
    geac_daily = nas.get_json('geac_daily_rev') if hasattr(nas, 'get_json') else {}
    geac_items = []
    co_total = 0
    dr_total = 0
    if isinstance(geac_cashout, dict):
        for card, amt in geac_cashout.items():
            co_total += (amt or 0)
            geac_items.append({'label': f'Cashout {card}', 'value': round(amt or 0, 2)})
    if isinstance(geac_daily, dict):
        for card, amt in geac_daily.items():
            dr_total += (amt or 0)
            geac_items.append({'label': f'Daily Rev {card}', 'value': round(amt or 0, 2)})
    sections.append({
        'id': 'geac', 'title': 'GEAC Cartes',
        'variance': round(geac_var, 2),
        'tolerance': 0.10,
        'status': 'ok' if abs(geac_var) < 0.10 else 'error',
        'items': geac_items,
        'explanation': f'Cashout: ${co_total:,.2f} | Daily Revenue: ${dr_total:,.2f} | AR Variance: ${geac_var:+,.2f}',
    })

    # 4. QUASIMODO — Global reconciliation
    quasi_var = nas.quasi_variance or 0
    quasi_items = []
    for card in ['debit', 'visa', 'mc', 'amex', 'discover']:
        fb_val = getattr(nas, f'quasi_fb_{card}', 0) or 0
        rec_val = getattr(nas, f'quasi_rec_{card}', 0) or 0
        diff = round(fb_val - rec_val, 2)
        if fb_val != 0 or rec_val != 0:
            quasi_items.append({
                'label': card.upper(),
                'fb': round(fb_val, 2),
                'rec': round(rec_val, 2),
                'diff': diff,
            })
    quasi_cash_cdn = nas.quasi_cash_cdn or 0
    quasi_cash_usd = nas.quasi_cash_usd or 0
    sections.append({
        'id': 'quasimodo', 'title': 'Quasimodo (Réconciliation)',
        'variance': round(quasi_var, 2),
        'tolerance': 0.02,
        'status': 'ok' if abs(quasi_var) < 0.02 else ('warning' if abs(quasi_var) < 1.00 else 'error'),
        'items': quasi_items,
        'explanation': f'Cash CDN: ${quasi_cash_cdn:,.2f} | Cash USD: ${quasi_cash_usd:,.2f} | AMEX factor: {nas.quasi_amex_factor or 0.9735} | Variance globale: ${quasi_var:+,.2f}',
    })

    # 5. DIFF.CAISSE — Formula check
    diff_caisse = nas.diff_caisse_formula or 0
    sections.append({
        'id': 'diff_caisse', 'title': 'Diff.Caisse (Formule)',
        'variance': round(diff_caisse, 2),
        'tolerance': 1.00,
        'status': 'ok' if abs(diff_caisse) < 1.00 else 'warning',
        'items': [
            {'label': 'GEAC Daily Rev (UX)', 'value': round(dr_total, 2)},
            {'label': 'Transelect Restaurant', 'value': round(rest_total, 2)},
        ],
        'explanation': f'Formule: -GEAC_UX + Trans_Rest = -{dr_total:,.2f} + {rest_total:,.2f} = ${diff_caisse:+,.2f}',
    })

    # 6. HP/ADMIN impact
    hp_entries = nas.get_json('hp_admin_entries') if hasattr(nas, 'get_json') else []
    hp_total = 0
    hp_items = []
    if isinstance(hp_entries, list):
        for e in hp_entries:
            amt = sum(e.get(f, 0) or 0 for f in
                      ['nourriture', 'boisson', 'biere', 'vin', 'mineraux', 'autre', 'pourboire'])
            hp_total += amt
            area = e.get('area', '?')
            hp_items.append({'label': f'{area} ({e.get("raison", "")})', 'value': round(amt, 2)})
    sections.append({
        'id': 'hp_admin', 'title': 'HP/Admin (Déductions F&B)',
        'variance': round(hp_total, 2),
        'tolerance': None,  # info only
        'status': 'info',
        'items': hp_items,
        'explanation': f'Total HP déduit du F&B: ${hp_total:,.2f}. Vérifie que chaque entrée correspond à une facture autorisée.',
    })

    # 7. JOUR — Revenue overview
    total_fb = nas.jour_total_fb or 0
    total_rev = nas.jour_total_revenue or 0
    occ_pct = nas.jour_occupancy_rate or 0
    adr = nas.jour_adr or 0
    sections.append({
        'id': 'jour', 'title': 'Jour (Revenus)',
        'variance': 0,
        'tolerance': None,
        'status': 'info',
        'items': [
            {'label': 'Total F&B (après HP)', 'value': round(total_fb, 2)},
            {'label': 'Total Revenu', 'value': round(total_rev, 2)},
            {'label': 'Occupation', 'value': f'{occ_pct:.1f}%'},
            {'label': 'ADR', 'value': round(adr, 2)},
        ],
        'explanation': f'Revenu total: ${total_rev:,.2f} | F&B net: ${total_fb:,.2f} | Occ: {occ_pct:.1f}% | ADR: ${adr:,.2f}',
    })

    # 8. SD Variance
    sd_entries = nas.get_json('sd_entries') if hasattr(nas, 'get_json') else []
    sd_items = []
    sd_total = 0
    if isinstance(sd_entries, list):
        for e in sd_entries:
            amt = e.get('amount', 0) or 0
            sd_total += amt
            sd_items.append({'label': f'{e.get("department", "?")} — {e.get("name", "?")}', 'value': round(amt, 2)})
    sections.append({
        'id': 'sd', 'title': 'SD / Dépenses',
        'variance': 0,
        'tolerance': None,
        'status': 'info',
        'items': sd_items,
        'explanation': f'{len(sd_items)} entrée(s) SD pour un total de ${sd_total:,.2f}',
    })

    return sections


def _explain_recap(balance, items):
    """Generate a human-readable explanation of the recap balance."""
    if abs(balance) < 0.02:
        return 'Le recap est balancé (±$0.02).'
    parts = []
    for item in items:
        if item['correction'] != 0:
            parts.append(f"{item['label']}: correction de ${item['correction']:+,.2f}")
    if parts:
        return f'Écart de ${balance:+,.2f}. Corrections appliquées: ' + '; '.join(parts)
    return f'Écart de ${balance:+,.2f}. Aucune correction enregistrée — vérifie les montants de lecture.'


# ═══════════════════════════════════════
# API — UNLOCK / RELOCK
# ═══════════════════════════════════════

@rj_correction_bp.route('/api/rj/correction/unlock/<audit_date>', methods=['POST'])
@auth_required
def unlock_session(audit_date):
    """Unlock a locked session for correction."""
    try:
        d = datetime.strptime(audit_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400

    nas = NightAuditSession.query.filter_by(audit_date=d).first()
    if not nas:
        return jsonify({'error': 'Session non trouvée'}), 404
    if nas.status not in ('locked', 'submitted'):
        return jsonify({'error': f'Session est déjà en statut "{nas.status}"'}), 400

    data = request.get_json(force=True) or {}
    reason = data.get('reason', '')

    # Snapshot current state before unlock
    _snapshot_before_correction(nas)

    nas.status = 'correcting'
    nas.correction_count = (nas.correction_count or 0) + 1
    nas.correction_reason = reason
    nas.last_corrected_by = data.get('corrected_by', session.get('username', 'unknown'))
    nas.last_corrected_at = datetime.utcnow()

    # Log the unlock event
    log = SessionEditLog(
        audit_date=d,
        section='system',
        field_name='status',
        old_value='locked',
        new_value='correcting',
        edited_by=nas.last_corrected_by,
        correction_round=nas.correction_count,
        note=f'Déverrouillée pour correction: {reason}'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True, 'status': 'correcting', 'correction_count': nas.correction_count})


@rj_correction_bp.route('/api/rj/correction/relock/<audit_date>', methods=['POST'])
@auth_required
def relock_session(audit_date):
    """Relock a correcting session after corrections are done."""
    try:
        d = datetime.strptime(audit_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400

    nas = NightAuditSession.query.filter_by(audit_date=d).first()
    if not nas:
        return jsonify({'error': 'Session non trouvée'}), 404
    if nas.status != 'correcting':
        return jsonify({'error': f'Session n\'est pas en correction (statut: {nas.status})'}), 400

    # Recalculate everything
    nas.calculate_all()
    nas.status = 'locked'
    nas.completed_at = datetime.utcnow()

    # Log the relock event
    log = SessionEditLog(
        audit_date=d,
        section='system',
        field_name='status',
        old_value='correcting',
        new_value='locked',
        edited_by=session.get('username', 'unknown'),
        correction_round=nas.correction_count or 1,
        note='Reverrouillée après correction'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'success': True,
        'status': 'locked',
        'recap_balance': nas.recap_balance or 0,
        'transelect_variance': nas.transelect_variance or 0,
        'quasi_variance': nas.quasi_variance or 0,
    })


# ═══════════════════════════════════════
# API — EDIT HISTORY
# ═══════════════════════════════════════

@rj_correction_bp.route('/api/rj/correction/history/<audit_date>')
@auth_required
def get_history(audit_date):
    """Get the correction history (edit log) for a session."""
    try:
        d = datetime.strptime(audit_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Format de date invalide'}), 400

    logs = SessionEditLog.query.filter_by(audit_date=d)\
        .order_by(SessionEditLog.edited_at.desc()).all()
    return jsonify({'history': [l.to_dict() for l in logs]})


# ═══════════════════════════════════════
# HELPER — Log field changes
# ═══════════════════════════════════════

def log_field_changes(nas, section, new_data, fields):
    """Compare old vs new values and log any changes.
    Called from save endpoints when session is in 'correcting' status.
    """
    if nas.status != 'correcting':
        return

    editor = session.get('username', 'unknown')
    round_num = nas.correction_count or 1

    for field in fields:
        old_val = getattr(nas, field, None)
        new_val = new_data.get(field)
        if new_val is None:
            continue

        # Normalize for comparison
        old_str = str(round(old_val, 2)) if isinstance(old_val, float) else str(old_val or '')
        if isinstance(new_val, float):
            new_str = str(round(new_val, 2))
        else:
            new_str = str(new_val or '')

        if old_str != new_str:
            log = SessionEditLog(
                audit_date=nas.audit_date,
                section=section,
                field_name=field,
                old_value=old_str,
                new_value=new_str,
                edited_by=editor,
                correction_round=round_num,
            )
            db.session.add(log)


def log_json_changes(nas, section, field_name, old_json, new_json):
    """Log changes to a JSON column (dueback_entries, sd_entries, etc.)."""
    if nas.status != 'correcting':
        return

    old_str = json.dumps(old_json, ensure_ascii=False) if old_json else '[]'
    new_str = json.dumps(new_json, ensure_ascii=False) if new_json else '[]'

    if old_str != new_str:
        log = SessionEditLog(
            audit_date=nas.audit_date,
            section=section,
            field_name=field_name,
            old_value=old_str[:2000],  # Truncate for DB
            new_value=new_str[:2000],
            edited_by=session.get('username', 'unknown'),
            correction_round=nas.correction_count or 1,
        )
        db.session.add(log)


def _snapshot_before_correction(nas):
    """Take a snapshot of key values before correction starts."""
    snapshot_fields = [
        'recap_balance', 'transelect_variance', 'geac_ar_variance',
        'quasi_variance', 'diff_caisse_formula',
        'jour_total_fb', 'jour_total_revenue', 'jour_adr',
    ]
    editor = session.get('username', 'unknown')
    for field in snapshot_fields:
        val = getattr(nas, field, None)
        if val is not None:
            log = SessionEditLog(
                audit_date=nas.audit_date,
                section='snapshot',
                field_name=field,
                old_value=str(round(val, 2) if isinstance(val, float) else val),
                new_value=None,
                edited_by=editor,
                correction_round=(nas.correction_count or 0) + 1,
                note='Valeur avant correction'
            )
            db.session.add(log)
