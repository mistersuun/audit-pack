"""Inspect DR advance deposit activity and balance calculation — find exact AD on hand today."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers import ParserFactory

with open(r'K:\Audition\04 - April\23-04-2026\DAILY_REV.pdf', 'rb') as f:
    dr = ParserFactory.create('daily_revenue', f.read(), filename='DAILY_REV.pdf').get_result()['data']

print('=== balance ===')
for k, v in dr.get('balance', {}).items():
    print(f'  {k}: {v}')

print('\n=== advance_deposit (if present) ===')
ad = dr.get('advance_deposit', {})
for k, v in ad.items():
    print(f'  {k}: {v}')

print('\n=== non_revenue ===')
for k, v in dr.get('non_revenue', {}).items():
    if isinstance(v, dict):
        for kk, vv in v.items():
            if vv:
                print(f'  {k}.{kk}: {vv}')
    else:
        if v:
            print(f'  {k}: {v}')

# Check if DR has Balance Today on p.7
print('\n=== top-level keys ===')
for k in dr.keys():
    print(f'  {k}')
