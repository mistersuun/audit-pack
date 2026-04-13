"""House Totals text parser for Sheraton Laval night audit.

Parses the Lightspeed POS "Sales Journal Report for Entire house" text dump.
Feeds the Recap tab's Comptant Positouch and Remb Gratuité fields, plus
per-card POS payment totals used as the POSITOUCH column of Transelect.

Key extracted values from the PAYMENT TOTALS section:
  - CASH n tickets + PAIDOUTS -N   → cash received at till
  - EXPECTED DEPOSIT               → net cash owed to the bank (can be negative)
  - PAIDOUTS                       → gross tips paid out of till
  - TIPS TO SERVERS                → same magnitude as PAIDOUTS, sign-flipped
  - VISA / MASTERCARD / AMEX /
    INTERAC / CHAMBRE              → per-card POS payment totals
  - PANNE VISA / PANNE MASTER ...  → terminal-failure counts
  - TOTAL SALES+TAX                → day's gross revenue

The Recap formula verified on 2026-04-06:
    comptant_positouch = abs(PAIDOUTS) + EXPECTED_DEPOSIT
                       = 763.98 + (-534.64) = 229.34   ← matches Recap row 6
    remb_gratuite      = -abs(PAIDOUTS) = -763.98      ← matches Recap row 10
"""

import re
from datetime import datetime
from .base_parser import BaseParser


# Payment line labels → normalized extracted-data keys.
# Order matters only for readability; we match by label literal.
_PAYMENT_LABELS = {
    'VISA':       'visa',
    'MASTERCARD': 'mastercard',
    'AMEX':       'amex',
    'INTERAC':    'interac',
    'CHAMBRE':    'chambre',
    'ADMIN':      'admin',
    'HOTEL PROM': 'hotel_prom',
    'FORFAIT':    'forfait',
}

_PANNE_LABELS = {
    'PANNE VISA':     'panne_visa',
    'PANNE MASTER':   'panne_mastercard',
    'PANNE INTERACT': 'panne_interac',
    'PANNE AMEX':     'panne_amex',
    'PANNE LIEN':     'panne_lien',
}


