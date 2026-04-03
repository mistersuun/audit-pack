import sys, xlrd
sys.path.insert(0, '.')

from utils.rj_filler import RJFiller
from utils.rj_mapper import get_jour_row_for_day, TRANSELECT_TO_JOUR_CARD_MAP, TRANSELECT_TOTAUX_ROW, JOUR_RECAP_SOURCE
from utils.parsers.sales_journal_parser import SalesJournalParser
from utils.parsers.daily_revenue_parser import DailyRevenueParser
from utils.parsers.ar_summary_parser import ARSummaryParser
from utils.parsers.hp_excel_parser import HPExcelParser

DAY = 24
G4  = 80.0  # Club Lounge forfait (manual daily value)
# Update this path to match the actual HP file for March 2026
HP_FILE = 'K:/HP_Mars_2026.xlsx'

def fv(v):
    try: return float(v)
    except: return 0.0

print('=' * 65)
print('STEP 1 — PARSE SOURCE DOCUMENTS')
print('=' * 65)

with open('K:/sALES_Journal_24th_March.txt', 'rb') as f:
    sj = SalesJournalParser(f.read(), 'sALES_Journal_24th_March.txt')
sj.parse()
sj_dep = sj.extracted_data.get('departments', {})
sj_pmt = sj.extracted_data.get('payments', {})
sj_tax = sj.extracted_data.get('taxes', {})
sj_adj = sj.extracted_data.get('adjustments', {})
print('SJ  OK  total_balanced=%.2f' % sj.extracted_data.get('total_balanced', 0))

with open('K:/Daily_Rev_24th.pdf', 'rb') as f:
    dr = DailyRevenueParser(f.read(), 'Daily_Rev_24th.pdf')
dr.parse()
dr_rev = dr.extracted_data.get('revenue', {})
dr_tax = dr.extracted_data.get('non_revenue', {}).get('chambres_tax', {})
dr_set = dr.extracted_data.get('settlements', {})
print('DR  OK  date=%s' % dr.extracted_data.get('report_date', '?'))

with open('K:/AR_Sum_24th.pdf', 'rb') as f:
    ar = ARSummaryParser(f.read(), 'AR_Sum_24th.pdf')
ar.parse()
ar_cf = ar.extracted_data.get('ar_transfers', 0)
if not ar_cf:
    ar_cf = ar.extracted_data.get('rj_mapping', {}).get('geac_ux', {}).get('ar_transfers', 0)
print('AR  OK  balanced=%s  CF=%.2f' % (ar.extracted_data.get('balanced'), ar_cf))

with open(HP_FILE, 'rb') as f:
    hp = HPExcelParser(f.read(), HP_FILE, day=DAY)
hp.parse()
hp_deductions = hp.get_daily_deductions(DAY)
print('HP  OK  day=%d  deductions=%s' % (DAY, {k: round(v,2) for k,v in hp_deductions.items()}))
print('        BQ=%.2f  BR=%.2f' % (hp.extracted_data.get(f'day_{DAY}_bq_tips', 0),
                                     hp.extracted_data.get(f'day_{DAY}_br_tips', 0)))

print()
print('=' * 65)
print('STEP 2 — LOAD RJ23, FILL TRANSELECT')
print('=' * 65)

filler = RJFiller('K:/RJ 2026-2027/01-MARS 2026/Rj 23-03-2026.xls')
ts = filler._get_sheet_by_name('transelect')

# Load Correction to copy terminal slip data (manually entered by auditor from physical slips)
corr_wb     = xlrd.open_workbook('K:/RJ 2026-2027/01-MARS 2026/Rj 24-03-2026 - Correction.xls', formatting_info=True)
corr_ts     = corr_wb.sheet_by_name('transelect')
corr_recap  = corr_wb.sheet_by_name('Recap')

