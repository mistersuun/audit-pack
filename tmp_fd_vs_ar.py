"""Check FD vs AR difference — candidate for col 42 AP GEAC compensation."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers import ParserFactory

DOC_DIR = r'K:\Audition\04 - April\23-04-2026'
with open(f'{DOC_DIR}\\DAILY_REV.pdf', 'rb') as f:
    dr = ParserFactory.create('daily_revenue', f.read(), filename='DAILY_REV.pdf').get_result()['data']
with open(f'{DOC_DIR}\\AR_SUMMARY.pdf', 'rb') as f:
    ar = ParserFactory.create('ar_summary', f.read(), filename='AR_SUMMARY.pdf').get_result()['data']

fd = abs(dr.get('settlements', {}).get('facture_direct', 0))
gf = abs(ar.get('front_office_transfers', {}).get('guest_folios', 0))
ar_payments = abs(ar.get('payments', 0) or 0)
dr_ar_misc = dr.get('revenue', {}).get('ar_activity', {}).get('total', 0) or 0

print(f'DR Facture Direct: ${fd:,.2f}')
print(f'AR Guest Folios:   ${gf:,.2f}')
print(f'AR Payments:       ${ar_payments:,.2f}')
print(f'DR AR Misc:        ${dr_ar_misc:,.2f}')
print(f'FD - AR:           ${fd - gf:,.2f}')
print()
print(f'AP = -(FD - AR) = {-(fd - gf):+.2f}')
print(f'CF = AR - AR_Pay - AR_Misc = {gf - ar_payments - dr_ar_misc:+.2f}')

print('\n--- DR settlements ---')
for k, v in dr.get('settlements', {}).items():
    print(f'  {k}: {v}')

print('\n--- AR summary top-level ---')
for k, v in ar.items():
    if isinstance(v, (int, float)):
        print(f'  {k}: {v}')
    elif isinstance(v, dict):
        for k2, v2 in v.items():
            if isinstance(v2, (int, float)):
                print(f'  {k}.{k2}: {v2}')
