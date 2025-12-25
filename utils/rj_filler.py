"""
Utility to fill RJ Excel file with form data.
"""

import xlrd
from xlrd import open_workbook
from xlutils.copy import copy as copy_workbook
import io
from datetime import datetime
from utils.rj_mapper import (
    CELL_MAPPINGS,
    DUEBACK_RECEPTIONIST_COLUMNS,
    RESET_RANGES,
    DUBACK_TO_SETD_MAPPING,
    get_dueback_row_for_day,
    get_setd_row_for_day
)


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


    def reset_tabs(self):
        """
        Clear specific ranges in Recap, transelect, and geac_ux sheets.
        
        Returns:
            Number of cells cleared.
        """
        cells_cleared = 0
        
        for sheet_name, ranges in RESET_RANGES.items():
            try:
                # In xlutils, sheets are accessed by index or name. 
                # We need to find the index corresponding to the name from the read-workbook.
                # However, wb.get_sheet(name) works if the name is correct.
                # xlwt sheet names are accessible.
                
                # Check if sheet exists in output workbook
                sheet_idx = -1
                for idx in range(len(self.wb._Workbook__worksheets)):
                    if self.wb.get_sheet(idx).name == sheet_name:
                        sheet_idx = idx
                        break
                
                if sheet_idx == -1:
                    print(f"Warning: Sheet {sheet_name} not found for reset.")
                    continue
                    
                sheet = self.wb.get_sheet(sheet_idx)
                
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
                print(f"Error resetting tab {sheet_name}: {e}")
                
        return cells_cleared


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
            print(f"Error reading DUBACK#: {e}")
            return 0
            
        # 2. Write to SetD in the WRITE workbook (self.wb)
        try:
            # Find SetD sheet
            setd_sheet_idx = -1
            for idx in range(len(self.wb._Workbook__worksheets)):
                if self.wb.get_sheet(idx).name == 'SetD':
                    setd_sheet_idx = idx
                    break
            
            if setd_sheet_idx == -1:
                return 0
                
            setd_sheet = self.wb.get_sheet(setd_sheet_idx)
            
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
                
                # Fuzzy match / exact match
                target_col_idx = setd_col_map.get(target_name)
                
                # Attempt partial match if exact not found
                if target_col_idx is None:
                    for s_name, s_idx in setd_col_map.items():
                        if target_name.lower() in s_name.lower() or s_name.lower() in target_name.lower():
                            target_col_idx = s_idx
                            break
                            
                if target_col_idx is not None:
                    setd_sheet.write(target_row_idx, target_col_idx, amount)
                    updates += 1
                    
        except Exception as e:
            print(f"Error writing SetD: {e}")
            
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
        # Implementation depends on finding the right row.
        # Since 'depot' rows aren't strictly numbered by day, we might need to search or append.
        # For now, let's assume we search for the date in the first few columns.
        
        try:
            depot_read_sheet = self.rb.sheet_by_name('depot')
            
            # Search for the date row
            target_row_idx = -1
            
            # Simple date match logic (needs refinement based on actual date format in Excel)
            # Assuming dates are in Col A or B
            for r in range(depot_read_sheet.nrows):
                cell_val = depot_read_sheet.cell_value(r, 0) # Col A
                # Check for match (logic omitted for brevity, would need date parsing)
                pass
                
            # If finding date is hard, we can just append to the first empty row after headers
            # Row 8 is header. Start looking from Row 9.
            for r in range(9, 200):
                val = depot_read_sheet.cell_value(r, 1) # Check Col B (Amount)
                if val == '' or val is None:
                    target_row_idx = r
                    break
            
            if target_row_idx != -1:
                # Find sheet index for writing
                sheet_idx = -1
                for idx in range(len(self.wb._Workbook__worksheets)):
                    if self.wb.get_sheet(idx).name == 'depot':
                        sheet_idx = idx
                        break
                
                sheet = self.wb.get_sheet(sheet_idx)
                sheet.write(target_row_idx, 0, date_str) # Write Date
                sheet.write(target_row_idx, 1, float(amount)) # Write Amount
                return True
                
        except Exception as e:
            print(f"Error updating deposit: {e}")
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
        sheet = self.wb.get_sheet(sheet_name)
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

        sheet = self.wb.get_sheet('DUBACK#')
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
        sheet = self.wb.get_sheet('DUBACK#')
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
        sheet = self.wb.get_sheet('SetD')
        row = get_setd_row_for_day(day)

        col_idx = excel_col_to_index(account_col)
        row_idx = row - 1  # Excel row to 0-based index

        sheet.write(row_idx, col_idx, float(amount))


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
