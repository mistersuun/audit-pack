"""
Market Segment Production PDF Parser for Galaxy Lightspeed PMS.

Extracts market segment data from the "Market Segment Production" report (mktsegprd),
which provides TODAY and MTD totals, plus breakdown by market segment categories.

The report format includes:
- Pages 1-2: TODAY and MTD columns
- Pages 3-4: YTD and MTD Budget columns
- Pages 5-6: Summary sections
- Last page: Grand total line

Market segment codes:
- T-codes (T10, T12, etc.): Transient
- G-codes (G10, G20, etc.): Group
- W-codes (W10, W20, etc.) + W50: Contract
"""

import re
import io
from datetime import datetime
from utils.parsers.base_parser import BaseParser


class MarketSegmentParser(BaseParser):
    """
    Parse Market Segment Production PDF from Galaxy Lightspeed PMS.

    Extracts TODAY and MTD totals, plus market segment breakdown by category
    (transient, group, contract) for DBRS tab auto-fill.
    """

    FIELD_MAPPINGS = {
        # TODAY totals
        'today_guests': 'dbrs_house_count',
        'today_rooms': 'dbrs_rooms_sold',
        'today_revenue': 'dbrs_daily_rev_today',
        'today_avg_rate': 'dbrs_adr',
        'today_occupancy': 'dbrs_occupancy',

        # MTD totals
        'mtd_guests': 'dbrs_mtd_guests',
        'mtd_rooms': 'dbrs_mtd_rooms',
        'mtd_revenue': 'dbrs_mtd_revenue',
        'mtd_avg_rate': 'dbrs_mtd_adr',
        'mtd_occupancy': 'dbrs_mtd_occupancy',

        # Market segment breakdown (TODAY)
        'transient_rooms': 'dbrs_seg_transient_rooms',
        'transient_revenue': 'dbrs_seg_transient_revenue',
        'group_rooms': 'dbrs_seg_group_rooms',
        'group_revenue': 'dbrs_seg_group_revenue',
        'contract_rooms': 'dbrs_seg_contract_rooms',
        'contract_revenue': 'dbrs_seg_contract_revenue',
    }

    def __init__(self, file_bytes, filename=None):
        super().__init__(file_bytes, filename)
        self.raw_text = None
        self.segments = []

    def parse(self):
        """Parse the Market Segment Production PDF."""
        try:
            import pdfplumber
        except ImportError:
            self.validation_errors.append("pdfplumber not installed")
            self._parsed = True
            return

        try:
            with pdfplumber.open(io.BytesIO(self.file_bytes)) as pdf:
                # Extract text from all pages
                all_text = ""
                for page in pdf.pages:
                    all_text += page.extract_text() + "\n"

                self.raw_text = all_text
                self._extract_metadata()
                self._parse_segments()
                self._extract_totals()
                self._categorize_segments()
                self._compute_dbrs_mapping()

                self.confidence = 0.92
                self._parsed = True

        except Exception as e:
            self.validation_errors.append(f"PDF parsing failed: {str(e)}")
            self.confidence = 0.0
            self._parsed = True

    def _extract_metadata(self):
        """Extract report date, auditor, and property name."""
        # Pattern: "Sheraton Laval YULLS Market Segment Production"
        property_match = re.search(r'(Sheraton\s+[A-Za-z\s]+YULLS)', self.raw_text)
        if property_match:
            self.extracted_data['property'] = property_match.group(1).strip()

        # Pattern: "Souleymane Camara Ordered by Market Segment Order 25-FEB-2026"
        auditor_match = re.search(r'^([A-Za-z\s]+)\s+Ordered\s+by', self.raw_text, re.MULTILINE)
        if auditor_match:
            self.extracted_data['auditor'] = auditor_match.group(1).strip()

        # Pattern: "For 24-FEB-2026"
        date_match = re.search(r'For\s+(\d{2}-[A-Z]{3}-\d{4})', self.raw_text)
        if date_match:
            self.extracted_data['report_date'] = date_match.group(1)

    def _parse_segments(self):
        """Parse individual market segment lines from the TODAY section only."""
        # Extract only the first section (TODAY + MTD columns, before YTD columns)
        # This is roughly from "Market Segment Guests Rooms..." to "* TOTAL"
        # We look for the first page headers ending before the YTD section starts

        # Find the first TODAY section - from "TODAY" header to the first "* TOTAL" line
        today_section_match = re.search(
            r'-----\s+TODAY\s+.*?\n(.*?)\*\s+TOTAL',
            self.raw_text,
            re.DOTALL
        )

        if not today_section_match:
            return

        today_section = today_section_match.group(1)

        # Pattern for segment lines:
        # T10 Premium Reta 4 4 2482.21 620.55 1.59 184 135 71068.79 526.44 2.23
        # GC Corporate Gr 85 85 20940.87 246.36 33.73 1576 1406 362013.91 257.48 23.25
        # Columns: Code Name Guests Rooms Revenue AvgRate %Occup Guests(MTD) Rooms(MTD) Revenue(MTD) AvgRate(MTD) %Occup(MTD)
        # Codes can be: T##, W##, or GX (2-letter group codes like GC, GG, GN, GO, GP, GS, GT)
        segment_pattern = r'([A-Z]{1,2}\d{0,2})\s+([A-Za-z\s/\-]+?)\s+(\d+)\s+(\d+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+(\d+)\s+(\d+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})'

        for match in re.finditer(segment_pattern, today_section):
            segment = {
                'code': match.group(1),
                'name': match.group(2).strip(),
                'today_guests': int(match.group(3)),
                'today_rooms': int(match.group(4)),
                'today_revenue': self._safe_float(match.group(5)),
                'today_avg_rate': self._safe_float(match.group(6)),
                'today_occupancy': self._safe_float(match.group(7)),
                'mtd_guests': int(match.group(8)),
                'mtd_rooms': int(match.group(9)),
                'mtd_revenue': self._safe_float(match.group(10)),
                'mtd_avg_rate': self._safe_float(match.group(11)),
                'mtd_occupancy': self._safe_float(match.group(12)),
            }
            self.segments.append(segment)

    def _extract_totals(self):
        """Extract grand totals from the first page (TODAY and MTD summary line)."""
        # Pattern: "* TOTAL 262 247 63280.73 256.20 98.02 6639 5077 1294861.38 255.04 83.95"
        # The line format is: * TOTAL [today_guests] [today_rooms] [today_revenue] [today_avg_rate] [today_occupancy] [mtd_guests] [mtd_rooms] [mtd_revenue] [mtd_avg_rate] [mtd_occupancy]
        total_pattern = r'\*\s+TOTAL\s+(\d+)\s+(-?\d+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+(\d+)\s+(\d+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})'

        match = re.search(total_pattern, self.raw_text)
        if match:
            self.extracted_data['today_guests'] = int(match.group(1))
            self.extracted_data['today_rooms'] = int(match.group(2))
            self.extracted_data['today_revenue'] = self._safe_float(match.group(3))
            self.extracted_data['today_avg_rate'] = self._safe_float(match.group(4))
            self.extracted_data['today_occupancy'] = self._safe_float(match.group(5))
            self.extracted_data['mtd_guests'] = int(match.group(6))
            self.extracted_data['mtd_rooms'] = int(match.group(7))
            self.extracted_data['mtd_revenue'] = self._safe_float(match.group(8))
            self.extracted_data['mtd_avg_rate'] = self._safe_float(match.group(9))
            self.extracted_data['mtd_occupancy'] = self._safe_float(match.group(10))
        else:
            # Fallback: calculate from segments (should not happen with proper PDF)
            self._calculate_totals_from_segments()

    def _calculate_totals_from_segments(self):
        """Calculate totals by summing all segment values."""
        if not self.segments:
            return

        today_guests = sum(seg['today_guests'] for seg in self.segments)
        today_rooms = sum(seg['today_rooms'] for seg in self.segments)
        today_revenue = sum(seg['today_revenue'] for seg in self.segments)
        mtd_guests = sum(seg['mtd_guests'] for seg in self.segments)
        mtd_rooms = sum(seg['mtd_rooms'] for seg in self.segments)
        mtd_revenue = sum(seg['mtd_revenue'] for seg in self.segments)

        self.extracted_data['today_guests'] = today_guests
        self.extracted_data['today_rooms'] = today_rooms
        self.extracted_data['today_revenue'] = round(today_revenue, 2)
        self.extracted_data['mtd_guests'] = mtd_guests
        self.extracted_data['mtd_rooms'] = mtd_rooms
        self.extracted_data['mtd_revenue'] = round(mtd_revenue, 2)

        # Calculate average rates
        if today_rooms > 0:
            self.extracted_data['today_avg_rate'] = round(
                today_revenue / today_rooms, 2
            )
        if mtd_rooms > 0:
            self.extracted_data['mtd_avg_rate'] = round(
                mtd_revenue / mtd_rooms, 2
            )

    def _categorize_segments(self):
        """Categorize segments by type: transient (T), group (G), contract (W)."""
        transient_rooms = 0
        transient_revenue = 0.0
        group_rooms = 0
        group_revenue = 0.0
        contract_rooms = 0
        contract_revenue = 0.0

        for seg in self.segments:
            code = seg['code']
            code_letter = code[0]

            if code_letter == 'T':
                # Transient segment
                transient_rooms += seg['today_rooms']
                transient_revenue += seg['today_revenue']
            elif code_letter == 'G':
                # Group segment
                group_rooms += seg['today_rooms']
                group_revenue += seg['today_revenue']
            elif code_letter == 'W':
                # Contract segment (all W codes including W50)
                contract_rooms += seg['today_rooms']
                contract_revenue += seg['today_revenue']

        self.extracted_data['transient_rooms'] = transient_rooms
        self.extracted_data['transient_revenue'] = round(transient_revenue, 2)
        self.extracted_data['group_rooms'] = group_rooms
        self.extracted_data['group_revenue'] = round(group_revenue, 2)
        self.extracted_data['contract_rooms'] = contract_rooms
        self.extracted_data['contract_revenue'] = round(contract_revenue, 2)

    def _compute_dbrs_mapping(self):
        """Compute DBRS-specific mappings."""
        dbrs_mapping = {
            # TODAY totals
            'today_guests': self.extracted_data.get('today_guests', 0),
            'today_rooms': self.extracted_data.get('today_rooms', 0),
            'today_revenue': self.extracted_data.get('today_revenue', 0.0),
            'today_avg_rate': self.extracted_data.get('today_avg_rate', 0.0),
            'today_occupancy': self.extracted_data.get('today_occupancy', 0.0),

            # MTD totals
            'mtd_guests': self.extracted_data.get('mtd_guests', 0),
            'mtd_rooms': self.extracted_data.get('mtd_rooms', 0),
            'mtd_revenue': self.extracted_data.get('mtd_revenue', 0.0),
            'mtd_avg_rate': self.extracted_data.get('mtd_avg_rate', 0.0),
            'mtd_occupancy': self.extracted_data.get('mtd_occupancy', 0.0),

            # Market segment breakdown
            'transient_rooms': self.extracted_data.get('transient_rooms', 0),
            'transient_revenue': self.extracted_data.get('transient_revenue', 0.0),
            'group_rooms': self.extracted_data.get('group_rooms', 0),
            'group_revenue': self.extracted_data.get('group_revenue', 0.0),
            'contract_rooms': self.extracted_data.get('contract_rooms', 0),
            'contract_revenue': self.extracted_data.get('contract_revenue', 0.0),
        }

        self.extracted_data['dbrs_mapping'] = dbrs_mapping

    def validate(self):
        """Validate extracted data."""
        if not self.extracted_data:
            self.validation_errors.append("No data extracted from PDF")
            return False

        # Check critical fields exist
        required_fields = [
            'today_guests', 'today_rooms', 'today_revenue',
            'mtd_guests', 'mtd_rooms', 'mtd_revenue'
        ]
        for field in required_fields:
            if field not in self.extracted_data:
                self.validation_warnings.append(f"Missing field: {field}")

        # Validate basic sanity checks
        if self.extracted_data.get('today_guests', 0) < 0:
            self.validation_warnings.append(
                "Today guests count is negative"
            )

        if self.extracted_data.get('today_rooms', 0) < 0:
            self.validation_warnings.append(
                "Today rooms count is negative"
            )

        if self.extracted_data.get('today_revenue', 0.0) < 0:
            self.validation_warnings.append(
                "Today revenue is negative"
            )

        # Validate segment totals don't exceed grand total
        segment_total_rooms = (
            self.extracted_data.get('transient_rooms', 0) +
            self.extracted_data.get('group_rooms', 0) +
            self.extracted_data.get('contract_rooms', 0)
        )
        if segment_total_rooms > self.extracted_data.get('today_rooms', 0):
            self.validation_warnings.append(
                f"Segment rooms ({segment_total_rooms}) exceed today rooms "
                f"({self.extracted_data.get('today_rooms', 0)})"
            )

        return len(self.validation_errors) == 0
