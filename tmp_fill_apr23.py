"""Fill Apr 23 (Day 23, jour row 25) RJ with FORMULAS via Excel COM.

Inputs supplied by user:
  G4 = 40, AdvDep = 294,582.46
  Adj Piazza Nourr = 41.22, Adj Spesa Nourr = 1.94, Adj Serv Cham Nourr = 11.02
Source docs: DR, MS, SJ, AR (no HP this night — hp deductions set to 0)
"""
import sys, time, os, shutil
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers import ParserFactory
from utils.geac_filler import compute_geac_data
from utils.transelect_filler import compute_transelect_data
from utils.jour_mapper import JourMapper
from utils.rj_filler_com import RJFillerCOM

DOC_DIR = r'K:\Audition\04 - April\23-04-2026'
RJ_PATH = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'

with open(f'{DOC_DIR}\\DAILY_REV.pdf', 'rb') as f:
    dr = ParserFactory.create('daily_revenue', f.read(), filename='DAILY_REV.pdf').get_result()['data']
with open(f'{DOC_DIR}\\SALES_JOURNAL.txt', 'rb') as f:
    sj = ParserFactory.create('sales_journal', f.read(), filename='SALES_JOURNAL.txt').get_result()['data']
with open(f'{DOC_DIR}\\AR_SUMMARY.pdf', 'rb') as f:
    ar = ParserFactory.create('ar_summary', f.read(), filename='AR_SUMMARY.pdf').get_result()['data']
with open(f'{DOC_DIR}\\MARKET_SEGMENT.pdf', 'rb') as f:
    ms = ParserFactory.create('market_segment', f.read(), filename='MARKET_SEGMENT.pdf').get_result()['data']
with open(r'K:\HP 2026-2027\04-April 2026\HP 04 2026.xlsx', 'rb') as f:
    hp = ParserFactory.create('hp_excel', f.read(), filename='HP 04 2026.xlsx', day=23).get_result()['data']

G4 = 40.0
DEPOSIT = 294582.46
ADJ_PIAZ_NOURR = 41.22
ADJ_SPESA_NOURR = 1.94
ADJ_SC_NOURR = 11.02

dept = sj.get('departments', {})
piazza = dept.get('piazza', {})
banquet = dept.get('banquet', {})
spesa = dept.get('spesa', {})
chambres = dept.get('chambres', {})
settlements = dr.get('settlements', {})
revenue = dr.get('revenue', {})
balance = dr.get('balance', {})

hp_ded = hp.get('jour_deductions', {})
hp_j = abs(hp_ded.get('9', 0))
hp_k = abs(hp_ded.get('10', 0))
hp_l = abs(hp_ded.get('11', 0))
hp_m = abs(hp_ded.get('12', 0))
hp_n = abs(hp_ded.get('13', 0))
hp_o = abs(hp_ded.get('14', 0))
hp_aj = abs(hp_ded.get('35', 0))
bq_tip = hp_ded.get('68', 0)
br_tip = hp_ded.get('69', 0)
print(f'HP deductions: J={hp_j} K={hp_k} L={hp_l} M={hp_m} N={hp_n} O={hp_o} AJ={hp_aj} | BQ_tip={bq_tip} BR_tip={br_tip}')

nb = abs(balance.get('new_balance', 0))
fd = abs(settlements.get('facture_direct', 0))
gf = abs(ar.get('front_office_transfers', {}).get('guest_folios', 0))
dr_autres = revenue.get('autres_revenus', {})
ch_rev = revenue.get('chambres', {}).get('total', 0)
dr_internet = revenue.get('internet', {}).get('total', 0)
agl = revenue.get('comptabilite', {}).get('autres_grand_livre', 0)
art = dr_autres.get('autre_a_payer_taxable', 0)

