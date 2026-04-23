import sys
import shutil
import xlrd
from xlutils.copy import copy as xl_copy

src = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 14-04-2026.xls'
backup = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 14-04-2026_BEFORE_JOUR_FILL.xls'

# Backup first
shutil.copy2(src, backup)
print(f'Backup: {backup}')

# Read with formatting preserved
rb = xlrd.open_workbook(src, formatting_info=True, on_demand=False)
wb = xl_copy(rb)
jour_idx = rb.sheet_names().index('jour')
ws = wb.get_sheet(jour_idx)

DAY_ROW = 15  # Day 14 = Excel row 16 = 0-indexed 15

# Only write columns that are currently EMPTY in Day 14
# Skipping: 0,1,2 (day/balouv/DC placeholder), 60-65 (CC filled), 72-78 (Recap), 95+ (existing)
to_write = {
    3:   -1932162.28,   # D  Bal_Ferm = -|NewBal 1,476,889.24| - AdvDep 455,273.04
    4:    2626.00,      # E  Pause Spesa (SJ Bqt PAUSE SPESA)
    9:    2970.04,      # J  Piazza Nour (SJ 3585 - HP 612 - adj 2.96)
    10:   1503.00,      # K  Piazza Alcool (SJ 1550 - HP Boisson 47)
    11:    539.50,      # L  Piazza Bieres (SJ 539.50 - HP 0)
    12:     91.00,      # M  Piazza Mineraux (SJ 156.50 - HP 65.5)
    13:    455.00,      # N  Piazza Vin (SJ 539 - HP 84)
    14:   1212.84,      # O  Spesa Nour (SJ 1223.89 - HP Tabagie Nour 7 - adj 4.05)
    19:    226.00,      # T  S.Ch. Nour
    21:     11.00,      # V  S.Ch. Biere
    22:      4.25,      # W  S.Ch. Min
    23:     28.00,      # X  S.Ch. Vin
    24:   8410.00,      # Y  Bqt Nour
    29:   1986.48,      # AD Pourboires (Bqt Pourb a Payer)
    31:     80.00,      # AF Divers Bqt (Bqt EQ. DIVERS)
    32:   9300.00,      # AG Location Salles
    35:    775.59,      # AJ Tabagie (SJ 1021.03 - HP 245.44)
    36:  50655.88,      # AK Chambres (DR 50,695.88 - G4 40)
    40:    257.80,      # AO Nettoyeur
    41:      0,         # AP GEAC comp (FD = AR)
    44: -157384.06,     # AS Autres GL (no DEPOT UTIL)
    46:     18.00,      # AU Autre Rev (SJ FR/Etage 18; no InterHotel today)
    48:    460.00,      # AW Internet (DR 0 + SJ Bqt Internet 460)
    49:   8304.69,      # AX TVQ = TVQ chamb 5231.01 + SJ TVQ 3047.97 + TVQ Autres 25.71 (NO F&B OPERA)
    50:   4164.44,      # AY TPS = TPS chamb 2623.45 + SJ TPS 1528.09 + TPS Autres 12.90 (NO F&B OPERA)
    51:   1775.29,      # AZ TVH
    57:   -130.16,      # BF Diff Forfait = -(SJ Forfait 170.16 - G4 40)
    61:    685.66,      # BJ Discover (X24 compensation: X24 = -685.66 weekday -> BJ = +685.66)
    68:     36.99,      # BQ HP Admin Pourb (positive)
    69:     76.35,      # BR HP Promo Pourb (positive)
    83:  -4676.36,      # CF Transfer A/R = DR FD 2384.64 - DR AR Misc 7061.00
}

print(f'\n=== Writing Day 14 (row {DAY_ROW+1}) ===')
for col, val in sorted(to_write.items()):
    ws.write(DAY_ROW, col, val)
    print(f'  {xlrd.colname(col)}{DAY_ROW+1} = {val}')

print(f'\nSaving to {src} ...')
wb.save(src)
print('Done. DC should compute to $0.')
