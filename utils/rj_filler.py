"""
Utility to fill RJ Excel file with form data.
"""

import xlrd
from xlrd import open_workbook
from xlutils.copy import copy as copy_workbook
import io
from datetime import datetime
import logging
from utils.rj_mapper import (
    CELL_MAPPINGS,
    DUEBACK_RECEPTIONIST_COLUMNS,
    RESET_RANGES,
    DUBACK_TO_SETD_MAPPING,
    get_dueback_row_for_day,
    get_setd_row_for_day,
    JOUR_DAY_ROW_OFFSET,
    JOUR_RECAP_COLS,
    JOUR_RECAP_SOURCE,
    JOUR_CC_START_COL,
    JOUR_CC_SOURCE,
    get_jour_row_for_day,
)

logger = logging.getLogger(__name__)


# Configuration constants
MAX_DEPOSIT_ROWS = 200          # Maximum rows to search in depot sheet
DEPOT_HEADER_ROW = 1            # First data row in depot (0-indexed, after header)
DEFAULT_FILENAME = 'RJ.xls'     # Default RJ filename
UUID_LENGTH = 12                # Length of session ID substring


def excel_col_to_index(col_str):
    """Convert Excel column (e.g., 'A', 'B', 'AA') to 0-based index."""
    result = 0
    for char in col_str:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def excel_cell_to_indices(cell_str):
    """Convert Excel cell (e.g., 'B6', 'AA10') to (row_idx, col_idx)."""
    # Extract column letters and row number
    col = ''
    row = ''
    for char in cell_str:
        if char.isalpha():
            col += char
        else:
            row += char

    row_idx = int(row) - 1  # 0-based
    col_idx = excel_col_to_index(col)

    return row_idx, col_idx