def n(x): return f'{x:.2f}'
def formula_or_val(parts):
    nonzero = [(s, v) for (s, v) in parts if v]
    if not nonzero: return 0
    if len(nonzero) == 1 and nonzero[0][0] == '+':
        return nonzero[0][1]
    out = ''
    for s, v in nonzero:
        if s == '+' and out == '':
            out += n(v)
        elif s == '+':
            out += '+' + n(v)
        else:
            out += '-' + n(v)
    return '=' + out

jour = {}

jour[4] = f'=-{n(nb)}-{n(DEPOSIT)}'

jour[5] = formula_or_val([('+', banquet.get('pause_spesa', 0)), ('+', piazza.get('pause_spesa', 0))])

jour[10] = formula_or_val([('+', piazza.get('nourriture', 0)), ('-', hp_j), ('-', ADJ_PIAZ_NOURR)])
jour[11] = formula_or_val([('+', piazza.get('boisson', 0)), ('-', hp_k)])
jour[12] = formula_or_val([('+', piazza.get('bieres', 0)), ('-', hp_l)])
jour[13] = formula_or_val([('+', piazza.get('mineraux', 0)), ('-', hp_m)])
jour[14] = formula_or_val([('+', piazza.get('vins', 0)), ('-', hp_n)])

jour[15] = formula_or_val([('+', spesa.get('nourriture', 0)), ('-', hp_o), ('-', ADJ_SPESA_NOURR)])
if spesa.get('boisson'): jour[16] = spesa['boisson']
if spesa.get('bieres'): jour[17] = spesa['bieres']
if spesa.get('mineraux'): jour[18] = spesa['mineraux']
if spesa.get('vins'): jour[19] = spesa['vins']

jour[20] = formula_or_val([('+', chambres.get('nourriture', 0)), ('-', ADJ_SC_NOURR)])
if chambres.get('boisson'): jour[21] = chambres['boisson']
if chambres.get('bieres'): jour[22] = chambres['bieres']
if chambres.get('mineraux'): jour[23] = chambres['mineraux']
if chambres.get('vins'): jour[24] = chambres['vins']

if banquet.get('nourriture'): jour[25] = banquet['nourriture']
if banquet.get('boisson'): jour[26] = banquet['boisson']
if banquet.get('bieres'): jour[27] = banquet['bieres']
if banquet.get('mineraux'): jour[28] = banquet['mineraux']
if banquet.get('vins'): jour[29] = banquet['vins']

# AE Équipement Audio Visuel (col 31) — SJ banquet
if banquet.get('equip_audio_visuel'): jour[31] = banquet['equip_audio_visuel']

# AF Divers Banquet + Piazza (col 32) — SJ banquet.eq_divers + piazza.eq_divers
jour[32] = formula_or_val([
    ('+', banquet.get('eq_divers', 0)),
    ('+', piazza.get('eq_divers', 0)),
])

jour[30] = formula_or_val([
    ('+', piazza.get('pourboire_a_payer', 0)),
    ('+', banquet.get('pourboire_a_payer', 0)),
    ('+', spesa.get('pourboire_a_payer', 0)),
])

jour[33] = formula_or_val([
    ('+', banquet.get('location_salle', 0)),
    ('+', piazza.get('location_salle', 0)),
    ('+', dr_autres.get('location_salle_forfait', 0)),
])

socam = banquet.get('socam', 0)
if socam: jour[34] = socam

# AJ Tabagie = SJ Spesa Tabagie + SJ Chambres Tabagie − HP Tabagie
jour[36] = formula_or_val([
    ('+', spesa.get('tabagie', 0)),
    ('+', chambres.get('tabagie', 0)),
    ('-', hp_aj),
])

jour[37] = formula_or_val([('+', ch_rev), ('-', G4)])

if dr_autres.get('nettoyeur'): jour[41] = dr_autres['nettoyeur']
if fd or gf:
    jour[42] = f'=-({n(fd)}-{n(gf)})' if abs(fd - gf) > 0.01 else 0
