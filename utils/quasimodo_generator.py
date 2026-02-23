"""
Quasimodo GL File Generator.

Generates a Quasimodo .xls file from transelect data in the RJ.
The Quasimodo file is a GL-formatted Excel export used for credit card
reconciliation at Sheraton Laval Hotel (Property 858).

Structure (rows 0-indexed):
  Row 0:      Headers
  Rows 1-5:   MON source (DB, VI, MC, DC, AX) — Moneris F&B terminals
  Rows 6-10:  GLB source (DB, VI, MC, DC, AX) — Global F&B batch
  Rows 11-15: REC source (DB, VI, MC, DC, AX) — Reception (FreedomPay)
  Row 16:     CAN (Canadian deposit)
  Row 17:     US  (US deposit)
  Row 18:     TRANSIT (negative balance, sums everything to 0)
  Row 19:     Empty
  Row 20:     Amex Elavon gross (FreedomPay, before escompte)
  Rows 21-34: Empty padding

Grand total rule: MON + GLB + REC + CAN + US + TRANSIT = 0.00
"""

import io
import logging
from datetime import datetime

import xlwt

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

CARD_ORDER = ['DB', 'VI', 'MC', 'DC', 'AX']

CARD_LABELS = {
    'DB': 'DEBIT',
    'VI': 'VISA',
    'MC': 'MC',
    'DC': 'DC',
    'AX': 'AX',
}

MONTH_NAMES_FR = {
    1: 'JANVIER', 2: 'FEVRIER', 3: 'MARS', 4: 'AVRIL',
    5: 'MAI', 6: 'JUIN', 7: 'JUILLET', 8: 'AOUT',
    9: 'SEPTEMBRE', 10: 'OCTOBRE', 11: 'NOVEMBRE', 12: 'DECEMBRE',
}

GL_CARDS = '100200'
GL_REC_VI = '100210'   # REC Visa uses different GL
GL_REC_MC = '100210'   # REC MasterCard uses different GL
GL_US = '100300'
GL_TRANSIT = '100400'

