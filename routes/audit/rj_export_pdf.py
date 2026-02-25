"""
RJ Natif — PDF Export (Hotel DBR Standard v4)
Full Daily Business Report pulling from ALL data sources:
  - NightAuditSession (RJ Natif session)
  - DailyJourMetrics (revenue, occupation, KPIs)
  - DailyCardMetrics (card POS vs bank, discount, tx counts)
  - DailyLaborMetrics (labor cost per dept)
  - DailyCashRecon (cash lecture/correction/deposits/variance)
  - DailyTipMetrics (tips brut/net per dept)
  - MonthlyBudget (budget targets for variance)
  - DepartmentLabor (monthly labor summary)
  + Last Year same date + MTD comparisons

Layout:
  Page 1: Revenue Summary (Today/Budget/LY/MTD/LY MTD), Room Stats, Budget Performance
  Page 2: Card Settlement Detail, Labor by Dept, Cash Reconciliation, Tips
  Page 3: F&B Detail, Quasimodo, Variances, DueBack/SD
  Page 4: 30-day trend charts + stats
  Page 5: Analyse & Recommandations Automatiques (AI-generated insights and alerts)
"""

import io
from datetime import datetime, timedelta, date as date_type
from statistics import mean, stdev, median

from flask import Blueprint, jsonify, send_file
from database.models import (
    db, NightAuditSession, DailyJourMetrics,
    DailyCardMetrics, DailyLaborMetrics, DailyCashRecon,
    DailyTipMetrics, MonthlyBudget
)

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak
)
from reportlab.pdfgen import canvas

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

rj_export_bp = Blueprint('rj_export', __name__)

# Colors
C_DARK    = HexColor('#1a1a2e')
C_HDR     = HexColor('#2c3e50')
C_SEC     = HexColor('#34495e')
C_ALT     = HexColor('#f4f6f7')
C_GRID    = HexColor('#bdc3c7')
C_GL      = HexColor('#d5d8dc')
C_TOTAL   = HexColor('#d5dbdb')
C_SUB     = HexColor('#ebedef')
C_GOLD    = HexColor('#c9a84c')
C_GREEN   = HexColor('#27ae60')
C_RED     = HexColor('#c0392b')
CC = ['#2c3e50','#c0392b','#27ae60','#d4a017','#8e44ad','#16a085']


# ── Format ──────────────────────────────────────────────────────
def _f(v):
    if v is None: return ''
    try:
        n = float(v)
        if n == 0: return '-'
        return f"({abs(n):,.2f})" if n < 0 else f"{n:,.2f}"
    except: return ''

def _fi(v):
    if v is None: return ''
    try: return f"{int(float(v)):,}"
    except: return ''

def _fp(v):
    if v is None: return ''
    try: return f"{float(v):.1f}%"
    except: return ''

def _fh(v):
    """Format hours."""
    if v is None: return ''
    try: return f"{float(v):.1f}"
    except: return ''

def _vpct(c, p):
    try:
        cv, pv = float(c or 0), float(p or 0)
        if pv == 0: return '' if cv == 0 else 'N/A'
        return f"{((cv-pv)/abs(pv))*100:+.1f}%"
    except: return ''

def _to_date(d):
    if isinstance(d, date_type): return d
    if isinstance(d, str): return datetime.strptime(d, '%Y-%m-%d').date()
    return d


# ── Data Loaders ────────────────────────────────────────────────
def _load_jour(dt):
    m = DailyJourMetrics.query.filter_by(date=dt).first()
    return {c.name: getattr(m, c.name) for c in m.__table__.columns} if m else {}

def _load_cards(dt):
    rows = DailyCardMetrics.query.filter_by(date=dt).all()
    return {r.card_type: {'pos': r.pos_total, 'bank': r.bank_total,
            'rate': r.discount_rate, 'disc': r.discount_amount,
            'net': r.net_amount, 'tx': r.transaction_count} for r in rows}

def _load_labor(dt):
    rows = DailyLaborMetrics.query.filter_by(date=dt).order_by(DailyLaborMetrics.labor_cost.desc()).all()
    return [{'dept': r.department, 'reg': r.regular_hours, 'ot': r.overtime_hours,
             'cost': r.labor_cost, 'emp': r.employees_count} for r in rows if r.labor_cost and r.labor_cost > 0]

def _load_cash(dt):
    r = DailyCashRecon.query.filter_by(date=dt).first()
    return {c.name: getattr(r, c.name) for c in r.__table__.columns} if r else {}

def _load_tips(dt):
    rows = DailyTipMetrics.query.filter_by(date=dt).all()
    return [{'dept': r.department, 'brut': r.tips_brut, 'net': r.tips_net,
             'ded': r.deductions, 'emp': r.employees_tipped}
            for r in rows if r.tips_brut and r.tips_brut > 0]

def _load_budget(dt):
    d = _to_date(dt)
    b = MonthlyBudget.query.filter_by(year=d.year, month=d.month).first()
    return {c.name: getattr(b, c.name) for c in b.__table__.columns} if b else {}

def _load_mtd(dt):
    d = _to_date(dt)
    first = d.replace(day=1)
    rows = DailyJourMetrics.query.filter(
        DailyJourMetrics.date >= first, DailyJourMetrics.date <= d).all()
    if not rows: return {}
    n = len(rows)
    def s(f): return sum(float(getattr(r, f) or 0) for r in rows)
    def a(f): return mean([float(getattr(r, f) or 0) for r in rows])
    return {
        'days': n, 'total_revenue': s('total_revenue'), 'room_revenue': s('room_revenue'),
        'fb_revenue': s('fb_revenue'), 'avg_occ': a('occupancy_rate'),
        'avg_adr': a('adr'), 'total_rooms': s('total_rooms_sold'),
        'tps': s('tps_total'), 'tvq': s('tvq_total'), 'txh': s('tvh_total'),
        'cafe': s('cafe_link_total'), 'piazza': s('piazza_total'),
        'spesa': s('spesa_total'), 'banquet': s('banquet_total'),
        'room_svc': s('room_svc_total'),
    }

def _load_mtd_labor(dt):
    d = _to_date(dt)
    first = d.replace(day=1)
    rows = DailyLaborMetrics.query.filter(
        DailyLaborMetrics.date >= first, DailyLaborMetrics.date <= d).all()
    agg = {}
    for r in rows:
        if not r.labor_cost: continue
        dept = r.department
        if dept not in agg:
            agg[dept] = {'hours': 0, 'ot': 0, 'cost': 0, 'days': 0}
        agg[dept]['hours'] += float(r.regular_hours or 0)
        agg[dept]['ot'] += float(r.overtime_hours or 0)
        agg[dept]['cost'] += float(r.labor_cost or 0)
        agg[dept]['days'] += 1
    return agg

def _load_mtd_cards(dt):
    d = _to_date(dt)
    first = d.replace(day=1)
    rows = DailyCardMetrics.query.filter(
        DailyCardMetrics.date >= first, DailyCardMetrics.date <= d).all()
    agg = {}
    for r in rows:
        ct = r.card_type
        if ct not in agg:
            agg[ct] = {'pos': 0, 'bank': 0, 'disc': 0, 'tx': 0}
        agg[ct]['pos'] += float(r.pos_total or 0)
        agg[ct]['bank'] += float(r.bank_total or 0)
        agg[ct]['disc'] += float(r.discount_amount or 0)
        agg[ct]['tx'] += int(r.transaction_count or 0)
    return agg