# AS Autres G/L = DR AGL - SJ DEPOT UTIL
depot_util = 0
for dept_name, dept_data in dept.items():
    if isinstance(dept_data, dict):
        du = dept_data.get('depot_util', 0) or dept_data.get('DEPOT UTIL', 0) or 0
        depot_util += abs(du) if du else 0
# Also check at top level of SJ
depot_util += abs(sj.get('depot_util', 0) or 0)
depot_util += abs(sj.get('adjustments', {}).get('depot_util', 0) or 0)
print(f'DEPOT UTIL found in SJ: ${depot_util:.2f}')
if agl or depot_util:
    jour[45] = formula_or_val([('+', agl), ('-', depot_util)])
if dr_autres.get('sonifi'): jour[46] = dr_autres['sonifi']
# AU Autres Rev (col 47) = DR lit_pliant + SJ chambres.fr_etage + DR interhotel_xferin
# (user rule Apr 23: InterHotel goes to AU, not AW)
interhotel = balance.get('interhotel_xferin', 0) or 0
jour[47] = formula_or_val([
    ('+', dr_autres.get('lit_pliant', 0)),
    ('+', chambres.get('fr_etage', 0)),
    ('+', interhotel),
])

# AW Internet (col 49) = DR internet + SJ banquet/spesa internet (NO interhotel)
jour[49] = formula_or_val([
    ('+', dr_internet),
    ('+', banquet.get('internet', 0)),
    ('+', spesa.get('internet', 0)),
])

sj_tvq = sj.get('taxes', {}).get('tvq', 0)
dr_tvq_ch = dr.get('non_revenue', {}).get('chambres_tax', {}).get('tvq', 0)
dr_tvq_autres = dr.get('non_revenue', {}).get('autres_tax', {}).get('tvq_autres', 0)
dr_tvq_inet = dr.get('non_revenue', {}).get('internet_nonrev', {}).get('tvq', 0)
tvq_tel_local = dr.get('non_revenue', {}).get('telephones_tax', {}).get('tvq_local', 0)
tvq_tel_int = dr.get('non_revenue', {}).get('telephones_tax', {}).get('tvq_interurbain', 0)
dr_tvq_compta = dr.get('non_revenue', {}).get('comptabilite_nonrev', {}).get('tvq', 0)
jour[50] = formula_or_val([
    ('+', dr_tvq_ch), ('+', sj_tvq), ('+', dr_tvq_autres), ('+', dr_tvq_inet),
    ('+', tvq_tel_local), ('+', tvq_tel_int), ('+', dr_tvq_compta),
])

sj_tps = sj.get('taxes', {}).get('tps', 0)
dr_tps_ch = dr.get('non_revenue', {}).get('chambres_tax', {}).get('tps', 0)
dr_tps_autres = dr.get('non_revenue', {}).get('autres_tax', {}).get('tps_autres', 0)
dr_tps_inet = dr.get('non_revenue', {}).get('internet_nonrev', {}).get('tps', 0)
tps_tel_local = dr.get('non_revenue', {}).get('telephones_tax', {}).get('tps_local', 0)
tps_tel_int = dr.get('non_revenue', {}).get('telephones_tax', {}).get('tps_interurbain', 0)
dr_tps_compta = dr.get('non_revenue', {}).get('comptabilite_nonrev', {}).get('tps', 0)
jour[51] = formula_or_val([
    ('+', dr_tps_ch), ('+', sj_tps), ('+', dr_tps_autres), ('+', dr_tps_inet),
    ('+', tps_tel_local), ('+', tps_tel_int), ('+', dr_tps_compta),
])

tvh = dr.get('non_revenue', {}).get('chambres_tax', {}).get('taxe_hebergement', 0)
if tvh: jour[52] = tvh

if art: jour[55] = art

forfait = sj.get('adjustments', {}).get('forfait', 0)
jour[58] = f'=-({n(forfait)}-{n(G4)})'

if bq_tip: jour[69] = bq_tip
if br_tip: jour[70] = br_tip

