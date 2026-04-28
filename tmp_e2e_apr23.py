"""End-to-end verification for Apr 23 autofill pipeline.

Steps:
1. Login (Auditeur/audit2026)
2. Get CSRF token from dashboard
3. Upload unfilled RJ
4. Call /api/rj/fill-all (GEAC + Transelect + Jour + BJ compensation)
5. Call /api/rj/autofill-recap-from-docs (Recap B-cols → BU:CA in Jour)
6. Report H19:N19 values and final DC

Usage:
    python tmp_e2e_apr23.py
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

import requests

BASE = 'http://127.0.0.1:5000'
UNFILLED_RJ = r'.playwright-mcp\apr23\Rj_23-04-2026_UNFILLED.xls'
DOC_DIR = r'K:\Audition\04 - April\23-04-2026'
HT_PATH  = os.path.join(DOC_DIR, 'HOUSE_TOTALS.txt')
DEB_PATH = os.path.join(DOC_DIR, '90_2.pdf')

# ---- 0. Check paths ----
missing = [p for p in [UNFILLED_RJ, HT_PATH, DEB_PATH] if not os.path.exists(p)]
if missing:
    print('ERROR: Missing files:')
    for m in missing:
        print(f'  {m}')
    sys.exit(1)

s = requests.Session()

# ---- 1. Login ----
resp = s.post(f'{BASE}/auth/login', data={
    'username': 'Auditeur',
    'password': 'audit2026',
    'role_type': 'auditor',
}, allow_redirects=True)
print(f'Login: {resp.status_code} → {resp.url}')
if 'login' in resp.url.lower() and 'dashboard' not in resp.url.lower():
    print('ERROR: Login failed — still on login page')
    sys.exit(1)

# ---- 2. Get CSRF token ----
resp2 = s.get(f'{BASE}/dashboard')
m = re.search(r'name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)["\']', resp2.text)
if not m:
    m = re.search(r'content=["\']([0-9a-f]{32,})["\'][^>]*name=["\']csrf-token["\']', resp2.text)
csrf = m.group(1) if m else ''
print(f'CSRF token: {csrf[:20]}...' if csrf else 'CSRF: NOT FOUND')
if not csrf:
    print('ERROR: No CSRF token')
    sys.exit(1)

HEADERS = {'X-CSRF-Token': csrf}

# ---- 3. Upload unfilled RJ ----
with open(UNFILLED_RJ, 'rb') as f:
    resp = s.post(
        f'{BASE}/api/rj/upload',
        files={'rj_file': ('Rj_23-04-2026_UNFILLED.xls', f, 'application/octet-stream')},
        headers=HEADERS,
    )
print(f'\nUpload: {resp.status_code}')
data = resp.json()
if not data.get('success'):
    print(f'Upload failed: {data}')
    sys.exit(1)
print(f'  Uploaded — day={data.get("day")}')

# ---- 4. Parse documents ----
HP_PATH = r'K:\HP 2026-2027\04-April 2026\HP 04 2026.xlsx'
DOCS = [
    ('DAILY_REV.pdf',    'daily_revenue',  DOC_DIR),
    ('SALES_JOURNAL.txt','sales_journal',  DOC_DIR),
    ('AR_SUMMARY.pdf',   'ar_summary',     DOC_DIR),
    ('MARKET_SEGMENT.pdf','market_segment',DOC_DIR),
    ('HP 04 2026.xlsx',  'hp_excel',       os.path.dirname(HP_PATH)),
]
parsed_data = {}
print('\nParsing docs:')
for fname, doc_type, fdir in DOCS:
    fpath = os.path.join(fdir, fname)
    if not os.path.exists(fpath):
        print(f'  SKIP (missing): {fname}')
        continue
    extra_data = {'doc_type': doc_type}
    if doc_type == 'hp_excel':
        extra_data['day'] = '23'
    with open(fpath, 'rb') as f:
        resp = s.post(
            f'{BASE}/api/rj/parse',
            files={'file': (fname, f)},
            data=extra_data,
            headers=HEADERS,
        )
    if resp.status_code == 200 and resp.json().get('success'):
        parsed_data[doc_type] = resp.json().get('data', {})
        print(f'  {doc_type}: OK')
    else:
        print(f'  {doc_type}: FAILED — {resp.text[:300]}')

# ---- 5. fill-all ----
payload = {
    'parsed_data': parsed_data,
    'manual_values': {
        'g4': 40.0,
        'deposit_on_hand': 294582.46,
    },
    'adjustments': [
        {'department': 'piazza',   'type': 'nourriture', 'amount': 41.22},
        {'department': 'spesa',    'type': 'nourriture', 'amount': 1.94},
        {'department': 'chambres', 'type': 'nourriture', 'amount': 11.02},
    ],
    'day': 23,
    '_csrf_token': csrf,
}
resp = s.post(
    f'{BASE}/api/rj/fill-all',
    json=payload,
    headers={'X-CSRF-Token': csrf, 'Content-Type': 'application/json'},
)
print(f'\nfill-all: {resp.status_code}')
if resp.status_code != 200:
    print(f'  RAW: {resp.text[:500]}')
    sys.exit(1)
fa = resp.json()
if not fa.get('success'):
    print(f'  FAILED: {fa}')
    sys.exit(1)
dc_fill = fa.get('dc_value')
print(f'  DC after fill-all (with BJ): ${dc_fill:,.2f}')
print(f'  geac={fa.get("geac_cells")}  transelect={fa.get("transelect_cells")}  jour={fa.get("jour_cells")}')
if fa.get('summary', {}).get('warnings'):
    print(f'  Warnings: {fa["summary"]["warnings"][:3]}')

# ---- 6. autofill-recap-from-docs ----
print('\nautofill-recap-from-docs:')
files = {}
try:
    if os.path.exists(HT_PATH):
        files['house_totals'] = open(HT_PATH, 'rb')
    if os.path.exists(DEB_PATH):
        files['debourse'] = open(DEB_PATH, 'rb')

    resp = s.post(
        f'{BASE}/api/rj/autofill-recap-from-docs',
        files=files,
        data={
            'surplus_deficit': '-228.44',
            'argent_recu': '11916.20',
            'day': '23',
        },
        headers=HEADERS,
    )
finally:
    for fobj in files.values():
        fobj.close()

print(f'  Status: {resp.status_code}')
if resp.status_code != 200:
    print(f'  RAW: {resp.text[:500]}')
    sys.exit(1)
ar_resp = resp.json()
if not ar_resp.get('success'):
    print(f'  FAILED: {ar_resp}')
    sys.exit(1)

dc_final = ar_resp.get('dc_value')
recap_vals = ar_resp.get('recap_h19_n19', [])
recap_labels = ['H19 ArgentReçu', 'I19 RembServ', 'J19 RembGrat', 'K19 DepotUS', 'L19 DueBack', 'M19 EchangeUS', 'N19 Surplus']
known = [11916.20, -336.29, -1200.01, 0.0, -336.29, 0.0, -228.44]

print(f'  Parsed inputs: {ar_resp.get("parsed")}')
print(f'\n  H19:N19 → Jour BU:CA:')
all_match = True
for lbl, val, kv in zip(recap_labels, recap_vals, known):
    if isinstance(val, (int, float)):
        match = abs(val - kv) < 0.02
        flag = '✓' if match else f'✗ (expected {kv:,.2f})'
        if not match:
            all_match = False
        print(f'    {lbl}: {val:,.2f}  {flag}')
    else:
        print(f'    {lbl}: {val}')
        all_match = False

print(f'\n  DC FINAL: ${dc_final:,.2f}' if isinstance(dc_final, (int, float)) else f'\n  DC: {dc_final}')
if isinstance(dc_final, (int, float)):
    if abs(dc_final) <= 0.50:
        print('  *** BALANCED (within $0.50) ***')
    else:
        print(f'  *** NOT BALANCED — off by ${dc_final:,.2f} ***')
if all_match:
    print('  All H19:N19 values match known-good targets.')
else:
    print('  Some H19:N19 values differ from known-good targets — investigate.')