# Copy Correction Transelect rows 6-13 (POS terminal slip section, all columns)
# This represents what the auditor physically enters from terminal slips.
# It CANNOT be derived from the SJ because terminal slips ≠ Positouch system totals
# (the difference is the -2,248.90 Diff.Caisse variance).
print('Copying terminal slip section from Correction (rows 6-13, manual entry)...')
for r in range(6, 14):
    for c in range(corr_ts.ncols):
        v = corr_ts.cell_value(r, c)
        if v != '' and v != 0.0:
            ts.write(r, c, v)

# SJ fills col X (Positouch system total) — used for variance calculation X20
POSITOUCH_COL = 23
sj_pos_total = (sj_pmt.get('interac',0) + sj_pmt.get('visa',0)
                + sj_pmt.get('mastercard',0) + sj_pmt.get('amex',0))
ts.write(13, POSITOUCH_COL, sj_pos_total)
print('Positouch col X (SJ system total): %.2f' % sj_pos_total)

# DR fills FreedomPay section (rows 19-24, col B=1) — label swap applied
FREEDOMPAY_COL = 1
ts.write(19, FREEDOMPAY_COL, abs(dr_set.get('carte_debit', 0)))
ts.write(20, FREEDOMPAY_COL, abs(dr_set.get('american_express', 0)))  # PDF AmEx -> GEAC Visa
ts.write(21, FREEDOMPAY_COL, abs(dr_set.get('mastercard', 0)))
ts.write(22, FREEDOMPAY_COL, 0.0)
ts.write(23, FREEDOMPAY_COL, abs(dr_set.get('visa', 0)))              # PDF Visa -> GEAC AmEx
fp_total = (abs(dr_set.get('carte_debit',0)) + abs(dr_set.get('american_express',0))
            + abs(dr_set.get('mastercard',0)) + abs(dr_set.get('visa',0)))
ts.write(24, FREEDOMPAY_COL, fp_total)
print('FreedomPay col B (from DR): DEBIT=%.2f VISA=%.2f MASTER=%.2f AMEX=%.2f  TOTAL=%.2f'
      % (abs(dr_set.get('carte_debit',0)), abs(dr_set.get('american_express',0)),
         abs(dr_set.get('mastercard',0)), abs(dr_set.get('visa',0)), fp_total))

# Row 37 = FreedomPay amounts + terminal slip amounts (from Correction row 31 TOTAUX TRANSELECT)
# In the live Excel file this is formula-driven; we write it directly for the test.
corr_ts_row31 = corr_ts.row_values(31)  # TOTAUX TRANSELECT (terminal slip breakdown)
ts_combined = {
    0: abs(dr_set.get('visa', 0)),                                           # amex_elavon  (FP only)
    1: 0.0,                                                                   # discover
    2: abs(dr_set.get('mastercard',0)) + fv(corr_ts_row31[6]),               # master (FP+slips)
    3: abs(dr_set.get('american_express',0)) + fv(corr_ts_row31[8]),         # visa   (FP+slips)
    4: abs(dr_set.get('carte_debit',0))      + fv(corr_ts_row31[15]),        # debit  (FP+slips)
    5: fv(corr_ts_row31[16]),                                                 # amex_global (slips only)
}
for c, v in ts_combined.items():
    ts.write(37, c, v)
lbl = ['amex_el','discover','master','visa','debit','amex_gl']
print('Row37 (FP + terminal slips): %s'
      % '  '.join('%s=%.2f'%(lbl[c],v) for c,v in ts_combined.items()))

print()
print('=' * 65)
print('STEP 3 — FILL JOUR DAY %d REVENUE COLUMNS' % DAY)
print('=' * 65)

piazza  = sj_dep.get('piazza',  {})
chbr    = sj_dep.get('chambres',{})
banquet = sj_dep.get('banquet', {})
spesa   = sj_dep.get('spesa',   {})