class HouseTotalsParser(BaseParser):
    """Parser for house_totals.txt — Lightspeed Sales Journal Report."""

    FIELD_MAPPINGS = {
        # Recap tab auto-fill
        'comptant_positouch':  'cash_pos_lecture',
        'remb_gratuite':       'remb_gratuite_lecture',
    }

    def __init__(self, file_bytes, filename=None, **kwargs):
        super().__init__(file_bytes, filename, **kwargs)
        self.raw_text = None

    def parse(self):
        try:
            self.raw_text = self._decode_bytes()
            payment_block = self._extract_payment_totals_block(self.raw_text)
            if not payment_block:
                self.validation_errors.append("PAYMENT TOTALS section not found")
                self.confidence = 0.0
                self._parsed = True
                return

            expected_deposit = self._parse_amount(payment_block, r'EXPECTED DEPOSIT\s+(-?[\d,]+\.\d{2})(-?)')
            # PAIDOUTS line has no leading dash and sits below EXPECTED DEPOSIT
            paidouts = self._parse_amount(payment_block, r'(?<!-)PAIDOUTS\s+(-?[\d,]+\.\d{2})(-?)', allow_zero=True)
            # TIPS TO SERVERS is gross paidouts sign-flipped
            tips_to_servers = self._parse_amount(payment_block, r'TIPS TO SERVERS\s+(-?[\d,]+\.\d{2})(-?)')
            total_sales_tax = self._parse_amount(payment_block, r'TOTAL SALES\+TAX\s+(-?[\d,]+\.\d{2})(-?)')

            # CASH ticket count (same line) + signed total
            cash_tickets, cash_signed = self._parse_tally_line(payment_block, r'CASH\s+(\d+)')

            # Per-card payment totals
            payments = {}
            for label, key in _PAYMENT_LABELS.items():
                _, amount = self._parse_tally_line(payment_block, rf'{re.escape(label)}\s+(\d+)')
                payments[key] = amount

            # Per-card panne counts
            pannes = {}
            for label, key in _PANNE_LABELS.items():
                count, amount = self._parse_tally_line(payment_block, rf'{re.escape(label)}\s+(\d+)')
                pannes[key] = {'count': count, 'amount': amount}

            # Recap-derived values per master doc Part 7 (verified Apr 06)
            comptant_positouch = round(abs(paidouts) + expected_deposit, 2) if paidouts is not None else 0.0
            remb_gratuite = round(-abs(paidouts), 2) if paidouts is not None else 0.0

            self.extracted_data = {
                'report_date': self._extract_report_date(self.raw_text),
                'cash_tickets': cash_tickets,
                'expected_deposit': expected_deposit,
                'paidouts': paidouts,
                'tips_to_servers': tips_to_servers,
                'total_sales_tax': total_sales_tax,
                'payments': payments,
                'pannes': pannes,
                'comptant_positouch': comptant_positouch,
                'remb_gratuite': remb_gratuite,
            }

            # Confidence: strong if we have the two keystone values
            conf = 0.0
            if expected_deposit is not None: conf += 0.35
            if paidouts is not None:         conf += 0.35
            if total_sales_tax is not None:  conf += 0.15
            if payments.get('visa') is not None: conf += 0.15
            self.confidence = round(conf, 2)
            self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"Parse error: {e}")
            self.confidence = 0.0
            self._parsed = True

    def validate(self):
        if self.extracted_data.get('expected_deposit') is None:
            self.validation_errors.append("EXPECTED DEPOSIT value missing")
            return False
        if self.extracted_data.get('paidouts') is None:
            self.validation_errors.append("PAIDOUTS value missing")
            return False
        return True

    # ── internals ──────────────────────────────────────────────────────────

    def _extract_report_date(self, text):
        """Report header contains 'SALES JOURNAL REPORT FOR MM/DD/YYYY'."""
        m = re.search(r'SALES JOURNAL REPORT FOR (\d{2}/\d{2}/\d{4})', text)
        return m.group(1) if m else None

    def _extract_payment_totals_block(self, text):
        """Isolate the PAYMENT TOTALS section so later regexes don't false-match."""
        m = re.search(r'PAYMENT TOTALS for Entire house.*?(?=REPORT DATE:|\Z)', text, re.DOTALL)
        return m.group(0) if m else None

    def _parse_amount(self, text, pattern, allow_zero=True):
        """Pull a signed decimal from a 2-group regex: (number)(trailing-minus?).

        Handles both trailing-minus ("534.64-") and leading-minus ("-534.64")
        formats emitted by Positouch. The caller's pattern MUST include the
        two capture groups as shown; a single-group regex will raise IndexError.
        """
        m = re.search(pattern, text)
        if not m:
            return None
        try:
            val = float(m.group(1).replace(',', ''))
        except ValueError:
            return None
        if m.group(2) == '-':
            val = -val
        if val == 0 and not allow_zero:
            return None
        return round(val, 2)

    def _parse_tally_line(self, text, label_pattern):
        """Parse a 'LABEL count ... amount' line.

        Returns (count, amount). count is int or 0; amount is signed float or 0.0.
        """
        # Count first (right after the label)
        m = re.search(label_pattern, text)
        if not m:
            return 0, 0.0
        count = int(m.group(1))
        # Amount is the first decimal number after the count on the SAME line
        line_start = text.rfind('\n', 0, m.start()) + 1
        line_end = text.find('\n', m.end())
        line = text[line_start:line_end if line_end != -1 else len(text)]
        amt_match = re.search(r'(-?[\d,]+\.\d{2})(-?)', line[m.end() - line_start:])
        if not amt_match:
            return count, 0.0
        raw = amt_match.group(1).replace(',', '')
        try:
            val = float(raw)
        except ValueError:
            return count, 0.0
        if amt_match.group(2) == '-':
            val = -val
        return count, round(val, 2)
