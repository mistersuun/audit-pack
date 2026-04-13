"""Debourse (Dept 90 / Sub 90.2) PDF parser.

Parses the GEAC Cashier Detail report filtered to department 90 (Debourse)
sub-department 2 (Remboursement Serveur). Used for the Recap tab's
"Moins Remboursement Client" line and the DUBACK# per-cashier distribution.

Verified 2026-04-06:
  - 6 tickets (mixologue, dragan, caroline, MIXO, isabelle leclair, jonathan samedy)
  - Subtotal for Sub: 2 Remboursement Serveur  505.61
  - ** TOTAL FOR DEPT: 90 Debourse              505.61

These 505.61 feed:
  - Recap row 11 (Moins Remboursement Client) = −505.61
  - Recap row 15 (Due Back Réception)          = +505.61
  - jour col 73 (RmbSrv)                       = −505.61
  - jour col 76 (DueBk)                        = −505.61
"""

import re
from .base_parser import BaseParser


_TICKET_RE = re.compile(
    r'200858\s+NG\s+Depot\s+Restaurant.*?\*\*TICKET\s+TOTAL:\s*([\d,]+\.\d{2})',
    re.DOTALL,
)
# Named cashier ID token (ICARON, SCAMA677, TTHAN639, and 3-letter abbreviations).
_CASHIER_RE = re.compile(r'([A-Z]{3,10}\d{0,4})\s+\d{1,2}:\d{2}\s+\d+\s+NEW')
_DEPT_TOTAL_RE = re.compile(r'TOTAL\s+FOR\s+DEPT:\s*90\s+Debourse\s+([\d,]+\.\d{2})')
_SUBTOTAL_RE = re.compile(r'Subtotal\s+for\s+Sub:\s*2\s+Remboursement\s+Serveur\s+([\d,]+\.\d{2})')


class DebourseParser(BaseParser):
    """Parser for house_90_2 (Cashier Detail, Dept 90 / Sub 90.2)."""

    FIELD_MAPPINGS = {
        'debourse_total':    'remb_client_lecture',  # Recap Moins Remb Client
        'debourse_total_dueback': 'dueback_reception_lecture',  # Recap Due Back Réc
    }

    def parse(self):
        try:
            text = self._extract_pdf_text()
            if not text:
                # _extract_pdf_text already appended a validation error
                self.confidence = 0.0
                self._parsed = True
                return

            # Subtotal + Dept total should match. Subtotal is the earlier line
            # on page 1; Dept total is the "** TOTAL FOR DEPT: 90" line.
            subtotal = self._first_amount(_SUBTOTAL_RE, text)
            dept_total = self._first_amount(_DEPT_TOTAL_RE, text)
            # Prefer dept_total (more authoritative), fall back to subtotal.
            debourse_total = dept_total if dept_total is not None else subtotal

            tickets = self._extract_tickets(text)

            self.extracted_data = {
                'report_date': self._extract_report_date(text),
                'tickets': tickets,
                'ticket_count': len(tickets),
                'subtotal': subtotal,
                'dept_90_total': dept_total,
                'debourse_total': debourse_total,
                # Mirror field for downstream dispatcher convenience
                'debourse_total_dueback': debourse_total,
            }

            conf = 0.0
            if debourse_total is not None: conf += 0.5
            if tickets:                    conf += 0.3
            # Tickets and subtotal agreement is a strong signal
            if tickets and subtotal and abs(sum(t['amount'] for t in tickets) - subtotal) < 0.02:
                conf += 0.2
            self.confidence = round(conf, 2)
            self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"Parse error: {e}")
            self.confidence = 0.0
            self._parsed = True

    def validate(self):
        if self.extracted_data.get('debourse_total') is None:
            self.validation_errors.append("Debourse total not found")
            return False
        tickets = self.extracted_data.get('tickets') or []
        subtotal = self.extracted_data.get('subtotal')
        if tickets and subtotal is not None:
            ticket_sum = round(sum(t['amount'] for t in tickets), 2)
            if abs(ticket_sum - subtotal) > 0.02:
                self.validation_warnings.append(
                    f"Ticket sum {ticket_sum} != subtotal {subtotal}"
                )
        return True

    # ── internals ──────────────────────────────────────────────────────────

    def _extract_report_date(self, text):
        """Header: 'Transaction Date: 06-Apr-26' → '06-Apr-2026'."""
        m = re.search(r'Transaction Date:\s*(\d{2}-[A-Z][a-z]{2}-\d{2,4})', text)
        if not m:
            return None
        raw = m.group(1)
        # Normalize 2-digit year to 4-digit (20XX)
        parts = raw.split('-')
        if len(parts) == 3 and len(parts[2]) == 2:
            parts[2] = '20' + parts[2]
            raw = '-'.join(parts)
        return raw

    def _extract_tickets(self, text):
        """Return list of {amount, description, cashier} for each Depot Restaurant ticket."""
        tickets = []
        for m in _TICKET_RE.finditer(text):
            try:
                amount = float(m.group(1).replace(',', ''))
            except ValueError:
                continue

            # Cashier token sits BETWEEN "Depot Restaurant" and "**TICKET TOTAL"
            # on the same line as the ticket, so search the match text itself.
            cashier_match = _CASHIER_RE.search(text[m.start():m.end()])
            cashier = cashier_match.group(1) if cashier_match else None

            # Description is the line immediately after the TICKET TOTAL line.
            desc_match = re.search(r'\n\s*([^\n]+)', text[m.end():m.end() + 200])
            description = desc_match.group(1).strip() if desc_match else None

            tickets.append({
                'amount': round(amount, 2),
                'cashier': cashier,
                'description': description,
            })
        return tickets

    def _first_amount(self, pattern, text):
        """Return the first decimal amount captured by pattern, or None."""
        m = pattern.search(text)
        if not m:
            return None
        try:
            return round(float(m.group(1).replace(',', '')), 2)
        except ValueError:
            return None
