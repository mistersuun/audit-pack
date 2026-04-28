"""Verify Recap H19:N19 formula sources.

Opens the Apr 23 backup (unfilled) via COM, reads every formula in H19:N19,
and checks whether my B-column inputs (B7, B11, B12, B16, B19, B24) are the
correct cells to write to drive those formulas.

Usage:
    python tmp_verify_recap.py
"""
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

BAK_PATH = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls.bak.xls'

# Mapping col number -> letter for display
def col_letter(n):
    """Convert 1-based col number to Excel letter(s)."""
    result = ''
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result

TARGET_CELLS = [
    # (row, col_1based, label)
    (19, 8,  'H19'),
    (19, 9,  'I19'),
    (19, 10, 'J19'),
    (19, 11, 'K19'),
    (19, 12, 'L19'),
    (19, 13, 'M19'),
    (19, 14, 'N19'),
]

# Input cells the endpoint writes
INPUT_CELLS = [
    (7,  2, 'B7  — Comptant Positouch (H19 Argent Reçu?)'),
    (11, 2, 'B11 — Remb Gratuité'),
    (12, 2, 'B12 — Remb Client'),
    (16, 2, 'B16 — Due Back Réception'),
    (19, 2, 'B19 — Surplus/Déficit'),
    (24, 2, 'B24 — Argent Reçu (manual)'),
]

# Known-good target values for Apr 23
KNOWN_GOOD = {
    'H19': 11916.20,
    'I19': -336.29,
    'J19': -1200.01,
    'K19': 0.0,
    'L19': -336.29,
    'M19': 0.0,
    'N19': -228.44,
}

try:
    import win32com.client as win32
except ImportError:
    print('ERROR: pywin32 not available')
    sys.exit(1)

