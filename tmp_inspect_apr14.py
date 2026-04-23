"""Inspect Apr 14 RJ jour Day 14 + Day 13 cell-by-cell.
Reads formulas (not just values) so we know which cells are computed vs manual.
"""
import win32com.client as win32

PATH = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 14-04-2026.xls'

def col_letter(n):
    """1-indexed col number to letter"""
    s = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

excel = win32.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False

try:
    wb = excel.Workbooks.Open(PATH)
    ws = wb.Sheets('jour')

    # Header from row 1 + 2 (col labels)
    print('=== HEADER (row 1 + 2) ===')
    for c in range(1, 117):
        h1 = ws.Cells(1, c).Value
        h2 = ws.Cells(2, c).Value
        if h1 or h2:
            label = col_letter(c)
            print(f'  {label}({c}): row1={h1!r} row2={h2!r}')

    # Day 13 (row 15) reference - already filled, balanced
    print('\n=== DAY 13 (row 15) - REFERENCE ===')
    for c in range(1, 117):
        cell = ws.Cells(15, c)
        if cell.Formula or cell.Value not in (None, '', 0):
            label = col_letter(c)
            f = cell.Formula
            v = cell.Value
            is_formula = cell.HasFormula
            tag = 'FORMULA' if is_formula else 'VALUE'
            print(f'  {label}15 [{tag}]: formula={f!r}  value={v!r}')

    # Day 14 (row 16) current state
    print('\n=== DAY 14 (row 16) - CURRENT STATE ===')
    for c in range(1, 117):
        cell = ws.Cells(16, c)
        if cell.Formula or cell.Value not in (None, '', 0):
            label = col_letter(c)
            f = cell.Formula
            v = cell.Value
            is_formula = cell.HasFormula
            tag = 'FORMULA' if is_formula else 'VALUE'
            print(f'  {label}16 [{tag}]: formula={f!r}  value={v!r}')

    wb.Close(SaveChanges=False)
finally:
    excel.Quit()