class RJFiller:
    """Fill RJ Excel file with form data."""

    def __init__(self, file_path_or_bytes):
        """
        Initialize with an RJ file.

        Args:
            file_path_or_bytes: Either a file path (str) or file bytes (BytesIO)
        """
        if isinstance(file_path_or_bytes, str):
            self.rb = open_workbook(file_path_or_bytes, formatting_info=True)
        else:
            self.rb = open_workbook(file_contents=file_path_or_bytes.read(), formatting_info=True)

        self.wb = copy_workbook(self.rb)

        # Build sheet name → index cache for fast lookups
        self._sheet_index_cache = {}
        for idx in range(len(self._get_worksheets())):
            name = self.wb.get_sheet(idx).name
            self._sheet_index_cache[name] = idx

    def _get_worksheets(self):
        """
        Get the list of worksheets from the xlwt workbook.

        Encapsulates access to the private _Workbook__worksheets attribute
        for maintainability. If xlwt changes its internal structure, only
        this method needs updating.

        Returns:
            List of worksheet objects from the xlwt workbook.

        Raises:
            AttributeError: If xlwt's internal structure is incompatible.
        """
        try:
            # xlwt stores worksheets in a name-mangled private attribute
            # Access via _Workbook__worksheets (Python name mangling for __worksheets)
            return self.wb._Workbook__worksheets
        except AttributeError:
            # Fallback: try common alternative attribute names
            for attr in ('_worksheets', 'worksheets', '_sheets', 'sheets'):
                if hasattr(self.wb, attr):
                    return getattr(self.wb, attr)
            raise AttributeError(
                "Cannot access xlwt Workbook worksheets. "
                "xlwt version may be incompatible or internal structure has changed."
            )

    def _get_sheet_by_name(self, sheet_name):
        """
        Get a writable sheet by name from the xlwt workbook.

        xlwt's get_sheet() only accepts integer indices, not names.
        This helper resolves the name to an index first.

        Args:
            sheet_name: Name of the sheet (e.g., 'Recap', 'DUBACK#', 'jour')

        Returns:
            xlwt Sheet object

        Raises:
            ValueError: If sheet not found
        """
        if sheet_name in self._sheet_index_cache:
            return self.wb.get_sheet(self._sheet_index_cache[sheet_name])

        # Fallback: scan sheets (in case cache is stale)
        for idx in range(len(self._get_worksheets())):
            if self.wb.get_sheet(idx).name == sheet_name:
                self._sheet_index_cache[sheet_name] = idx
                return self.wb.get_sheet(idx)

        raise ValueError(f"Sheet '{sheet_name}' not found in workbook. "
                         f"Available: {list(self._sheet_index_cache.keys())}")


    def reset_tabs(self):
        """
        Clear specific ranges in Recap, transelect, and geac_ux sheets.

        Returns:
            Number of cells cleared.
        """
        cells_cleared = 0

        for sheet_name, ranges in RESET_RANGES.items():
            try:
                try:
                    sheet = self._get_sheet_by_name(sheet_name)
                except ValueError:
                    logger.warning(f"Sheet {sheet_name} not found for reset.")
                    continue
                
                for rng in ranges:
                    row_start = rng.get('row') if 'row' in rng else rng.get('row_start')
                    row_end = rng.get('row') + 1 if 'row' in rng else rng.get('row_end', row_start + 1)
                    
                    col_start = rng.get('col') if 'col' in rng else rng.get('col_start')
                    col_end = rng.get('col') + 1 if 'col' in rng else rng.get('col_end', col_start + 1)
                    
                    for r in range(row_start, row_end):
                        for c in range(col_start, col_end):
                            sheet.write(r, c, None) # Write None/Empty
                            cells_cleared += 1
                            
            except Exception as e:
                logger.error(f"Error resetting tab {sheet_name}: {e}")
                
        return cells_cleared

    def reset_single_tab(self, sheet_name):
        """
        Clear specific ranges in a single sheet.

        Args:
            sheet_name: Name of the sheet to reset ('Recap', 'transelect', 'geac_ux', 'depot')

        Returns:
            Number of cells cleared.
        """
        if sheet_name not in RESET_RANGES:
            raise ValueError(f"Unknown sheet name for reset: {sheet_name}")

        cells_cleared = 0
        ranges = RESET_RANGES[sheet_name]

        try:
            sheet = self._get_sheet_by_name(sheet_name)

            for rng in ranges:
                row_start = rng.get('row') if 'row' in rng else rng.get('row_start')
                row_end = rng.get('row') + 1 if 'row' in rng else rng.get('row_end', row_start + 1)

                col_start = rng.get('col') if 'col' in rng else rng.get('col_start')
                col_end = rng.get('col') + 1 if 'col' in rng else rng.get('col_end', col_start + 1)

                for r in range(row_start, row_end):
                    for c in range(col_start, col_end):
                        sheet.write(r, c, None)
                        cells_cleared += 1

        except Exception as e:
            raise Exception(f"Error resetting tab {sheet_name}: {e}")

        return cells_cleared

    def update_controle(self, vjour=None, mois=None, annee=None, idate=None):
        """
        Update the controle sheet with new day/date values.

        Args:
            vjour: Day number (1-31)
            mois: Month (1-12)
            annee: Year (e.g., 2026)
            idate: Excel date serial number (optional, calculated if not provided)

        Returns:
            Dict with updated fields.
        """
        sheet = self._get_sheet_by_name('controle')
        updated = {}

        # B3 = vjour (day number)
        if vjour is not None:
            sheet.write(2, 1, int(vjour))
            updated['vjour'] = vjour

        # B4 = mois (month)
        if mois is not None:
            sheet.write(3, 1, int(mois))
            updated['mois'] = mois

        # B5 = annee (year)
        if annee is not None:
            sheet.write(4, 1, int(annee))
            updated['annee'] = annee

        # B28 = idate (Excel date serial)
        # If idate not provided but we have day/month/year, calculate it
        if idate is not None:
            sheet.write(27, 1, idate)
            updated['idate'] = idate
        elif vjour and mois and annee:
            # Calculate Excel date serial (days since 1900-01-01)
            # Excel incorrectly considers 1900 a leap year, so we need to adjust
            from datetime import date
            try:
                d = date(int(annee), int(mois), int(vjour))
                # Excel serial: days since 1899-12-30 (Excel's epoch with leap year bug)
                excel_epoch = date(1899, 12, 30)
                excel_serial = (d - excel_epoch).days
                sheet.write(27, 1, excel_serial)
                updated['idate'] = excel_serial
            except ValueError as e:
                # Invalid date, skip idate update
                pass

        return updated

    def sync_duback_to_setd(self, current_day):
        """
        Read DUBACK# amounts for the current day and write them to SetD.
        
        Args:
            current_day: Day number (int)
            
        Returns:
            Number of updates made.
        """
        updates = 0
        
        # 1. Read DUBACK# from the READ-ONLY workbook (self.rb) to get values
        try:
            duback_sheet = self.rb.sheet_by_name('DUBACK#')
            
            # Find the row for operations for the current day
            _, op_row_idx = get_dueback_row_for_day(current_day)
            op_row_idx = op_row_idx - 1 # 0-based
            
            # Read header row (Row 2 -> Index 1) to map names to columns
            name_to_col = {}
            header_row = duback_sheet.row_values(1) # Index 1
            for col_idx, cell_val in enumerate(header_row):
                if cell_val:
                    name_to_col[str(cell_val).strip()] = col_idx
            
            # Read values for the day
            day_values = {}
            row_data = duback_sheet.row_values(op_row_idx)
            for name, col_idx in name_to_col.items():
                val = row_data[col_idx]
                # Check if value is numeric and non-zero (optional)
                if isinstance(val, (int, float)):
                    day_values[name] = val
                    
        except Exception as e:
            logger.error(f"Error reading DUBACK#: {e}")
            return 0
            
        # 2. Write to SetD in the WRITE workbook (self.wb)
        try:
            try:
                setd_sheet = self._get_sheet_by_name('SetD')
            except ValueError:
                return 0
            
            # Find target row in SetD
            target_row_idx = get_setd_row_for_day(current_day) - 1
            
            # Find column mapping in SetD (Row 2 -> Index 1)
            # Need to read from self.rb again to find where names are in SetD
            setd_read_sheet = self.rb.sheet_by_name('SetD')
            setd_header = setd_read_sheet.row_values(1) # Index 1
            
            setd_col_map = {}
            for col_idx, cell_val in enumerate(setd_header):
                if cell_val:
                    setd_col_map[str(cell_val).strip()] = col_idx
            
            # Perform the update
            for name, amount in day_values.items():
                target_name = DUBACK_TO_SETD_MAPPING.get(name, name)

                # Exact match only (case-insensitive)
                target_col_idx = None
                for s_name, s_idx in setd_col_map.items():
                    if target_name.strip().lower() == s_name.strip().lower():
                        target_col_idx = s_idx
                        break

                if target_col_idx is not None:
                    setd_sheet.write(target_row_idx, target_col_idx, amount)
                    updates += 1
                    
        except Exception as e:
            logger.error(f"Error writing SetD: {e}")
            
        return updates


    def update_deposit(self, date_str, amount):
        """
        Update the 'depot' tab with the verified amount for a date.

        Args:
            date_str: Date string (e.g. '2024-12-19') or datetime object
            amount: Verified amount

        Returns:
            True if successful
        """
        try:
            depot_read_sheet = self.rb.sheet_by_name('depot')
            target_row_idx = -1

            # Parse the target date for comparison
            if isinstance(date_str, str):
                try:
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    target_date = None
            else:
                target_date = None

            # Search for existing date row in column A (starting after header rows)
            for r in range(1, depot_read_sheet.nrows):
                cell_val = depot_read_sheet.cell_value(r, 0)  # Col A
                cell_type = depot_read_sheet.cell_type(r, 0)

                if cell_val == '' or cell_val is None:
                    continue

                matched = False

                # Check if cell contains an xlrd date number
                if cell_type == xlrd.XL_CELL_DATE and target_date:
                    try:
                        date_tuple = xlrd.xldate_as_tuple(cell_val, self.rb.datemode)
                        cell_date = datetime(*date_tuple[:3]).date()
                        if cell_date == target_date:
                            matched = True
                    except (ValueError, TypeError):
                        pass

                # Check if cell contains the date as a string
                if not matched and isinstance(cell_val, str):
                    if cell_val.strip() == date_str:
                        matched = True
                    # Also try parsing common date formats
                    if not matched:
                        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                            try:
                                if datetime.strptime(cell_val.strip(), fmt).date() == target_date:
                                    matched = True
                                    break
                            except (ValueError, TypeError):
                                continue

                if matched:
                    target_row_idx = r
                    break

            # If no existing date found, find first empty row after headers
            if target_row_idx == -1:
                for r in range(DEPOT_HEADER_ROW, MAX_DEPOSIT_ROWS):
                    if r >= depot_read_sheet.nrows:
                        target_row_idx = r
                        break
                    val_a = depot_read_sheet.cell_value(r, 0)
                    val_b = depot_read_sheet.cell_value(r, 1)
                    if (val_a == '' or val_a is None) and (val_b == '' or val_b is None):
                        target_row_idx = r
                        break

            if target_row_idx != -1:
                sheet = self._get_sheet_by_name('depot')
                sheet.write(target_row_idx, 0, date_str)      # Write Date
                sheet.write(target_row_idx, 1, float(amount))  # Write Amount
                return True

        except Exception as e:
            logger.error(f"Error updating deposit: {e}")
            return False

        return False


    def fill_sheet(self, sheet_name, data_dict):
        """
        Fill a sheet with data using the mapping configuration.

        Args:
            sheet_name: Name of the sheet (e.g., 'Recap', 'controle')
            data_dict: Dictionary with field names and values

        Returns:
            Number of cells filled
        """
        if sheet_name not in CELL_MAPPINGS:
            raise ValueError(f"No mapping found for sheet '{sheet_name}'")

        mapping = CELL_MAPPINGS[sheet_name]
        sheet = self._get_sheet_by_name(sheet_name)
        cells_filled = 0

        for field_name, cell_addr in mapping.items():
            if field_name in data_dict:
                value = data_dict[field_name]

                # Skip empty values
                if value is None or value == '':
                    continue

                # Convert to appropriate type
                if isinstance(value, str):
                    try:
                        # Try to convert to number if possible
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        # Keep as string
                        pass

                # Write to cell
                row_idx, col_idx = excel_cell_to_indices(cell_addr)
                sheet.write(row_idx, col_idx, value)
                cells_filled += 1

        return cells_filled


    def fill_dueback_day(self, day, receptionist, amount, line_type='nouveau'):
        """
        Fill DueBack for a specific day and receptionist.

        Args:
            day: Day number (1-31)
            receptionist: Receptionist name (must match DUEBACK_RECEPTIONIST_COLUMNS)
            amount: Amount to enter
            line_type: 'previous' for line 1 (Previous DueBack) or 'nouveau' for line 2 (Nouveau DueBack)
        """
        if receptionist not in DUEBACK_RECEPTIONIST_COLUMNS:
            raise ValueError(f"Unknown receptionist: {receptionist}")

        sheet = self._get_sheet_by_name('DUBACK#')
        col = DUEBACK_RECEPTIONIST_COLUMNS[receptionist]

        # Get the rows for this day
        balance_row, operations_row = get_dueback_row_for_day(day)

        # Determine which row to fill
        if line_type == 'previous':
            target_row = balance_row  # Line 1 - Previous DueBack
        else:  # 'nouveau'
            target_row = operations_row  # Line 2 - Nouveau DueBack

        # Convert column letter to index
        col_idx = excel_col_to_index(col)
        row_idx = target_row - 1  # Excel row to 0-based index

        # Write the amount
        sheet.write(row_idx, col_idx, float(amount))

    def fill_dueback_by_col(self, day, col_letter, amount, line_type='nouveau'):
        """
        Fill DueBack for a specific day using a column letter (dynamic receptionists).

        Args:
            day: Day number (1-31)
            col_letter: Excel column letter (e.g., 'C')
            amount: Amount to enter
            line_type: 'previous' (balance) or 'nouveau' (operations)
        """
        sheet = self._get_sheet_by_name('DUBACK#')
        balance_row, operations_row = get_dueback_row_for_day(day)
        target_row = balance_row if line_type == 'previous' else operations_row
        col_idx = excel_col_to_index(col_letter)
        row_idx = target_row - 1
        sheet.write(row_idx, col_idx, float(amount))


    def fill_setd_day(self, day, amount, account_col='B'):
        """
        Fill SetD for a specific day.

        Args:
            day: Day number (1-31)
            amount: Amount to enter
            account_col: Column for the account (default 'B' for RJ)
        """
        sheet = self._get_sheet_by_name('SetD')
        row = get_setd_row_for_day(day)

        col_idx = excel_col_to_index(account_col)
        row_idx = row - 1  # Excel row to 0-based index

        sheet.write(row_idx, col_idx, float(amount))


    def envoie_dans_jour(self, day=None):
        """
        Copy Recap H19:N19 to jour sheet at ar_[day] row.
        Replicates VBA macro envoie_dans_jour().

        Args:
            day: Day number (1-31). If None, reads from controle vjour.

        Returns:
            Dict with copied values and target info.
        """
        # Get day from controle if not provided
        if day is None:
            # Read vjour from controle
            for idx in range(len(self.rb.sheet_names())):
                if self.rb.sheet_names()[idx] == 'controle':
                    sheet = self.rb.sheet_by_index(idx)
                    day = int(sheet.cell_value(2, 1))  # B3
                    break

        if not day or day < 1 or day > 31:
            raise ValueError(f"Invalid day: {day}")

        # Read H19:N19 from Recap (row 18, cols 7-13)
        recap_values = []
        recap_sheet = None
        for idx in range(len(self.rb.sheet_names())):
            if self.rb.sheet_names()[idx] == 'Recap':
                recap_sheet = self.rb.sheet_by_index(idx)
                break

        if recap_sheet is None:
            raise ValueError("Recap sheet not found")

        # H=7, I=8, J=9, K=10, L=11, M=12, N=13 (0-indexed)
        for col in range(7, 14):  # H to N
            try:
                val = recap_sheet.cell_value(18, col)  # Row 19 (0-indexed = 18)
                recap_values.append(val if val != '' else 0)
            except Exception:
                recap_values.append(0)

        jour_sheet = self._get_sheet_by_name('jour')

        # ar_[day] named ranges map to jour sheet
        # Based on RJ structure, ar_ ranges are in columns BU-CA area
        # Row depends on day: typically header + day rows
        # From documentation: ar_[day] is at row = 4 + day (rows 5-35 for days 1-31)
        # Columns: BU(72), BV(73), BW(74), BX(75), BY(76), BZ(77), CA(78)
        # But H19:N19 in Recap has 7 values that map to these columns

        # Target row in jour for day (uses centralized constant from rj_mapper)
        target_row = get_jour_row_for_day(day)

        # Target columns: BU-CA (from rj_mapper.JOUR_RECAP_COLS)
        for i, col in enumerate(JOUR_RECAP_COLS):
            if i < len(recap_values):
                jour_sheet.write(target_row, col, recap_values[i])

        return {
            'day': day,
            'recap_values': recap_values,
            'target_row': target_row + 1,  # 1-indexed for display
            'columns': 'BU:CA'
        }

    def calcul_carte(self, day=None):
        """
        Copy credit card totals from transelect to jour at CC_[day].
        Replicates VBA macro calcul_carte().

        Args:
            day: Day number (1-31). If None, reads from controle vjour.

        Returns:
            Dict with copied values and target info.
        """
        # Get day from controle if not provided
        if day is None:
            for idx in range(len(self.rb.sheet_names())):
                if self.rb.sheet_names()[idx] == 'controle':
                    sheet = self.rb.sheet_by_index(idx)
                    day = int(sheet.cell_value(2, 1))  # B3
                    break

        if not day or day < 1 or day > 31:
            raise ValueError(f"Invalid day: {day}")

        # Read total_carte_crédit from transelect
        # This is typically the total row in transelect credit card section
        # Based on transelect structure, total is around row 13-14 area
        trans_sheet = None
        for idx in range(len(self.rb.sheet_names())):
            if self.rb.sheet_names()[idx] == 'transelect':
                trans_sheet = self.rb.sheet_by_index(idx)
                break

        if trans_sheet is None:
            raise ValueError("transelect sheet not found")

        # Read credit card totals - the exact cells depend on transelect structure
        # Typically it's a summary row with totals for different card types
        # From transelect analysis: row 14 has totals, columns B onwards
        # total_carte_crédit named range likely covers the card totals

        # Read row 14 (0-indexed = 13) columns B to T (1 to 19)
        card_totals = []
        for col in range(1, 20):  # B to T
            try:
                val = trans_sheet.cell_value(13, col)  # Row 14
                if val and isinstance(val, (int, float)):
                    card_totals.append(val)
                else:
                    card_totals.append(0)
            except Exception:
                card_totals.append(0)

        jour_sheet = self._get_sheet_by_name('jour')

        # CC_[day] named ranges in jour (from rj_mapper constants)
        target_row = get_jour_row_for_day(day)

        # Write card totals to jour starting at BF (from rj_mapper.JOUR_CC_START_COL)
        start_col = JOUR_CC_START_COL

        for i, val in enumerate(card_totals):
            if val != 0:
                jour_sheet.write(target_row, start_col + i, val)

        return {
            'day': day,
            'card_totals': card_totals,
            'target_row': target_row + 1,
            'start_column': 'BF'
        }

    def fill_jour_day(self, day, jour_values):
        """
        Write computed values to the jour sheet for a specific day.

        This is the bridge between JourMapper output and the actual Excel file.
        Uses the same get_jour_row_for_day() that envoie_dans_jour() and
        calcul_carte() already use.

        Args:
            day: Day number (1-31)
            jour_values: dict {column_index: value} from JourMapper.compute_all()

        Returns:
            dict with 'day', 'filled_count', 'target_row', 'columns_filled'
        """
        if not day or day < 1 or day > 31:
            raise ValueError(f"Invalid day: {day}")

        if not jour_values:
            return {'day': day, 'filled_count': 0, 'target_row': None, 'columns_filled': []}

        jour_sheet = self._get_sheet_by_name('jour')
        target_row = get_jour_row_for_day(day)

        filled = 0
        columns_filled = []

        for col_idx, value in jour_values.items():
            if value is not None:
                try:
                    jour_sheet.write(target_row, int(col_idx), float(value))
                    filled += 1
                    columns_filled.append(int(col_idx))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not write col {col_idx} = {value}: {e}")

        return {
            'day': day,
            'filled_count': filled,
            'target_row': target_row + 1,  # 1-indexed for display
            'columns_filled': sorted(columns_filled),
        }

    def save(self, output_path_or_buffer):
        """
        Save the modified workbook.

        Args:
            output_path_or_buffer: File path (str) or BytesIO buffer
        """
        self.wb.save(output_path_or_buffer)


    def save_to_bytes(self):
        """
        Save the modified workbook to a BytesIO buffer.

        Returns:
            BytesIO buffer with the Excel file
        """
        buffer = io.BytesIO()
        self.wb.save(buffer)
        buffer.seek(0)
        return buffer


# Example usage functions for common operations

def fill_recap_form(rj_filler, form_data):
    """Fill the RECAP sheet with form data."""
    return rj_filler.fill_sheet('Recap', form_data)


def fill_transelect_form(rj_filler, form_data):
    """Fill the TRANSELECT sheet with form data."""
    return rj_filler.fill_sheet('transelect', form_data)


def fill_geac_form(rj_filler, form_data):
    """Fill the GEAC/UX sheet with form data."""
    return rj_filler.fill_sheet('geac_ux', form_data)


def fill_controle_form(rj_filler, form_data):
    """Fill the controle sheet with form data."""
    return rj_filler.fill_sheet('controle', form_data)
