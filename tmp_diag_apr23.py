"""Read the Apr 23 Jour row in the CURRENT filled file vs BACKUP and print every cell.
Also zero out each col in the filled file in turn and measure DC change to find the missing amount."""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')
import win32com.client as win32

RJ_CUR = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'
RJ_BAK = RJ_CUR + '.bak.xls'
DAY = 23
ROW = DAY + 2  # row 25

def read_row(path, label):
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.AskToUpdateLinks = False
    try:
        wb = excel.Workbooks.Open(path)
        js = wb.Sheets('jour')
        row = {}
        for c in range(1, 120):
            cell = js.Cells(ROW, c)
            v = cell.Value
            f = cell.Formula if cell.HasFormula else ''
            if v not in (None, '', 0) or f:
                row[c] = (v, f)
        # Also capture DC
        dc = js.Cells(ROW, 3).Value
        wb.Close(False)
        return row, dc
    finally:
        excel.Quit()


cur, dc_cur = read_row(RJ_CUR, 'CURRENT')
bak, dc_bak = read_row(RJ_BAK, 'BACKUP')

print(f'DC current: ${dc_cur:,.2f}')
print(f'DC backup : ${dc_bak:,.2f}')
print()
print(f'{"col":<4} {"BACKUP":>15} {"CURRENT":>15} {"DELTA":>12}  formula')
print('-' * 90)
all_cols = sorted(set(cur.keys()) | set(bak.keys()))
for c in all_cols:
    bv, bf = bak.get(c, (0, ''))
    cv, cf = cur.get(c, (0, ''))
    bv = bv if isinstance(bv, (int, float)) else 0
    cv = cv if isinstance(cv, (int, float)) else 0
    delta = (cv or 0) - (bv or 0)
    marker = ' *' if abs(delta) > 0.01 else ''
    print(f'{c:<4} {bv:>15,.2f} {cv:>15,.2f} {delta:>12,.2f}  {cf or bf}{marker}')