corr_jour = corr_wb.sheet_by_name('jour')
jour_row   = get_jour_row_for_day(DAY)
non_rev = dr.extracted_data.get('non_revenue', {})
# Combined TVQ/TPS: chambres + autres_revenus + internet + comptabilite (non-revenue section)
dr_tvq_total = non_rev.get('total_tvq', dr_tax.get('tvq', 0))
dr_tps_total = non_rev.get('total_tps', dr_tax.get('tps', 0))

jour_fills = {
    3:  fv(corr_jour.cell_value(jour_row, 3)),  # D new_bal (DR p7 + Advance Deposit doc)
    # F&B revenue cols: SJ gross − HP food deductions
    9:  piazza.get('nourriture', 0)  - hp_deductions.get(9, 0),
    10: piazza.get('boisson', 0)     - hp_deductions.get(10, 0),
    11: piazza.get('bieres', 0)      - hp_deductions.get(11, 0),
    12: piazza.get('mineraux', 0)    - hp_deductions.get(12, 0),
    13: piazza.get('vins', 0)        - hp_deductions.get(13, 0),
    14: spesa.get('nourriture', 0)   - hp_deductions.get(14, 0),
    19: chbr.get('nourriture', 0)    - hp_deductions.get(19, 0),
    22: chbr.get('mineraux', 0)      - hp_deductions.get(22, 0),
    24: banquet.get('nourriture', 0) - hp_deductions.get(24, 0),
    29: piazza.get('pourboire_a_payer',0) + banquet.get('pourboire_a_payer',0),
    32: piazza.get('location_salle',0) + banquet.get('location_salle',0),
    35: spesa.get('tabagie', 0)      - hp_deductions.get(35, 0),
    36: dr_rev.get('chambres',{}).get('total',0) - G4,
    44: dr_rev.get('comptabilite',{}).get('total',0),
    46: chbr.get('fr_etage', 0),
    48: dr_rev.get('internet',{}).get('total',0),
    # TVQ/TPS: all non-revenue departments (chambres + autres_revenus + internet + comptabilite)
    49: dr_tvq_total + sj_tax.get('tvq',0),
    50: dr_tps_total + sj_tax.get('tps',0),
    51: dr_tax.get('taxe_hebergement',0),
    54: dr_rev.get('autres_revenus',{}).get('total',0),
    57: -sj_adj.get('forfait',0) + G4,
    # HP tips: direct values (not deductions from other cols)
    68: hp_deductions.get(68, 0),  # BQ: Admin HP tips
    69: hp_deductions.get(69, 0),  # BR: Promo HP tips
    83: ar_cf,
}

jour_sheet = filler._get_sheet_by_name('jour')
for col, val in jour_fills.items():
    jour_sheet.write(jour_row, col, val)
print('%d revenue cells written to Jour row %d (day %d).' % (len(jour_fills), jour_row, DAY))

print()
print('=' * 65)
print('STEP 4 — RUN MACROS')
print('=' * 65)

# calcul_carte: Transelect row37 -> Jour BI/BJ/BK/BL/BM/BN
# calcul_carte reads from self.rb (xlrd). We must save+reload so the
# Transelect writes are visible to the read path.
import io as _io
buf = filler.save_to_bytes()
buf_bytes = buf.read() if hasattr(buf, 'read') else buf.getvalue()
filler = RJFiller(_io.BytesIO(buf_bytes))
result_cc = filler.calcul_carte(DAY)
print('calcul_carte  -> %s' % result_cc.get('card_totals'))

# For envoie_jour, copy Recap H19:N19 from Correction (DR fills this in production)
recap_sheet = filler._get_sheet_by_name('Recap')
recap_vals = {}
for i in range(7):
    src_col = JOUR_RECAP_SOURCE['cols'][i]
    v = fv(corr_recap.cell_value(18, src_col))
    recap_sheet.write(18, src_col, v)
    recap_vals[src_col] = v
print('Recap H19:N19 (from Correction): %s' % {k: round(v,2) for k,v in recap_vals.items()})

