"""
Night Audit PDF Report Generator for the General Manager.

Generates a professional one-page PDF summary containing:
- Hotel & audit date information
- Recap totals (cash, cheques, reimbursements, due back, surplus/deficit, deposit)
- Transelect card totals (Visa, MC, Amex, Debit)
- GEAC/UX cash-out summary
- DueBack summary
- Validation status
- Weather conditions

Uses reportlab for PDF generation.
"""

import io
import logging
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

HOTEL_NAME = "Sheraton Laval"
HOTEL_PROPERTY = "Propriété 858"
HOTEL_ROOMS = 252

# Color palette (Sheraton/Marriott inspired)
COLOR_DARK = colors.HexColor('#1a1a2e')
COLOR_PRIMARY = colors.HexColor('#16213e')
COLOR_ACCENT = colors.HexColor('#0f3460')
COLOR_HIGHLIGHT = colors.HexColor('#e94560')
COLOR_LIGHT_BG = colors.HexColor('#f8f9fa')
COLOR_BORDER = colors.HexColor('#dee2e6')
COLOR_GREEN = colors.HexColor('#28a745')
COLOR_RED = colors.HexColor('#dc3545')
COLOR_AMBER = colors.HexColor('#ffc107')


# ============================================================================
# STYLES
# ============================================================================

def _build_styles():
    """Build custom paragraph styles for the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=COLOR_DARK,
        spaceAfter=4,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6c757d'),
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=COLOR_PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
        borderPadding=(0, 0, 2, 0),
    ))

    styles.add(ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#495057'),
    ))

    styles.add(ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_DARK,
        alignment=TA_RIGHT,
    ))

    styles.add(ParagraphStyle(
        'CellValueBold',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLOR_DARK,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#adb5bd'),
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        'StatusOK',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_GREEN,
    ))

    styles.add(ParagraphStyle(
        'StatusError',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_RED,
    ))

    styles.add(ParagraphStyle(
        'StatusInfo',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6c757d'),
    ))

    return styles


# ============================================================================
# HELPERS
# ============================================================================

def _fmt(value, decimals=2):
    """Format a numeric value as currency string."""
    if value is None:
        return "—"
    try:
        v = float(value)
        if v == 0:
            return "0.00 $"
        sign = "-" if v < 0 else ""
        return f"{sign}{abs(v):,.{decimals}f} $"
    except (ValueError, TypeError):
        return str(value)


def _safe_float(value):
    """Safely convert to float, return 0 on failure."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _date_str(controle):
    """Build a display date string from controle data."""
    jour = controle.get('jour')
    mois = controle.get('mois')
    annee = controle.get('annee')

    if jour and mois and annee:
        try:
            d = datetime(int(annee), int(mois), int(jour))
            # French month names
            mois_fr = [
                '', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
            ]
            return f"{int(jour)} {mois_fr[int(mois)]} {int(annee)}"
        except (ValueError, TypeError):
            pass

    return "Date non configurée"


def _status_icon(status):
    """Return a text icon for validation status."""
    icons = {
        'ok': '[OK]',
        'warning': '[!]',
        'error': '[X]',
        'info': '[i]',
    }
    return icons.get(status, '[?]')


# ============================================================================
# TABLE BUILDERS
# ============================================================================