def _load_trend(dt, days=30):
    end = _to_date(dt)
    start = end - timedelta(days=days)
    rows = DailyJourMetrics.query.filter(
        DailyJourMetrics.date >= start, DailyJourMetrics.date <= end
    ).order_by(DailyJourMetrics.date).all()
    d = {k: [] for k in ['dates','revenues','fb_revenues','room_rev','occ_rates','adr_values',
        'cafe','piazza','spesa','banquet','room_svc','visa','mc','amex','debit']}
    for r in rows:
        dt2 = r.date if isinstance(r.date, date_type) else datetime.strptime(r.date,'%Y-%m-%d').date()
        d['dates'].append(dt2)
        d['revenues'].append(float(r.total_revenue or 0))
        d['fb_revenues'].append(float(r.fb_revenue or 0))
        d['room_rev'].append(float(r.room_revenue or 0))
        d['occ_rates'].append(float(r.occupancy_rate or 0))
        d['adr_values'].append(float(r.adr or 0))
        d['cafe'].append(float(r.cafe_link_total or 0))
        d['piazza'].append(float(r.piazza_total or 0))
        d['spesa'].append(float(r.spesa_total or 0))
        d['banquet'].append(float(r.banquet_total or 0))
        d['room_svc'].append(float(r.room_svc_total or 0))
        d['visa'].append(float(r.visa_total or 0))
        d['mc'].append(float(r.mastercard_total or 0))
        d['amex'].append(float(r.amex_elavon_total or 0) + float(r.amex_global_total or 0))
        d['debit'].append(float(r.debit_total or 0))
    return d


# ── Canvas ──────────────────────────────────────────────────────
class _C(canvas.Canvas):
    def __init__(self, *a, **kw):
        self._ad = kw.pop('audit_date',''); self._aud = kw.pop('auditor','')
        canvas.Canvas.__init__(self, *a, **kw)
        self._pp = []
    def showPage(self):
        self._pp.append(dict(self.__dict__)); self._startPage()
    def save(self):
        n = len(self._pp)
        for i, p in enumerate(self._pp):
            self.__dict__.update(p); self._hf(i+1, n); canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    def _hf(self, pg, tot):
        self.saveState(); pw, ph = letter; mx = 0.4*inch
        self.setFillColor(C_DARK)
        self.rect(0, ph-0.5*inch, pw, 0.5*inch, fill=True, stroke=False)
        self.setStrokeColor(C_GOLD); self.setLineWidth(2)
        self.line(0, ph-0.5*inch, pw, ph-0.5*inch)
        self.setFillColor(white); self.setFont('Helvetica-Bold', 9.5)
        self.drawString(mx+4, ph-0.33*inch, 'SHERATON LAVAL')
        self.setFont('Helvetica', 7)
        self.drawRightString(pw-mx-4, ph-0.22*inch, 'DAILY BUSINESS REPORT / RAPPORT JOURNALIER')
        self.drawRightString(pw-mx-4, ph-0.35*inch, f"Date: {self._ad}")
        self.setStrokeColor(C_GRID); self.setLineWidth(0.4)
        self.line(mx, 0.38*inch, pw-mx, 0.38*inch)
        self.setFont('Helvetica', 5.5); self.setFillColor(HexColor('#888'))
        self.drawString(mx, 0.22*inch, f"Night Auditor: {self._aud}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Galaxy Lightspeed PMS")
        self.drawRightString(pw-mx, 0.22*inch, f"{pg}/{tot}")
        self.restoreState()


# ── Table builder ───────────────────────────────────────────────
def _tbl(data, cw, secs=None, tots=None, subs=None, hr=1):
    secs = secs or set(); tots = tots or set(); subs = subs or set()
    t = Table(data, colWidths=cw, repeatRows=hr)
    cmds = [
        ('BACKGROUND',(0,0),(-1,hr-1), C_HDR), ('TEXTCOLOR',(0,0),(-1,hr-1), white),
        ('FONTNAME',(0,0),(-1,hr-1),'Helvetica-Bold'), ('FONTSIZE',(0,0),(-1,hr-1), 6),
        ('TOPPADDING',(0,0),(-1,hr-1), 2.5), ('BOTTOMPADDING',(0,0),(-1,hr-1), 2.5),
        ('ALIGN',(0,0),(-1,hr-1),'CENTER'),
        ('FONTNAME',(0,hr),(-1,-1),'Helvetica'), ('FONTSIZE',(0,hr),(-1,-1), 6),
        ('TOPPADDING',(0,hr),(-1,-1), 1.8), ('BOTTOMPADDING',(0,hr),(-1,-1), 1.8),
        ('ALIGN',(1,hr),(-1,-1),'RIGHT'), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('GRID',(0,0),(-1,-1), 0.2, C_GL), ('BOX',(0,0),(-1,-1), 0.4, C_GRID),
    ]
    for i in range(hr, len(data)):
        if i in secs:
            cmds += [('BACKGROUND',(0,i),(-1,i),C_SEC),('TEXTCOLOR',(0,i),(-1,i),white),
                     ('FONTNAME',(0,i),(-1,i),'Helvetica-Bold'),('SPAN',(0,i),(-1,i)),
                     ('ALIGN',(0,i),(-1,i),'LEFT')]
        elif i in tots:
            cmds += [('BACKGROUND',(0,i),(-1,i),C_TOTAL),('FONTNAME',(0,i),(-1,i),'Helvetica-Bold'),
                     ('LINEABOVE',(0,i),(-1,i),0.6,C_GRID)]
        elif i in subs:
            cmds += [('BACKGROUND',(0,i),(-1,i),C_SUB),('FONTNAME',(0,i),(-1,i),'Helvetica-Bold')]
        elif (i-hr)%2==1 and i not in secs:
            cmds.append(('BACKGROUND',(0,i),(-1,i),C_ALT))
    t.setStyle(TableStyle(cmds))
    return t


# ── Charts ──────────────────────────────────────────────────────
def _mk(fn, w=3.3, h=1.85):
    fig, ax = plt.subplots(figsize=(w, h)); fig.patch.set_facecolor('white')
    fn(fig, ax)
    for sp in ['top','right']: ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=5); ax.grid(True, alpha=0.12, lw=0.3)
    plt.tight_layout(pad=0.3)
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=160, bbox_inches='tight')
    plt.close(fig); buf.seek(0)
    return Image(buf, width=w*inch, height=h*inch)


