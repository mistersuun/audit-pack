"""
Utility to read RJ Excel file and extract current values.
"""

import xlrd
from datetime import datetime
import io
import logging

logger = logging.getLogger(__name__)


# Configuration constants
JOUR_TOTAL_COLUMNS = 117  # Total number of columns in jour sheet


class RJReader:
    """Read RJ Excel file and extract data."""

    def __init__(self, file_path_or_bytes):
        """
        Initialize with an RJ file.

        Args:
            file_path_or_bytes: Either a file path (str) or file bytes (BytesIO)
        """
        if isinstance(file_path_or_bytes, str):
            self.wb = xlrd.open_workbook(file_path_or_bytes)
        else:
            file_path_or_bytes.seek(0)
            self.wb = xlrd.open_workbook(file_contents=file_path_or_bytes.read())

    def read_controle(self):
        """Read controle sheet (setup info)."""
        sheet = self.wb.sheet_by_name('controle')

        data = {
            'prepare_par': self._get_cell_value(sheet, 1, 1),  # B2
            'jour': self._get_cell_value(sheet, 2, 1),         # B3
            'mois': self._get_cell_value(sheet, 3, 1),         # B4
            'annee': self._get_cell_value(sheet, 4, 1),        # B5
        }

        return data

    def read_dueback(self, day=None):
        """
        Read DueBack sheet.

        Args:
            day: Specific day to read (1-31), or None for all days

        Returns:
            dict with structure:
            {
                'receptionists': [(col_idx, last_name, first_name), ...],
                'days': {
                    1: {'previous': {...}, 'nouveau': {...}},
                    2: {'previous': {...}, 'nouveau': {...}},
                    ...
                }
            }
        """
        sheet = self.wb.sheet_by_name('DUBACK#')

        # Read receptionist names from headers (row 2 & 3)
        # Row 2 = Last Name, Row 3 = First Name
        # Start from col C (index 2) and read all columns until no more names found
        receptionists = []
        for col_idx in range(2, sheet.ncols):  # Start from col C, read all available columns
            last_name = self._get_cell_value(sheet, 1, col_idx)   # Row 2 (index 1)
            first_name = self._get_cell_value(sheet, 2, col_idx)  # Row 3 (index 2)

            if last_name and last_name != '':
                receptionists.append({
                    'col_idx': col_idx,
                    'col_letter': self._col_idx_to_letter(col_idx),
                    'last_name': str(last_name).strip(),
                    'first_name': str(first_name).strip() if first_name else '',
                    'full_name': f"{first_name} {last_name}".strip() if first_name else str(last_name).strip()
                })
            # Continue reading even if one column is empty (in case there are gaps)

        # Read data for each day
        days_data = {}

        start_day = day if day else 1
        end_day = day + 1 if day else 32

        for d in range(start_day, end_day):
            # Calculate row numbers for this day
            row_previous = 2 + (d * 2)      # Previous Due Back (balance_row)
            row_nouveau = row_previous + 1   # Nouveau Due Back (operations_row)

            if row_previous >= sheet.nrows:
                break

            # Read Previous Due Back
            previous = {}
            for recep in receptionists:
                value = self._get_cell_value(sheet, row_previous, recep['col_idx'])
                if value and value != 0:
                    previous[recep['col_letter']] = {
                        'name': recep['full_name'],
                        'amount': value
                    }

            # Read Nouveau Due Back
            nouveau = {}
            for recep in receptionists:
                value = self._get_cell_value(sheet, row_nouveau, recep['col_idx'])
                if value and value != 0:
                    nouveau[recep['col_letter']] = {
                        'name': recep['full_name'],
                        'amount': value
                    }

            # Read RJ column (col B)
            rj_previous = self._get_cell_value(sheet, row_previous, 1)
            rj_nouveau = self._get_cell_value(sheet, row_nouveau, 1)

            days_data[d] = {
                'previous': previous,
                'nouveau': nouveau,
                'rj_previous': rj_previous if rj_previous else 0,
                'rj_nouveau': rj_nouveau if rj_nouveau else 0
            }

        return {
            'receptionists': receptionists,
            'days': days_data
        }

    def read_recap(self):
        """Read RECAP sheet."""
        sheet = self.wb.sheet_by_name('Recap')

        # Structure: Row labels in col A, Lecture in col B, Corr in col C, Net in col D
        data = {
            'date': self._get_cell_value(sheet, 0, 4),  # E1
            'comptant_lightspeed_lecture': self._get_cell_value(sheet, 5, 1),
            'comptant_lightspeed_corr': self._get_cell_value(sheet, 5, 2),
            'comptant_positouch_lecture': self._get_cell_value(sheet, 6, 1),
            'comptant_positouch_corr': self._get_cell_value(sheet, 6, 2),
            'cheque_payment_lecture': self._get_cell_value(sheet, 7, 1),
            'cheque_payment_corr': self._get_cell_value(sheet, 7, 2),
            'remb_gratuite_lecture': self._get_cell_value(sheet, 10, 1),
            'remb_gratuite_corr': self._get_cell_value(sheet, 10, 2),
            'remb_client_lecture': self._get_cell_value(sheet, 11, 1),
            'remb_client_corr': self._get_cell_value(sheet, 11, 2),
            'due_back_reception_lecture': self._get_cell_value(sheet, 15, 1),
            'due_back_reception_corr': self._get_cell_value(sheet, 15, 2),
            'due_back_nb_lecture': self._get_cell_value(sheet, 16, 1),
            'due_back_nb_corr': self._get_cell_value(sheet, 16, 2),
            'surplus_deficit_lecture': self._get_cell_value(sheet, 18, 1),
            'surplus_deficit_corr': self._get_cell_value(sheet, 18, 2),
            'depot_canadien_lecture': self._get_cell_value(sheet, 21, 1),
            'depot_canadien_corr': self._get_cell_value(sheet, 21, 2),
            'prepare_par': self._get_cell_value(sheet, 25, 1),
        }

        return data

    def read_transelect(self):
        """Read TRANSELECT sheet with all fields from TRANSELECT_MAPPING."""
        sheet = self.wb.sheet_by_name('transelect')

        # TRANSELECT_MAPPING defines all cell references
        data = {
            'date': self._get_cell_value(sheet, 4, 1),  # B5
            'prepare_par': self._get_cell_value(sheet, 5, 1),  # B6

            # Section 1: POSitouch
            'bar_701_debit': self._get_cell_value(sheet, 8, 1),  # B9
            'bar_701_visa': self._get_cell_value(sheet, 9, 1),  # B10
            'bar_701_master': self._get_cell_value(sheet, 10, 1),  # B11
            'bar_701_amex': self._get_cell_value(sheet, 12, 1),  # B13

            'bar_702_debit': self._get_cell_value(sheet, 8, 2),  # C9
            'bar_702_visa': self._get_cell_value(sheet, 9, 2),  # C10
            'bar_702_master': self._get_cell_value(sheet, 10, 2),  # C11
            'bar_702_amex': self._get_cell_value(sheet, 12, 2),  # C13

            'bar_703_debit': self._get_cell_value(sheet, 8, 3),  # D9
            'bar_703_visa': self._get_cell_value(sheet, 9, 3),  # D10
            'bar_703_master': self._get_cell_value(sheet, 10, 3),  # D11
            'bar_703_amex': self._get_cell_value(sheet, 12, 3),  # D13

            'spesa_704_debit': self._get_cell_value(sheet, 8, 4),  # E9
            'spesa_704_visa': self._get_cell_value(sheet, 9, 4),  # E10
            'spesa_704_master': self._get_cell_value(sheet, 10, 4),  # E11
            'spesa_704_amex': self._get_cell_value(sheet, 12, 4),  # E13

            'room_705_visa': self._get_cell_value(sheet, 9, 5),  # F10

            # Section 2: Reception/Bank
            'reception_debit': self._get_cell_value(sheet, 19, 3),  # D20 (Terminal K053)
            'reception_debit_term8': self._get_cell_value(sheet, 19, 2),  # C20 (Terminal 8.0)
            'reception_visa_term': self._get_cell_value(sheet, 20, 3),  # D21
            'reception_master_term': self._get_cell_value(sheet, 21, 3),  # D22
            'reception_amex_term': self._get_cell_value(sheet, 23, 3),  # D24

            'fusebox_visa': self._get_cell_value(sheet, 20, 1),  # B21
            'fusebox_master': self._get_cell_value(sheet, 21, 1),  # B22
            'fusebox_amex': self._get_cell_value(sheet, 23, 1),  # B24

            # Quasimodo reconciliation fields
            'quasimodo_debit': self._get_cell_value(sheet, 19, 4),  # E20
            'quasimodo_visa': self._get_cell_value(sheet, 20, 4),   # E21
            'quasimodo_master': self._get_cell_value(sheet, 21, 4), # E22
            'quasimodo_amex': self._get_cell_value(sheet, 23, 4),   # E24
        }

        return data

    def read_geac_ux(self):
        """Read GEAC/UX sheet with all fields from GEAC_UX_MAPPING."""
        sheet = self.wb.sheet_by_name('geac_ux')

        data = {
            'date': self._get_cell_value(sheet, 21, 4),  # E22

            # Daily Cash Out (Row 6)
            'amex_cash_out': self._get_cell_value(sheet, 5, 1),  # B6
            'diners_cash_out': self._get_cell_value(sheet, 5, 4),  # E6
            'master_cash_out': self._get_cell_value(sheet, 5, 6),  # G6
            'visa_cash_out': self._get_cell_value(sheet, 5, 9),  # J6
            'discover_cash_out': self._get_cell_value(sheet, 5, 10),  # K6

            # Total (Row 10)
            'amex_total': self._get_cell_value(sheet, 9, 1),  # B10
            'diners_total': self._get_cell_value(sheet, 9, 4),  # E10
            'master_total': self._get_cell_value(sheet, 9, 6),  # G10
            'visa_total': self._get_cell_value(sheet, 9, 9),  # J10
            'discover_total': self._get_cell_value(sheet, 9, 10),  # K10

            # Daily Revenue (Row 12)
            'amex_daily_revenue': self._get_cell_value(sheet, 11, 1),  # B12
            'diners_daily_revenue': self._get_cell_value(sheet, 11, 4),  # E12
            'master_daily_revenue': self._get_cell_value(sheet, 11, 6),  # G12
            'visa_daily_revenue': self._get_cell_value(sheet, 11, 9),  # J12
            'discover_daily_revenue': self._get_cell_value(sheet, 11, 10),  # K12

            # Balance Previous Day (Row 32)
            'balance_previous': self._get_cell_value(sheet, 31, 1),  # B32
            'balance_previous_guest': self._get_cell_value(sheet, 31, 4),  # E32

            # Balance Today (Row 37)
            'balance_today': self._get_cell_value(sheet, 36, 1),  # B37
            'balance_today_guest': self._get_cell_value(sheet, 36, 4),  # E37

            # Facture Direct (Row 41)
            'facture_direct': self._get_cell_value(sheet, 40, 1),  # B41
            'facture_direct_guest': self._get_cell_value(sheet, 40, 6),  # G41

            # Adv deposit (Row 44)
            'adv_deposit': self._get_cell_value(sheet, 43, 1),  # B44
            'adv_deposit_applied': self._get_cell_value(sheet, 43, 9),  # J44

            # New Balance (Row 53)
            'new_balance': self._get_cell_value(sheet, 52, 1),  # B53
            'new_balance_guest': self._get_cell_value(sheet, 52, 4),  # E53
        }

        return data

    def get_current_audit_day(self):
        """
        Get the current audit day from controle sheet.

        Returns:
            int: Day number from controle B3
        """
        sheet = self.wb.sheet_by_name('controle')
        day_value = self._get_cell_value(sheet, 2, 1)  # B3
        if isinstance(day_value, (int, float)):
            return int(day_value)
        return 0

    def read_jour_day(self, day):
        """
        Read a specific day's row from the jour sheet.

        The jour sheet has day rows starting at row 5 (index 4) for day 1.
        Each row has 117 columns.

        Args:
            day: Day number (1-31)

        Returns:
            dict: Column index (0-based) -> cell value mapping for that day's row
        """
        try:
            sheet = self.wb.sheet_by_name('jour')
        except Exception:
            logger.debug("jour sheet not found when reading jour day data")
            return {}

        # Day 1 = row 5 (index 4), Day 2 = row 6 (index 5), etc.
        row_idx = 4 + (day - 1)

        if row_idx >= sheet.nrows:
            return {}

        # Read all columns for this day's row
        day_data = {}
        for col_idx in range(min(JOUR_TOTAL_COLUMNS, sheet.ncols)):
            value = self._get_cell_value(sheet, row_idx, col_idx)
            if value is not None:
                day_data[col_idx] = value

        return day_data

    def read_setd_day(self, day):
        """
        Read a specific day's row from the SetD sheet.

        Day 1 = row 5 (index 4), and so on.

        Args:
            day: Day number (1-31)

        Returns:
            dict: Column letter (A, B, C, ...) -> cell value mapping for that day's row
        """
        try:
            sheet = self.wb.sheet_by_name('SetD')
        except Exception:
            logger.debug("SetD sheet not found when reading setd day data")
            return {}

        # Day 1 = row 5 (index 4), Day 2 = row 6 (index 5), etc.
        row_idx = 4 + (day - 1)

        if row_idx >= sheet.nrows:
            return {}

        # Read all columns for this day's row, keyed by column letter
        day_data = {}
        for col_idx in range(sheet.ncols):
            value = self._get_cell_value(sheet, row_idx, col_idx)
            if value is not None:
                col_letter = self._col_idx_to_letter(col_idx)
                day_data[col_letter] = value

        return day_data

    def read_transelect_totals(self):
        """
        Read transelect data and calculate totals by card type.

        This convenience method reads transelect and returns totals by card type,
        suitable for Quasimodo integration.

        Returns:
            dict: {
                'visa': sum of all visa fields,
                'mastercard': sum of all mastercard fields,
                'amex': sum of all amex fields,
                'debit': sum of all debit fields,
                'discover': 0  # Not in transelect
            }
        """
        data = self.read_transelect()

        # Section 1: POSitouch fields
        visa_total = (
            self._safe_float(data.get('bar_701_visa')) +
            self._safe_float(data.get('bar_702_visa')) +
            self._safe_float(data.get('bar_703_visa')) +
            self._safe_float(data.get('spesa_704_visa')) +
            self._safe_float(data.get('room_705_visa')) +
            self._safe_float(data.get('reception_visa_term'))
        )

        mastercard_total = (
            self._safe_float(data.get('bar_701_master')) +
            self._safe_float(data.get('bar_702_master')) +
            self._safe_float(data.get('bar_703_master')) +
            self._safe_float(data.get('spesa_704_master')) +
            self._safe_float(data.get('reception_master_term')) +
            self._safe_float(data.get('fusebox_master'))
        )

        amex_total = (
            self._safe_float(data.get('bar_701_amex')) +
            self._safe_float(data.get('bar_702_amex')) +
            self._safe_float(data.get('bar_703_amex')) +
            self._safe_float(data.get('spesa_704_amex')) +
            self._safe_float(data.get('reception_amex_term')) +
            self._safe_float(data.get('fusebox_amex'))
        )

        debit_total = (
            self._safe_float(data.get('bar_701_debit')) +
            self._safe_float(data.get('bar_702_debit')) +
            self._safe_float(data.get('bar_703_debit')) +
            self._safe_float(data.get('spesa_704_debit')) +
            self._safe_float(data.get('reception_debit')) +
            self._safe_float(data.get('reception_debit_term8'))
        )

        return {
            'visa': visa_total,
            'mastercard': mastercard_total,
            'amex': amex_total,
            'debit': debit_total,
            'discover': 0
        }

    def read_geac_cash_out(self):
        """
        Read GEAC/UX Daily Cash Out row and return by card type.

        This convenience method reads just the Daily Cash Out (row 6) from GEAC/UX,
        suitable for Quasimodo integration.

        Returns:
            dict: {
                'visa': amount,
                'mastercard': amount,
                'amex': amount,
                'debit': 0,
                'discover': amount,
                'diners': amount
            }
        """
        data = self.read_geac_ux()

        return {
            'visa': self._safe_float(data.get('visa_cash_out')),
            'mastercard': self._safe_float(data.get('master_cash_out')),
            'amex': self._safe_float(data.get('amex_cash_out')),
            'debit': 0,
            'discover': self._safe_float(data.get('discover_cash_out')),
            'diners': self._safe_float(data.get('diners_cash_out'))
        }

    def read_all(self):
        """Read all important sheets and return complete RJ data."""
        return {
            'controle': self.read_controle(),
            'dueback': self.read_dueback(),
            'recap': self.read_recap(),
            'transelect': self.read_transelect(),
            'geac_ux': self.read_geac_ux(),
        }

    def _safe_float(self, value):
        """
        Safely convert a value to float, returning 0 if conversion fails.

        Args:
            value: Value to convert (None, str, int, float, etc.)

        Returns:
            float: Converted value or 0 if conversion fails
        """
        if value is None:
            return 0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    def _get_cell_value(self, sheet, row_idx, col_idx):
        """Get cell value safely."""
        try:
            if row_idx < sheet.nrows and col_idx < sheet.ncols:
                cell = sheet.cell(row_idx, col_idx)
                value = cell.value

                # Convert empty strings to None
                if value == '':
                    return None

                return value
            return None
        except Exception:
            logger.debug(f"Error reading cell at row {row_idx}, col {col_idx}")
            return None

    def _col_idx_to_letter(self, col_idx):
        """Convert column index to letter (0 -> A, 1 -> B, etc.)."""
        result = ''
        while col_idx >= 0:
            result = chr(65 + (col_idx % 26)) + result
            col_idx = col_idx // 26 - 1
        return result

    def read_sheet_range(self, sheet_name, start_row=0, end_row=None, start_col=0, end_col=None):
        """
        Read a range of cells from a sheet for live preview.
        
        Args:
            sheet_name: Name of the sheet to read
            start_row: Starting row index (0-based, default 0)
            end_row: Ending row index (0-based, None = all rows)
            start_col: Starting column index (0-based, default 0)
            end_col: Ending column index (0-based, None = all columns)
        
        Returns:
            dict with:
            {
                'sheet_name': sheet_name,
                'rows': [[cell_value, ...], ...],
                'nrows': number of rows,
                'ncols': number of columns
            }
        """
        try:
            sheet = self.wb.sheet_by_name(sheet_name)
        except xlrd.biffh.XLRDError:
            return {
                'sheet_name': sheet_name,
                'rows': [],
                'nrows': 0,
                'ncols': 0,
                'error': f'Sheet "{sheet_name}" not found'
            }
        
        # Determine actual range
        actual_end_row = end_row if end_row is not None else sheet.nrows
        actual_end_col = end_col if end_col is not None else sheet.ncols
        
        # Limit to sheet bounds
        actual_end_row = min(actual_end_row, sheet.nrows)
        actual_end_col = min(actual_end_col, sheet.ncols)
        
        # Read cells
        rows = []
        for row_idx in range(start_row, actual_end_row):
            row_data = []
            for col_idx in range(start_col, actual_end_col):
                value = self._get_cell_value(sheet, row_idx, col_idx)
                # Format value for display
                if value is None:
                    row_data.append('')
                elif isinstance(value, float) and value == int(value):
                    row_data.append(int(value))
                else:
                    row_data.append(value)
            rows.append(row_data)
        
        return {
            'sheet_name': sheet_name,
            'rows': rows,
            'nrows': len(rows),
            'ncols': actual_end_col - start_col if rows else 0
        }
    
    def get_available_sheets(self):
        """Get list of all available sheet names."""
        return self.wb.sheet_names()

    def get_dueback_day_total(self, day):
        """
        Get the total from column Z for a specific day in DueBack sheet.

        Args:
            day: Day number (1-31)

        Returns:
            float: Total value from column Z balance_row

        Note:
            The Total Z is stored in the balance_row (first row of each day),
            NOT in the operations_row (second row).
        """
        from utils.rj_mapper import get_dueback_row_for_day

        try:
            sheet = self.wb.sheet_by_name('DUBACK#')
        except Exception:
            logger.debug("DUBACK# sheet not found when reading dueback day total")
            return 0.0

        # Get balance_row (contains Total Z)
        balance_row, _ = get_dueback_row_for_day(day)

        # Column Z is index 25
        Z_COL = 25

        # Get total value
        total = self._get_cell_value(sheet, balance_row, Z_COL)

        # Return numeric value or 0
        if isinstance(total, (int, float)):
            return float(total)

        return 0.0

    def get_dueback_column_b(self, day):
        """
        Get Column B values (R/J) for a specific day in DueBack sheet.

        Column B contains a reference to the 'jour' sheet (=+jour!BY[row])
        and is READ-ONLY - it cannot be calculated from receptionist entries.

        Args:
            day: Day number (1-31)

        Returns:
            dict: {
                'previous': float,  # Balance row (Previous DueBack)
                'current': float,   # Operations row (Current DueBack)
                'net': float        # Previous + Current
            }
        """
        from utils.rj_mapper import get_dueback_row_for_day

        try:
            sheet = self.wb.sheet_by_name('DUBACK#')
        except Exception:
            logger.debug("DUBACK# sheet not found when reading dueback column B")
            return {'previous': 0.0, 'current': 0.0, 'net': 0.0}

        # Get both rows for this day
        balance_row, operations_row = get_dueback_row_for_day(day)

        # Column B is index 1
        B_COL = 1

        # Get both values
        previous = self._get_cell_value(sheet, balance_row, B_COL)
        current = self._get_cell_value(sheet, operations_row, B_COL)

        # Convert to numeric
        previous_val = float(previous) if isinstance(previous, (int, float)) else 0.0
        current_val = float(current) if isinstance(current, (int, float)) else 0.0

        return {
            'previous': previous_val,
            'current': current_val,
            'net': previous_val + current_val
        }
