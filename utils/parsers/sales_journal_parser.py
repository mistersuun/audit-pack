"""Sales Journal Report parser for Sheraton Laval night audit system.

Parses Sales Journal reports from Positouch/LightSpeed POS system.
Handles RTF and plain text formats, extracts revenue by department,
payment methods, taxes, and adjustments.
"""

import re
from datetime import datetime
from pathlib import Path
from .base_parser import BaseParser


class SalesJournalParser(BaseParser):
    """Parser for Sales Journal reports from POS system."""

    # Map extracted fields to RJ cell references
    FIELD_MAPPINGS = {
        # Recap sheet
        'comptant_lightspeed': 'Recap!B6',

        # TransElect sheet
        'visa': 'TransElect!B2',
        'mastercard': 'TransElect!B3',
        'amex': 'TransElect!B4',
        'interac': 'TransElect!B5',

        # HP sheet
        'hotel_promotion': 'HP!B2',

        # Jour sheet
        'piazza_total': 'Jour!B5',
        'banquet_total': 'Jour!B6',
        'chambres_total': 'Jour!B7',
        'spesa_total': 'Jour!B8',
        'tabagie': 'Jour!B9',
        'tps': 'Jour!B10',
        'tvq': 'Jour!B11',
    }

    def __init__(self, file_bytes, filename=None):
        """Initialize parser with file bytes."""
        super().__init__(file_bytes, filename)
        self.raw_text = None
        self.report_date = None
        self.report_time = None

    @classmethod
    def load_from_file(cls, file_path):
        """Load and parse a Sales Journal file.

        Args:
            file_path: Path to .rtf or .txt file

        Returns:
            Parsed result dict with extracted data
        """
        file_path = Path(file_path)

        # Read file as bytes
        with open(file_path, 'rb') as f:
            file_bytes = f.read()

        # Create parser instance
        parser = cls(file_bytes, filename=file_path.name)

        # Parse and return result
        return parser.get_result()

    def parse(self):
        """Parse the Sales Journal file.

        Extracts:
        - Report metadata (date, time)
        - Department revenue
        - Payment methods
        - Taxes
        - Adjustments
        - RJ mapping for direct insertion
        """
        try:
            # Decode RTF or text
            self.raw_text = self._decode_file()

            # Clean up the text
            clean_text = self._clean_rtf(self.raw_text)

            # Parse report metadata
            self._parse_metadata(clean_text)

            # Parse departments
            departments = self._parse_departments(clean_text)

            # Parse taxes
            taxes = self._parse_taxes(clean_text)

            # Parse payment methods
            payments = self._parse_payments(clean_text)

            # Parse adjustments (page 2)
            adjustments = self._parse_adjustments(clean_text)

            # Calculate totals
            total_balanced = self._extract_total(clean_text)

            # Build extracted data
            self.extracted_data = {
                'report_date': self.report_date,
                'report_time': self.report_time,
                'audit_date': self.report_date,
                'total_balanced': total_balanced,
                'departments': departments,
                'taxes': taxes,
                'payments': payments,
                'adjustments': adjustments,
                'rj_mapping': self._build_rj_mapping(departments, taxes, payments, adjustments),
            }

            # Calculate confidence score
            self.confidence = 0.95 if self.report_date else 0.5
            self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"Parse error: {str(e)}")
            self.confidence = 0.0
            self._parsed = True

    def validate(self):
        """Validate extracted data.

        Checks:
        - Report date is present
        - Total balance is numeric
        - Departments have data
        """
        is_valid = True

        if not self.report_date:
            self.validation_errors.append("Report date not found")
            is_valid = False

        if not self.extracted_data.get('departments'):
            self.validation_errors.append("No departments found")
            is_valid = False

        total = self.extracted_data.get('total_balanced')
        if total is None or total == 0:
            self.validation_warnings.append("Total balance is zero or missing")

        return is_valid

    def _decode_file(self):
        """Decode file bytes to text.

        Returns:
            String content of file
        """
        # Try UTF-8 first, then fall back to latin-1
        try:
            return self.file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return self.file_bytes.decode('latin-1')
            except UnicodeDecodeError:
                return self.file_bytes.decode('cp1252')

    def _clean_rtf(self, text):
        """Remove RTF markup from text.

        Args:
            text: Raw RTF or plain text

        Returns:
            Cleaned text with RTF tags removed
        """
        # First, handle RTF line breaks (\ at end of line)
        text = text.replace('\\\n', '\n')

        # Remove RTF header and tag content like {\fonttbl ...}
        text = re.sub(r'\{[^{}]*\}', '', text)

        # Remove RTF control sequences
        # Pattern: backslash followed by letters and optional digits
        text = re.sub(r'\\[a-z]+\d*\s?', '', text)

        # Remove remaining braces
        text = re.sub(r'[{}]', '', text)

        # Clean up stray backslashes
        text = re.sub(r'\\', '', text)

        # Clean up multiple spaces to single space (but preserve newlines)
        lines = text.split('\n')
        lines = [re.sub(r'  +', ' ', line) for line in lines]
        text = '\n'.join(lines)

        return text

    def _parse_metadata(self, text):
        """Extract report date and time.

        Args:
            text: Cleaned report text
        """
        # Pattern: REPORT DATE: MM/DD/YYYY
        date_match = re.search(r'REPORT DATE:\s*(\d{2}/\d{2}/\d{4})', text)
        if date_match:
            self.report_date = date_match.group(1)

        # Pattern: REPORT TIME: HH:MM:SS.xx
        time_match = re.search(r'REPORT TIME:\s*(\d{1,2}:\d{2}:\d{2}\.\d+)', text)
        if time_match:
            self.report_time = time_match.group(1)

    def _parse_departments(self, text):
        """Parse department revenue sections.

        Args:
            text: Cleaned report text

        Returns:
            Dict of departments with line items and totals
        """
        departments = {}

        # Split by pages to handle page headers
        pages = self._split_pages(text)

        # Process main revenue sections (page 1 has the content after first PAGE: marker)
        if len(pages) > 1:
            main_content = pages[1]
        elif len(pages) > 0:
            main_content = pages[0]
        else:
            main_content = text

        # Department names to look for (revenue departments)
        dept_names = ['CAFE LINK', 'PIAZZA', 'BAR CUPOLA', 'CHAMBRES', 'BANQUET',
                      'SPESA', 'CLUB LOUNG']

        # Keywords that mark the end of department section
        end_keywords = ['TPS', 'TVQ', 'COMPTANT', 'VISA', 'MASTERCARD', 'AMEX',
                        'INTERAC', 'CHAMBRE', 'CORRECTION', 'ADMINISTRATION']

        lines = main_content.split('\n')
        current_dept = None

        for i, line in enumerate(lines):
            # Skip empty lines and header lines
            if not line.strip() or '---' in line or 'PAGE:' in line or 'REPORT' in line or 'Account' in line:
                continue

            stripped = line.strip()

            # Check if we hit end-of-departments section
            if any(keyword == stripped.split()[0] if stripped.split() else False
                   for keyword in end_keywords):
                current_dept = None
                continue

            # Check if this line is a department header (exact match with dept names)
            if stripped in dept_names:
                current_dept = self._normalize_name(stripped)
                if current_dept not in departments:
                    departments[current_dept] = {}
                continue

            # Check if this is a line item (indented with amount)
            if current_dept and self._is_line_item(line):
                item_name, debits, credits = self._parse_line_item(line)
                if item_name:
                    item_key = self._normalize_name(item_name)

                    # Items in departments are ALWAYS stored as revenue (credits)
                    # except for special items like CORRECTION, EMPL 30%, etc.
                    # which belong in adjustments, not departments
                    if item_key not in ['correction', 'empl_30', 'pourboire_charge',
                                        'administration', 'hotel_promotion', 'forfait']:
                        # Standardize sub-item key for jour mapping
                        std_key = self._standardize_subitem(item_key)
                        # Credit column = positive (sales revenue)
                        # Debit column = negative (corrections/comps/deductions)
                        if credits > 0:
                            departments[current_dept][std_key] = departments[current_dept].get(std_key, 0) + credits
                        elif debits > 0:
                            departments[current_dept][std_key] = departments[current_dept].get(std_key, 0) - debits

        # Calculate department totals and remove empty departments
        depts_with_items = {}
        for dept in departments:
            total = sum(v for k, v in departments[dept].items() if isinstance(v, (int, float)))
            if total != 0:  # Keep departments with any non-zero total (including negative net)
                departments[dept]['total'] = round(total, 2)
                depts_with_items[dept] = departments[dept]

        return depts_with_items

    def _parse_taxes(self, text):
        """Extract TPS and TVQ amounts.

        Args:
            text: Cleaned report text

        Returns:
            Dict with tax amounts
        """
        taxes = {}

        # Pattern: TPS/TVQ followed by number
        tps_match = re.search(r'TPS\s+(\d+\.\d+)', text)
        if tps_match:
            taxes['tps'] = float(tps_match.group(1))

        tvq_match = re.search(r'TVQ\s+(\d+\.\d+)', text)
        if tvq_match:
            taxes['tvq'] = float(tvq_match.group(1))

        return taxes

    def _parse_payments(self, text):
        """Extract payment method amounts.

        Args:
            text: Cleaned report text

        Returns:
            Dict with payment amounts
        """
        payments = {}

        # Payment method patterns
        payment_items = {
            'comptant': r'COMPTANT\s+(\d+\.\d+)',
            'visa': r'VISA\s+(\d+\.\d+)',
            'mastercard': r'MASTERCARD\s+(\d+\.\d+)',
            'amex': r'AMEX\s+(\d+\.\d+)',
            'interac': r'INTERAC\s+(\d+\.\d+)',
            'chambre': r'CHAMBRE\s+(\d+\.\d+)',
            'correction': r'CORRECTION\s+(\d+\.\d+)',
        }

        for key, pattern in payment_items.items():
            match = re.search(pattern, text)
            if match:
                payments[key] = float(match.group(1))

        return payments

    def _parse_adjustments(self, text):
        """Extract adjustment amounts from page 2.

        Args:
            text: Cleaned report text

        Returns:
            Dict with adjustment amounts
        """
        adjustments = {}

        # Split by pages
        pages = self._split_pages(text)

        # Process page 2 (adjustments are typically on the second PAGE: marker)
        # pages[0] = before first PAGE:
        # pages[1] = after first PAGE: (contains main data)
        # pages[2] = after second PAGE: (contains adjustments)
        if len(pages) > 2:
            page2 = pages[2]
        elif len(pages) > 1:
            page2 = pages[1]
        else:
            page2 = text

        # Adjustment patterns
        adjustment_items = {
            'administration': r'ADMINISTRATION\s+(\d+\.\d+)',
            'hotel_promotion': r'HOTEL PROMOTION\s+(\d+\.\d+)',
            'forfait': r'FORFAIT\s+(\d+\.\d+)',
            'empl_30': r'EMPL 30%\s+(\d+\.\d+)',
            'pourboire_charge': r'POURBOIRE CHARGE\s+(\d+\.\d+)',
        }

        for key, pattern in adjustment_items.items():
            match = re.search(pattern, page2)
            if match:
                adjustments[key] = float(match.group(1))

        return adjustments

    def _extract_total(self, text):
        """Extract final balanced total.

        Args:
            text: Cleaned report text

        Returns:
            Total amount as float
        """
        # Pattern: number followed by asterisk (balanced total)
        # Format: 31137.86 *
        match = re.search(r'(\d+\.\d+)\s*\*\s+(\d+\.\d+)\s*\*', text)
        if match:
            # Both debit and credit should be equal
            return float(match.group(1))

        return 0.0

    def _split_pages(self, text):
        """Split report text by pages.

        Args:
            text: Full report text

        Returns:
            List of page content strings
        """
        # Split by PAGE: X header
        pages = re.split(r'PAGE:\s*\d+', text)
        # Remove empty pages
        return [p.strip() for p in pages if p.strip()]

    def _is_line_item(self, line):
        """Check if line contains a line item with amount.

        Args:
            line: Text line to check

        Returns:
            True if line appears to be a line item
        """
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            return False

        # Must contain at least one number (amount)
        if not re.search(r'\d+\.\d+', stripped):
            return False

        # Must have text before the number (account name)
        # Pattern: word characters/spaces before a number
        if not re.match(r'[A-Z\s\/%&\.]+\s+\d', stripped):
            return False

        return True

    def _parse_line_item(self, line):
        """Parse a single line item to extract name and amounts.

        Args:
            line: Line text to parse

        Returns:
            Tuple of (item_name, debits_amount, credits_amount)
        """
        # Original line with leading spaces preserved
        original = line
        stripped = line.lstrip()

        # Find all numeric values in the line
        numbers = re.findall(r'(\d+\.\d+)', stripped)

        if not numbers:
            return None, 0.0, 0.0

        # Extract account name (text before first number)
        name_match = re.match(r'^([A-Z\s\/%&\.]+?)\s+\d', stripped)
        if not name_match:
            return None, 0.0, 0.0

        name = name_match.group(1).strip()

        # Parse numbers - determine debit vs credit by checking for trailing spaces
        # In the original RTF format:
        # - DEBIT numbers have significant trailing spaces (indicating more columns after)
        # - CREDIT numbers are typically followed by minimal/no spaces (end of line)

        if len(numbers) == 1:
            # Single number - check for trailing spaces after it
            amount = float(numbers[0])
            num_str = numbers[0]

            # Find what comes after the first number
            num_pos = stripped.find(num_str)
            if num_pos >= 0:
                after_num = stripped[num_pos + len(num_str):]
                # If there are multiple trailing spaces, it's in debit column
                # (more columns to follow)
                trailing_spaces = len(after_num) - len(after_num.lstrip())

                # If more than 3 trailing spaces, it's a debit
                # Otherwise it's a credit (right column)
                if trailing_spaces > 0:  # Any trailing space after number = debit column
                    return name, amount, 0.0
                else:
                    return name, 0.0, amount
            else:
                # Default: single amounts are usually credits (revenue)
                return name, 0.0, amount

        elif len(numbers) == 2:
            # Two numbers: first is debit, second is credit
            debits = float(numbers[0])
            credits = float(numbers[1])
            return name, debits, credits

        else:
            # Multiple numbers - take first as debit, last as credit
            debits = float(numbers[0])
            credits = float(numbers[-1])
            return name, debits, credits

    # Map POS sub-item names to standard jour column keys
    SUBITEM_STANDARDIZATION = {
        # Food
        'nourriture': 'nourriture',
        'food': 'nourriture',
        # Alcohol / spirits
        'alcool': 'boisson',
        'boisson': 'boisson',
        'spiritueux': 'boisson',
        'liqueur': 'boisson',
        # Beer
        'bieres': 'bieres',
        'biere': 'bieres',
        'biere_draught': 'bieres',
        'biere_fut': 'bieres',
        'beer': 'bieres',
        # Non-alcoholic
        'mineraux': 'mineraux',
        'non_alcool': 'mineraux',
        'non_alcool_bar': 'mineraux',
        'soft_drink': 'mineraux',
        'boisson_gazeuse': 'mineraux',
        # Wine
        'vins': 'vins',
        'vin': 'vins',
        'wine': 'vins',
        # Tobacco
        'tabagie': 'tabagie',
        'tabac': 'tabagie',
    }

    def _normalize_name(self, name):
        """Normalize a name for use as dictionary key.

        Args:
            name: Name to normalize

        Returns:
            Normalized key (lowercase, underscores, no spaces)
        """
        return name.strip().lower().replace(' ', '_').replace('/', '_').replace('.', '')

    def _standardize_subitem(self, raw_key):
        """Standardize a sub-item key to match jour column expectations.

        Maps various POS report names (alcool, biere, vin, etc.) to the
        standard keys used in daily_rev_jour_mapping.py:
        nourriture, boisson, bieres, mineraux, vins, tabagie.

        Args:
            raw_key: Normalized sub-item key from POS report

        Returns:
            Standardized key (e.g., 'alcool' -> 'boisson')
        """
        return self.SUBITEM_STANDARDIZATION.get(raw_key, raw_key)

    def _build_rj_mapping(self, departments, taxes, payments, adjustments):
        """Build RJ mapping dict with pre-computed values.

        Args:
            departments: Department data
            taxes: Tax data
            payments: Payment data
            adjustments: Adjustment data

        Returns:
            Dict organized by RJ sheet sections
        """
        mapping = {
            'recap': {
                'comptant_lightspeed': payments.get('comptant', 0.0),
            },
            'transelect': {
                'visa': payments.get('visa', 0.0),
                'mastercard': payments.get('mastercard', 0.0),
                'amex': payments.get('amex', 0.0),
                'interac': payments.get('interac', 0.0),
            },
            'hp': {
                'hotel_promotion': adjustments.get('hotel_promotion', 0.0),
            },
            'jour': {
                'piazza_total': departments.get('piazza', {}).get('total', 0.0),
                'banquet_total': departments.get('banquet', {}).get('total', 0.0),
                'chambres_total': departments.get('chambres', {}).get('total', 0.0),
                'spesa_total': departments.get('spesa', {}).get('total', 0.0),
                'tabagie': departments.get('spesa', {}).get('tabagie', 0.0),
                'tps': taxes.get('tps', 0.0),
                'tvq': taxes.get('tvq', 0.0),
            }
        }

        return mapping


