"""Dry-run JourMapper for Apr 23 — verify AE/AF/AJ/AU/AW/AX/AY/CB compute to expected values."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers import ParserFactory
from utils.jour_mapper import JourMapper
from utils.daily_rev_jour_mapping import DAILY_REV_TO_JOUR

DOC = r'K:\Audition\04 - April\23-04-2026'
with open(f'{DOC}\\DAILY_REV.pdf', 'rb') as f:
    dr = ParserFactory.create('daily_revenue', f.read(), filename='DAILY_REV.pdf').get_result()['data']
with open(f'{DOC}\\SALES_JOURNAL.txt', 'rb') as f:
    sj = ParserFactory.create('sales_journal', f.read(), filename='SALES_JOURNAL.txt').get_result()['data']
with open(f'{DOC}\\AR_SUMMARY.pdf', 'rb') as f:
    ar = ParserFactory.create('ar_summary', f.read(), filename='AR_SUMMARY.pdf').get_result()['data']
with open(f'{DOC}\\MARKET_SEGMENT.pdf', 'rb') as f:
    ms = ParserFactory.create('market_segment', f.read(), filename='MARKET_SEGMENT.pdf').get_result()['data']
with open(r'K:\HP 2026-2027\04-April 2026\HP 04 2026.xlsx', 'rb') as f:
    hp = ParserFactory.create('hp_excel', f.read(), filename='HP 04 2026.xlsx', day=23).get_result()['data']

mapper = JourMapper(
    daily_rev_data=dr, sales_journal_data=sj, ar_summary_data=ar,
    hp_data=hp, market_segment_data=ms,
    manual_values={'g4': 40, 'club_lounge': 40, 'deposit_on_hand': 294582.46},
    adjustments=[
        {'department': 'piazza_nourriture', 'amount': 41.22},
        {'department': 'spesa_nourriture', 'amount': 1.94},
        {'department': 'chambres_nourriture', 'amount': 11.02},
    ],
)
result = mapper.compute_all()

# Expected from user's Apr 23 fix
expected = {
    'AE': 12068.00,    # col 31
    'AF': 8500.00,     # col 32 = -17.4 + 8517.4
    'AJ': 707.28,      # col 36 = 863.19 + 12 - 167.91
    'AU': 62.97,       # col 47 = 33 + 29.97
    'AW': -26.08,      # col 49 (no interhotel anymore)
    'AX': 20285.58,    # col 50 with comptabilite.tvq
    'AY': 10169.56,    # col 51 with comptabilite.tps
    'CB': -600.00,     # col 80 GiveX negative
}

print(f'{"col":<4} {"idx":>4} {"mapper":>14} {"expected":>14} {"diff":>12}  verdict')
print('-' * 70)
for col_letter, exp in expected.items():
    cfg = DAILY_REV_TO_JOUR.get(col_letter, {})
    idx = cfg.get('column_index')
    if idx is None:
        print(f'{col_letter:<4} MAPPING MISSING')
        continue
    got = result.get(idx)
    gotn = got if isinstance(got, (int, float)) else 0
    diff = gotn - exp
    ok = '✓' if abs(diff) < 0.05 else '✗'
    print(f'{col_letter:<4} {idx:>4} {gotn:>14,.2f} {exp:>14,.2f} {diff:>+12,.2f}  {ok}')

# Also print any warnings/errors
print('\nMapper warnings:', mapper.warnings[:5] if mapper.warnings else 'none')
print('Mapper errors:', mapper.errors[:5] if mapper.errors else 'none')
