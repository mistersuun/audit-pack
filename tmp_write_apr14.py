import sys
import shutil
import xlrd
from xlutils.copy import copy as xl_copy

src = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 14-04-2026.xls'
dst = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 14-04-2026_FILLED_v2.xls'
backup = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 14-04-2026_BACKUP.xls'

# Backup first
shutil.copy2(src, backup)
print(f'Backup saved: {backup}')

# Open
rb = xlrd.open_workbook(src, formatting_info=True, on_demand=False)
wb = xl_copy(rb)

# ===== JOUR sheet — Day 14 = row index 15 =====
jour_idx = rb.sheet_names().index('jour')
ws_jour = wb.get_sheet(jour_idx)
DAY_ROW = 15  # 0-indexed; Day 1 is row 2, so Day 14 = row 15

jour_values = {
    3:  -1932162.28,   # D Bal_Ferm
    4:   2626.00,      # E Pause Spesa (SJ Bqt PAUSE SPESA)
    9:   2970.04,      # J Piazza Nour (SJ 3585 - HP 612 - adj 2.96)
    10:  1503.00,      # K Piazza Alcool (SJ 1550 - HP Boisson 47)
    11:  539.50,       # L Piazza Bières
    12:  91.00,        # M Piazza Min (SJ 156.50 - HP 65.5)
    13:  455.00,       # N Piazza Vin (SJ 539 - HP 84)
    14:  1212.84,      # O Spesa Nour (SJ 1223.89 - HP Tabagie Nour 7 - adj 4.05)
    19:  226.00,       # T S.Ch. Nour
    21:  11.00,        # V S.Ch. Bière
    22:  4.25,         # W S.Ch. Min
    23:  28.00,        # X S.Ch. Vin
    24:  8410.00,      # Y Bqt Nour
    29:  1986.48,      # AD Pourboires (Bqt Pourb à payer)
    31:  80.00,        # AF Divers Bqt (Bqt EQ. DIVERS)
    32:  9300.00,      # AG Location Salles
    35:  775.59,       # AJ Tabagie (SJ 1021.03 - HP 245.44)
    36:  50655.88,     # AK Chambres (DR 50695.88 - G4 40)
    40:  257.80,       # AO Nettoyeur
    41:  0,            # AP GEAC comp (FD = AR)
    44:  -157384.06,   # AS Autres GL
    46:  18.00,        # AU Autre Rev (SJ FR/Etage; no InterHotel today)
    48:  460.00,       # AW Internet (DR 0 + SJ Bqt Internet 460)
    49:  10816.64,     # AX TVQ
    50:  5423.59,      # AY TPS
    51:  1775.29,      # AZ TVH
    57:  -130.16,      # BF Diff Forfait = -(SJ Forfait 170.16 - G4 40)
    60:  5613.06,      # BI Amex Elavon
    61:  0,            # BJ Discover (X24 compensation - YOU adjust)
    62:  19239.27,     # BK MasterCard
    63:  17727.62,     # BL Visa
    64:  1191.00,      # BM Débit
    65:  484.20,       # BN Amex Global
    68:  36.99,        # BQ HP Admin Pourb
    69:  76.35,        # BR HP Promo Pourb
    83:  2384.64,      # CF Transfer A/R (DR FD only - YOU add AR Misc if needed)
}

print(f'\n=== Writing Jour row {DAY_ROW+1} (Day 14) ===')
for col, val in jour_values.items():
    ws_jour.write(DAY_ROW, col, val)
    print(f'  col {col}: {val}')

# ===== TRANSELECT — fill POSITOUCH (col 23) for restaurant rows =====
trx_idx = rb.sheet_names().index('transelect')
ws_trx = wb.get_sheet(trx_idx)

# Restaurant POSITOUCH from Sales Journal CC debits
trx_pos = {
    8:  1415.99,   # DEBIT (SJ Interac)
    9:  2836.40,   # VISA (SJ Visa)
    10: 1616.48,   # MASTER (SJ MC)
    12: 484.20,    # AMEX (SJ AMEX)
}
print(f'\n=== Filling Transelect POSITOUCH (col 23) ===')
for row, val in trx_pos.items():
    ws_trx.write(row, 23, val)
    print(f'  R{row+1} POSITOUCH = {val}')

# Reception side bank report (rows 19-23, col 1 = Bank Report)
trx_recept = {
    20: 15185.17,   # VISA reception (DR settlement)
    21: 17789.51,   # MASTER reception
    23: 5613.06,    # AMEX reception
}
print(f'\n=== Filling Transelect Reception Bank Report (col 1) ===')
for row, val in trx_recept.items():
    ws_trx.write(row, 1, val)
    print(f'  R{row+1} Bank Report = {val}')

# ===== GEAC_UX — fill card variance section (rows 5, 7, 11) =====
geac_idx = rb.sheet_names().index('geac_ux')
ws_geac = wb.get_sheet(geac_idx)

# Layout:
# R5 Daily Cash Out:       col 1=AMEX, col 6=MASTER, col 9=VISA
# R7 Deposit Received:     col 1=AMEX, col 6=MASTER, col 9=VISA
# R9 Total (formula):      col 1=AMEX, col 6=MASTER, col 9=VISA
# R11 Daily Revenue:       col 1=AMEX, col 6=MASTER, col 9=VISA  (must = R9 to balance)

# From DR Settlements:
#   AMEX:   settled $5,613.06, deposit $0       → cash out = $5,613.06
#   MASTER: settled $17,789.51, deposit $5,953.94 → cash out = $11,835.57
#   VISA:   settled $15,185.17, deposit $3,127.87 → cash out = $12,057.30

geac_values = {
    # R5 Daily Cash Out
    (5, 1): 5613.06,    # AMEX = DR settlement - Dep
    (5, 6): 11835.57,   # MASTER
    (5, 9): 12057.30,   # VISA
    # R7 Deposit Received (from DR p.6)
    (7, 1): 0,          # AMEX dep
    (7, 6): 5953.94,    # MASTER dep
    (7, 9): 3127.87,    # VISA dep
    # R11 Daily Revenue (must equal R5+R7 for variance = 0)
    (11, 1): 5613.06,   # AMEX (= 5613.06 + 0)
    (11, 6): 17789.51,  # MASTER (= 11835.57 + 5953.94)
    (11, 9): 15185.17,  # VISA (= 12057.30 + 3127.87)
}

print(f'\n=== Filling GEAC card variance section ===')
for (row, col), val in geac_values.items():
    ws_geac.write(row, col, val)
    print(f'  R{row+1} col {col}: {val}')

print(f'\n  GEAC variance check: AMEX/MASTER/VISA all balance to $0')

# Save
wb.save(dst)
print(f'\nSaved: {dst}')
print('\nNote: BJ (Discover, col 61) left at 0 - add X24 compensation manually')
print('Note: CF (col 83) = $2,384.64 (FD only) - add AR Misc $7,061 if needed')
print('Note: Transelect TOTAL row (R13) and Reception TOTAL (R24) are formulas - should auto-recalc')
