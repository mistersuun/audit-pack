#!/usr/bin/env python3
"""
SD (Sommaire Journalier) Reader
Reads and extracts data from SD Excel files
"""

import xlrd
from io import BytesIO


class SDReader:
    """
    Reader for SD (Sommaire Journalier des Dépôts) Excel files.

    SD file structure:
    - 31 sheets (one per day: '1', '2', '3', ..., '31')
    - Each sheet has:
      - Row 4 (index 3): DATE
      - Row 6 (index 5): Headers (DÉPARTEMENT, NOM LETTRES MOULÉES, CDN/US, MONTANT, MONTANT VÉRIFIÉ, REMBOURSEMENT, VARIANCE)
      - Rows 8+ (index 7+): Data entries
    """

    def __init__(self, file_path_or_bytes):
        """
        Initialize SD reader.

        Args:
            file_path_or_bytes: Either a file path (str) or BytesIO object
        """
        if isinstance(file_path_or_bytes, str):
            self.wb = xlrd.open_workbook(file_path_or_bytes, formatting_info=False)
        else:
            file_path_or_bytes.seek(0)
            self.wb = xlrd.open_workbook(file_contents=file_path_or_bytes.read(), formatting_info=False)

    def get_available_days(self):
        """
        Get list of available day sheets.

        Returns:
            list: List of day numbers (as integers)
        """
        days = []
        for sheet_name in self.wb.sheet_names():
            try:
                day = int(sheet_name)
                if 1 <= day <= 31:
                    days.append(day)
            except ValueError:
                # Not a day sheet
                continue
        return sorted(days)

    def read_day_data(self, day):
        """
        Read all entries for a specific day.

        Args:
            day: Day number (1-31)

        Returns:
            dict: {
                'day': int,
                'date': str or float,
                'entries': [
                    {
                        'departement': str,
                        'nom': str,
                        'cdn_us': str,
                        'montant': float,
                        'montant_verifie': float,
                        'remboursement': float,
                        'variance': float
                    },
                    ...
                ]
            }

        Raises:
            ValueError: If day is not between 1-31
            Exception: If sheet not found
        """
        if not 1 <= day <= 31:
            raise ValueError(f"Day must be between 1-31, got {day}")

        sheet_name = str(day)
        try:
            sheet = self.wb.sheet_by_name(sheet_name)
        except (KeyError, Exception) as e:
            raise Exception(f"Sheet '{sheet_name}' not found in SD file") from e

        # Read date from row 4 (index 3), column B (index 1)
        date_value = sheet.cell(3, 1).value if sheet.ncols > 1 else ''

        # Read entries starting from row 8 (index 7)
        entries = []
        row_idx = 7

        while row_idx < sheet.nrows:
            # Column mapping:
            # A (0): DÉPARTEMENT
            # B (1): NOM LETTRES MOULÉES
            # C (2): CDN/US
            # D (3): MONTANT
            # E (4): MONTANT VÉRIFIÉ (optional)
            # F (5): REMBOURSEMENT (optional)
            # G (6): VARIANCE (optional)

            departement = self._get_cell_value(sheet, row_idx, 0)
            nom = self._get_cell_value(sheet, row_idx, 1)
            cdn_us = self._get_cell_value(sheet, row_idx, 2)
            montant = self._get_cell_value(sheet, row_idx, 3)
            montant_verifie = self._get_cell_value(sheet, row_idx, 4) if sheet.ncols > 4 else None
            remboursement = self._get_cell_value(sheet, row_idx, 5) if sheet.ncols > 5 else None
            variance = self._get_cell_value(sheet, row_idx, 6) if sheet.ncols > 6 else None

            # Stop if we hit an empty row (no département and no nom)
            if not departement and not nom:
                # But check a few more rows in case there's data below
                empty_count = 0
                for check_row in range(row_idx, min(row_idx + 5, sheet.nrows)):
                    if not self._get_cell_value(sheet, check_row, 0) and not self._get_cell_value(sheet, check_row, 1):
                        empty_count += 1
                    else:
                        break
                if empty_count >= 3:
                    # Found 3+ consecutive empty rows, stop
                    break

            # Add entry if there's at least a département or nom
            # Skip TOTAL row and SIGNATURE rows (not real entries)
            dept_upper = str(departement).strip().upper() if departement else ''
            nom_upper = str(nom).strip().upper() if nom else ''
            is_total = dept_upper == 'TOTAL'
            is_signature = 'SIGNATURE' in nom_upper

            if (departement or nom) and not is_total and not is_signature:
                entries.append({
                    'departement': departement or '',
                    'nom': nom or '',
                    'cdn_us': cdn_us or '',
                    'montant': montant if isinstance(montant, (int, float)) else 0,
                    'montant_verifie': montant_verifie if isinstance(montant_verifie, (int, float)) else None,
                    'remboursement': remboursement if isinstance(remboursement, (int, float)) else None,
                    'variance': variance if isinstance(variance, (int, float)) else None
                })

            row_idx += 1

        return {
            'day': day,
            'date': date_value,
            'entries': entries
        }

    def get_totals_for_day(self, day):
        """
        Get totals for a specific day from the TOTAL row in the Excel file.

        Reads directly from the TOTAL row (row 38, index 37+) for accuracy,
        falling back to calculated sums if the row is not found.

        Args:
            day: Day number (1-31)

        Returns:
            dict: {
                'total_montant': float,
                'total_verifie': float,
                'total_remboursement': float,
                'total_variance': float
            }
        """
        # Try to read the TOTAL row directly from Excel (more reliable)
        sheet_name = str(day)
        try:
            sheet = self.wb.sheet_by_name(sheet_name)
            for row_idx in range(sheet.nrows):
                dept = self._get_cell_value(sheet, row_idx, 0)
                if str(dept).strip().upper() == 'TOTAL':
                    montant = self._get_cell_value(sheet, row_idx, 3)
                    verifie = self._get_cell_value(sheet, row_idx, 4) if sheet.ncols > 4 else 0
                    remb = self._get_cell_value(sheet, row_idx, 5) if sheet.ncols > 5 else 0
                    variance = self._get_cell_value(sheet, row_idx, 6) if sheet.ncols > 6 else 0
                    return {
                        'total_montant': float(montant) if isinstance(montant, (int, float)) else 0,
                        'total_verifie': float(verifie) if isinstance(verifie, (int, float)) else 0,
                        'total_remboursement': float(remb) if isinstance(remb, (int, float)) else 0,
                        'total_variance': float(variance) if isinstance(variance, (int, float)) else 0,
                    }
        except Exception:
            pass

        # Fallback: calculate from entries
        data = self.read_day_data(day)
        totals = {
            'total_montant': 0,
            'total_verifie': 0,
            'total_remboursement': 0,
            'total_variance': 0
        }

        for entry in data['entries']:
            totals['total_montant'] += entry['montant']
            if entry['montant_verifie'] is not None:
                totals['total_verifie'] += entry['montant_verifie']
            if entry['remboursement'] is not None:
                totals['total_remboursement'] += entry['remboursement']
            if entry['variance'] is not None:
                totals['total_variance'] += entry['variance']

        return totals

    def _get_cell_value(self, sheet, row, col):
        """
        Safely get cell value.

        Args:
            sheet: xlrd sheet object
            row: Row index
            col: Column index

        Returns:
            Cell value or empty string
        """
        if row >= sheet.nrows or col >= sheet.ncols:
            return ''

        cell = sheet.cell(row, col)
        return cell.value if cell.value != '' else ''