def _build_recap_table(recap, styles):
    """Build the Recap summary table."""
    def row(label, lecture_key, corr_key):
        lec = _safe_float(recap.get(lecture_key))
        corr = _safe_float(recap.get(corr_key))
        net = lec + corr
        return [
            Paragraph(label, styles['CellLabel']),
            Paragraph(_fmt(lec), styles['CellValue']),
            Paragraph(_fmt(corr), styles['CellValue']),
            Paragraph(_fmt(net), styles['CellValueBold']),
        ]

    header = [
        Paragraph('<b>Poste</b>', styles['CellLabel']),
        Paragraph('<b>Lecture</b>', styles['CellValue']),
        Paragraph('<b>Corr.</b>', styles['CellValue']),
        Paragraph('<b>Net</b>', styles['CellValueBold']),
    ]

    data = [
        header,
        row('Comptant LightSpeed', 'comptant_lightspeed_lecture', 'comptant_lightspeed_corr'),
        row('Comptant POSitouch', 'comptant_positouch_lecture', 'comptant_positouch_corr'),
        row('Chèque Payment', 'cheque_payment_lecture', 'cheque_payment_corr'),
        row('Remb. Gratuités', 'remb_gratuite_lecture', 'remb_gratuite_corr'),
        row('Remb. Client', 'remb_client_lecture', 'remb_client_corr'),
        row('Due Back Réception', 'due_back_reception_lecture', 'due_back_reception_corr'),
        row('Due Back N/B', 'due_back_nb_lecture', 'due_back_nb_corr'),
        row('Surplus / Déficit', 'surplus_deficit_lecture', 'surplus_deficit_corr'),
        row('Dépôt Canadien', 'depot_canadien_lecture', 'depot_canadien_corr'),
    ]

    col_widths = [150, 80, 80, 80]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        # Highlight surplus/deficit row
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#fff3cd')),
        # Highlight depot row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4edda')),
    ]))

    return t


def _build_cards_table(transelect_totals, geac_cashout, styles):
    """Build the credit card summary table (Transelect + GEAC)."""
    cards = ['visa', 'mastercard', 'amex', 'debit']
    card_labels = {
        'visa': 'Visa',
        'mastercard': 'MasterCard',
        'amex': 'Amex',
        'debit': 'Débit',
    }

    header = [
        Paragraph('<b>Carte</b>', styles['CellLabel']),
        Paragraph('<b>Transelect</b>', styles['CellValue']),
        Paragraph('<b>GEAC Cash-Out</b>', styles['CellValue']),
    ]

    data = [header]
    total_trans = 0
    total_geac = 0

    for card in cards:
        t_val = _safe_float(transelect_totals.get(card))
        g_val = _safe_float(geac_cashout.get(card))
        total_trans += t_val
        total_geac += g_val

        data.append([
            Paragraph(card_labels.get(card, card), styles['CellLabel']),
            Paragraph(_fmt(t_val), styles['CellValue']),
            Paragraph(_fmt(g_val), styles['CellValue']),
        ])

    # Add Diners/Discover from GEAC only
    for extra in ['diners', 'discover']:
        g_val = _safe_float(geac_cashout.get(extra))
        if g_val != 0:
            total_geac += g_val
            data.append([
                Paragraph(extra.capitalize(), styles['CellLabel']),
                Paragraph("—", styles['CellValue']),
                Paragraph(_fmt(g_val), styles['CellValue']),
            ])

    # Total row
    data.append([
        Paragraph('<b>TOTAL</b>', styles['CellLabel']),
        Paragraph(_fmt(total_trans), styles['CellValueBold']),
        Paragraph(_fmt(total_geac), styles['CellValueBold']),
    ])

    col_widths = [100, 100, 100]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, COLOR_LIGHT_BG]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e3e5')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ]))

    return t


