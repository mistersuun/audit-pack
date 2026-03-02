"""Cashier Summary PDF Parser for Galaxy Lightspeed PMS.

Parses two similar PDF reports from Galaxy Lightspeed:
1. Daily Cashout (cshsum) - settlement summaries by cashier
2. Cashier Cashout (cshout) - same plus cash paidouts

Both reports have the same structure with pages per cashier containing:
- Settlement Summary table (card codes + amounts)
- Totals row

The Cashier Cashout also includes:
- Cash drops per cashier (marked as "Total Drop:")
- Grand total cash drop in the summary section

Example settlement line:
200858AX American Express       2,760.36     0.00          0.00          0.00          2,760.36

Card code mapping:
- AX = American Express
- VI = Visa
- MC = Master Card
- DB = facture direct
- IN = Interac
- DI = Discover
"""

import re
import pdfplumber
from io import BytesIO
from utils.parsers.base_parser import BaseParser


class CashierSummaryParser(BaseParser):
    """Parser for Cashier Summary reports (cshsum/cshout) from Galaxy Lightspeed."""

    FIELD_MAPPINGS = {
        'total_amex': 'geac_cashout_amex',
        'total_visa': 'geac_cashout_visa',
        'total_mc': 'geac_cashout_mc',
        'total_debit': 'geac_cashout_debit',
        'total_discover': 'geac_cashout_discover',
        'total_facture': 'geac_cashout_facture',
        'total_settlements': 'geac_total_settlements',
        'total_deposits_rcvd': 'geac_deposits_received',
        'total_cash_drop': 'recap_cash_drop',
    }

    # Card code to card type mapping
    CARD_CODE_MAP = {
        'AX': 'amex',
        'VI': 'visa',
        'MC': 'mc',
        'DB': 'facture',
        'IN': 'debit',
        'DI': 'discover',
    }

    def __init__(self, file_bytes, filename=None):
        super().__init__(file_bytes, filename)
        self.raw_text = None
        self.cashiers = {}
        self.report_type = None  # 'cshsum' or 'cshout'

    def parse(self):
        """Parse the Cashier Summary PDF and extract structured data."""
        try:
            # Extract text from PDF
            self.raw_text = self._extract_text_from_pdf()

            # Detect report type
            self._detect_report_type()

            # Parse cashier sections
            self._parse_cashier_sections()

            # Calculate grand totals
            self._calculate_grand_totals()

            # Extract metadata
            self._extract_metadata()

            # Set confidence based on successful parsing
            self.confidence = 0.95 if self.extracted_data.get('total_settlements', 0) > 0 else 0.70
            self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"Parse error: {str(e)}")
            self.confidence = 0.0
            self._parsed = True

    def validate(self):
        """Validate extracted data."""
        is_valid = True

        # Check that we extracted at least some data
        if not self.cashiers:
            self.validation_errors.append("No cashier data extracted from PDF")
            is_valid = False

        # Check required totals
        required_fields = ['total_settlements']
        for field in required_fields:
            if field not in self.extracted_data or self.extracted_data[field] is None:
                self.validation_errors.append(f"Missing required field: {field}")
                is_valid = False
            elif self.extracted_data[field] == 0:
                self.validation_warnings.append(f"Field {field} is zero")

        # Validate that at least one card type has a value
        card_types = ['total_amex', 'total_visa', 'total_mc', 'total_debit', 'total_discover', 'total_facture']
        card_totals = sum(self.extracted_data.get(ct, 0) for ct in card_types)
        if card_totals == 0:
            self.validation_warnings.append("No card settlements extracted")

        # If cshout, verify we got a cash drop
        if self.report_type == 'cshout':
            if self.extracted_data.get('total_cash_drop', 0) == 0:
                self.validation_warnings.append("Cashier Cashout report but no cash drop extracted")

        return is_valid

    def _extract_text_from_pdf(self):
        """Extract text from PDF using pdfplumber, or read as plain text."""
        # Try PDF first
        try:
            text = ""
            with pdfplumber.open(BytesIO(self.file_bytes)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            if text.strip():
                return text
        except Exception:
            pass  # Not a valid PDF, try plain text

        # Fallback: treat as plain text (TXT/RTF format from Galaxy Lightspeed)
        try:
            text = self.file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = self.file_bytes.decode('latin-1')
            except Exception as e:
                raise Exception(f"Failed to read file as PDF or text: {str(e)}")

        return text

    def _detect_report_type(self):
        """Detect if this is a Daily Cashout (cshsum) or Cashier Cashout (cshout)."""
        # cshout reports mention cash drops ("Total Drop:")
        # cshsum reports are settlement-only
        if 'Total Drop:' in self.raw_text or 'Total Drop' in self.raw_text:
            self.report_type = 'cshout'
        else:
            self.report_type = 'cshsum'

    # Department code → RJ department key mapping (for allowances)
    DEPT_CODE_MAP = {
        '1': 'chambres',
        '4': 'club_lounge',
        '10': 'restaurant_piazza',
        '11': 'banquet',
        '28': 'la_spesa',
        '35': 'autres_revenus',
        '36': 'internet',
        '40': 'comptabilite',
        '90': 'debourse',
    }

    def _parse_cashier_sections(self):
        """Parse individual cashier sections from the PDF.

        NOTE: The report may have "For All Cashiers" summary blocks with
        aggregated totals. We detect them and use the dept_lines from the
        FIRST "All Cashiers" block (the one with the full department table)
        to get allowances without double-counting.
        """
        # Use finditer to locate each "For Cashier:" and "For All Cashiers" marker
        # so we know exactly which blocks are cashier vs grand total
        markers = list(re.finditer(r'For (Cashier:\s+\S+|All Cashiers)', self.raw_text))

        self._grand_total_dept_lines = None

        for idx, marker in enumerate(markers):
            # Determine block boundaries
            start = marker.end()
            end = markers[idx + 1].start() if idx + 1 < len(markers) else len(self.raw_text)
            block = self.raw_text[start:end]

            marker_text = marker.group(1)
            is_all_cashiers = (marker_text == 'All Cashiers')

            if is_all_cashiers:
                # Extract dept lines (allowances) from grand total block
                dept_lines = self._extract_dept_lines(block)
                if dept_lines and self._grand_total_dept_lines is None:
                    # Use the FIRST "All Cashiers" block with dept lines
                    self._grand_total_dept_lines = dept_lines

                settlements = self._extract_settlement_lines(block)
                if settlements.get('total', 0) > 0 and 'ALL_CASHIERS' not in self.cashiers:
                    self.cashiers['ALL_CASHIERS'] = {
                        'settlements': settlements,
                        'cash_drop': self._extract_cash_drop(block),
                        'dept_lines': dept_lines,
                        'is_grand_total': True,
                    }
                continue

            # Individual cashier
            cashier_name = marker_text.replace('Cashier:', '').strip()

            settlements = self._extract_settlement_lines(block)
            cash_drop = self._extract_cash_drop(block)
            dept_lines = self._extract_dept_lines(block)

            self.cashiers[cashier_name] = {
                'settlements': settlements,
                'cash_drop': cash_drop,
                'dept_lines': dept_lines,
            }

    def _extract_settlement_lines(self, cashier_block):
        """Extract settlement line items from a cashier block.

        Pattern:
        200858AX American Express       2,760.36     0.00          0.00          0.00          2,760.36

        NOTE: Cashier blocks may have TWO "Totals:" lines:
        - First: from the "Hotel Dpt Description..." table (ignore this one)
        - Second: from the "Settlement Summary" table (this is what we want)
        """
        settlements = {
            'amex': 0.0,
            'visa': 0.0,
            'mc': 0.0,
            'debit': 0.0,
            'discover': 0.0,
            'facture': 0.0,
            'total': 0.0,
            'dept_charges': 0.0,
            'deposits_received': 0.0,
            'ar_payments': 0.0,
        }

        # Extract ONLY the Settlement Summary section
        # Handle both PDF-extracted text ("Settlement Summary") and
        # raw TXT format ("S E T T L E M E N T   S U M M A R Y")
        settlement_section_start = cashier_block.find('Settlement Summary')
        if settlement_section_start == -1:
            settlement_section_start = cashier_block.find('S E T T L E M E N T')
        if settlement_section_start == -1:
            # No settlement section found
            return settlements

        # Use only the text from "Settlement Summary" onwards
        settlement_section = cashier_block[settlement_section_start:]

        # Pattern to match settlement lines: code + name + amounts
        # PDF format: "200858AX American Express  2,760.36  0.00  0.00  0.00  2,760.36"
        # TXT format: "200858 AX    American Express  2,760.36  0.00  0.00  0.00  2,760.36"
        line_pattern = r'200858\s*([A-Z]{2})\s+([A-Za-z\s]+?)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)'

        for match in re.finditer(line_pattern, settlement_section):
            card_code = match.group(1)
            card_desc = match.group(2).strip()
            settlement_amount = self._safe_float(match.group(3))
            dept_charges = self._safe_float(match.group(4))
            deposits_rcvd = self._safe_float(match.group(5))
            ar_payments = self._safe_float(match.group(6))
            total = self._safe_float(match.group(7))

            # Map card code to card type
            card_type = self.CARD_CODE_MAP.get(card_code)
            if card_type:
                settlements[card_type] = settlement_amount

        # Extract Totals line from Settlement Summary section only
        # Totals:                        25,038.87     0.00          0.00          0.00         25,038.87
        totals_match = re.search(
            r'Totals:\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)',
            settlement_section
        )
        if totals_match:
            settlements['total'] = self._safe_float(totals_match.group(1))
            settlements['dept_charges'] = self._safe_float(totals_match.group(2))
            settlements['deposits_received'] = self._safe_float(totals_match.group(3))
            settlements['ar_payments'] = self._safe_float(totals_match.group(4))
            # Total column (last one) should equal first column, already captured above

        return settlements

    def _extract_dept_lines(self, cashier_block):
        """Extract department charges & allowances from the Hotel Dpt Description table.

        This is the table BEFORE the Settlement Summary section.
        Pattern per line:
        200858     4  Club Lounge                        0.00           47.72-          0.00           0.00           0.00           0.00

        Amounts may have trailing '-' to indicate negative (allowances/credits).

        Returns:
            list of dicts with dept_code, description, charges, allowances, sundry, cash
        """
        lines = []

        # Only parse the section BEFORE Settlement Summary
        settlement_start = cashier_block.find('Settlement Summary')
        if settlement_start == -1:
            settlement_start = cashier_block.find('S E T T L E M E N T')
        if settlement_start == -1:
            dept_section = cashier_block
        else:
            dept_section = cashier_block[:settlement_start]

        # Pattern: HOTEL  DEPT  DESCRIPTION  CHARGES  ALLOWANCES  SUNDRY  CASH  DEPT_PAIDOUTS  CASH_PAIDOUTS
        # 200858     4  Club Lounge                        0.00           47.72-          0.00           0.00           0.00           0.00
        dept_pattern = r'200858\s+(\d+)\s+([A-Za-zÀ-ÿ\s]+?)\s+([\d,]+\.?\d*)-?\s+([\d,]+\.?\d*)-?\s+([\d,]+\.?\d*)-?\s+([\d,]+\.?\d*)-?\s+([\d,]+\.?\d*)-?\s+([\d,]+\.?\d*)-?'

        for match in re.finditer(dept_pattern, dept_section):
            dept_code = match.group(1).strip()
            desc = match.group(2).strip()
            charges_str = match.group(3)
            allowances_str = match.group(4)

            charges = self._safe_float(charges_str)
            allowances = self._safe_float(allowances_str)

            # Check if allowances has trailing '-' in the raw text to mark negative
            # The regex strips it, so we check the original text
            raw_segment = match.group(0)
            if allowances > 0 and (allowances_str + '-') in raw_segment:
                allowances = -allowances

            dept_key = self.DEPT_CODE_MAP.get(dept_code, f'dept_{dept_code}')

            lines.append({
                'dept_code': dept_code,
                'dept_key': dept_key,
                'description': desc,
                'charges': charges,
                'allowances': allowances,
            })

        return lines

    def _extract_cash_drop(self, cashier_block):
        """Extract cash drop amount from a cashier block (cshout only).

        Pattern: "Total Drop: 504.36-" (note the trailing minus for negative)
        or "Total Drop: 504.36"
        """
        # Pattern for cash drop: "Total Drop: XXX.XX" or "Total Cash Drop: XXX.XX-"
        drop_match = re.search(r'Total (?:Cash )?Drop:\s*([\d,]+\.?\d*)(-?)', cashier_block)
        if drop_match:
            amount = self._safe_float(drop_match.group(1))
            is_negative = drop_match.group(2) == '-'
            return -amount if is_negative else amount

        return 0.0

    def _calculate_grand_totals(self):
        """Calculate grand totals across all cashiers."""
        totals = {
            'amex': 0.0,
            'visa': 0.0,
            'mc': 0.0,
            'debit': 0.0,
            'discover': 0.0,
            'facture': 0.0,
            'total_settlements': 0.0,
            'total_dept_charges': 0.0,
            'total_deposits_rcvd': 0.0,
            'total_ar_payments': 0.0,
            'total_cash_drop': 0.0,
        }

        for cashier_name, data in self.cashiers.items():
            # Skip "All Cashiers" grand total block to avoid double-counting
            if data.get('is_grand_total'):
                continue

            settlements = data['settlements']
            cash_drop = data['cash_drop']

            # Sum card totals
            totals['amex'] += settlements.get('amex', 0.0)
            totals['visa'] += settlements.get('visa', 0.0)
            totals['mc'] += settlements.get('mc', 0.0)
            totals['debit'] += settlements.get('debit', 0.0)
            totals['discover'] += settlements.get('discover', 0.0)
            totals['facture'] += settlements.get('facture', 0.0)
            totals['total_settlements'] += settlements.get('total', 0.0)
            totals['total_dept_charges'] += settlements.get('dept_charges', 0.0)
            totals['total_deposits_rcvd'] += settlements.get('deposits_received', 0.0)
            totals['total_ar_payments'] += settlements.get('ar_payments', 0.0)
            totals['total_cash_drop'] += cash_drop

        # Aggregate allowances by department
        # Prefer "All Cashiers" grand total block (already summed, no double-counting)
        # Fall back to summing individual cashiers if no grand total block
        allowances_by_dept = {}
        grand_total_lines = getattr(self, '_grand_total_dept_lines', None)
        if grand_total_lines:
            for dept_line in grand_total_lines:
                allow = dept_line.get('allowances', 0)
                if allow != 0:
                    dept_key = dept_line['dept_key']
                    allowances_by_dept[dept_key] = allowances_by_dept.get(dept_key, 0) + allow
        else:
            # Fallback: sum individual cashiers (no grand total section)
            for cashier_name, data in self.cashiers.items():
                if data.get('is_grand_total'):
                    continue
                for dept_line in data.get('dept_lines', []):
                    allow = dept_line.get('allowances', 0)
                    if allow != 0:
                        dept_key = dept_line['dept_key']
                        allowances_by_dept[dept_key] = allowances_by_dept.get(dept_key, 0) + allow

        self.extracted_data = {
            'report_type': self.report_type,
            'total_amex': totals['amex'],
            'total_visa': totals['visa'],
            'total_mc': totals['mc'],
            'total_debit': totals['debit'],
            'total_discover': totals['discover'],
            'total_facture': totals['facture'],
            'total_settlements': totals['total_settlements'],
            'total_dept_charges': totals['total_dept_charges'],
            'total_deposits_rcvd': totals['total_deposits_rcvd'],
            'total_ar_payments': totals['total_ar_payments'],
            'total_cash_drop': totals['total_cash_drop'],
            'num_cashiers': len(self.cashiers),
            'cashier_details': self.cashiers,
            # Add grand_totals dict for card types (for convenience)
            'grand_totals': {
                'AX': totals['amex'],
                'VI': totals['visa'],
                'MC': totals['mc'],
                'DB': totals['facture'],
                'IN': totals['debit'],
                'DI': totals['discover'],
            },
            # Allowances by department (negative values = credits/deductions)
            'allowances_by_dept': allowances_by_dept,
            'total_allowances': round(sum(allowances_by_dept.values()), 2),
        }

    def _extract_metadata(self):
        """Extract report date, property, and other metadata."""
        # Pattern: "Sheraton Laval" or similar property name
        property_match = re.search(r'(Sheraton\s+[A-Za-z]+)', self.raw_text)
        if property_match:
            self.extracted_data['property'] = property_match.group(1).strip()

        # Pattern: Date like "06-FEB-2026"
        date_match = re.search(r'(\d{2}-[A-Z]{3}-\d{4})', self.raw_text)
        if date_match:
            self.extracted_data['report_date'] = date_match.group(1)

        # Try to find report generation timestamp
        time_match = re.search(r'(\d{2}:\d{2})\s+(AM|PM)', self.raw_text)
        if time_match:
            self.extracted_data['report_time'] = f"{time_match.group(1)} {time_match.group(2)}"