print(f'Opening: {BAK_PATH}')
excel = win32.DispatchEx('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False

try:
    wb = excel.Workbooks.Open(BAK_PATH)
    recap = wb.Sheets('Recap')

    print('\n=== Recap H19:N19 — Formula inspection ===')
    for row, col, label in TARGET_CELLS:
        cell = recap.Cells(row, col)
        has_formula = cell.HasFormula
        formula = cell.Formula if has_formula else '(no formula)'
        value = cell.Value
        known = KNOWN_GOOD.get(label)
        val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
        known_str = f'{known:,.2f}' if known is not None else 'N/A'
        match = '==' if known is not None and isinstance(value, (int, float)) and abs(value - known) < 0.01 else '!='
        cell_type = 'FORMULA' if has_formula else 'VALUE'
        print(f'  {label} ({cell_type}): {formula:50s} = {val_str:12s}  (known good: {known_str}) {match}')

    print('\n=== Input cells — current values in unfilled workbook ===')
    for row, col, label in INPUT_CELLS:
        cell = recap.Cells(row, col)
        has_formula = cell.HasFormula
        formula = cell.Formula if has_formula else '(no formula)'
        value = cell.Value
        val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
        cell_type = 'FORMULA' if has_formula else 'VALUE'
        print(f'  {label} ({cell_type}): {formula:50s} = {val_str}')

    print('\n=== Checking whether B7 feeds H19 (write test) ===')
    # Read H19 before
    h19_before = recap.Cells(19, 8).Value

    # Write 11916.20 to B7, recalc, read H19
    b7_cell = recap.Cells(7, 2)
    b7_orig_formula = b7_cell.Formula
    b7_orig_value = b7_cell.Value
    b7_has_formula = b7_cell.HasFormula

    print(f'  B7 before: formula={b7_orig_formula}, value={b7_orig_value}')
    print(f'  H19 before: {h19_before}')

    if not b7_has_formula:
        b7_cell.Value = 11916.20
        excel.Calculate()
        time.sleep(0.2)
        h19_after = recap.Cells(19, 8).Value
        print(f'  After writing B7=11916.20 → H19={h19_after}')
        if isinstance(h19_after, (int, float)) and abs(h19_after - 11916.20) < 0.01:
            print('  CONFIRMED: B7 drives H19')
        else:
            print(f'  WARNING: B7 does NOT directly drive H19 (H19={h19_after})')
        # Restore
        b7_cell.Value = b7_orig_value
    else:
        print(f'  B7 has formula ({b7_orig_formula}) — writing B7 directly may be blocked by formula guard')
        print('  NOTE: The endpoint uses write_sheet_cell which SKIPS cells with computed formulas.')
        print('  The formula guard in write_sheet_cell will catch =SUM, =IF, =D, etc.')
        print('  Check if B7 formula starts with a guarded prefix.')

    print('\n=== Scanning entire Recap row 19 for formula sources ===')
    print('  (Looking for cells that reference B7/B11/B12/B16/B19/B24)')
    interesting_refs = {'B7', 'B11', 'B12', 'B16', 'B19', 'B24'}
    # Check all cells in row 19
    for col_num in range(1, 30):
        cell = recap.Cells(19, col_num)
        if cell.HasFormula:
            f = cell.Formula
            found = [ref for ref in interesting_refs if ref in f]
            if found or col_num >= 7:  # always show H-N range
                letter = col_letter(col_num)
                value = cell.Value
                val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
                mark = f'  *** refs: {found}' if found else ''
                print(f'  {letter}19: {f:55s} = {val_str}{mark}')

    print('\n=== Scan of Recap rows 1-25 looking for cells that ref B7/B11/B12/B16/B19/B24 ===')
    for row in range(1, 26):
        for col_num in range(1, 30):
            cell = recap.Cells(row, col_num)
            if cell.HasFormula:
                f = cell.Formula
                found = [ref for ref in interesting_refs if ref in f]
                if found:
                    letter = col_letter(col_num)
                    value = cell.Value
                    val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
                    print(f'  {letter}{row}: {f:55s} = {val_str}  (refs: {found})')

    print('\n=== Deep inspection of rows 11-22 cols A-F (the intermediate layer) ===')
    KEY_ROWS = [7, 11, 12, 13, 15, 16, 19, 20, 21, 22]
    for row in KEY_ROWS:
        for col_num in range(1, 7):  # A-F
            cell = recap.Cells(row, col_num)
            letter = col_letter(col_num)
            has_f = cell.HasFormula
            formula = cell.Formula if has_f else '(val)'
            value = cell.Value
            val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
            if has_f or value not in (None, 0, 0.0):
                print(f'  {letter}{row}: {formula:50s} = {val_str}')

    print('\n=== Named range "Argent_Recu" resolution ===')
    try:
        for nm in wb.Names:
            if 'Argent' in nm.Name or 'argent' in nm.Name.lower():
                print(f'  Name: {nm.Name}  RefersTo: {nm.RefersTo}')
    except Exception as ex:
        print(f'  Error reading names: {ex}')

    print('\n=== What drives E16, E19, E21? ===')
    for row, col_num, label in [(16, 5, 'E16'), (19, 5, 'E19'), (21, 5, 'E21'), (15, 5, 'E15'), (13, 4, 'D13')]:
        cell = recap.Cells(row, col_num)
        has_f = cell.HasFormula
        formula = cell.Formula if has_f else '(val)'
        value = cell.Value
        val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
        print(f'  {label}: {formula:55s} = {val_str}')

    print('\n=== Trace B24 dependencies (D10 and E22) ===')
    trace_cells = [
        (10, 4, 'D10'), (22, 5, 'E22'),
        # More rows around row 10
        (8,  4, 'D8'),  (9,  4, 'D9'),  (10, 2, 'B10'), (10, 3, 'C10'),
        (10, 5, 'E10'),
    ]
    for row, col_num, label in trace_cells:
        cell = recap.Cells(row, col_num)
        has_f = cell.HasFormula
        formula = cell.Formula if has_f else '(val)'
        value = cell.Value
        val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
        print(f'  {label}: {formula:55s} = {val_str}')

    print('\n=== Rows 1-24, cols A-F: complete dump (non-empty cells) ===')
    for row in range(1, 25):
        for col_num in range(1, 7):
            cell = recap.Cells(row, col_num)
            has_f = cell.HasFormula
            formula = cell.Formula if has_f else None
            value = cell.Value
            if value is not None or has_f:
                letter = col_letter(col_num)
                val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
                f_str = formula if formula else '(val)'
                print(f'  {letter}{row}: {f_str:55s} = {val_str}')

    print('\n=== Read the ACTUAL filled Apr 23 file to see what cells were written ===')
    wb.Close(SaveChanges=False)
    print('Backup closed. Opening actual filled file...')
    FILLED_PATH = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'
    wb2 = excel.Workbooks.Open(FILLED_PATH)
    recap2 = wb2.Sheets('Recap')
    print('\n  Rows 6-24, cols A-F in FILLED file:')
    for row in range(6, 25):
        for col_num in range(1, 7):
            cell = recap2.Cells(row, col_num)
            has_f = cell.HasFormula
            formula = cell.Formula if has_f else None
            value = cell.Value
            if value is not None and value != 0:
                letter = col_letter(col_num)
                val_str = f'{value:,.2f}' if isinstance(value, (int, float)) else str(value)
                f_str = formula if formula else '(val)'
                print(f'    {letter}{row}: {f_str:55s} = {val_str}')
    print()
    print('  H19:N19 in FILLED file:')
    for r, c, lbl in TARGET_CELLS:
        cell = recap2.Cells(r, c)
        val = cell.Value
        val_str = f'{val:,.2f}' if isinstance(val, (int, float)) else str(val)
        print(f'    {lbl}: {cell.Formula if cell.HasFormula else "(val)":50s} = {val_str}')
    wb2.Close(SaveChanges=False)
    print('\nDone — both workbooks closed without saving.')

except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    try:
        excel.Quit()
    except Exception:
        pass