def _build_dueback_table(dueback, styles):
    """Build the DueBack summary table."""
    receptionists = dueback.get('receptionists', [])

    if not receptionists:
        return Paragraph("Aucune donnée DueBack disponible.", styles['StatusInfo'])

    header = [
        Paragraph('<b>Réceptionniste</b>', styles['CellLabel']),
        Paragraph('<b>Précédent</b>', styles['CellValue']),
        Paragraph('<b>Nouveau</b>', styles['CellValue']),
    ]

    data = [header]
    # Only show receptionists who have non-zero values in the latest day
    days = dueback.get('days', {})
    if not days:
        return Paragraph("Aucune donnée DueBack pour ce jour.", styles['StatusInfo'])

    # Get the latest (highest) day
    latest_day = max(days.keys()) if days else None
    if latest_day is None:
        return Paragraph("Aucune donnée DueBack.", styles['StatusInfo'])

    day_data = days[latest_day]
    previous = day_data.get('previous', {})
    nouveau = day_data.get('nouveau', {})

    total_prev = 0
    total_new = 0

    for recep in receptionists:
        col_letter = recep['col_letter']
        prev_val = _safe_float(previous.get(col_letter, {}).get('amount')) if col_letter in previous else 0
        new_val = _safe_float(nouveau.get(col_letter, {}).get('amount')) if col_letter in nouveau else 0

        if prev_val != 0 or new_val != 0:
            total_prev += prev_val
            total_new += new_val
            data.append([
                Paragraph(recep.get('full_name', recep.get('last_name', '?')), styles['CellLabel']),
                Paragraph(_fmt(prev_val), styles['CellValue']),
                Paragraph(_fmt(new_val), styles['CellValue']),
            ])

    if len(data) == 1:
        return Paragraph("Aucun DueBack actif pour ce jour.", styles['StatusInfo'])

    # Total
    data.append([
        Paragraph('<b>TOTAL</b>', styles['CellLabel']),
        Paragraph(_fmt(total_prev), styles['CellValueBold']),
        Paragraph(_fmt(total_new), styles['CellValueBold']),
    ])

    col_widths = [140, 80, 80]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, COLOR_LIGHT_BG]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e3e5')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ]))

    return t


