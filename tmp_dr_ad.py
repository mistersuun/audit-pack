"""Dump DR advance_deposits — D25 off by exactly $177.36."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers import ParserFactory

with open(r'K:\Audition\04 - April\23-04-2026\DAILY_REV.pdf', 'rb') as f:
    dr = ParserFactory.create('daily_revenue', f.read(), filename='DAILY_REV.pdf').get_result()['data']

print('=== DR advance_deposits ===')
ad = dr.get('advance_deposits', {})
print(json.dumps(ad, indent=2, default=str))

print('\n=== DR deposits_received ===')
dr_recvd = dr.get('deposits_received', {})
print(json.dumps(dr_recvd, indent=2, default=str))

print('\nSum of key activities:')
if isinstance(ad, dict):
    rec = ad.get('received', ad.get('receive', 0)) or 0
    app = ad.get('applied', 0) or 0
    can = ad.get('cancelled', ad.get('canceled', 0)) or 0
    dna = ad.get('dna', 0) or 0
    prev = ad.get('yesterday', ad.get('previous', ad.get('prev', 0))) or 0
    today = ad.get('today', ad.get('on_hand', 0)) or 0
    total = ad.get('total', 0) or 0
    print(f'  prev: {prev}')
    print(f'  received: {rec}')
    print(f'  applied: {app}')
    print(f'  cancelled: {can}')
    print(f'  dna: {dna}')
    print(f'  today: {today}')
    print(f'  total: {total}')
    computed_today = prev + rec - app - can - dna
    print(f'  computed today = prev + rec - app - can - dna = {computed_today}')
    print(f'  vs user given: 294582.46')
    print(f'  difference: {294582.46 - computed_today:.2f}')
