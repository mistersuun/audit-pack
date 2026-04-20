"""DBRS auto-fill and Master DBR paste utility.

Fills the DBRS staging workbook from parsed Daily Revenue and Market Segment data,
then copies the computed DBRS Insertion values into the corporate Master DBR file.

Uses pywin32 Excel COM — Windows only, requires Excel installed.
See docs/RJ_AUTOFILL_MASTER.md section 14 for full spec.
"""

import os
from datetime import datetime


class DBRSFiller:
    """Fill DBRS staging workbook and paste into Master DBR."""

    DBRS_PATH = r'K:\DBRS\DBRS_formule.2025_corriger.xlsm'
    MASTER_PATHS = [
        r'K:\Audition\04 - April\2026DBR MasterSheraton.xls',
        r'Y:\2026DBR MasterSheraton.xls',
    ]

    # DailyRev tab row mapping: row -> DR page 1 room charge label.
    # Rows 2-40 map to DR p.1 room charge lines (all must be filled, even zeros).
    # Row 44 = Room Charge + Allowance (from DR p.1).
    # Row 47 = G4 / Club Lounge deduction (user-provided).
    # DBRS formulas reference: R44-R47 for ALLOWANCE, R28+R31 for OTHER,
    # R29+R38 for NO SHOWS, R27+R26 for EARLY DEP/LATE DEP.
    DAILYREV_ROWS = {
        # Rows 2-30: Main room charge categories
        2: 'Room Chrg - Premium',
        3: 'Room Chrg - Standard',
        4: 'Room Chrg - eChannel',
        5: 'Room Chrg - Special',
        6: 'Room Chrg - Wholesal',
        7: 'Room Chrg - Govt./Mi',
        8: 'Room Chrg - Weekend',
        9: 'Room Chrg - AAA',
        10: 'Room Chrg - Packages',
        11: 'Room Chrg - Advance',
        12: 'Room Chrg - Senior D',
        13: 'Room Chrg - Associat',
        14: 'Rm Chrg - Reward Red',
        15: 'Room Chrg - Other Di',
        16: 'Room Chrg - Complime',
        17: 'Room Chrg - GRP OTH',
        18: 'Room Chrg - GRP - Co',
        19: 'Room Chrg - GRP - As',
        20: 'Room Chrg - GRP Tour',
        21: 'Room Chrg - GRP - Go',
        22: 'Room Charge OPEN',
        23: 'Room Chrg - Contract',
        24: 'Room Chrg Opaque',
        25: 'Room Chrg SVO Tours',
        26: 'Early Departure Fee',
        27: 'Late Checkout Fee',
        28: 'Reservation/Cancella',
        29: 'Guaranteed No Show',
        30: 'Day Use Room Charge',
        # Rows 31-40: Additional room categories (CRITICAL for DBRS formulas)
        31: 'Cancellation Fee-Tra',
        32: 'Room Chrg - GRP Asso',
        33: 'Resort Service Fee',
        34: 'Package',
        35: 'Room Charge HOLD FOR',
        36: 'Other Room Charges',
        37: 'Loyalty Redemption O',
        38: 'Guaranteed No Show-C',
        39: 'Attrition',
        40: 'NA',
    }

    # Special DailyRev rows NOT from standard room charge list
    # Row 44: Room Charge + Allowance (DR p.1 "Room Charge + Allowa" Today value)
    # Row 47: G4 / Club Lounge deduction (user-provided, same as Jour AK deduction)
    DAILYREV_SPECIAL_ROWS = {
        44: 'Room Charge + Allowa',  # DR p.1
        47: '_G4_CLUB_LOUNGE',       # User-provided G4 value
    }

    # Market Segment tab row mapping: row -> segment code prefix.
    # Only data rows are listed — subtotal/formula rows are intentionally absent.
    # The HasFormula guard in fill_dbrs_staging provides a runtime safety net,
    # but skipping those rows here is the primary defense.
    MARKET_SEGMENT_ROWS = {
        3: '* NOT SPECIFIED',
        5: 'T10',
        8: 'T11',
        9: 'T12',
        12: 'T14',
        13: 'T15',
        14: 'T16',
        17: 'T17',
        18: 'T18',
        21: 'T19',
        22: 'T23',
        23: 'T20',
        24: 'T22',
        25: 'T21',
        26: 'T24',
        29: 'T25',
        32: 'T27',
        33: 'T28',
        36: 'T29',
        37: 'T30',
        38: 'T33',
        39: 'T34',
        42: 'T35',
        43: 'T40',
        44: 'T41',
        45: 'T42',
        48: 'T43',
        51: 'T44',
        52: 'T90',
        55: 'W26',
        58: 'W50',
        59: 'GC',
        62: 'T62',
        65: 'T38',
        68: 'W58',
        71: 'GG',
        72: 'GN',
        73: 'GO',
        74: 'GP',
        75: 'GS',
        76: 'GT',
        79: 'T31',
        80: 'T37',
        83: 'W51',
        84: 'W55',
        85: 'W59',
        88: 'T26',
        89: 'T36',
        90: 'T39',
        91: 'T32',
    }

    def __init__(self):
        self.excel = None

    def _start_excel(self):
        """Start Excel COM application."""
        import win32com.client as win32
        self.excel = win32.Dispatch('Excel.Application')
        self.excel.Visible = False
        self.excel.DisplayAlerts = False
        self.excel.AskToUpdateLinks = False

    def _quit_excel(self):
        """Quit Excel COM application."""
        if self.excel:
            self.excel.Quit()
            self.excel = None

    def fill_dbrs_staging(self, dr_room_charges, ms_rooms_by_segment, g4=0):
        """Fill the DBRS staging workbook with parsed data.

        Args:
            dr_room_charges: dict mapping room charge labels to Today values
                e.g. {'Room Chrg - Premium': 2690.0, 'Room Chrg - Standard': 7406.88, ...}
            ms_rooms_by_segment: dict mapping segment codes to Rooms count today
                e.g. {'T10': 5, 'T12': 22, 'T17': 29, 'GC': 100, ...}
            g4: Club Lounge / accommodation production deduction (user-provided).
                Goes to DailyRev row 47. Used by DBRS ALLOWANCE formula (R81 = R44 - R47).

        Returns:
            dict with 'dbrs_insertion' key containing B2:B89 computed values
            as {row: value} for all non-zero non-None rows.
        """
        self._start_excel()
        try:
            wb = self.excel.Workbooks.Open(self.DBRS_PATH)

            # Fill DailyRev tab — col B, rows 2-40 (all room charge categories)
            ws_dr = wb.Sheets('DailyRev')
            for row, label in self.DAILYREV_ROWS.items():
                value = dr_room_charges.get(label, 0)
                ws_dr.Cells(row, 2).Value = value  # Column B

            # Fill special DailyRev rows (44 = Allowance, 47 = G4)
            # Row 44: Room Charge + Allowance from DR p.1
            ws_dr.Cells(44, 2).Value = dr_room_charges.get('Room Charge + Allowa', 0)
            # Row 47: G4 / Club Lounge (user-provided)
            ws_dr.Cells(47, 2).Value = g4

            # Fill Market Segment tab — col B, data rows only.
            # HasFormula guard is a runtime safety net in case row numbering
            # shifts in a future version of the workbook.
            ws_ms = wb.Sheets('Market Segment')
            for row, code in self.MARKET_SEGMENT_ROWS.items():
                value = ms_rooms_by_segment.get(code, 0)
                cell = ws_ms.Cells(row, 2)
                if not cell.HasFormula:
                    cell.Value = value

            # Force full recalculation before reading output
            self.excel.Calculate()

            # Read DBRS Insertion B2:B89 — skip None and zero
            ws_ins = wb.Sheets('DBRS Insertion')
            insertion_values = {}
            for r in range(2, 90):
                val = ws_ins.Cells(r, 2).Value
                if val is not None and val != 0:
                    insertion_values[r] = val

            wb.Save()
            wb.Close()

            return {'dbrs_insertion': insertion_values}

        finally:
            self._quit_excel()

    def paste_to_master(self, audit_date, insertion_values, master_path=None):
        """Paste DBRS Insertion values into the Master DBR file.

        Implements the "Paste Special → Values + Skip blanks" step described in
        section 14.6 of docs/RJ_AUTOFILL_MASTER.md.  Formula cells (ADR rows,
        SUBTOTAL rows) are left untouched by the HasFormula guard.

        Args:
            audit_date: datetime.date for the audit night
            insertion_values: dict {row: value} from fill_dbrs_staging
            master_path: explicit path to master file; auto-detected if None

        Returns:
            dict with 'month_tab', 'day_column', 'rows_written' keys.
        """
        if master_path is None:
            for path in self.MASTER_PATHS:
                if os.path.exists(path):
                    master_path = path
                    break
            if master_path is None:
                raise FileNotFoundError(
                    'Master DBR file not found. '
                    f'Tried: {self.MASTER_PATHS}'
                )

        month_names = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
        ]
        month_tab = month_names[audit_date.month - 1]
        # Day column: day 1 = col B (2), day 2 = col C (3), ... day N = col N+1
        day_col = audit_date.day + 1

        self._start_excel()
        try:
            wb = self.excel.Workbooks.Open(master_path)

            # Update Setup date (F8)
            ws_setup = wb.Sheets('Setup')
            ws_setup.Cells(8, 6).Value = audit_date

            # Paste into month tab — DBRS Insertion row N → month tab row N+96.
            # HasFormula guard preserves ADR formulas and SUBTOTAL rows,
            # matching the manual "Paste Special → Values + Skip blanks" behaviour.
            ws_month = wb.Sheets(month_tab)
            for ins_row, value in insertion_values.items():
                target_row = ins_row + 96
                cell = ws_month.Cells(target_row, day_col)
                if not cell.HasFormula:
                    cell.Value = value

            self.excel.Calculate()
            wb.Save()
            wb.Close()

            return {
                'month_tab': month_tab,
                'day_column': day_col,
                'rows_written': len(insertion_values),
            }

        finally:
            self._quit_excel()

    def fill_and_paste(self, audit_date, dr_room_charges, ms_rooms_by_segment, g4=0, master_path=None):
        """Full workflow: fill DBRS staging, then paste into Master.

        Args:
            audit_date: datetime.date
            dr_room_charges: dict of room charge label -> Today value
            ms_rooms_by_segment: dict of segment code -> Rooms today
            g4: Club Lounge deduction (user-provided)
            master_path: optional explicit path to Master DBR file

        Returns:
            dict with 'staging' and 'paste' sub-dicts.
        """
        staging_result = self.fill_dbrs_staging(dr_room_charges, ms_rooms_by_segment, g4=g4)
        paste_result = self.paste_to_master(
            audit_date,
            staging_result['dbrs_insertion'],
            master_path,
        )
        return {
            'staging': staging_result,
            'paste': paste_result,
        }