# Save+reload again so envoie_jour sees the Recap writes
buf2 = filler.save_to_bytes()
buf2_bytes = buf2.read() if hasattr(buf2, 'read') else buf2.getvalue()
filler = RJFiller(_io.BytesIO(buf2_bytes))
result_ej = filler.envoie_dans_jour(DAY)
print('envoie_jour   -> %s' % result_ej)

print()
print('=' * 65)
print('STEP 5 — COMPARE WITH CORRECTION RJ')
print('=' * 65)

saved_buf = filler.save_to_bytes()
saved     = saved_buf.read() if hasattr(saved_buf, 'read') else saved_buf.getvalue()
check_wb  = xlrd.open_workbook(file_contents=saved)
sim_row  = check_wb.sheet_by_name('jour').row_values(jour_row)
corr_row = corr_wb.sheet_by_name('jour').row_values(jour_row)

col_names = {
    9:'J  Piazza Nourr', 10:'K  Alcool', 11:'L  Bieres', 12:'M  Mineraux',
    13:'N  Vins', 14:'O  Spesa Nourr', 19:'T  ChSvc Nourr', 22:'W  ChSvc Min',
    24:'Y  Banquet Nourr', 29:'AD Pourboires', 32:'AG Loc Salles',
    35:'AJ Tabagie', 36:'AK Chambres', 44:'AS Autres GL', 46:'AU FR_Etage',
    48:'AW Internet', 49:'AX TVQ', 50:'AY TPS', 51:'AZ Tax Heberg',
    54:'BC Autres Rev', 57:'BF Forfait',
    60:'BI AmexElavon', 61:'BJ Discover', 62:'BK Master', 63:'BL Visa',
    64:'BM Debit', 65:'BN AmexGlobal',
    68:'BQ HP Admin (tips)', 69:'BR HP Promo (tips)',
    72:'BU Cash', 73:'BV Remb', 74:'BW Gratuite', 76:'BY DueBack',
    78:'CA Surplus', 83:'CF AR Transfer'
}

print('%-22s %12s %12s %8s' % ('Column','Simulated','Correction','Delta'))
print('-'*58)
for c in sorted(col_names.keys()):
    sv = fv(sim_row[c]);  cv = fv(corr_row[c])
    d  = sv - cv
    flag = '  <-- HP' if abs(d) > 0.01 else ''
    if abs(sv) > 0.001 or abs(cv) > 0.001:
        print('%-22s %12.2f %12.2f %+8.2f%s' % (col_names[c], sv, cv, d, flag))

# Diff.Caisse
B  = fv(sim_row[1]);  D  = fv(sim_row[3])
Bc = fv(corr_row[1]); Dc = fv(corr_row[3])
E_BF_s  = sum(fv(sim_row[c])  for c in range(4,58))
BI_CI_s = sum(fv(sim_row[c])  for c in range(60,87))
diff_s  = (D  - B)  - (E_BF_s  - BI_CI_s)
E_BF_c  = sum(fv(corr_row[c]) for c in range(4,58))
BI_CI_c = sum(fv(corr_row[c]) for c in range(60,87))
diff_c  = (Dc - Bc) - (E_BF_c - BI_CI_c)

print()
print('%-22s %12s %12s' % ('', 'Simulated', 'Correction'))
print('%-22s %12.2f %12.2f' % ('E:BF  (revenue)', E_BF_s, E_BF_c))
print('%-22s %12.2f %12.2f' % ('BI:CI (settlement)', BI_CI_s, BI_CI_c))
print('%-22s %12.2f %12.2f' % ('Diff.Caisse', diff_s, diff_c))
print()
delta = abs(diff_s - diff_c)
if delta < 1.0:
    print('PASS  Diff.Caisse matches within $1.')
else:
    print('DELTA = %.2f  (HP deductions + DR pages 4-5 taxes not yet parsed)' % (diff_s - diff_c))
    print('       Once HP is added, expected delta shrinks to ~0.')
