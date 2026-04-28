"""Hunt for $177.36 missing in Apr 23 Jour row.
Dump SJ+DR+AR fields, find any value near 177 or combinations that sum to it."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers import ParserFactory

DOC_DIR = r'K:\Audition\04 - April\23-04-2026'
with open(f'{DOC_DIR}\\DAILY_REV.pdf', 'rb') as f:
    dr = ParserFactory.create('daily_revenue', f.read(), filename='DAILY_REV.pdf').get_result()['data']
with open(f'{DOC_DIR}\\SALES_JOURNAL.txt', 'rb') as f:
    sj = ParserFactory.create('sales_journal', f.read(), filename='SALES_JOURNAL.txt').get_result()['data']
with open(f'{DOC_DIR}\\AR_SUMMARY.pdf', 'rb') as f:
    ar = ParserFactory.create('ar_summary', f.read(), filename='AR_SUMMARY.pdf').get_result()['data']

TARGET = 177.36

def walk(d, path=''):
    """Yield (path, value) for every numeric leaf."""
    if isinstance(d, dict):
        for k, v in d.items():
            yield from walk(v, f'{path}.{k}' if path else k)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            yield from walk(v, f'{path}[{i}]')
    elif isinstance(d, (int, float)) and d != 0:
        yield (path, d)

print('=== Searching SJ for values near $177.36 ===')
for src_name, src in [('SJ', sj), ('DR', dr), ('AR', ar)]:
    for path, val in walk(src):
        if abs(abs(val) - TARGET) < 5:
            print(f'  {src_name}: {path} = {val}')

print('\n=== All SJ department totals ===')
for dept_name, dept in sj.get('departments', {}).items():
    if isinstance(dept, dict):
        print(f'\n{dept_name}:')
        for k, v in dept.items():
            if isinstance(v, (int, float)) and v != 0:
                print(f'  {k}: {v}')

print('\n=== SJ top-level ===')
for k, v in sj.items():
    if k == 'departments': continue
    if isinstance(v, (int, float)) and v != 0:
        print(f'  {k}: {v}')
    elif isinstance(v, dict):
        for k2, v2 in v.items():
            if isinstance(v2, (int, float)) and v2 != 0:
                print(f'  {k}.{k2}: {v2}')
