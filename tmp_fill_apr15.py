"""Fill Apr 15 (Day 15, row 17) — Transelect + GEAC + Jour via Excel COM."""
import win32com.client as win32
import shutil, time

PATH = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 15-04-2026.xls'
BACKUP = PATH.replace('.xls', '_BAK.xls')
shutil.copy2(PATH, BACKUP)
print(f'Backup: {BACKUP}')

DAY_ROW = 17  # Day 15 = Excel row 17

def col_num(letter):
    n = 0
    for ch in letter.upper():
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n

excel = win32.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False

try:
    wb = excel.Workbooks.Open(PATH)

    # ==================== TRANSELECT ====================
    ws = wb.Sheets('transelect')
    print('\n=== TRANSELECT ===')

    # Restaurant POSITOUCH (col X=24) from SJ
    trx = {(9,24): 568.08, (10,24): 1782.26, (11,24): 912.63, (13,24): 310.23}
    # Restaurant TOTAL 1 (col V=22) estimated = SJ - pannes
    trx.update({(9,22): 550.59, (10,22): 1719.76, (11,22): 912.63, (13,22): 310.23})
    # Reception Bank Report (col B=2) + Daily Revenue (col P=16)
    trx.update({
        (21,2): 12126.86, (21,16): 12126.86,  # VISA
        (22,2): 9945.62,  (22,16): 9945.62,   # MASTER
        (24,2): 7576.83,  (24,16): 7576.83,   # AMEX
    })
    for (r,c), val in sorted(trx.items()):
        cell = ws.Cells(r, c)
        if not cell.HasFormula:
            cell.Value = val
            print(f'  R{r}C{c} = {val}')

    # ==================== GEAC ====================
    ws = wb.Sheets('geac_ux')
    print('\n=== GEAC ===')

    geac = {
        # Top: Card variance (B=2, G=7, J=10)
        (6,2): '=7576.83-5707.24',    # AMEX Cash Out
        (6,7): '=9945.62-474.09',     # MC Cash Out
        (6,10): '=12126.86-993.65',   # VISA Cash Out
        (8,2): '=5707.24',            # AMEX Dep
        (8,7): '=474.09',             # MC Dep
        (8,10): '=993.65',            # VISA Dep
        (12,2): '=7576.83',           # AMEX Daily Rev
        (12,7): '=9945.62',           # MC Daily Rev
        (12,10): '=12126.86',         # VISA Daily Rev
        # Bottom: Balance Sheet
        (32,2): '=1476889.24',        # B32 Bal Prev Day
        (32,5): '=1476889.24',        # E32 Yesterday ending
        (37,2): '=66631.01',          # B37 Bal Today
        (37,5): '=-66631.01',         # E37 Credit Activities
        (41,2): '=1641.73',           # B41 FD
        (41,7): '=5197.27',           # G41 AR Guest Folios (!=FD)
        (44,2): '=64522.13',          # B44 Adv Dep Applied
        (44,10): '=64522.13',         # J44
        (53,2): '=1543520.25',        # B53 New Balance
        (53,5): '=1543520.25',        # E53 ending balance
    }
    for (r,c), val in sorted(geac.items()):
        cell = ws.Cells(r, c)
        if not cell.HasFormula:
            cell.Formula = str(val)
            print(f'  R{r}C{c} = {val}')

    # ==================== JOUR ====================
    ws = wb.Sheets('jour')
    print(f'\n=== JOUR row {DAY_ROW} ===')

    jour = {
        col_num('D'):  '=-1543520.25-397611.02',       # Bal_Ferm
        col_num('E'):  '=4115',                          # Pause Spesa
        col_num('J'):  '=2828.5-195',                    # Piazza Nour - HP
        col_num('K'):  '=206',                           # Piazza Alcool
        col_num('L'):  '=241',                           # Piazza Bieres
        col_num('M'):  '=34-21',                         # Piazza Min - HP
        col_num('N'):  '=364',                           # Piazza Vins
        col_num('O'):  '=1116.57-3.4',                   # Spesa Nour - adj
        col_num('T'):  '=276',                           # SCh Nour
        col_num('U'):  '=15',                            # SCh Alcool
        col_num('W'):  '=15.5',                          # SCh NAB
        col_num('X'):  '=36',                            # SCh Vin
        col_num('Y'):  '=12375',                         # Bqt Nour
        col_num('AD'): '=2957.76',                       # Pourboires
        col_num('AE'): '=-966.61',                       # Eq AV (DEBIT=negative)
        col_num('AF'): '=80',                            # Divers Bqt
        col_num('AG'): '=14650',                         # Location Salles
        col_num('AJ'): '=731.95-198.4',                  # Tabagie - HP
        col_num('AK'): '=499.01-60',                     # Chambres - G4
        col_num('AO'): '=298.7',                         # Nettoyeur
        col_num('AP'): '=-(1641.73-5197.27)',             # GEAC comp (FD<AR -> positive)
        col_num('AS'): '=-8269.7',                       # Autres GL
        col_num('AU'): '=27',                            # FR/Etage (no InterHotel)
        col_num('AW'): '=0+460',                         # Internet (DR 0 + SJ Bqt 460)
        col_num('AX'): '=51.49+3891.46+29.8',            # TVQ (Chamb+SJ+Autres NO F&B OPERA)
        col_num('AY'): '=25.81+1950.85+14.94',           # TPS (same rule)
        col_num('AZ'): '=17.5',                          # TVH
        col_num('BF'): '=-(142.6-60)',                    # Diff Forfait
        col_num('BI'): '=7576.83',                       # AMEX Elavon (Reception)
        col_num('BJ'): '=0',                             # Discover (no comp)
        col_num('BK'): '=9945.62+912.63',                # MC (Recept+Rest bank)
        col_num('BL'): '=12126.86+1719.76',              # Visa (Recept+Rest est)
        col_num('BM'): '=550.59',                        # Debit (Rest bank est)
        col_num('BN'): '=310.23',                        # AMEX Global (Rest)
        col_num('BQ'): '=35.68',                         # HP Admin Pourb
        col_num('BR'): '=0',                             # HP Promo Pourb (none)
        col_num('CF'): '=1641.73',                       # Transfer AR (FD only, AR Misc=0)
    }

    for c, formula in sorted(jour.items()):
        cell = ws.Cells(DAY_ROW, c)
        if cell.HasFormula and cell.Formula.startswith('=') and cell.Formula not in (f'={formula[1:]}',):
            # Check if it's a built-in formula like B/C/CW etc
            existing = cell.Formula
            if any(existing.startswith(p) for p in ['=D', '=SUM', '=ROUND', '=IF']):
                print(f'  SKIP {chr(64+c) if c<27 else ""}{DAY_ROW}: existing formula {existing}')
                continue
        cell.Formula = formula
        time.sleep(0.01)
        val = cell.Value
        def cl(n):
            s=''
            while n>0: n,r=divmod(n-1,26); s=chr(65+r)+s
            return s
        print(f'  {cl(c)}{DAY_ROW} = {formula:40s} -> {val}')

    # Force recalc
    excel.Calculate()
    time.sleep(0.2)
    dc = ws.Cells(DAY_ROW, 3).Value
    print(f'\n=== DC (C{DAY_ROW}) = {dc} ===')

    wb.Save()
    print('Saved.')
    wb.Close()
finally:
    excel.Quit()
