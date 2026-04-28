"""Bisect the $177.36 residual by zeroing each col and checking DC delta.
Identifies which column contains the excess $177.36 (or the missing amount)."""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client as win32

RJ = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'
ROW = 25
TARGET = 0.0

excel = win32.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False
try:
    wb = excel.Workbooks.Open(RJ)
    js = wb.Sheets('jour')

    dc_start = js.Cells(ROW, 3).Value
    print(f'DC start: ${dc_start:,.2f}\n')

    # Grab all non-formula, non-zero cells in row 25
    candidates = []
    for c in range(4, 120):
        cell = js.Cells(ROW, c)
        if c == 3: continue  # DC itself
        if cell.HasFormula:
            continue  # don't touch formulas (but check them)
        v = cell.Value
        if v is None or v == 0:
            continue
        candidates.append((c, v))

    # Also check formula cells (capture their computed value)
    formula_cells = []
    for c in range(4, 120):
        cell = js.Cells(ROW, c)
        if cell.HasFormula:
            v = cell.Value
            if v is not None and v != 0:
                formula_cells.append((c, v, cell.Formula))

    print(f'{len(candidates)} non-formula value cells, {len(formula_cells)} formula cells\n')
    print(f'{"col":<5} {"value":>12} {"DC after zero":>15} {"delta":>12}')
    print('-' * 55)

    # Zero each non-formula cell, measure DC, restore
    for c, v in candidates:
        cell = js.Cells(ROW, c)
        orig = cell.Value
        cell.Value = 0
        excel.Calculate()
        dc_new = js.Cells(ROW, 3).Value
        cell.Value = orig
        excel.Calculate()
        delta = dc_new - dc_start
        marker = ''
        if abs(dc_new) < abs(dc_start) - 100:
            marker = ' ★ fixes DC'
        elif abs(delta - 177.36) < 5:
            marker = ' ★ matches +177'
        elif abs(delta + 177.36) < 5:
            marker = ' ★ matches -177'
        vs = f'{v:,.2f}' if isinstance(v, (int, float)) else str(v)
        print(f'{c:<5} {vs:>12} {dc_new:>15,.2f} {delta:>+12,.2f}{marker}')

    wb.Close(False)
finally:
    excel.Quit()
