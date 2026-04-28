"""Compare my Apr 23 row (25) fill vs the auditor's Apr 22 (row 24) in backup — find cols I forgot."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client as win32

RJ_CUR = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'
RJ_BAK = RJ_CUR + '.bak.xls'

def read_row(path, row_num):
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.AskToUpdateLinks = False
    try:
        wb = excel.Workbooks.Open(path)
        js = wb.Sheets('jour')
        out = {}
        for c in range(1, 120):
            cell = js.Cells(row_num, c)
            v = cell.Value
            f = cell.Formula if cell.HasFormula else ''
            if v not in (None, '', 0) or f:
                out[c] = (v, f)
        wb.Close(False)
        return out
    finally:
        excel.Quit()

apr22 = read_row(RJ_BAK, 24)  # yesterday (full)
apr23 = read_row(RJ_CUR, 25)  # my fill

print(f'{"col":<4} {"Apr22 (backup)":>16} {"Apr23 (my fill)":>18}  label')
print('-' * 90)
for c in sorted(set(apr22.keys()) | set(apr23.keys())):
    v22, f22 = apr22.get(c, (0, ''))
    v23, f23 = apr23.get(c, (0, ''))
    v22n = v22 if isinstance(v22, (int, float)) else 0
    v23n = v23 if isinstance(v23, (int, float)) else 0
    # Flag cols where Apr 22 has data but Apr 23 doesn't
    in_22 = abs(v22n) > 0.01 or f22
    in_23 = abs(v23n) > 0.01 or f23
    if in_22 and not in_23:
        mark = ' <-- MISSED in 23'
    elif in_23 and not in_22:
        mark = ' <-- EXTRA in 23'
    else:
        mark = ''
    print(f'{c:<4} {v22n:>16,.2f} {v23n:>18,.2f}  {f23 or f22}{mark}')
