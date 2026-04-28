"""Check the user's fixed Apr 23 RJ — DC, all balance checkpoints, what changed vs my fill."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client as win32

RJ = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'
ROW = 25

excel = win32.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False
try:
    wb = excel.Workbooks.Open(RJ)

    # JOUR row 25
    js = wb.Sheets('jour')
    print('=== JOUR row 25 (Apr 23) ===\n')
    print(f'DC (col 3): ${js.Cells(ROW, 3).Value:,.2f}')
    print(f'Bal Ferm (col 4): ${js.Cells(ROW, 4).Value:,.2f}')
    print(f'Bal Ouv (col 2): ${js.Cells(ROW, 2).Value:,.2f}')

    # DC cell comment
    try:
        cmt = js.Cells(ROW, 3).Comment
        if cmt:
            print(f'DC comment: {cmt.Text()}')
    except:
        pass

    print('\n--- Full JOUR row 25 non-zero cells ---')
    print(f'{"col":<4} {"value":>15}  formula/label')
    for c in range(1, 120):
        cell = js.Cells(ROW, c)
        v = cell.Value
        f = cell.Formula if cell.HasFormula else ''
        if v not in (None, '', 0, 0.0) or f and f != '0':
            vs = f'{v:,.2f}' if isinstance(v, (int, float)) else str(v)
            print(f'{c:<4} {vs:>15}  {f}')

    # Recap check
    print('\n=== RECAP sheet ===')
    try:
        rc = wb.Sheets('Recap')
        print('D23 (Balance finale):', rc.Cells(23, 4).Value)
        # H19:N19 are the totals pushed to jour BU:CA
        print('H19:N19 row (pushed to Jour BU:CA):')
        for col, letter in [(8, 'H'), (9, 'I'), (10, 'J'), (11, 'K'), (12, 'L'), (13, 'M'), (14, 'N')]:
            v = rc.Cells(19, col).Value
            print(f'  {letter}19: {v}')
    except Exception as e:
        print(f'Recap read error: {e}')

    # GEAC check
    print('\n=== GEAC variance (rows 13/14) ===')
    try:
        g = wb.Sheets('geac_ux')
        for r in [13, 14]:
            for c in range(1, 12):
                v = g.Cells(r, c).Value
                if v not in (None, 0, ''):
                    print(f'  row {r} col {c}: {v}')
    except Exception as e:
        print(f'GEAC read error: {e}')

    # Transelect variance
    print('\n=== TRANSELECT variance ===')
    try:
        t = wb.Sheets('transelect')
        print(f'  Row 14 col Y (X24 variance): {t.Cells(14, 25).Value}')
        print(f'  Row 20 col X (variance carry): {t.Cells(20, 24).Value}')
    except Exception as e:
        print(f'Transelect read error: {e}')

    wb.Close(False)
finally:
    excel.Quit()
