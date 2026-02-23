#!/usr/bin/env python3
"""
SD (Sommaire Journalier) Writer
Writes data to SD Excel files
"""

import xlrd
from xlutils.copy import copy
from io import BytesIO


class SDWriter:
    """
    Writer for SD (Sommaire Journalier des Dépôts) Excel files.
    Allows modifying entries in the SD file.
    """

    @staticmethod
    def write_entries(sd_bytes, day, entries):
        """
        Write entries to a specific day in the SD file.

        Args:
            sd_bytes: BytesIO containing the SD Excel file
            day: Day number (1-31)
            entries: List of entry dicts:
                [
                    {
                        'departement': str,
                        'nom': str,
                        'cdn_us': str,
                        'montant': float,
                        'montant_verifie': float (optional),
                        'remboursement': float (optional),
                        'variance': float (optional)
                    },
                    ...
                ]

        Returns:
            BytesIO: Updated SD file

        Raises:
            ValueError: If day is not between 1-31
            Exception: If sheet not found
        """
        if not 1 <= day <= 31:
            raise ValueError(f"Day must be between 1-31, got {day}")

        # Read SD file
        sd_bytes.seek(0)
        rb = xlrd.open_workbook(file_contents=sd_bytes.read(), formatting_info=True)
        wb = copy(rb)

        # Get sheet for this day
        sheet_name = str(day)
        try:
            sheet_write = wb.get_sheet(sheet_name)
        except (KeyError, Exception) as e:
            raise Exception(f"Sheet '{sheet_name}' not found in SD file") from e

        # Starting row for data entries (row 8 in Excel = index 7)
        start_row = 7

        # Write each entry
        for i, entry in enumerate(entries):
            row_idx = start_row + i

            # Column mapping:
            # A (0): DÉPARTEMENT
            # B (1): NOM LETTRES MOULÉES
            # C (2): CDN/US
            # D (3): MONTANT
            # E (4): MONTANT VÉRIFIÉ
            # F (5): REMBOURSEMENT
            # G (6): VARIANCE

            sheet_write.write(row_idx, 0, entry.get('departement', ''))
            sheet_write.write(row_idx, 1, entry.get('nom', ''))
            sheet_write.write(row_idx, 2, entry.get('cdn_us', ''))
            sheet_write.write(row_idx, 3, entry.get('montant', 0))

            # Optional columns
            if entry.get('montant_verifie') is not None:
                sheet_write.write(row_idx, 4, entry['montant_verifie'])
            if entry.get('remboursement') is not None:
                sheet_write.write(row_idx, 5, entry['remboursement'])
            if entry.get('variance') is not None:
                sheet_write.write(row_idx, 6, entry['variance'])

        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return output

    @staticmethod
    def clear_day_entries(sd_bytes, day):
        """
        Clear all entries for a specific day (but keep headers).

        Args:
            sd_bytes: BytesIO containing the SD Excel file
            day: Day number (1-31)

        Returns:
            BytesIO: Updated SD file with cleared entries

        Raises:
            ValueError: If day is not between 1-31
            Exception: If sheet not found
        """
        if not 1 <= day <= 31:
            raise ValueError(f"Day must be between 1-31, got {day}")

        # Read SD file
        sd_bytes.seek(0)
        rb = xlrd.open_workbook(file_contents=sd_bytes.read(), formatting_info=True)
        wb = copy(rb)

        # Get sheet for this day
        sheet_name = str(day)
        try:
            sheet_read = rb.sheet_by_name(sheet_name)
            sheet_write = wb.get_sheet(sheet_name)
        except (KeyError, Exception) as e:
            raise Exception(f"Sheet '{sheet_name}' not found in SD file") from e

        # Clear rows starting from row 8 (index 7)
        start_row = 7

        # Clear up to 40 rows (typical max for entries)
        for row_idx in range(start_row, min(start_row + 40, sheet_read.nrows)):
            for col_idx in range(7):  # Columns A-G
                sheet_write.write(row_idx, col_idx, '')

        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return output


# For testing
if __name__ == "__main__":
    import os
    from sd_reader import SDReader

    sd_file = '/Users/canaldesuez/Documents/Projects/audit-pack/documentation/complete_updated_files_to_analyze/SD. Novembre 2025-Copie.xls'

    if not os.path.exists(sd_file):
        print(f"❌ File not found: {sd_file}")
        exit(1)

    # Load SD file
    with open(sd_file, 'rb') as f:
        sd_bytes = BytesIO(f.read())

    print("=" * 100)
    print("TEST SD WRITER")
    print("=" * 100)

    # Test 1: Read original data for day 1
    print("\n1. Original data for day 1:")
    reader = SDReader(sd_bytes)
    original_data = reader.read_day_data(1)
    print(f"   Entries: {len(original_data['entries'])}")
    print(f"   First entry: {original_data['entries'][0]}")

    # Test 2: Write new entries
    print("\n2. Writing new test entries for day 1...")
    new_entries = [
        {
            'departement': 'TEST DEPT',
            'nom': 'Test Person 1',
            'cdn_us': 'CDN',
            'montant': 123.45,
            'montant_verifie': 123.45,
            'remboursement': 0,
            'variance': 0
        },
        {
            'departement': 'TEST DEPT',
            'nom': 'Test Person 2',
            'cdn_us': 'US',
            'montant': 67.89,
            'montant_verifie': 70.00,
            'remboursement': 2.11,
            'variance': 0
        }
    ]

    updated_sd = SDWriter.write_entries(sd_bytes, 1, new_entries)
    print("   ✅ Entries written")

    # Test 3: Read updated data
    print("\n3. Reading updated data for day 1:")
    reader2 = SDReader(updated_sd)
    updated_data = reader2.read_day_data(1)
    print(f"   Entries: {len(updated_data['entries'])}")
    print(f"   First entry: {updated_data['entries'][0]}")
    print(f"   Second entry: {updated_data['entries'][1]}")

    # Test 4: Verify totals
    print("\n4. Totals after update:")
    totals = reader2.get_totals_for_day(1)
    print(f"   Total montant: ${totals['total_montant']:.2f}")
    print(f"   Total vérifié: ${totals['total_verifie']:.2f}")

    # Test 5: Clear entries
    print("\n5. Clearing entries for day 1...")
    cleared_sd = SDWriter.clear_day_entries(updated_sd, 1)
    print("   ✅ Entries cleared")

    # Test 6: Read cleared data
    print("\n6. Reading cleared data for day 1:")
    reader3 = SDReader(cleared_sd)
    cleared_data = reader3.read_day_data(1)
    print(f"   Entries: {len(cleared_data['entries'])}")

    # Test 7: Save test file
    temp_file = '/tmp/SD_test_modified.xls'
    with open(temp_file, 'wb') as f:
        updated_sd.seek(0)
        f.write(updated_sd.read())
    print(f"\n7. Saved test file to: {temp_file}")
    print(f"   You can open it in Excel to verify manually.")

    print("\n" + "=" * 100)
    print("✅ All tests completed!")
