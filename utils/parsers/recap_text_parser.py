"""Recap text parser for Sheraton Laval night audit system.

Parses Server Recap text files (Sales Journal Reports) showing per-server
payment breakdowns. Extracts per-server details for Transelect Restaurant
tab and aggregated grand totals for Recap tab.

Handles multi-page reports with server sections separated by server headers.
"""

import re
from datetime import datetime
from pathlib import Path
from .base_parser import BaseParser


class RecapTextParser(BaseParser):
    """Parser for Server Recap text reports from POS system."""

    # Map extracted fields to RJ native API endpoints/fields
    FIELD_MAPPINGS = {
        # Recap sheet totals
        'grand_total_visa': 'recap_visa',
        'grand_total_mc': 'recap_mc',
        'grand_total_amex': 'recap_amex',
        'grand_total_interac': 'recap_interac',
        'grand_total_cash': 'recap_cash',
        'grand_total_chambre': 'recap_chambre',
        'grand_total_sales': 'recap_total_sales',

        # Transelect Restaurant detail (per-server breakdown)
        'server_details': 'transelect_restaurant_data',
    }

    def __init__(self, file_bytes, filename=None):
        """Initialize parser with file bytes."""
        super().__init__(file_bytes, filename)
        self.raw_text = None
        self.report_date = None
        self.report_time = None
        self.servers = {}  # Dict of server_id -> server data
        self.grand_totals = {}  # Aggregated totals across all servers

    @classmethod
    def load_from_file(cls, file_path):
        """Load and parse a Server Recap text file.

        Args:
            file_path: Path to .txt file

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
        """Parse the Server Recap text file.

        Extracts:
        - Report metadata (date, time)
        - Per-server breakdown (name, sales, payment methods)
        - Grand totals by payment type
        - Server details for Transelect Restaurant mapping
        """
        try:
            # Decode text file
            self.raw_text = self._decode_file()

            # Parse report metadata
            self._parse_metadata(self.raw_text)

            # Split by server sections
            self.servers = self._parse_servers(self.raw_text)

            # Aggregate grand totals across all servers
            self.grand_totals = self._calculate_grand_totals(self.servers)

            # Extract grand total line (if present)
            grand_total_sales = self._extract_grand_total_sales(self.raw_text)

            # Build extracted data
            self.extracted_data = {
                'report_date': self.report_date,
                'report_time': self.report_time,
                'audit_date': self.report_date,
                'servers': self.servers,
                'grand_total_visa': self.grand_totals.get('visa', 0.0),
                'grand_total_mc': self.grand_totals.get('mastercard', 0.0),
                'grand_total_amex': self.grand_totals.get('amex', 0.0),
                'grand_total_interac': self.grand_totals.get('interac', 0.0),
                'grand_total_cash': self.grand_totals.get('cash', 0.0),
                'grand_total_chambre': self.grand_totals.get('chambre', 0.0),
                'grand_total_hotel_prom': self.grand_totals.get('hotel_prom', 0.0),
                'grand_total_sales': grand_total_sales or self.grand_totals.get('total_sales', 0.0),
                'server_details': self._build_server_details(self.servers),
            }

            # Calculate confidence score
            confidence = 0.0
            if self.report_date:
                confidence += 0.3
            if len(self.servers) > 0:
                confidence += 0.4
            if self.grand_totals.get('total_sales', 0) > 0:
                confidence += 0.3
            self.confidence = confidence

            self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"Parse error: {str(e)}")
            self.confidence = 0.0
            self._parsed = True

    def validate(self):
        """Validate extracted data.

        Checks:
        - Report date is present
        - At least one server found
        - Grand totals are numeric and reasonable
        """
        is_valid = True

        if not self.report_date:
            self.validation_errors.append("Report date not found")
            is_valid = False

        if not self.servers:
            self.validation_errors.append("No servers found in report")
            is_valid = False

        total_sales = self.extracted_data.get('grand_total_sales', 0)
        if total_sales == 0:
            self.validation_warnings.append("Grand total sales is zero")

        # Check if totals seem reasonable (not negative)
        for key in ['grand_total_visa', 'grand_total_mc', 'grand_total_amex',
                    'grand_total_interac', 'grand_total_cash', 'grand_total_chambre']:
            val = self.extracted_data.get(key, 0)
            if val < 0:
                self.validation_warnings.append(f"{key} is negative: {val}")

        return is_valid

    def _decode_file(self):
        """Decode file bytes to text.

        Returns:
            String content of file
        """
        # Try UTF-8 first, then fall back to latin-1, then cp1252
        try:
            return self.file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return self.file_bytes.decode('latin-1')
            except UnicodeDecodeError:
                return self.file_bytes.decode('cp1252')

    def _parse_metadata(self, text):
        """Extract report date and time from header.

        Args:
            text: Full report text
        """
        # Pattern: REPORT DATE: MM/DD/YYYY
        date_match = re.search(r'REPORT DATE:\s*(\d{2}/\d{2}/\d{4})', text)
        if date_match:
            self.report_date = date_match.group(1)

        # Pattern: REPORT TIME: HH:MM:SS.xx
        time_match = re.search(r'REPORT TIME:\s*(\d{1,2}:\d{2}:\d{2}\.\d+)', text)
        if time_match:
            self.report_time = time_match.group(1)

    def _parse_servers(self, text):
        """Parse individual server sections from report.

        Each server block contains:
        - Server header with ID and name
        - Total sales and check count
        - Payment method breakdown (VISA, MC, AMEX, INTERAC, CASH, etc.)
        - Department/category breakdown (CHAMBRE, HOTEL PROM, etc.)

        Args:
            text: Full report text

        Returns:
            Dict of server_id -> server data dict
        """
        servers = {}

        # Split by server sections using "PAYMENT TOTALS for" pattern
        # Pattern: "PAYMENT TOTALS for 340-SPIRO KATSENIS"
        # The pattern captures: (server_id)-(server_name on same line) and continues to next server or end
        server_pattern = r'PAYMENT TOTALS for\s+(\d+)-([^\n]+)(.+?)(?=PAYMENT TOTALS for|TOTAL OF SERVERS|$)'

        matches = re.finditer(server_pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            server_id = match.group(1).strip()
            server_name = match.group(2).strip()
            # Reconstruct the full block including the header and content
            server_block = 'PAYMENT TOTALS for ' + match.group(1) + '-' + match.group(2) + match.group(3)

            # Extract total sales from "TOTAL SALES+TAX:    1666.96" line
            total_sales = self._extract_float_after_pattern(
                server_block,
                r'TOTAL SALES\s*\+\s*TAX:\s*(\d+(?:,\d+)*\.\d+)',
                0.0
            )

            # Extract number of checks from "NUMBER OF CHECKS PAID:   30" line
            num_checks = self._extract_int_after_pattern(
                server_block,
                r'NUMBER OF CHECKS PAID:\s*(\d+)',
                0
            )

            # Parse payment methods
            payments = self._parse_payment_methods(server_block)

            # Parse departments/categories
            departments = self._parse_departments(server_block)

            # Build server record
            servers[server_id] = {
                'id': server_id,
                'name': server_name,
                'total_sales': total_sales,
                'num_checks': num_checks,
                'payments': payments,
                'departments': departments,
            }

        return servers

    def _parse_payment_methods(self, server_block):
        """Extract payment method totals from a server block.

        In the actual format, payment types appear with variable spacing and count:
        VISA           8                                                    380.48
        MASTERCARD     3                                                    238.17

        CASH is special - it only shows a count on the CASH line. The actual cash
        amount appears on the "EXPECTED DEPOSIT" line in the format section above.

        Args:
            server_block: Text block for single server

        Returns:
            Dict of payment_method -> amount
        """
        payments = {}

        # Patterns for credit card payment methods
        # Match the payment type at the start of a line, then grab the amount at the end
        payment_patterns = {
            'visa': r'^VISA\s+\d+\s+(-?\d+(?:,\d+)*\.\d+)',
            'mastercard': r'^MASTERCARD\s+\d+\s+(-?\d+(?:,\d+)*\.\d+)',
            'amex': r'^AMEX\s+\d+\s+(-?\d+(?:,\d+)*\.\d+)',
            'interac': r'^INTERAC\s+\d+\s+(-?\d+(?:,\d+)*\.\d+)',
        }

        for method, pattern in payment_patterns.items():
            match = re.search(pattern, server_block, re.IGNORECASE | re.MULTILINE)
            if match:
                payments[method] = self._safe_float(match.group(1))
            else:
                payments[method] = 0.0

        # Cash is extracted from "EXPECTED DEPOSIT" line, which appears in the
        # TYPE/NO section at the top, before the payment method breakdown
        cash_match = re.search(r'^EXPECTED DEPOSIT\s+(-?\d+(?:,\d+)*\.\d+)', server_block, re.IGNORECASE | re.MULTILINE)
        if cash_match:
            payments['cash'] = self._safe_float(cash_match.group(1))
        else:
            payments['cash'] = 0.0

        return payments

    def _parse_departments(self, server_block):
        """Extract department/category revenue from server block.

        Common departments: CHAMBRE, HOTEL PROM, ADMIN, FORFAIT, PANNE LIEN, etc.
        These appear with variable spacing similar to payment methods.

        Args:
            server_block: Text block for single server

        Returns:
            Dict of department -> amount
        """
        departments = {}

        # Departments we're looking for - match them at line start
        dept_patterns = {
            'chambre': r'^CHAMBRE\s+\d+\s+(-?\d+(?:,\d+)*\.\d+)',
            'hotel_prom': r'^HOTEL PROM\s+\d+\s+(-?\d+(?:,\d+)*\.\d+)',
            'admin': r'^ADMIN\s+\d+\s+(-?\d+(?:,\d+)*\.\d+)',
            'forfait': r'^FORFAIT\s+\d+\s+(-?\d+(?:,\d+)*\.\d+)',
        }

        for dept, pattern in dept_patterns.items():
            match = re.search(pattern, server_block, re.IGNORECASE | re.MULTILINE)
            if match:
                departments[dept] = self._safe_float(match.group(1))

        return departments

    def _calculate_grand_totals(self, servers):
        """Aggregate totals across all servers by payment method.

        Args:
            servers: Dict of server_id -> server data

        Returns:
            Dict of payment_method -> aggregated amount
        """
        grand_totals = {
            'visa': 0.0,
            'mastercard': 0.0,
            'amex': 0.0,
            'interac': 0.0,
            'cash': 0.0,
            'chambre': 0.0,
            'hotel_prom': 0.0,
            'total_sales': 0.0,
        }

        for server_id, server_data in servers.items():
            # Aggregate payment methods
            for method in ['visa', 'mastercard', 'amex', 'interac', 'cash']:
                grand_totals[method] += server_data.get('payments', {}).get(method, 0.0)

            # Aggregate departments
            for dept in ['chambre', 'hotel_prom']:
                grand_totals[dept] += server_data.get('departments', {}).get(dept, 0.0)

            # Aggregate total sales
            grand_totals['total_sales'] += server_data.get('total_sales', 0.0)

        # Round all to 2 decimals
        for key in grand_totals:
            grand_totals[key] = round(grand_totals[key], 2)

        return grand_totals

    def _extract_grand_total_sales(self, text):
        """Extract the grand total sales line at end of report.

        Pattern: "GRAND TOTAL ... 12345.67" or similar

        Args:
            text: Full report text

        Returns:
            Grand total amount as float, or None
        """
        # Try various grand total patterns (handles commas as thousands separators)
        patterns = [
            r'GRAND TOTAL\s+(\d+(?:,\d+)*\.\d+)',  # Matches 24,273.34
            r'GRAND TOTAL.+?(\d+(?:,\d+)*\.\d+)\s*$',
            r'Total\s+all\s+servers.+?(\d+(?:,\d+)*\.\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return self._safe_float(match.group(1))

        return None

    def _build_server_details(self, servers):
        """Build server details structure for Transelect Restaurant tab.

        Format the server breakdown for direct insertion into
        transelect_restaurant DOM.

        Args:
            servers: Dict of server_id -> server data

        Returns:
            List of dicts with server and payment details
        """
        server_list = []

        for server_id, server_data in sorted(servers.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            payments = server_data.get('payments', {})

            server_entry = {
                'id': server_id,
                'name': server_data.get('name', f"Server {server_id}"),
                'total': server_data.get('total_sales', 0.0),
                'visa': payments.get('visa', 0.0),
                'mastercard': payments.get('mastercard', 0.0),
                'amex': payments.get('amex', 0.0),
                'interac': payments.get('interac', 0.0),
                'cash': payments.get('cash', 0.0),
            }

            server_list.append(server_entry)

        return server_list

    def _extract_float_after_pattern(self, text, pattern, default=0.0):
        """Find and extract float value after regex pattern.

        Args:
            text: Text to search
            pattern: Regex pattern with one capturing group
            default: Default value if not found

        Returns:
            Float value or default
        """
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return self._safe_float(match.group(1), default)
        return default

    def _extract_int_after_pattern(self, text, pattern, default=0):
        """Find and extract integer value after regex pattern.

        Args:
            text: Text to search
            pattern: Regex pattern with one capturing group
            default: Default value if not found

        Returns:
            Int value or default
        """
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                return default
        return default

    def _safe_float(self, value, default=0.0):
        """Safely convert value to float, handling various formats.

        Handles North American format: 15,773.09 (comma=thousands, dot=decimal)

        Args:
            value: Value to convert (string with commas/dots)
            default: Default if conversion fails

        Returns:
            Float value or default
        """
        if value is None:
            return default
        try:
            if isinstance(value, str):
                # Handle currency and whitespace
                cleaned = value.replace('$', '').replace(' ', '').strip()

                # North American format: 1,234.56 (comma=thousands, dot=decimal)
                # Remove commas (thousands separators), keep the dot
                cleaned = cleaned.replace(',', '')

                if cleaned == '' or cleaned == '-':
                    return default

                return float(cleaned)
            return float(value)
        except (ValueError, TypeError):
            return default
