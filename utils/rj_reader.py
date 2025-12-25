"""
Utility to read RJ Excel file and extract current values.
"""

import xlrd
from datetime import datetime
import io


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
            row_previous = 3 + (d * 2)      # Previous Due Back
            row_nouveau = row_previous + 1   # Nouveau Due Back

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
        """Read TRANSELECT sheet."""
        sheet = self.wb.sheet_by_name('transelect')

        data = {
            'date': self._get_cell_value(sheet, 4, 1),  # B5
            'prepare_par': self._get_cell_value(sheet, 5, 1),  # B6

            # BAR 701-703, SPESA 704, ROOM 705
            'bar_701_debit': self._get_cell_value(sheet, 8, 1),
            'bar_701_visa': self._get_cell_value(sheet, 9, 1),
            'bar_701_master': self._get_cell_value(sheet, 10, 1),
            'bar_701_amex': self._get_cell_value(sheet, 12, 1),

            # Add more fields as needed...
        }

        return data

    def read_geac_ux(self):
        """Read GEAC/UX sheet."""
        sheet = self.wb.sheet_by_name('geac_ux')

        data = {
            'date': self._get_cell_value(sheet, 21, 4),  # E22
            'amex_cash_out': self._get_cell_value(sheet, 5, 1),  # B6
            'master_cash_out': self._get_cell_value(sheet, 5, 6),  # G6
            'visa_cash_out': self._get_cell_value(sheet, 5, 9),  # J6

            # Add more fields as needed...
        }

        return data

    def read_all(self):
        """Read all important sheets and return complete RJ data."""
        return {
            'controle': self.read_controle(),
            'dueback': self.read_dueback(),
            'recap': self.read_recap(),
            'transelect': self.read_transelect(),
            'geac_ux': self.read_geac_ux(),
        }

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
            return None

    def _col_idx_to_letter(self, col_idx):
        """Convert column index to letter (0 -> A, 1 -> B, etc.)."""
        result = ''
        while col_idx >= 0:
            result = chr(65 + (col_idx % 26)) + result
            col_idx = col_idx // 26 - 1
        return result
