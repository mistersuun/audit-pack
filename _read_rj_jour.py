"""Read RJ JOUR sheet for day 22 and cross-check against source documents."""
import xlrd

wb = xlrd.open_workbook(r'K:\RJ 2026-2027\01-MARS 2026\Rj 22-03-2026.xls')
print('All sheets:', wb.sheet_names())

# Find the Jour sheet (case-insensitive)
jour_name = None
for name in wb.sheet_names():
    if name.lower().startswith('jour'):
        jour_name = name
        break
if not jour_name:
    print('ERROR: No Jour sheet found!')
    exit(1)
print(f'Using sheet: {jour_name}')
jour = wb.sheet_by_name(jour_name)
print(f'JOUR: {jour.nrows} rows x {jour.ncols} cols')

def col_letter(n):
    s = ''
    while n >= 0:
        s = chr(n % 26 + 65) + s
        n = n // 26 - 1
    return s

# Header rows
print('\n=== HEADER ROW 1 ===')
for col in range(min(jour.ncols, 100)):
    val = jour.cell_value(1, col)
    if val != '':
        print(f'  {col:3d} ({col_letter(col):>3s}): {val}')

# Day 22 data - row index = day + 1 = 23
row_idx = 23
print(f'\n=== ROW {row_idx} (DAY 22) - ALL NON-ZERO VALUES ===')
for col in range(min(jour.ncols, 100)):
    val = jour.cell_value(row_idx, col)
    if val != '' and val != 0 and val != 0.0:
        print(f'  {col:3d} ({col_letter(col):>3s}): {val}')

# Also print ALL values (including zeros) for key columns
# A=0, B=1, C=2, D=3, E-I=4-8, AK=36, AX=49, AY=50, BI=60, BJ-BN=61-65, CK-CR=88-95
key_cols = list(range(0, 10)) + list(range(36, 60)) + list(range(60, 70)) + list(range(76, 100))
print(f'\n=== KEY COLUMNS (including zeros) ===')
for col in key_cols:
    if col < jour.ncols:
        val = jour.cell_value(row_idx, col)
        print(f'  {col:3d} ({col_letter(col):>3s}): {val}')

# Expected values from source documents
print('\n=== EXPECTED VALUES (from source PDFs) ===')
expected = {
    'Chambres Total (AK if CL=0)': 29290.02,
    'TVQ tax (AX)': 3043.94,
    'TPS tax (AY)': 1526.11,
    'AR Transfers': 4176.58,
    'Rooms sold (CK)': 134,
    'Guests (CL)': 192,
    'Occupancy % (CM)': 53.17,
    'ADR (CN)': 239.36,
    'AX cards': 9075.13,
    'MC cards': 45976.05,
    'VI cards': 40320.28,
    'DB cards': 3167.53,
    'DlyRev New Balance': -939821.42,
}
for label, val in expected.items():
    print(f'  {label}: {val}')
