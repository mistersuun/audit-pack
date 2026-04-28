"""Verify RJ Balancer produces the right values for Apr 23 after the parsing fixes."""
import io, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.rj_balancer import (
    parse_sj, parse_dr_pdf, parse_hp, parse_ar_pdf, parse_rj_transelect,
    parse_rj_geac, parse_rj_recap, parse_rj_jour, calculate_jour,
    AdvDepData,
)

DOC = r'K:\Audition\04 - April\23-04-2026'
RJ = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'
DAY = 23

with open(f'{DOC}\\SALES_JOURNAL.txt', 'rb') as f:
    sj = parse_sj(io.BytesIO(f.read()))
with open(f'{DOC}\\DAILY_REV.pdf', 'rb') as f:
    dr = parse_dr_pdf(io.BytesIO(f.read()))
with open(f'{DOC}\\AR_SUMMARY.pdf', 'rb') as f:
    ar = parse_ar_pdf(io.BytesIO(f.read()))
with open(r'K:\HP 2026-2027\04-April 2026\HP 04 2026.xlsx', 'rb') as f:
    hp = parse_hp(io.BytesIO(f.read()), DAY)
with open(RJ, 'rb') as f:
    rj_bytes = f.read()
    tr = parse_rj_transelect(io.BytesIO(rj_bytes))
    geac = parse_rj_geac(io.BytesIO(rj_bytes))
    recap = parse_rj_recap(io.BytesIO(rj_bytes))
    jour = parse_rj_jour(io.BytesIO(rj_bytes), DAY)

# Confirm the balancer parsed the new SJ fields
print(f'sj.piaz_eq_divers = {sj.piaz_eq_divers}  (expected -17.4)')
print(f'sj.ch_tab = {sj.ch_tab}  (expected 12)')
print(f'sj.bqt_eq_audio = {sj.bqt_eq_audio}  (expected 12068)')
print(f'sj.bqt_eq_divers = {sj.bqt_eq_divers}  (expected 8517.4)')
print(f'sj.ch_fretage = {sj.ch_fretage}  (expected 33)')
print(f'dr.interhotel_xferin = {dr.interhotel_xferin}  (expected 29.97)')
print(f'dr.givex = {dr.givex}  (expected 600)')
print(f'dr.tvq_comptab = {dr.tvq_comptab}  (expected 602.99)')
print(f'dr.tps_comptab = {dr.tps_comptab}  (expected 302.25)')

adv = AdvDepData(yesterday=294582.46, received=0, applied=0, cancelled=0, dna=0)
results = calculate_jour(
    sj, dr, ar, hp, adv, tr, geac, recap, jour,
    g4=40, adj_piaz=41.22, adj_mar=1.94,
)

calc = {c['col']: c.get('calc', 0) for c in results.get('columns', [])}
# Expected (Apr 23 ground truth)
expected = {
    30: 12068.00,   # AE
    31: 8500.00,    # AF
    35: 707.28,     # AJ (before HP subtraction in calc is different — see note below)
    46: 62.97,      # AU
    48: -26.08,     # AW
    49: 20285.58,   # AX
    50: 10169.56,   # AY
    79: -600.00,    # CB col — actually CA in balancer numbering (0-indexed)
}
print(f'\n{"col":<4} {"balancer":>14} {"expected":>14} {"diff":>12}  verdict')
print('-' * 60)
for col, exp in expected.items():
    got = calc.get(col, 0)
    diff = got - exp
    ok = '✓' if abs(diff) < 0.1 else '✗'
    print(f'{col:<4} {got:>14,.2f} {exp:>14,.2f} {diff:>+12,.2f}  {ok}')