# For testing
if __name__ == "__main__":
    import os

    sd_file = '/Users/canaldesuez/Documents/Projects/audit-pack/documentation/complete_updated_files_to_analyze/SD. Novembre 2025-Copie.xls'

    if not os.path.exists(sd_file):
        print(f"❌ File not found: {sd_file}")
        exit(1)

    reader = SDReader(sd_file)

    print("=" * 100)
    print("TEST SD READER")
    print("=" * 100)

    # Test 1: Get available days
    print("\n1. Available days:")
    days = reader.get_available_days()
    print(f"   {days}")

    # Test 2: Read day 1
    print("\n2. Read day 1:")
    day1_data = reader.read_day_data(1)
    print(f"   Date: {day1_data['date']}")
    print(f"   Entries: {len(day1_data['entries'])}")
    print("\n   First 5 entries:")
    for i, entry in enumerate(day1_data['entries'][:5], 1):
        print(f"   {i}. {entry['departement']:15} | {entry['nom']:20} | {entry['cdn_us']:5} | ${entry['montant']:>10.2f}")

    # Test 3: Get totals for day 1
    print("\n3. Totals for day 1:")
    totals = reader.get_totals_for_day(1)
    for key, value in totals.items():
        print(f"   {key}: ${value:.2f}")

    # Test 4: Read day 23
    print("\n4. Read day 23:")
    day23_data = reader.read_day_data(23)
    print(f"   Date: {day23_data['date']}")
    print(f"   Entries: {len(day23_data['entries'])}")

    print("\n" + "=" * 100)
    print("✅ All tests completed!")