# ── Recommendations Engine ──────────────────────────────────────
def _generate_recommendations(s, jour, cards, labor, cash, tips, budget, mtd, ly_jour, ly_mtd, mtd_labor, mtd_cards, trend):
    """
    Analyzes audit data and generates intelligent recommendations.
    Returns: list of {category: str, icon: str, items: [{text: str, severity: 'info'|'warning'|'alert'|'positive'}]}
    """
    recs = {}

    # Extract key values with safety
    tot_rev = float(jour.get('total_revenue') or 0)
    room_rev = float(jour.get('room_revenue') or 0)
    fb_rev = float(jour.get('fb_revenue') or 0)
    occ = float(jour.get('occupancy_rate') or 0)
    adr_v = float(jour.get('adr') or 0)

    ly_rev = float(ly_jour.get('total_revenue') or 0)
    ly_room = float(ly_jour.get('room_revenue') or 0)
    ly_fb = float(ly_jour.get('fb_revenue') or 0)
    ly_adr = float(ly_jour.get('adr') or 0)
    ly_occ = float(ly_jour.get('occupancy_rate') or 0)

    m_rev = mtd.get('total_revenue', 0)
    m_room = mtd.get('room_revenue', 0)
    m_fb = mtd.get('fb_revenue', 0)
    m_days = mtd.get('days', 1) or 1

    bd_total = float(budget.get('total_revenue_budget', 0) or 0) / 28 if budget else 0
    bd_room = float(budget.get('room_revenue_budget', 0) or 0) / 28 if budget else 0
    bd_fb = float(budget.get('fb_revenue_budget', 0) or 0) / 28 if budget else 0
    bd_occ = float(budget.get('occupancy_budget', 0) or 0)
    bd_adr = float(budget.get('adr_budget', 0) or 0)
    bd_labor = float(budget.get('labor_cost_budget', 0) or 0) / 28 if budget else 0

    bd_mtd_total = bd_total * m_days

    # 1. PERFORMANCE REVENUS
    recs['perf'] = {'category': 'PERFORMANCE REVENUS', 'icon': '💰', 'items': []}

    if tot_rev > 0 and bd_total > 0:
        var_pct = (tot_rev - bd_total) / bd_total * 100
        if var_pct < -5:
            recs['perf']['items'].append({
                'text': f"Revenus du jour {var_pct:.1f}% sous le budget. Analyser les causes (occ., tarifs, mix).",
                'severity': 'alert'
            })
        elif var_pct > 5:
            recs['perf']['items'].append({
                'text': f"Revenus du jour {var_pct:+.1f}% au-dessus du budget. Excellente performance.",
                'severity': 'positive'
            })

    if ly_rev > 0:
        ly_var = (tot_rev - ly_rev) / ly_rev * 100
        if ly_var < -3:
            recs['perf']['items'].append({
                'text': f"Baisse de {abs(ly_var):.1f}% vs l'an dernier. Enquêter sur tendance.",
                'severity': 'alert'
            })
        elif ly_var > 3:
            recs['perf']['items'].append({
                'text': f"Hausse de {ly_var:.1f}% vs l'an dernier. Tendance positive.",
                'severity': 'positive'
            })

    if m_rev > 0 and bd_mtd_total > 0:
        mtd_var = (m_rev - bd_mtd_total) / bd_mtd_total * 100
        if mtd_var > 5:
            recs['perf']['items'].append({
                'text': f"Cumul mois {mtd_var:+.1f}% du budget. Maintenir la cadence.",
                'severity': 'positive'
            })

    # 2. OCCUPATION & TARIFICATION
    recs['occ'] = {'category': 'OCCUPATION & TARIFICATION', 'icon': '🛏️', 'items': []}

    if bd_occ > 0:
        occ_var = bd_occ - occ
        if occ_var > 10:
            recs['occ']['items'].append({
                'text': f"Occupation {occ:.1f}% vs budget {bd_occ:.1f}%. Écart de {occ_var:.1f}pts.",
                'severity': 'alert'
            })

    if ly_adr > 0:
        adr_var = (adr_v - ly_adr) / ly_adr * 100
        if abs(adr_var) > 5:
            sev = 'warning' if adr_var < 0 else 'positive'
            recs['occ']['items'].append({
                'text': f"ADR {adr_var:+.1f}% vs l'an dernier ({adr_v:.0f}$ vs {ly_adr:.0f}$).",
                'severity': sev
            })

    if occ > 0 and bd_occ > 0 and adr_v > 0 and bd_adr > 0:
        if occ > bd_occ + 5 and adr_v < bd_adr * 0.95:
            recs['occ']['items'].append({
                'text': "Occupation forte mais ADR faible. Optimiser la stratégie tarifaire.",
                'severity': 'warning'
            })

    comp_rooms = int(float(s.get('jour_rooms_comp') or 0))
    if comp_rooms > 5:
        recs['occ']['items'].append({
            'text': f"{comp_rooms} chambres complimentaires. Vérifier justifications.",
            'severity': 'info'
        })

    # 3. RESTAURATION (F&B)
    recs['fb'] = {'category': 'RESTAURATION (F&B)', 'icon': '🍽️', 'items': []}

    if room_rev > 0 and fb_rev > 0:
        fb_capture = fb_rev / room_rev * 100
        if ly_room > 0:
            ly_capture = ly_fb / ly_room * 100
            capture_var = fb_capture - ly_capture
            if capture_var < -5:
                recs['fb']['items'].append({
                    'text': f"Taux F&B {fb_capture:.1f}% vs {ly_capture:.1f}% l'an dernier. Baisse de {abs(capture_var):.1f}pts.",
                    'severity': 'warning'
                })

    # Check each F&B dept vs LY
    fb_depts = [('cafe', 'Café Link'), ('piazza', 'Piazza'), ('spesa', 'Spesa'),
                ('banquet', 'Banquet'), ('chambres_svc', 'Svc. Chambres')]
    worst_dept = None
    worst_var = 0

    for fk, fl in fb_depts:
        tv = sum(float(s.get(f'jour_{fk}_{c}') or 0) for c in ['nourriture','boisson','bieres','mineraux','vins'])
        lyv = float(ly_jour.get(f'{fk}_total') or 0) if fk != 'chambres_svc' else 0
        if lyv > 0:
            var = (tv - lyv) / lyv * 100
            if var < worst_var:
                worst_var = var
                worst_dept = fl

    if worst_dept and worst_var < -10:
        recs['fb']['items'].append({
            'text': f"{worst_dept} en baisse de {abs(worst_var):.1f}% vs l'an dernier.",
            'severity': 'warning'
        })

    # 4. MAIN-D'OEUVRE (LABOR)
    recs['labor'] = {'category': 'MAIN-D\'OEUVRE (LABOR)', 'icon': '👥', 'items': []}

    if labor and tot_rev > 0:
        t_cost = sum(float(l.get('cost', 0) or 0) for l in labor)
        labor_pct = t_cost / tot_rev * 100

        if labor_pct > 35:
            recs['labor']['items'].append({
                'text': f"Ratio main-d'oeuvre {labor_pct:.1f}%. Objectif <30%. À surveiller.",
                'severity': 'alert'
            })
        elif labor_pct > 30:
            recs['labor']['items'].append({
                'text': f"Ratio main-d'oeuvre {labor_pct:.1f}%. Au-dessus de l'objectif 30%.",
                'severity': 'warning'
            })

        # OT ratio
        t_reg = sum(float(l.get('reg', 0) or 0) for l in labor)
        t_ot = sum(float(l.get('ot', 0) or 0) for l in labor)
        if t_reg > 0:
            ot_ratio = t_ot / t_reg * 100
            if ot_ratio > 15:
                recs['labor']['items'].append({
                    'text': f"Heures supplémentaires {ot_ratio:.1f}% des H.REG. Coûts élevés.",
                    'severity': 'warning'
                })

        # Top 3 depts
        top3 = sorted(labor, key=lambda x: float(x.get('cost', 0) or 0), reverse=True)[:3]
        if top3:
            top_depts = ', '.join([l.get('dept', '') for l in top3])
            recs['labor']['items'].append({
                'text': f"Départements les plus coûteux: {top_depts}.",
                'severity': 'info'
            })

    # 5. RECONCILIATION & CONTROLES
    recs['recon'] = {'category': 'RECONCILIATION & CONTROLES', 'icon': '✓', 'items': []}

    if cash:
        quasi_var = float(cash.get('quasimodo_variance') or 0)
        if abs(quasi_var) > 1:
            recs['recon']['items'].append({
                'text': f"Variance Quasimodo: ${quasi_var:+.2f}. Audit de réconciliation requis.",
                'severity': 'alert'
            })
        else:
            recs['recon']['items'].append({
                'text': f"Variance Quasimodo: ${quasi_var:+.2f}. Accepté.",
                'severity': 'positive'
            })

        diff_caisse = float(cash.get('diff_caisse') or 0)
        if abs(diff_caisse) > 5:
            recs['recon']['items'].append({
                'text': f"Différence caisse: ${diff_caisse:+.2f}. Enquête nécessaire.",
                'severity': 'alert'
            })
        elif abs(diff_caisse) > 0:
            recs['recon']['items'].append({
                'text': f"Différence caisse: ${diff_caisse:+.2f}.",
                'severity': 'info'
            })

    # Internet/Sonifi variances
    if s.get('internet_variance'):
        iv = float(s.get('internet_variance') or 0)
        if abs(iv) > 0.02:
            recs['recon']['items'].append({
                'text': f"Variance Internet (CD36): ${iv:+.2f}.",
                'severity': 'warning'
            })

    if s.get('sonifi_variance'):
        sv = float(s.get('sonifi_variance') or 0)
        if abs(sv) > 0.02:
            recs['recon']['items'].append({
                'text': f"Variance Sonifi (CD35): ${sv:+.2f}.",
                'severity': 'warning'
            })

    # Card discount rate anomalies
    if cards:
        for ct_name, c_data in cards.items():
            rate = float(c_data.get('rate', 0) or 0)
            if rate > 0.03 or (ct_name == 'AMEX' and rate > 0.035):
                recs['recon']['items'].append({
                    'text': f"Taux de rabais {ct_name} élevé: {rate*100:.2f}%.",
                    'severity': 'info'
                })

    # DueBack check
    dbe = s.get('dueback_entries', [])
    if isinstance(dbe, list) and dbe:
        high_entries = [e for e in dbe if isinstance(e, dict) and float(e.get('nouveau', 0) or 0) > 500]
        if high_entries:
            recs['recon']['items'].append({
                'text': f"{len(high_entries)} entries DueBack > $500. À examiner.",
                'severity': 'info'
            })

    # 6. TENDANCES (30-day trend analysis)
    recs['trend'] = {'category': 'TENDANCES (30 JOURS)', 'icon': '📈', 'items': []}

    if trend and len(trend.get('dates', [])) > 7:
        td = trend
        revs = td.get('revenues', [])
        occs = td.get('occ_rates', [])
        adrs = td.get('adr_values', [])

        if len(revs) > 7:
            last7 = mean(revs[-7:])
            mean30 = mean(revs)
            if last7 > mean30 * 1.05:
                recs['trend']['items'].append({
                    'text': f"Revenue 7j moyen {last7:.0f}$ > moyenne 30j {mean30:.0f}$. Tendance positive.",
                    'severity': 'positive'
                })
            elif last7 < mean30 * 0.95:
                recs['trend']['items'].append({
                    'text': f"Revenue 7j moyen {last7:.0f}$ < moyenne 30j {mean30:.0f}$. Tendance baissière.",
                    'severity': 'warning'
                })

        if len(revs) > 1:
            vol = stdev(revs) / mean(revs) * 100 if mean(revs) > 0 else 0
            if vol > 20:
                recs['trend']['items'].append({
                    'text': f"Volatilité des revenus: {vol:.1f}%. Stabilité faible.",
                    'severity': 'warning'
                })

        if revs:
            best_day = max(revs)
            worst_day = min(revs)
            days = len(revs)
            recs['trend']['items'].append({
                'text': f"Meilleur jour: ${best_day:.0f}, Pire: ${worst_day:.0f} (écart {((best_day-worst_day)/worst_day*100):.0f}%).",
                'severity': 'info'
            })

        # Consecutive days below average
        if revs:
            avg = mean(revs)
            consec = 0
            max_consec = 0
            for r in revs:
                if r < avg:
                    consec += 1
                    max_consec = max(max_consec, consec)
                else:
                    consec = 0
            if max_consec > 3:
                recs['trend']['items'].append({
                    'text': f"{max_consec} jours consécutifs sous la moyenne. Enquêter causes.",
                    'severity': 'warning'
                })

    # Filter and return
    result = [r for r in recs.values() if r['items']]
    return result


