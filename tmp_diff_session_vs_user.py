"""Download the current /rj/v2 session RJ and diff row 25 against user's fixed Apr 23."""
import sys, os, tempfile
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')
import win32com.client as win32
import urllib.request, http.cookiejar

USER_FIXED = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'
ROW = 25

def read_row(path):
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False; excel.DisplayAlerts = False; excel.AskToUpdateLinks = False
    try:
        wb = excel.Workbooks.Open(path)
        js = wb.Sheets('jour')
        out = {}
        for c in range(1, 120):
            cell = js.Cells(ROW, c)
            v = cell.Value
            fl = cell.Formula if cell.HasFormula else ''
            if v not in (None, '', 0, 0.0) or (fl and fl != '0'):
                out[c] = (v, fl)
        wb.Close(False)
        return out
    finally:
        excel.Quit()

# Session download requires auth cookie — use the manually-saved last session copy.
# Instead, run the end-to-end pipeline script (same as fill-all + autofill-recap-from-docs endpoints)
# on a fresh copy of the backup and compare.
import io, time, shutil
from utils.parsers import ParserFactory
from utils.parsers.house_totals_parser import HouseTotalsParser
from utils.parsers.debourse_parser import DebourseParser
from utils.geac_filler import compute_geac_data
from utils.transelect_filler import compute_transelect_data
from utils.jour_mapper import JourMapper
from utils.rj_filler_com import RJFillerCOM

DOC = r'K:\Audition\04 - April\23-04-2026'
BAK = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls.bak.xls'
DAY = 23

tmp = tempfile.NamedTemporaryFile(suffix='.xls', delete=False)
tmp.close()
shutil.copy2(BAK, tmp.name)
OUT = tmp.name

def parse(type_, path, **kw):
    with open(path, 'rb') as f:
        return ParserFactory.create(type_, f.read(), filename=path.split('\\')[-1], **kw).get_result()['data']

dr = parse('daily_revenue', f'{DOC}\\DAILY_REV.pdf')
sj = parse('sales_journal', f'{DOC}\\SALES_JOURNAL.txt')
ar = parse('ar_summary', f'{DOC}\\AR_SUMMARY.pdf')
ms = parse('market_segment', f'{DOC}\\MARKET_SEGMENT.pdf')
hp = parse('hp_excel', r'K:\HP 2026-2027\04-April 2026\HP 04 2026.xlsx', day=DAY)
with open(f'{DOC}\\HOUSE_TOTALS.txt', 'rb') as fh:
    ht = HouseTotalsParser(fh.read(), filename='HOUSE_TOTALS.txt'); ht.parse()
with open(f'{DOC}\\90_2.pdf', 'rb') as fh:
    db = DebourseParser(fh.read(), filename='90_2.pdf'); db.parse()

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
jour_0 = mapper.compute_all()
jour_1 = {c + 1: v for c, v in jour_0.items()}
geac = compute_geac_data(dr, ar)
trans = compute_transelect_data(sj, dr)

with RJFillerCOM(OUT) as f:
    f.write_geac(geac)
    f.write_transelect(trans)
    f.excel.Calculate(); time.sleep(0.3)
    ts = f.wb.Sheets('transelect')
    for i in range(1, 7):
        v = ts.Cells(38, i).Value
        if isinstance(v, (int, float)):
            jour_1[60 + i] = v
    x24 = ts.Cells(20, 24).Value or 0
    f.write_jour_row(DAY, jour_1)
    f.excel.Calculate(); time.sleep(0.3)
    js = f.wb.Sheets('jour')
    dc_before = js.Cells(ROW, 3).Value or 0
    if x24:
        sign_pos = abs(dc_before + x24)
        sign_neg = abs(dc_before - x24)
        bj = f'={x24:.2f}' if sign_pos < sign_neg else f'=-({x24:.2f})'
        js.Cells(ROW, 62).Formula = bj
        f.excel.Calculate(); time.sleep(0.3)
    # Recap write (replicate Agent 1's corrected logic)
    rc = f.wb.Sheets('Recap')
    comp = ht.extracted_data.get('comptant_positouch', 0)
    rg = ht.extracted_data.get('remb_gratuite', 0)
    dt = abs(db.extracted_data.get('debourse_total') or 0)
    surplus = abs(-228.44)
    argent = 11916.20
    b9 = argent - comp - dt - dt - surplus
    rc.Cells(7, 2).Value = comp
    rc.Cells(9, 2).Value = b9
    rc.Cells(11, 2).Value = rg
    rc.Cells(12, 2).Value = -dt
    rc.Cells(16, 2).Value = dt
    rc.Cells(17, 2).Value = dt
    rc.Cells(19, 2).Value = surplus
    f.excel.Calculate(); time.sleep(0.3)
    for i, col in enumerate(range(8, 15)):
        v = rc.Cells(19, col).Value or 0
        cell = js.Cells(ROW, 73 + i)
        if not cell.HasFormula:
            cell.Value = v
    f.excel.Calculate(); time.sleep(0.3)
    dc_final = js.Cells(ROW, 3).Value
    print(f'Pipeline DC = ${dc_final:,.2f}\n')

pipeline = read_row(OUT)
user = read_row(USER_FIXED)

print(f'{"col":<4} {"pipeline":>14} {"user":>14} {"diff":>12}  formula/label')
print('-' * 90)
for c in sorted(set(pipeline.keys()) | set(user.keys())):
    if c in (2, 3): continue
    pv, pf = pipeline.get(c, (0, ''))
    uv, uf = user.get(c, (0, ''))
    pvn = pv if isinstance(pv, (int, float)) else 0
    uvn = uv if isinstance(uv, (int, float)) else 0
    diff = pvn - uvn
    mark = '  <-- ' if abs(diff) > 0.05 else ''
    print(f'{c:<4} {pvn:>14,.2f} {uvn:>14,.2f} {diff:>+12,.2f}  {pf or uf}{mark}')

os.unlink(OUT)
