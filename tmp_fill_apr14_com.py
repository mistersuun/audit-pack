"""Fill Apr 14 Day 14 Jour row using Excel COM.
Preserves formulas, tab colors, macros. Writes formulas (=a+b-c) for transparency.
"""
import sys
import time
import win32com.client as win32

PATH = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 14-04-2026.xls'
DAY_ROW = 16  # Day 14 = Excel row 16 (1-indexed)

# Each entry: (Excel column letter, formula string, comment)
JOUR_FILL = [
    # Bal_Ferm
    ('D', '=-1476889.24-455273.04', 'Bal_Ferm = -|NewBal| - AdvDep'),
    # F&B from SJ
    ('E', '=2626', 'Pause Spesa (SJ Bqt PAUSE SPESA)'),
    ('J', '=3585-612-2.96', 'Piazza Nour (SJ - HP 612 - adj 2.96)'),
    ('K', '=1550-47', 'Piazza Alcool (SJ - HP Boisson 47)'),
    ('L', '=539.5', 'Piazza Bieres (SJ, no HP)'),
    ('M', '=156.5-65.5', 'Piazza Min (SJ - HP 65.5)'),
    ('N', '=539-84', 'Piazza Vin (SJ - HP 84)'),
    ('O', '=1223.89-7-4.05', 'Spesa Nour (SJ - HP Tabagie 7 - adj 4.05)'),
    ('T', '=226', 'S.Ch. Nour (SJ)'),
    ('V', '=11', 'S.Ch. Biere'),
    ('W', '=4.25', 'S.Ch. Min'),
    ('X', '=28', 'S.Ch. Vin'),
    ('Y', '=8410', 'Bqt Nour'),
    ('AD', '=1986.48', 'Pourb a Payer (Bqt)'),
    ('AF', '=80', 'Divers Bqt (EQ. DIVERS)'),
    ('AG', '=9300', 'Location Salles (Bqt)'),
    ('AJ', '=1021.03-245.44', 'Tabagie (SJ - HP 245.44)'),
    # Chambres
    ('AK', '=50695.88-40', 'Chambres (DR - G4 40)'),
    # DR autres
    ('AO', '=257.8', 'Nettoyeur (DR p.2)'),
    ('AP', '=0', 'GEAC comp (FD = AR)'),
    ('AS', '=-157384.06', 'Autres GL (DR p.2, no DEPOT UTIL)'),
    ('AU', '=18', 'Autre Rev (SJ FR/Etage 18; no InterHotel)'),
    ('AW', '=0+460', 'Internet (DR Internet 0 + SJ Bqt Internet 460)'),
    # Taxes per methodology (NO F&B OPERA taxes)
    ('AX', '=5231.01+3047.97+25.71', 'TVQ (Chamb + SJ + Autres)'),
    ('AY', '=2623.45+1528.09+12.9', 'TPS (Chamb + SJ + Autres)'),
    ('AZ', '=1775.29', 'TVH'),
    ('BF', '=-(170.16-40)', 'Diff Forfait = -(SJ Forfait - G4)'),
    # X24 compensation
    ('BJ', '=685.66', 'Discover (X24 = -685.66 weekday -> +685.66)'),
    # HP pourboires (positive debits)
    ('BQ', '=36.99', 'HP Admin Pourb'),
    ('BR', '=76.35', 'HP Promo Pourb'),
    # CF includes AR Misc as negative
    ('CF', '=2384.64-7061', 'Transfer A/R = DR FD - DR AR Misc'),
]

def col_to_num(letter):
    """Excel column letter -> number (A=1, Z=26, AA=27...)"""
    n = 0
    for ch in letter.upper():
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n

excel = win32.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False

try:
    print(f'Opening {PATH}...')
    wb = excel.Workbooks.Open(PATH)
    ws = wb.Sheets('jour')
    print(f'Opened jour sheet. Writing Day 14 formulas to row {DAY_ROW}...\n')

    for col_letter, formula, comment in JOUR_FILL:
        col_num = col_to_num(col_letter)
        cell = ws.Cells(DAY_ROW, col_num)
        cell.Formula = formula
        # Read back computed value
        time.sleep(0.01)
        val = cell.Value
        print(f'  {col_letter}{DAY_ROW} = {formula!r:35s} -> {val}  [{comment}]')

    # Read DC after fill
    dc = ws.Cells(DAY_ROW, col_to_num('C')).Value
    print(f'\n=== DC (C{DAY_ROW}) = {dc} ===')

    print(f'\nSaving (preserving format/macros)...')
    wb.Save()
    wb.Close()
    print('Saved successfully.')
finally:
    excel.Quit()