# ── PDF ─────────────────────────────────────────────────────────
def generate_rj_pdf(s, jour, cards, labor, cash, tips, budget, mtd, ly_jour, ly_mtd, mtd_labor, mtd_cards, trend):
    audit_date = s.get('audit_date','')
    auditor = s.get('auditor_name','') or ''
    bd = budget  # budget dict
    md = mtd     # mtd dict

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
        topMargin=0.62*inch, bottomMargin=0.48*inch,
        leftMargin=0.38*inch, rightMargin=0.38*inch)

    styles = getSampleStyleSheet()
    si = ParagraphStyle('i', parent=styles['Normal'], fontSize=6, leading=7.5)
    story = []

    # Info bar
    story.append(Spacer(1,3))
    parts = [f"<b>Date:</b> {audit_date}", f"<b>Auditeur:</b> {auditor}",
             f"<b>Statut:</b> {(s.get('status') or 'draft').upper()}"]
    w = s.get('weather_condition',''); t = s.get('temperature','')
    if w: parts.append(f"<b>Meteo:</b> {w} {t}C" if t else f"<b>Meteo:</b> {w}")
    cr = s.get('chambres_refaire','')
    if cr: parts.append(f"<b>Ch.refaire:</b> {cr}")
    story.append(Paragraph("  |  ".join(parts), si))
    story.append(Spacer(1,4))

    # Helper to add section/total/subtotal rows
    def _sr(rows, label, n):
        i = len(rows); return i
    # ════════════════════════════════════════════════════════════
    # PAGE 1 — REVENUE + ROOM STATS + BUDGET
    # ════════════════════════════════════════════════════════════
    cw = [1.5*inch, 0.72*inch, 0.72*inch, 0.55*inch, 0.72*inch, 0.72*inch, 0.55*inch, 0.72*inch, 0.55*inch]
    hdr = ['', "AUJ.", "BUDGET", "VAR%", "CUMUL", "BUD.MTD", "VAR%", "AN PREC.", "VAR%"]

    rows = [hdr]; secs=set(); tots=set(); subs=set()
    bd_days = md.get('days',1) or 1
    bd_room_day = float(bd.get('room_revenue_budget',0) or 0) / 28  # approximate
    bd_fb_day = float(bd.get('fb_revenue_budget',0) or 0) / 28
    bd_total_day = float(bd.get('total_revenue_budget',0) or 0) / 28
    bd_room_mtd = bd_room_day * bd_days
    bd_fb_mtd = bd_fb_day * bd_days
    bd_total_mtd = bd_total_day * bd_days
    bd_occ = float(bd.get('occupancy_budget',0) or 0)
    bd_adr = float(bd.get('adr_budget',0) or 0)

    room_rev = float(jour.get('room_revenue') or s.get('jour_room_revenue') or 0)
    fb_rev = float(jour.get('fb_revenue') or s.get('jour_total_fb') or 0)
    tot_rev = float(jour.get('total_revenue') or s.get('jour_total_revenue') or 0)
    occ = float(jour.get('occupancy_rate') or s.get('jour_occupancy_rate') or 0)
    adr_v = float(jour.get('adr') or s.get('jour_adr') or 0)
    revpar_v = adr_v * occ / 100 if occ else 0

    ly_room = float(ly_jour.get('room_revenue') or 0)
    ly_fb = float(ly_jour.get('fb_revenue') or 0)
    ly_rev = float(ly_jour.get('total_revenue') or 0)
    ly_occ = float(ly_jour.get('occupancy_rate') or 0)
    ly_adr = float(ly_jour.get('adr') or 0)

    m_room = md.get('room_revenue',0); m_fb = md.get('fb_revenue',0); m_rev = md.get('total_revenue',0)
    m_occ = md.get('avg_occ',0); m_adr = md.get('avg_adr',0)

    lm_room = ly_mtd.get('room_revenue',0); lm_fb = ly_mtd.get('fb_revenue',0); lm_rev = ly_mtd.get('total_revenue',0)

    def dr(label, today, bud, mtd_v, bud_mtd, ly_v):
        rows.append([f'  {label}', _f(today), _f(bud), _vpct(today,bud),
                     _f(mtd_v), _f(bud_mtd), _vpct(mtd_v,bud_mtd), _f(ly_v), _vpct(today,ly_v)])
    def tr(label, today, bud, mtd_v, bud_mtd, ly_v):
        i=len(rows); tots.add(i)
        rows.append([label, _f(today), _f(bud), _vpct(today,bud),
                     _f(mtd_v), _f(bud_mtd), _vpct(mtd_v,bud_mtd), _f(ly_v), _vpct(today,ly_v)])
    def sr(label):
        i=len(rows); secs.add(i); rows.append([label]+['']*8)
    def sbr(label, today, bud, mtd_v, bud_mtd, ly_v):
        i=len(rows); subs.add(i)
        rows.append([f'  {label}', _f(today), _f(bud), _vpct(today,bud),
                     _f(mtd_v), _f(bud_mtd), _vpct(mtd_v,bud_mtd), _f(ly_v), _vpct(today,ly_v)])

    sr('HEBERGEMENT')
    dr('Revenus chambres', room_rev, bd_room_day, m_room, bd_room_mtd, ly_room)
    tel = sum(float(s.get(f) or 0) for f in ['jour_tel_local','jour_tel_interurbain','jour_tel_publics'])
    if tel: dr('Telephones', tel, 0, 0, 0, 0)
    for lb, fld in [('Internet','jour_internet'),('Sonifi','jour_sonifi'),('Boutique','jour_boutique'),
                     ('Nettoyeur','jour_nettoyeur'),('Massage','jour_massage')]:
        v = float(s.get(fld) or 0)
        if v: dr(lb, v, 0, 0, 0, 0)
    sbr('S/T HEBERGEMENT', room_rev+tel, bd_room_day, m_room, bd_room_mtd, ly_room)

    sr('RESTAURATION (F&B)')
    fb_depts = [('Cafe Link','cafe'),('Piazza','piazza'),('Spesa','spesa'),
                ('Serv.Chambres','chambres_svc'),('Banquet','banquet')]
    fb_cats = ['nourriture','boisson','bieres','mineraux','vins']
    for dl, dk in fb_depts:
        tv = sum(float(s.get(f'jour_{dk}_{c}') or 0) for c in fb_cats)
        lyv = float(ly_jour.get(f'{dk}_total') or 0) if dk != 'chambres_svc' else 0
        mv = md.get(dk, 0)
        dr(dl, tv, 0, mv, 0, lyv)
    sbr('S/T F&B', fb_rev, bd_fb_day, m_fb, bd_fb_mtd, ly_fb)

    sr('TAXES')
    tps = float(s.get('jour_tps') or 0); tvq = float(s.get('jour_tvq') or 0)
    txh = float(s.get('jour_taxe_hebergement') or 0)
    dr('TPS (5%)', tps, 0, md.get('tps',0), 0, float(ly_jour.get('tps_total') or 0))
    dr('TVQ (9.975%)', tvq, 0, md.get('tvq',0), 0, float(ly_jour.get('tvq_total') or 0))
    dr('Taxe heberg. (3.5%)', txh, 0, md.get('txh',0), 0, float(ly_jour.get('tvh_total') or 0))

    tr('TOTAL REVENUS', tot_rev, bd_total_day, m_rev, bd_total_mtd, ly_rev)

    story.append(_tbl(rows, cw, secs=secs, tots=tots, subs=subs))
    story.append(Spacer(1,5))

    # Room stats + KPIs compact
    rcw = [1.0*inch,0.55*inch,0.55*inch, 0.12*inch, 1.0*inch,0.55*inch,0.55*inch, 0.12*inch, 1.0*inch,0.55*inch,0.55*inch]
    rh = ['CHAMBRES','AUJ.','AN PR.','','INVENTAIRE','AUJ.','AN PR.','','KPI','AUJ.','BUDGET']
    rs_sold = sum(int(float(s.get(f'jour_rooms_{t}') or 0)) for t in ['simple','double','suite','comp'])
    rs_hu = int(float(s.get('jour_rooms_hors_usage') or 0))
    ly_sold = int(float(ly_jour.get('total_rooms_sold') or 0))
    ly_cl = int(float(ly_jour.get('nb_clients') or 0))
    nb_cl = int(float(s.get('jour_nb_clients') or 0))
    rd = [rh,
        ['Simples',_fi(s.get('jour_rooms_simple')),'','','Disponibles',str(340-rs_hu),'','','Occ%',_fp(occ),_fp(bd_occ)],
        ['Doubles',_fi(s.get('jour_rooms_double')),'','','Vendues',str(rs_sold),str(ly_sold),'','ADR',_f(adr_v),_f(bd_adr)],
        ['Suites',_fi(s.get('jour_rooms_suite')),'','','Clients',str(nb_cl),str(ly_cl),'','RevPAR',_f(revpar_v),''],
        ['Comp.',_fi(s.get('jour_rooms_comp')),'','','H.Usage',str(rs_hu),'','','Cl/Ch',
         f"{nb_cl/rs_sold:.2f}" if rs_sold else '-', f"{ly_cl/ly_sold:.2f}" if ly_sold else '-'],
    ]
    rst = Table(rd, colWidths=rcw, repeatRows=1)
    rc = [('BACKGROUND',(0,0),(-1,0),C_HDR),('TEXTCOLOR',(0,0),(-1,0),white),
          ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),6),
          ('TOPPADDING',(0,0),(-1,-1),1.8),('BOTTOMPADDING',(0,0),(-1,-1),1.8),
          ('ALIGN',(1,0),(-1,-1),'RIGHT'),('GRID',(0,0),(-1,-1),0.2,C_GL),
          ('BOX',(0,0),(-1,-1),0.4,C_GRID),
          ('BACKGROUND',(3,0),(3,-1),C_SUB),('BACKGROUND',(7,0),(7,-1),C_SUB)]
    for i in range(1,len(rd)):
        if i%2==0:
            for rng in [(0,i,2,i),(4,i,6,i),(8,i,10,i)]:
                rc.append(('BACKGROUND',rng[:2],rng[2:],C_ALT))
    rst.setStyle(TableStyle(rc)); story.append(rst)

    # ════════════════════════════════════════════════════════════
    # PAGE 2 — CARDS + LABOR + CASH + TIPS
    # ════════════════════════════════════════════════════════════
    story.append(PageBreak()); story.append(Spacer(1,3))

    # Card Settlement
    if cards:
        ccw = [1.0*inch, 0.85*inch, 0.85*inch, 0.5*inch, 0.65*inch, 0.65*inch, 0.4*inch, 0.85*inch, 0.5*inch, 0.55*inch]
        ch = ['CARTE','POS','BANQUE','DISC%','DISC $','NET','TX','CUMUL POS','CUMUL TX','AN PR.']
        cr_rows = [ch]; ct = set()
        t_pos = t_bank = t_disc = t_net = t_tx = 0
        t_mpos = t_mtx = 0
        for ct_name in ['VISA','MC','AMEX','DEBIT','DISCOVER']:
            c = cards.get(ct_name, {})
            mc = mtd_cards.get(ct_name, {})
            ly_c = float(ly_jour.get(f'{ct_name.lower()}_total') or 0) if ct_name != 'AMEX' else (
                float(ly_jour.get('amex_elavon_total') or 0) + float(ly_jour.get('amex_global_total') or 0))
            pos = float(c.get('pos',0) or 0); bank = float(c.get('bank',0) or 0)
            disc = float(c.get('disc',0) or 0); net = float(c.get('net',0) or 0)
            tx = int(c.get('tx',0) or 0); rate = float(c.get('rate',0) or 0)
            mpos = float(mc.get('pos',0)); mtx = int(mc.get('tx',0))
            t_pos+=pos; t_bank+=bank; t_disc+=disc; t_net+=net; t_tx+=tx; t_mpos+=mpos; t_mtx+=mtx
            cr_rows.append([f'  {ct_name}', _f(pos), _f(bank), _fp(rate*100) if rate else '-',
                           _f(disc), _f(net), str(tx), _f(mpos), str(mtx), _f(ly_c)])
        i=len(cr_rows); ct.add(i)
        cr_rows.append(['TOTAL', _f(t_pos), _f(t_bank), '', _f(t_disc), _f(t_net), str(t_tx),
                        _f(t_mpos), str(t_mtx), ''])
        story.append(_tbl(cr_rows, ccw, tots=ct))
        story.append(Spacer(1,5))

    # Labor by Department
    if labor:
        lcw = [1.2*inch, 0.65*inch, 0.65*inch, 0.85*inch, 0.45*inch, 0.12*inch,
               1.2*inch, 0.65*inch, 0.85*inch]
        lh = ['DEPARTEMENT','H.REG','H.SUP','COUT $','EMP','','CUMUL MOIS','HEURES','COUT $']
        lr = [lh]; lt = set()
        t_hr=t_ot=t_cost=t_emp=0
        for l in labor:
            ml = mtd_labor.get(l['dept'], {})
            t_hr+=float(l['reg'] or 0); t_ot+=float(l['ot'] or 0)
            t_cost+=float(l['cost'] or 0); t_emp+=int(l['emp'] or 0)
            lr.append([f"  {l['dept']}", _fh(l['reg']), _fh(l['ot']), _f(l['cost']), str(l['emp']), '',
                       f"  {l['dept']}", _fh(ml.get('hours',0)+ml.get('ot',0)), _f(ml.get('cost',0))])
        i=len(lr); lt.add(i)
        tm_h = sum(v['hours']+v['ot'] for v in mtd_labor.values())
        tm_c = sum(v['cost'] for v in mtd_labor.values())
        lr.append(['TOTAL', _fh(t_hr), _fh(t_ot), _f(t_cost), str(t_emp), '',
                   'TOTAL', _fh(tm_h), _f(tm_c)])

        # Labor cost ratio
        labor_pct = (t_cost / tot_rev * 100) if tot_rev > 0 else 0
        bud_labor = float(bd.get('labor_cost_budget',0) or 0) / 28 if bd else 0
        i2=len(lr)
        lr.append(['RATIO MAIN-D\'OEUVRE', '', '', _fp(labor_pct), '', '', 'BUDGET/JOUR', '', _f(bud_labor)])

        story.append(_tbl(lr, lcw, tots=lt))
        story.append(Spacer(1,5))

    # Cash Reconciliation
    if cash:
        kcw = [1.6*inch, 1.0*inch, 1.0*inch, 1.0*inch, 0.8*inch, 1.0*inch, 0.8*inch]
        kh = ['CAISSE','LECTURE','CORRECTION','NET','','CONTROLE','VALEUR']
        kr = [kh]; kt = set()
        cls = float(cash.get('cash_ls_lecture',0) or 0); clc = float(cash.get('cash_ls_correction',0) or 0)
        cps = float(cash.get('cash_pos_lecture',0) or 0); cpc = float(cash.get('cash_pos_correction',0) or 0)
        kr.append(['  Cash LS', _f(cls), _f(clc), _f(cls+clc), '', 'Depot CDN', _f(cash.get('deposit_cdn'))])
        kr.append(['  Cash POS', _f(cps), _f(cpc), _f(cps+cpc), '', 'Depot USD', _f(cash.get('deposit_usd'))])
        kr.append(['  Cheque AR', _f(cash.get('cheque_ar')), '', '', '', 'Diff. caisse', _f(cash.get('diff_caisse'))])
        kr.append(['  Cheque DR', _f(cash.get('cheque_dr')), '', '', '', 'Quasi. var.', _f(cash.get('quasimodo_variance'))])
        kr.append(['  Remb. grat.', _f(cash.get('remb_gratuite')), '', '', '', 'Surplus/Def.', _f(cash.get('surplus_deficit'))])
        kr.append(['  Remb. client', _f(cash.get('remb_client')), '', '', '', '', ''])
        kr.append(['  DueBack', _f(cash.get('dueback_total')), '', '', '', '', ''])
        story.append(_tbl(kr, kcw))
        story.append(Spacer(1,5))

    # Tips
    if tips:
        tcw = [1.4*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.6*inch, 0.12*inch, 1.4*inch, 0.9*inch]
        th = ['DEPARTEMENT','BRUT','DEDUCTIONS','NET','EMP','','','']
        tr_rows = [th]; tt = set()
        tb=tn=td_t=te=0
        for tip in tips:
            tb+=float(tip['brut'] or 0); tn+=float(tip['net'] or 0)
            td_t+=float(tip['ded'] or 0); te+=int(tip['emp'] or 0)
            tr_rows.append([f"  {tip['dept']}", _f(tip['brut']), _f(tip['ded']),
                           _f(tip['net']), str(tip['emp']), '', '', ''])
        i=len(tr_rows); tt.add(i)
        tr_rows.append(['TOTAL', _f(tb), _f(td_t), _f(tn), str(te), '', '', ''])
        story.append(_tbl(tr_rows, tcw, tots=tt))

    # ════════════════════════════════════════════════════════════
    # PAGE 3 — F&B DETAIL + QUASIMODO + VARIANCES + SD
    # ════════════════════════════════════════════════════════════
    story.append(PageBreak()); story.append(Spacer(1,3))

    # F&B Detail
    fc = [1.2*inch, 0.7*inch, 0.7*inch, 0.65*inch, 0.65*inch, 0.65*inch, 0.75*inch, 0.75*inch]
    fh = ['DEPARTEMENT','NOURR.','BOISSON','BIERES','MINER.','VINS','TOTAL','AN PR.']
    fr = [fh]; ft = set()
    g = [0]*5; g_ly = 0
    for dl, dk in fb_depts:
        row = [f'  {dl}']; ds = 0
        for ci, cat in enumerate(fb_cats):
            v = float(s.get(f'jour_{dk}_{cat}') or 0); g[ci]+=v; ds+=v
            row.append(_f(v))
        row.append(_f(ds))
        lyv = float(ly_jour.get(f'{dk}_total') or 0) if dk != 'chambres_svc' else 0
        g_ly += lyv; row.append(_f(lyv))
        fr.append(row)
    i=len(fr); ft.add(i)
    fr.append(['TOTAL'] + [_f(x) for x in g] + [_f(sum(g)), _f(g_ly)])
    story.append(_tbl(fr, fc, tots=ft))
    story.append(Spacer(1,5))

    # Quasimodo
    qc = [1.1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch]
    qh = ['CARTE','F&B','RECEPTION','TOTAL','RJ','ECART','STATUT']
    qr = [qh]; qt = set()
    qcards = [('Debit','debit'),('Visa','visa'),('MC','mc'),('AMEX','amex'),('Discover','discover')]
    tfb=trec=0
    for lb, k in qcards:
        fv = float(s.get(f'quasi_fb_{k}') or 0); rv = float(s.get(f'quasi_rec_{k}') or 0)
        tfb+=fv; trec+=rv
        qr.append([f'  {lb}', _f(fv), _f(rv), _f(fv+rv), '', '', ''])
    qr.append(['  Cash CDN', '', '', _f(s.get('quasi_cash_cdn')), '', '', ''])
    qr.append(['  Cash USD', '', '', _f(s.get('quasi_cash_usd')), '', '', ''])
    q_tot = float(s.get('quasi_total') or 0); q_rj = float(s.get('quasi_rj_total') or 0)
    q_var = float(s.get('quasi_variance') or 0)
    i=len(qr); qt.add(i)
    qr.append(['TOTAL', _f(tfb), _f(trec), _f(q_tot), _f(q_rj), _f(q_var),
               'OK' if abs(q_var)<1 else 'ECART'])
    story.append(_tbl(qr, qc, tots=qt))
    story.append(Spacer(1,5))

    # Variances CD
    vc = [1.2*inch, 1.0*inch, 1.0*inch, 0.8*inch, 0.6*inch]
    vh = ['MODULE','SRC A','SRC B','ECART','STATUT']
    iv = float(s.get('internet_variance') or 0); sv = float(s.get('sonifi_variance') or 0)
    vr = [vh,
        ['  Internet (CD36)', _f(s.get('internet_ls_361')), _f(s.get('internet_ls_365')), _f(iv), 'OK' if abs(iv)<0.02 else 'ECART'],
        ['  Sonifi (CD35)', _f(s.get('sonifi_cd_352')), _f(s.get('sonifi_email')), _f(sv), 'OK' if abs(sv)<0.02 else 'ECART']]
    story.append(_tbl(vr, vc))
    story.append(Spacer(1,5))

    # DueBack
    dbe = s.get('dueback_entries', [])
    if isinstance(dbe, list):
        valid = [e for e in dbe if isinstance(e, dict) and e.get('name')]
        if valid:
            dc = [2.0*inch, 1.5*inch, 1.5*inch, 0.8*inch]
            dh = ['RECEPTIONNISTE','PREC.','NOUV.','ECART']
            drr = [dh] + [[f"  {e['name']}", _f(e.get('previous')), _f(e.get('nouveau')),
                           _f(float(e.get('nouveau') or 0)-float(e.get('previous') or 0))] for e in valid]
            story.append(_tbl(drr, dc))
            story.append(Spacer(1,5))

    # SD + AR + Market segments (same as before, compact)
    sde = s.get('sd_entries', [])
    if isinstance(sde, list):
        vs = [e for e in sde if isinstance(e, dict) and e.get('name')]
        if vs:
            sc = [0.8*inch, 1.5*inch, 0.5*inch, 0.8*inch, 0.5*inch, 0.5*inch]
            sh = ['DEPT','NOM','DEV','MONTANT','VER.','RMB.']
            sr_r = [sh] + [[e.get('department',''), e.get('name',''), e.get('currency','CDN'),
                           _f(e.get('amount')), 'X' if e.get('verified') else '', 'X' if e.get('reimbursement') else ''] for e in vs]
            story.append(_tbl(sr_r, sc))
            story.append(Spacer(1,5))

    ms = s.get('dbrs_market_segments')
    if ms and isinstance(ms, dict) and any(ms.values()):
        mc2 = [1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch]
        trv = float(ms.get('transient') or 0); grv = float(ms.get('group') or 0)
        ctv = float(ms.get('contract') or 0); otv = float(ms.get('other') or 0)
        tt_v = trv+grv+ctv+otv
        mr = [['SEGMENT','TRANSIENT','GROUPE','CONTRAT','AUTRE','TOTAL'],
              ['  Chambres', _fi(trv), _fi(grv), _fi(ctv), _fi(otv), _fi(tt_v)]]
        if tt_v > 0:
            mr.append(['  Mix %', _fp(trv/tt_v*100), _fp(grv/tt_v*100), _fp(ctv/tt_v*100), _fp(otv/tt_v*100), '100.0%'])
        story.append(_tbl(mr, mc2))

    # ════════════════════════════════════════════════════════════
    # PAGE 4 — TRENDS
    # ════════════════════════════════════════════════════════════
    story.append(PageBreak()); story.append(Spacer(1,3))
    hds = ParagraphStyle('hd', parent=styles['Normal'], fontSize=7, fontName='Helvetica-Bold', textColor=C_DARK)
    story.append(Paragraph(f"TENDANCES 30 JOURS — AU {audit_date}", hds))
    story.append(Spacer(1,3))

    target = _to_date(audit_date) if audit_date else None
    if trend and len(trend.get('dates',[])) > 3:
        def c1(fig, ax):
            ax.fill_between(trend['dates'], trend['revenues'], alpha=0.1, color=CC[0])
            ax.plot(trend['dates'], trend['revenues'], color=CC[0], lw=1.1, label='Total', marker='.', ms=1.5)
            ax.plot(trend['dates'], trend['fb_revenues'], color=CC[1], lw=0.7, label='F&B', ls='--', marker='.', ms=1)
            ax.plot(trend['dates'], trend['room_rev'], color=CC[2], lw=0.7, label='Chamb.', ls=':', marker='.', ms=1)
            if target in trend['dates']: ax.axvline(x=target, color=CC[3], ls=':', alpha=0.5, lw=0.7)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p: f"${x/1000:.0f}k"))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            ax.set_title('Revenus', fontsize=6.5, fontweight='bold', pad=2)
            ax.legend(fontsize=4, loc='upper left', ncol=3)
        def c2(fig, ax):
            ax.bar(trend['dates'], trend['occ_rates'], color=CC[4], alpha=0.5, width=0.8)
            ax2 = ax.twinx()
            ax2.plot(trend['dates'], trend['adr_values'], color=CC[3], lw=1.1, marker='D', ms=1.2)
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda x,p: f"${x:.0f}"))
            ax2.tick_params(labelsize=4.5); ax2.spines['top'].set_visible(False)
            if target in trend['dates']: ax.axvline(x=target, color=CC[3], ls=':', alpha=0.5, lw=0.7)
            ax.set_ylim(0,105)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            ax.set_title('Occ% / ADR', fontsize=6.5, fontweight='bold', pad=2)
        def c3(fig, ax):
            ax.stackplot(trend['dates'], trend['cafe'], trend['piazza'], trend['spesa'],
                         trend['banquet'], trend['room_svc'],
                         labels=['Cafe','Piaz.','Spe.','Ban.','R.S.'], colors=CC[:5], alpha=0.6)
            if target in trend['dates']: ax.axvline(x=target, color='#000', ls=':', alpha=0.4, lw=0.7)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p: f"${x/1000:.0f}k"))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            ax.set_title('F&B / Dept', fontsize=6.5, fontweight='bold', pad=2)
            ax.legend(fontsize=3.5, loc='upper left', ncol=3)
        def c4(fig, ax):
            for k, clr, lb in [('visa','#1a237e','Visa'),('mc','#b71c1c','MC'),('amex','#0277bd','AMEX'),('debit','#2e7d32','Deb.')]:
                ax.plot(trend['dates'], trend[k], color=clr, lw=0.8, label=lb, marker='.', ms=1.2)
            if target in trend['dates']: ax.axvline(x=target, color=CC[3], ls=':', alpha=0.5, lw=0.7)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p: f"${x/1000:.0f}k"))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            ax.set_title('Cartes', fontsize=6.5, fontweight='bold', pad=2)
            ax.legend(fontsize=4, loc='upper left', ncol=2)

        grid = Table([[_mk(c1), _mk(c2)], [_mk(c3), _mk(c4)]],
                     colWidths=[3.55*inch]*2, rowHeights=[1.95*inch]*2)
        grid.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),1),('RIGHTPADDING',(0,0),(-1,-1),1),
            ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
        story.append(grid)
        story.append(Spacer(1,6))

        # Stats table
        td = trend
        scw = [1.1*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.8*inch, 0.8*inch, 0.9*inch]
        sh2 = ['KPI (30J)','MOY.','MIN','MAX','ECART-T.','MEDIANE','TOTAL']
        def _rw(lb, vals, fn=_f):
            if not vals: return [lb]+['']*6
            return [lb, fn(mean(vals)), fn(min(vals)), fn(max(vals)),
                    fn(stdev(vals)) if len(vals)>1 else '', fn(median(vals)), fn(sum(vals))]
        sr2 = [sh2, _rw('Rev. totaux', td['revenues']), _rw('Rev. chambres', td['room_rev']),
               _rw('Rev. F&B', td['fb_revenues']),
               ['Occupation', _fp(mean(td['occ_rates'])), _fp(min(td['occ_rates'])), _fp(max(td['occ_rates'])),
                _fp(stdev(td['occ_rates'])) if len(td['occ_rates'])>1 else '', _fp(median(td['occ_rates'])), f"{len(td['dates'])}j"],
               ['ADR', _f(mean(td['adr_values'])), _f(min(td['adr_values'])), _f(max(td['adr_values'])),
                '', _f(median(td['adr_values'])), '']]
        story.append(_tbl(sr2, scw))
    else:
        story.append(Paragraph("Donnees insuffisantes (min. 3 jours)", ParagraphStyle('n',parent=styles['Normal'],fontSize=6,textColor=HexColor('#999'))))

    # ════════════════════════════════════════════════════════════
    # PAGE 5 — ANALYSE & RECOMMANDATIONS AUTOMATIQUES
    # ════════════════════════════════════════════════════════════
    story.append(PageBreak()); story.append(Spacer(1,3))

    # Title
    title_style = ParagraphStyle('title', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold',
                                  textColor=C_DARK, spaceAfter=2)
    story.append(Paragraph("ANALYSE & RECOMMANDATIONS AUTOMATIQUES", title_style))

    # Subtitle
    subtitle_style = ParagraphStyle('subtitle', parent=styles['Normal'], fontSize=7,
                                     textColor=HexColor('#666'), spaceAfter=6)
    story.append(Paragraph(f"Generees automatiquement a partir des donnees du {audit_date}", subtitle_style))

    # Generate recommendations
    recommendations = _generate_recommendations(s, jour, cards, labor, cash, tips, budget, mtd, ly_jour, ly_mtd, mtd_labor, mtd_cards, trend)

    # Count by severity for summary box
    alerts = sum(len([i for i in r['items'] if i['severity'] == 'alert']) for r in recommendations)
    warnings = sum(len([i for i in r['items'] if i['severity'] == 'warning']) for r in recommendations)
    positives = sum(len([i for i in r['items'] if i['severity'] == 'positive']) for r in recommendations)

    # Summary box
    if alerts > 0 or warnings > 0 or positives > 0:
        summary_text = []
        if alerts > 0: summary_text.append(f"<b>{alerts} alerte{'s' if alerts > 1 else ''}</b>")
        if warnings > 0: summary_text.append(f"<b>{warnings} avertissement{'s' if warnings > 1 else ''}</b>")
        if positives > 0: summary_text.append(f"<b>{positives} positif{'s' if positives > 1 else ''}</b>")
        summary_text = " | ".join(summary_text)

        summary_style = ParagraphStyle('summary', parent=styles['Normal'], fontSize=7,
                                       textColor=white, alignment=TA_CENTER, spaceAfter=6)
        summary_para = Paragraph(summary_text, summary_style)

        # Create summary box with background
        summary_table = Table([[summary_para]], colWidths=[7.2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#34495e')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, C_GRID),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 4))

    # Build recommendation sections
    if recommendations:
        for rec in recommendations:
            # Category header
            cat_style = ParagraphStyle('category', parent=styles['Normal'], fontSize=7.5,
                                       fontName='Helvetica-Bold', textColor=white, spaceAfter=3)
            cat_para = Paragraph(f"{rec['icon']} {rec['category']}", cat_style)

            cat_table = Table([[cat_para]], colWidths=[7.2*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), C_HDR),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(cat_table)

            # Items
            for item in rec['items']:
                text = item['text']
                severity = item['severity']

                # Map severity to color and symbol
                if severity == 'positive':
                    color = HexColor('#27ae60')
                    symbol = '✓'
                elif severity == 'alert':
                    color = HexColor('#c0392b')
                    symbol = '✗'
                elif severity == 'warning':
                    color = HexColor('#f39c12')
                    symbol = '⚠'
                else:  # info
                    color = HexColor('#2980b9')
                    symbol = 'ℹ'

                # Item text
                item_style = ParagraphStyle('item', parent=styles['Normal'], fontSize=6,
                                            textColor=C_DARK, spaceAfter=2, leftIndent=20)
                item_para = Paragraph(f"<font color='{color.hexval()}'><b>{symbol}</b></font> {text}", item_style)

                story.append(item_para)

            story.append(Spacer(1, 4))
    else:
        no_rec_style = ParagraphStyle('n', parent=styles['Normal'], fontSize=6.5,
                                      textColor=HexColor('#666'), leading=8)
        story.append(Paragraph("Aucune recommandation majeure. Audit conforme.", no_rec_style))

    # Build
    def mk(fn, **kw): return _C(fn, audit_date=audit_date, auditor=auditor, **kw)
    doc.build(story, canvasmaker=mk)
    buf.seek(0)
    return buf


# ── Routes ──────────────────────────────────────────────────────
def _prep(audit_date):
    nas = NightAuditSession.query.filter_by(audit_date=audit_date).first()
    if not nas: return None

    sd = nas.to_dict()
    d = _to_date(audit_date)

    # Find closest date with card/labor/cash data (might differ by 1 day)
    data_date = d
    if not DailyCardMetrics.query.filter_by(date=d).first():
        for offset in [1, -1, 2, -2]:
            alt = d + timedelta(days=offset)
            if DailyCardMetrics.query.filter_by(date=alt).first():
                data_date = alt; break

    jour = _load_jour(d) or _load_jour(data_date)
    cards = _load_cards(data_date)
    labor = _load_labor(data_date)
    cash = _load_cash(data_date) or _load_cash(d)
    tips_data = _load_tips(data_date)
    budget = _load_budget(d)
    mtd_data = _load_mtd(d)

    ly_d = d.replace(year=d.year-1)
    ly_jour = _load_jour(ly_d)
    ly_mtd = _load_mtd(ly_d)

    mtd_lab = _load_mtd_labor(d)
    mtd_crd = _load_mtd_cards(d)
    trend_data = _load_trend(d, days=30)

    return sd, jour, cards, labor, cash, tips_data, budget, mtd_data, ly_jour, ly_mtd, mtd_lab, mtd_crd, trend_data


@rj_export_bp.route('/api/rj/export/pdf/<audit_date>')
def export_rj_pdf(audit_date):
    try: datetime.strptime(audit_date, '%Y-%m-%d')
    except ValueError: return jsonify({'error': 'Format invalide'}), 400
    result = _prep(audit_date)
    if not result: return jsonify({'error': f'Aucune session pour {audit_date}'}), 404
    pdf = generate_rj_pdf(*result)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=f"RJ_{audit_date}.pdf")


@rj_export_bp.route('/api/rj/export/pdf/preview/<audit_date>')
def preview_rj_pdf(audit_date):
    try: datetime.strptime(audit_date, '%Y-%m-%d')
    except ValueError: return jsonify({'error': 'Format invalide'}), 400
    result = _prep(audit_date)
    if not result: return jsonify({'error': f'Aucune session pour {audit_date}'}), 404
    pdf = generate_rj_pdf(*result)
    return send_file(pdf, mimetype='application/pdf', as_attachment=False, download_name=f"RJ_{audit_date}.pdf")