AMEX_ESCOMPTE_RATE = 0.0265  # 2.65% FreedomPay Amex fee


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_float(value, default=0.0):
    """Convert value to float safely."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _gl_for_rec(card_code):
    """Return the GL code for a REC row."""
    if card_code == 'VI':
        return GL_REC_VI
    if card_code == 'MC':
        return GL_REC_MC
    return GL_CARDS


# ── Styles ───────────────────────────────────────────────────────────────────

def _make_styles():
    """Create xlwt style objects matching real Quasimodo formatting."""
    fmt_general = xlwt.XFStyle()

    fmt_decimal = xlwt.XFStyle()
    fmt_decimal.num_format_str = '0.00'

    fmt_text = xlwt.XFStyle()
    fmt_text.num_format_str = '@'

    # Accounting currency format for TRANSIT row
    fmt_currency = xlwt.XFStyle()
    fmt_currency.num_format_str = (
        '_ * #,##0.00_)\\ "$"_ '
        ';_ * \\(#,##0.00\\)\\ "$"_ '
        ';_ * "-"??_)\\ "$"_ '
        ';_ @_ '
    )

    return {
        'general': fmt_general,
        'decimal': fmt_decimal,
        'text': fmt_text,
        'currency': fmt_currency,
    }


# ── Generator ────────────────────────────────────────────────────────────────

class QuasimodoGenerator:
    """
    Generate a Quasimodo .xls file from transelect data.

    Usage::

        from utils.rj_reader import RJReader

        reader = RJReader(rj_bytes)
        transelect = reader.read_transelect()
        controle = reader.read_controle()

        gen = QuasimodoGenerator(transelect, controle)
        xls_bytes = gen.generate()
        filename = gen.get_filename()
    """

    def __init__(self, transelect_data, controle_data,
                 can_deposit=None, us_deposit=None):
        """
        Args:
            transelect_data: dict from RJReader.read_transelect()
            controle_data:   dict from RJReader.read_controle()
            can_deposit:     Canadian deposit amount (float or None)
            us_deposit:      US deposit amount (float or None)
        """
        self.transelect = transelect_data or {}
        self.controle = controle_data or {}
        self.can_deposit = _safe_float(can_deposit)
        self.us_deposit = _safe_float(us_deposit)

        # Derive date
        day = int(_safe_float(self.controle.get('jour', 1)))
        month = int(_safe_float(self.controle.get('mois', 1)))
        year = int(_safe_float(self.controle.get('annee', datetime.now().year)))
        try:
            self.date = datetime(year, month, day)
        except ValueError as e:
            raise ValueError(f'Invalid date: year={year}, month={month}, day={day}. {str(e)}')

    # ── Data computation ─────────────────────────────────────────────────

    def _date_code(self):
        """MMDD format, e.g. '0206' for Feb 6."""
        return f'{self.date.month:02d}{self.date.day:02d}'

    def _month_year(self):
        """e.g. 'FEVRIER 2026'."""
        return f'{MONTH_NAMES_FR[self.date.month]} {self.date.year}'

    def _compute_mon(self):
        """
        Sum Section 1 (POSitouch) by card type → MON source rows.

        MON = Moneris F&B terminal transactions.
        All Section 1 data (BAR 701/702/703, SPESA 704, ROOM 705)
        is attributed to MON since the transelect doesn't separate MON/GLB.
        """
        sf = lambda k: _safe_float(self.transelect.get(k))
        return {
            'DB': sf('bar_701_debit') + sf('bar_702_debit') +
                  sf('bar_703_debit') + sf('spesa_704_debit'),
            'VI': sf('bar_701_visa') + sf('bar_702_visa') +
                  sf('bar_703_visa') + sf('spesa_704_visa') +
                  sf('room_705_visa'),
            'MC': sf('bar_701_master') + sf('bar_702_master') +
                  sf('bar_703_master') + sf('spesa_704_master'),
            'DC': 0.0,   # No Discover at POSitouch
            'AX': sf('bar_701_amex') + sf('bar_702_amex') +
                  sf('bar_703_amex') + sf('spesa_704_amex'),
        }

    def _compute_glb(self):
        """GLB source — zeros (cannot be separated from transelect data)."""
        return {card: 0.0 for card in CARD_ORDER}

    def _compute_rec(self):
        """
        Section 2 Reception values → REC source rows.

        Uses terminal (D column) values first, falls back to fusebox (B column)
        since some RJ files only have one or the other filled.
        REC AX is the NET after FreedomPay escompte (2.65%).
        """
        sf = lambda k: _safe_float(self.transelect.get(k))

        # For each card type, prefer terminal value, fall back to fusebox
        visa = sf('reception_visa_term') or sf('fusebox_visa')
        mc = sf('reception_master_term') or sf('fusebox_master')
        # Debit can come from either terminal (K053=D20 or 8.0=C20)
        debit = sf('reception_debit') + sf('reception_debit_term8')

        # Amex: use fusebox (bank settlement) if available, else terminal
        amex_gross = sf('fusebox_amex') or sf('reception_amex_term')
        amex_net = amex_gross * (1 - AMEX_ESCOMPTE_RATE)

        return {
            'DB': debit,
            'VI': visa,
            'MC': mc,
            'DC': 0.0,   # No Discover at Reception
            'AX': amex_net,
        }

    def _amex_elavon_gross(self):
        """Amex Elavon gross amount (before escompte) for Row 20."""
        sf = lambda k: _safe_float(self.transelect.get(k))
        return sf('fusebox_amex') or sf('reception_amex_term')

    # ── File generation ──────────────────────────────────────────────────

    def generate(self):
        """
        Generate Quasimodo .xls and return as bytes.

        Returns:
            bytes: Complete .xls file content
        """
        wb = xlwt.Workbook()
        ws = wb.add_sheet(str(self.date.year))
        styles = _make_styles()

        date_code = self._date_code()
        month_year = self._month_year()

        mon = self._compute_mon()
        glb = self._compute_glb()
        rec = self._compute_rec()
        amex_gross = self._amex_elavon_gross()

        # ── Row 0: Headers ───────────────────────────────────────────────
        ws.write(0, 2, 'C / GL', styles['general'])
        ws.write(0, 3, month_year, styles['general'])
        ws.write(0, 4, 'E\n /CC1', styles['general'])
        ws.write(0, 5, 'F\n /CC2', styles['general'])
        ws.write(0, 6, 'G / DESC / SOURCE', styles['general'])
        ws.write(0, 7, 'H', styles['general'])

        running_total = 0.0
        row = 1

        # ── Rows 1-5: MON source ────────────────────────────────────────
        for card in CARD_ORDER:
            amount = mon[card]
            # Description always says "GLB" for MON rows (matches real files)
            desc = f'VENTES {month_year} {CARD_LABELS[card]} GLB'
            source = f'2 {card} {date_code} MON'

            self._write_data_row(ws, row, date_code, amount,
                                 GL_CARDS, desc, source, styles)
            running_total += amount
            row += 1

        # ── Rows 6-10: GLB source ───────────────────────────────────────
        for card in CARD_ORDER:
            amount = glb[card]
            # Description also says "GLB" for GLB rows (matches real files)
            desc = f'VENTES {month_year} {CARD_LABELS[card]} GLB'
            source = f'2 {card} {date_code} GLB'

            self._write_data_row(ws, row, date_code, amount,
                                 GL_CARDS, desc, source, styles)
            running_total += amount
            row += 1

        # ── Rows 11-15: REC source ──────────────────────────────────────
        for card in CARD_ORDER:
            amount = rec[card]
            desc = f'VENTES {month_year} {CARD_LABELS[card]} REC'
            source = f'2 {card} {date_code} REC'
            gl = _gl_for_rec(card)

            self._write_data_row(ws, row, date_code, amount,
                                 gl, desc, source, styles)
            running_total += amount
            row += 1

        # ── Row 16: CAN (Canadian deposit) ──────────────────────────────
        ws.write(row, 0, date_code, styles['general'])
        if self.can_deposit:
            ws.write(row, 1, self.can_deposit, styles['decimal'])
        else:
            ws.write(row, 1, '', styles['decimal'])
        ws.write(row, 2, GL_CARDS, styles['text'])
        ws.write(row, 3, f'VENTES {month_year} CAN', styles['general'])
        ws.write(row, 6, f'2 {date_code} CA', styles['general'])
        running_total += self.can_deposit
        row += 1

        # ── Row 17: US deposit ──────────────────────────────────────────
        ws.write(row, 0, date_code, styles['general'])
        if self.us_deposit:
            ws.write(row, 1, self.us_deposit, styles['decimal'])
        else:
            ws.write(row, 1, '', styles['decimal'])
        ws.write(row, 2, GL_US, styles['text'])
        ws.write(row, 3, f'VENTES {month_year} US', styles['general'])
        ws.write(row, 6, f'2 {date_code} US', styles['general'])
        running_total += self.us_deposit
        row += 1

        # ── Row 18: TRANSIT ─────────────────────────────────────────────
        transit = -running_total
        ws.write(row, 0, date_code, styles['general'])
        ws.write(row, 1, transit, styles['currency'])
        ws.write(row, 2, GL_TRANSIT, styles['text'])
        ws.write(row, 3, f'VENTES {month_year} TRANSIT', styles['general'])
        ws.write(row, 4, 2.0, styles['general'])
        ws.write(row, 6, f'2{date_code}', styles['general'])   # No space
        ws.write(row, 7, 0.0, styles['decimal'])
        row += 1

        # ── Row 19: Empty ───────────────────────────────────────────────
        row += 1

        # ── Row 20: Amex Elavon gross (FreedomPay) ──────────────────────
        if amex_gross > 0:
            ws.write(row, 1, amex_gross, styles['decimal'])
        row += 1

        # ── Padding rows 21-34: empty (xlwt handles automatically) ──────

        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        logger.info(
            'Quasimodo generated: %s (transit=%.2f, cards=%.2f)',
            self.get_filename(), transit, running_total
        )

        return output.getvalue()

    def _write_data_row(self, ws, row, date_code, amount, gl, desc, source, styles):
        """Write a single card data row (MON/GLB/REC)."""
        ws.write(row, 0, date_code, styles['general'])
        if amount:
            ws.write(row, 1, amount, styles['decimal'])
        else:
            ws.write(row, 1, '', styles['decimal'])
        ws.write(row, 2, gl, styles['text'])
        ws.write(row, 3, desc, styles['general'])
        ws.write(row, 6, source, styles['general'])

    # ── Filename / metadata ──────────────────────────────────────────────

    def get_filename(self):
        """
        Generate filename matching hotel convention.

        Example: 'Quasimodo Sheraton 06 Fevrier 2026.xls'
        """
        month_name = MONTH_NAMES_FR[self.date.month].capitalize()
        return f'Quasimodo Sheraton {self.date.day:02d} {month_name} {self.date.year}.xls'

    def get_summary(self):
        """Return a summary dict for the API response."""
        mon = self._compute_mon()
        glb = self._compute_glb()
        rec = self._compute_rec()
        amex_gross = self._amex_elavon_gross()

        cards_total = sum(mon.values()) + sum(glb.values()) + sum(rec.values())
        deposits_total = self.can_deposit + self.us_deposit
        transit = -(cards_total + deposits_total)

        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'date_code': self._date_code(),
            'filename': self.get_filename(),
            'mon': mon,
            'glb': glb,
            'rec': rec,
            'can_deposit': self.can_deposit,
            'us_deposit': self.us_deposit,
            'amex_elavon_gross': round(amex_gross, 2),
            'transit': round(transit, 2),
            'cards_total': round(cards_total, 2),
            'grand_total': 0.0,  # Always 0 by construction
        }