ar_payments = abs(ar.get('payments', 0) or 0)
dr_ar_misc = dr.get('revenue', {}).get('ar_activity', {}).get('total', 0) or 0
jour[84] = formula_or_val([('+', gf), ('-', ar_payments), ('-', dr_ar_misc)])

# CB Cert Cadx (col 80) — DR GiveX (always negative)
givex = dr.get('revenue', {}).get('givex', {}).get('total', 0) or 0
if givex:
    jour[80] = -abs(givex)

if ms.get('total_rooms_today') is not None: jour[89] = ms['total_rooms_today']
if ms.get('complimentary_rooms_today') is not None: jour[92] = ms['complimentary_rooms_today']
if ms.get('total_guests_today') is not None: jour[93] = ms['total_guests_today']

geac_data = compute_geac_data(dr, ar)
transelect_data = compute_transelect_data(sj, dr)

BAK = RJ_PATH + '.bak.xls'
if not os.path.exists(BAK):
    shutil.copy2(RJ_PATH, BAK)
    print(f'Created backup: {BAK}')
else:
    shutil.copy2(BAK, RJ_PATH)
    print(f'Restored from backup: {BAK}')

DAY = 23
print(f'\nFilling Day {DAY} with formulas...')

with RJFillerCOM(RJ_PATH) as filler:
    filler.write_geac(geac_data)
    filler.write_transelect(transelect_data)
    filler.excel.Calculate()
    time.sleep(0.3)

    ts = filler.wb.Sheets('transelect')
    for i in range(1, 7):
        v = ts.Cells(38, i).Value
        if v is not None and isinstance(v, (int, float)):
            jour[60 + i] = v

    x24 = ts.Cells(20, 24).Value or 0
    print(f'Transelect X24: ${x24:,.2f}')

    filler.write_jour_row(DAY, jour)
    filler.excel.Calculate()
    time.sleep(0.3)

    js = filler.wb.Sheets('jour')
    ROW = DAY + 2
    dc_before = js.Cells(ROW, 3).Value
    print(f'DC before BJ comp: ${dc_before:,.2f}')

    # BJ compensation — pick sign that drives DC toward 0.
    # Col 62 behaves as +delta on DC: writing +X adds +X to DC.
    # So BJ = -dc_before is the exact offset, but we want formula form for audit trail.
    # BJ compensation = X24 variance ONLY.
    # PANNE LIEN HOTEL is NEVER separately compensated — it's already in AK via DR chambres.
    if x24:
        if abs(dc_before + x24) < abs(dc_before - x24):
            bj_formula = f'={n(x24)}'
            print(f'BJ = X24 = {x24:+.2f}')
        else:
            bj_formula = f'=-({n(x24)})'
            print(f'BJ = -X24 = {-x24:+.2f}')
        js.Cells(ROW, 62).Formula = bj_formula
        filler.excel.Calculate()
        time.sleep(0.3)

    dc_final = js.Cells(ROW, 3).Value
    print(f'DC final: ${dc_final:,.2f}')

    if abs(dc_final) < 0.50:
        print('*** BALANCED ***')
    else:
        print(f'*** OFF BY ${dc_final:,.2f} — investigate common misses ***')

    print(f'\n=== FORMULAS WRITTEN TO JOUR ROW {ROW} ===')
    for col in sorted(jour.keys()):
        cell = js.Cells(ROW, col)
        f_str = cell.Formula if cell.HasFormula else ''
        v = cell.Value
        if f_str.startswith('='):
            print(f'  col {col:3d}: {f_str:45s} = ${v:,.2f}' if isinstance(v, (int,float)) else f'  col {col:3d}: {f_str}')
        elif v is not None:
            print(f'  col {col:3d}: (value)                                       = ${v:,.2f}' if isinstance(v,(int,float)) else f'  col {col:3d}: {v}')
    bj_cell = js.Cells(ROW, 62)
    print(f'  col  62: {bj_cell.Formula if bj_cell.HasFormula else bj_cell.Value}')

print('\nFile saved.')
