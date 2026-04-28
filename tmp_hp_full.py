"""Dump full HP data for Apr 23 to understand what went where."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers import ParserFactory

with open(r'K:\HP 2026-2027\04-April 2026\HP 04 2026.xlsx', 'rb') as f:
    hp = ParserFactory.create('hp_excel', f.read(), filename='HP 04 2026.xlsx', day=23).get_result()['data']

print('=== HP full data for day 23 ===')
for k, v in hp.items():
    if isinstance(v, dict):
        print(f'\n{k}:')
        for kk, vv in v.items():
            print(f'  {kk}: {vv}')
    else:
        print(f'{k}: {v}')

print('\n=== Sum of HP deductions ===')
deds = hp.get('jour_deductions', {})
total = sum(abs(v) for v in deds.values() if isinstance(v, (int, float)))
print(f'Total abs: {total:.2f}')