def _build_validation_table(checks, styles):
    """Build the validation status summary."""
    if not checks:
        return Paragraph("Validation non disponible.", styles['StatusInfo'])

    data = []
    for check in checks:
        status = check.get('status', 'info')
        name = check.get('name', '?')
        detail = check.get('detail', '')

        icon = _status_icon(status)
        style_name = {
            'ok': 'StatusOK',
            'error': 'StatusError',
            'warning': 'StatusError',
            'info': 'StatusInfo',
        }.get(status, 'StatusInfo')

        data.append([
            Paragraph(f"{icon} {name}", styles[style_name]),
            Paragraph(detail, styles['CellLabel']),
        ])

    col_widths = [160, 230]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, COLOR_LIGHT_BG),
    ]))

    return t


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_night_report(rj_data, validation_checks=None, weather=None):
    """
    Generate a Night Audit PDF report.

    Args:
        rj_data: dict from RJReader.read_all() containing:
            - controle: {jour, mois, annee, prepare_par}
            - recap: {field: value, ...}
            - transelect: raw transelect data (not needed if totals provided)
            - geac_ux: raw geac data (not needed if cashout provided)
            - dueback: {receptionists: [...], days: {...}}
            - transelect_totals (optional): pre-computed card totals
            - geac_cashout (optional): pre-computed GEAC cash-out by card
        validation_checks: list of dicts from /api/rj/validate
        weather: dict with {temperature, description} or None

    Returns:
        io.BytesIO buffer containing the PDF
    """
    buffer = io.BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        title="Rapport d'Audit de Nuit",
        author=HOTEL_NAME,
    )

    story = []

    # ------------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------------
    controle = rj_data.get('controle', {})
    date_display = _date_str(controle)
    prepare_par = controle.get('prepare_par', '—')
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M')

    story.append(Paragraph(
        f"{HOTEL_NAME} — Rapport d'Audit de Nuit",
        styles['ReportTitle']
    ))

    subtitle_parts = [
        f"Date d'audit : <b>{date_display}</b>",
        f"&nbsp;&nbsp;|&nbsp;&nbsp;Préparé par : <b>{prepare_par}</b>",
        f"&nbsp;&nbsp;|&nbsp;&nbsp;{HOTEL_PROPERTY} ({HOTEL_ROOMS} ch.)",
    ]
    story.append(Paragraph("".join(subtitle_parts), styles['ReportSubtitle']))

    # Weather line
    if weather:
        temp = weather.get('temperature', '?')
        desc = weather.get('description', '')
        weather_text = f"Météo : {temp}°C — {desc}"
        story.append(Paragraph(weather_text, styles['ReportSubtitle']))

    story.append(HRFlowable(
        width="100%", thickness=1, color=COLOR_PRIMARY,
        spaceBefore=2, spaceAfter=8
    ))

    # ------------------------------------------------------------------
    # SECTION 1: RECAP
    # ------------------------------------------------------------------
    recap = rj_data.get('recap', {})

    story.append(Paragraph("1. Recap — Résumé des encaissements", styles['SectionHeader']))
    story.append(_build_recap_table(recap, styles))
    story.append(Spacer(1, 6))

    # ------------------------------------------------------------------
    # SECTION 2: CARTES DE CRÉDIT (Transelect + GEAC)
    # ------------------------------------------------------------------
    story.append(Paragraph("2. Cartes de crédit — Transelect / GEAC", styles['SectionHeader']))

    # Use pre-computed totals if available, otherwise build from raw data
    transelect_totals = rj_data.get('transelect_totals', {})
    geac_cashout = rj_data.get('geac_cashout', {})

    story.append(_build_cards_table(transelect_totals, geac_cashout, styles))
    story.append(Spacer(1, 6))

    # ------------------------------------------------------------------
    # SECTION 3: DUEBACK
    # ------------------------------------------------------------------
    dueback = rj_data.get('dueback', {})

    story.append(Paragraph("3. DueBack — Soldes réceptionnistes", styles['SectionHeader']))
    story.append(_build_dueback_table(dueback, styles))
    story.append(Spacer(1, 6))

    # ------------------------------------------------------------------
    # SECTION 4: GEAC/UX BALANCE
    # ------------------------------------------------------------------
    geac = rj_data.get('geac_ux', {})
    if geac:
        story.append(Paragraph("4. GEAC/UX — Soldes", styles['SectionHeader']))

        balance_data = [
            [
                Paragraph('<b>Poste</b>', styles['CellLabel']),
                Paragraph('<b>Montant</b>', styles['CellValue']),
            ],
            [
                Paragraph('Balance veille', styles['CellLabel']),
                Paragraph(_fmt(geac.get('balance_previous')), styles['CellValue']),
            ],
            [
                Paragraph("Balance aujourd'hui", styles['CellLabel']),
                Paragraph(_fmt(geac.get('balance_today')), styles['CellValue']),
            ],
            [
                Paragraph('Facture Direct', styles['CellLabel']),
                Paragraph(_fmt(geac.get('facture_direct')), styles['CellValue']),
            ],
            [
                Paragraph('Adv. Deposit', styles['CellLabel']),
                Paragraph(_fmt(geac.get('adv_deposit')), styles['CellValue']),
            ],
            [
                Paragraph('New Balance', styles['CellLabel']),
                Paragraph(_fmt(geac.get('new_balance')), styles['CellValueBold']),
            ],
        ]

        col_widths = [180, 110]
        bt = Table(balance_data, colWidths=col_widths)
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_ACCENT),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        story.append(bt)
        story.append(Spacer(1, 6))

    # ------------------------------------------------------------------
    # SECTION 5: VALIDATION
    # ------------------------------------------------------------------
    if validation_checks:
        story.append(Paragraph("5. Validation", styles['SectionHeader']))
        story.append(_build_validation_table(validation_checks, styles))
        story.append(Spacer(1, 6))

    # ------------------------------------------------------------------
    # FOOTER
    # ------------------------------------------------------------------
    story.append(Spacer(1, 12))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=COLOR_BORDER,
        spaceBefore=4, spaceAfter=4
    ))
    story.append(Paragraph(
        f"Généré automatiquement le {generated_at} — {HOTEL_NAME} Night Audit App",
        styles['FooterText']
    ))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
