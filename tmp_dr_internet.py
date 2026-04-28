"""Dump DR revenue.internet and check what's in col 49 (AW) sources."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers import ParserFactory

with open(r'K:\Audition\04 - April\23-04-2026\DAILY_REV.pdf', 'rb') as f:
    dr = ParserFactory.create('daily_revenue', f.read(), filename='DAILY_REV.pdf').get_result()['data']
with open(r'K:\Audition\04 - April\23-04-2026\SALES_JOURNAL.txt', 'rb') as f:
    sj = ParserFactory.create('sales_journal', f.read(), filename='SALES_JOURNAL.txt').get_result()['data']

print('=== DR revenue ===')
for k, v in dr.get('revenue', {}).items():
    if isinstance(v, dict):
        for kk, vv in v.items():
            if vv:
                print(f'  revenue.{k}.{kk}: {vv}')
    elif v:
        print(f'  revenue.{k}: {v}')

print('\n=== SJ banquet internet + spesa internet ===')
print(f'  SJ banquet.internet: {sj.get("departments", {}).get("banquet", {}).get("internet")}')
print(f'  SJ spesa.internet: {sj.get("departments", {}).get("spesa", {}).get("internet")}')

# Specific check for fr_etage and tabagie in chambres
print('\n=== SJ chambres full ===')
for k, v in sj.get('departments', {}).get('chambres', {}).items():
    print(f'  chambres.{k}: {v}')
