"""Inspect DBRS sheet structure in the Apr 21 RJ to understand the layout."""
import sys, io
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

import xlrd

RJ_PATH = r'C:\Users\Auditeur\Documents\Projects\audit-pack\.playwright-mcp\test-files\Rj 21-04-2026-balanced.xls'

wb = xlrd.open_workbook(RJ_PATH, formatting_info=False)
print('=== Sheet names ===')
for name in wb.sheet_names():
    print(f'  {name!r}')

# Find DBRS-like sheet (case-insensitive)
dbrs_candidates = [n for n in wb.sheet_names() if 'dbrs' in n.lower() or 'dbr' in n.lower() or 'seg' in n.lower() or 'market' in n.lower()]
print(f'\n=== DBRS candidate sheets: {dbrs_candidates} ===\n')

for sheet_name in wb.sheet_names():
    # Show any sheet that might be DBRS
    if 'dbrs' in sheet_name.lower() or sheet_name.lower() in ('dbrs', 'dbr'):
        sh = wb.sheet_by_name(sheet_name)
        print(f'--- Sheet: {sheet_name!r}  rows={sh.nrows} cols={sh.ncols} ---')
        for r in range(min(sh.nrows, 60)):
            row_vals = []
            for c in range(min(sh.ncols, 20)):
                v = sh.cell_value(r, c)
                if v != '' and v is not None:
                    row_vals.append(f'{chr(65+c) if c<26 else "?"}{r+1}={v!r}')
            if row_vals:
                print(f'  row{r+1}: ' + ' | '.join(row_vals))
