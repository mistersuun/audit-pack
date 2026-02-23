#!/usr/bin/env python3
"""
Fonctions pour écrire/modifier le fichier RJ Excel
"""

import xlrd
from xlutils.copy import copy
from io import BytesIO


def copy_recap_to_jour(rj_bytes, day):
    """
    Copy Recap summary (row 19, columns H-N) to the 'jour' sheet for a specific day.

    Args:
        rj_bytes: BytesIO containing the RJ Excel file
        day: Day of the month (1-31)

    Returns:
        BytesIO: Updated RJ file with Recap data copied to jour

    Raises:
        ValueError: If day is not between 1-31
        Exception: If sheets not found

    Note:
        - Recap row 19 (index 18) columns H-N (indices 7-13) are copied
        - To jour sheet row = 1 + day, same columns (H-N)
        - Example: Day 23 → copies to jour row 24 (index 23)
    """
    if not 1 <= day <= 31:
        raise ValueError(f"Day must be between 1-31, got {day}")

    # Read RJ
    rj_bytes.seek(0)
    rb = xlrd.open_workbook(file_contents=rj_bytes.read(), formatting_info=True)
    wb = copy(rb)

    # Get sheets for reading
    try:
        recap_read = rb.sheet_by_name('Recap')
        jour_read = rb.sheet_by_name('jour')
    except (KeyError, Exception) as e:
        raise Exception("Sheets 'Recap' or 'jour' not found") from e

    # Get sheet for writing
    jour_write = wb.get_sheet('jour')

    # Source: Recap row 19 (index 18), columns H-N (indices 7-13)
    source_row = 18
    source_cols = range(7, 14)  # H=7, I=8, J=9, K=10, L=11, M=12, N=13

    # Destination: jour row = 1 + day
    # Day 1 → row 2 (index 1)
    # Day 23 → row 24 (index 23)
    dest_row = 1 + day

    # Copy values
    for col in source_cols:
        value = recap_read.cell(source_row, col).value
        jour_write.write(dest_row, col, value)

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return output


def get_recap_summary(rj_bytes):
    """
    Get the summary row (row 19, columns H-N) from Recap.

    Args:
        rj_bytes: BytesIO containing the RJ Excel file

    Returns:
        dict: Dictionary with column names and values
              Example: {'H': 4070.43, 'I': -1067.61, ...}

    Raises:
        Exception: If Recap sheet not found
    """
    rj_bytes.seek(0)
    rb = xlrd.open_workbook(file_contents=rj_bytes.read())

    try:
        recap = rb.sheet_by_name('Recap')
    except (KeyError, Exception) as e:
        raise Exception("Sheet 'Recap' not found") from e

    # Read row 19 (index 18), columns H-N (indices 7-13)
    row = 18
    cols_map = {
        'H': 7,
        'I': 8,
        'J': 9,
        'K': 10,
        'L': 11,
        'M': 12,
        'N': 13
    }

    result = {}
    for col_name, col_idx in cols_map.items():
        result[col_name] = recap.cell(row, col_idx).value

    return result


def get_jour_day_data(rj_bytes, day):
    """
    Get data for a specific day from the 'jour' sheet.

    Args:
        rj_bytes: BytesIO containing the RJ Excel file
        day: Day of the month (1-31)

    Returns:
        dict: Dictionary with data for that day

    Raises:
        ValueError: If day is not between 1-31
        Exception: If jour sheet not found
    """
    if not 1 <= day <= 31:
        raise ValueError(f"Day must be between 1-31, got {day}")

    rj_bytes.seek(0)
    rb = xlrd.open_workbook(file_contents=rj_bytes.read())

    try:
        jour = rb.sheet_by_name('jour')
    except (KeyError, Exception) as e:
        raise Exception("Sheet 'jour' not found") from e

    # Row for this day = 1 + day
    row = 1 + day

    # Read columns H-N (indices 7-13)
    cols_map = {
        'H': 7,
        'I': 8,
        'J': 9,
        'K': 10,
        'L': 11,
        'M': 12,
        'N': 13
    }

    result = {'day': day}
    for col_name, col_idx in cols_map.items():
        result[col_name] = jour.cell(row, col_idx).value

    return result


# For testing
if __name__ == "__main__":
    import os

    rj_file = '/Users/canaldesuez/Documents/Projects/audit-pack/documentation/complete_updated_files_to_analyze/Rj 12-23-2025-Copie.xls'

    if not os.path.exists(rj_file):
        print(f"❌ File not found: {rj_file}")
        exit(1)

    # Load file
    with open(rj_file, 'rb') as f:
        rj_bytes = BytesIO(f.read())

    print("=" * 100)
    print("TEST: Copier Recap vers jour")
    print("=" * 100)

    # Test 1: Get recap summary
    print("\n1. Recap Summary (row 19, H-N):")
    summary = get_recap_summary(rj_bytes)
    for col, value in summary.items():
        print(f"   {col}19: {value}")

    # Test 2: Get jour data for day 23 BEFORE copy
    print("\n2. Jour Day 23 BEFORE copy:")
    jour_before = get_jour_day_data(rj_bytes, 23)
    for col, value in jour_before.items():
        if col != 'day':
            print(f"   {col}24: {value}")

    # Test 3: Copy recap to jour for day 23
    print("\n3. Copying Recap to jour for day 23...")
    updated_rj = copy_recap_to_jour(rj_bytes, 23)
    print("   ✅ Copy completed")

    # Test 4: Get jour data for day 23 AFTER copy
    print("\n4. Jour Day 23 AFTER copy:")
    jour_after = get_jour_day_data(updated_rj, 23)
    for col, value in jour_after.items():
        if col != 'day':
            print(f"   {col}24: {value}")

    # Test 5: Verify values match
    print("\n5. Verification:")
    match = True
    for col in ['H', 'I', 'J', 'K', 'L', 'M', 'N']:
        if summary[col] != jour_after[col]:
            print(f"   ❌ {col}: {summary[col]} != {jour_after[col]}")
            match = False

    if match:
        print("   ✅ All values match! Copy successful.")
    else:
        print("   ❌ Some values don't match.")

    # Test 6: Save to temp file
    temp_file = '/tmp/RJ_test_copy.xls'
    with open(temp_file, 'wb') as f:
        f.write(updated_rj.read())
    print(f"\n6. Saved test file to: {temp_file}")
    print(f"   You can open it in Excel to verify manually.")

    print("\n" + "=" * 100)
