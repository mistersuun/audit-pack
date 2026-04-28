"""Read Transelect variances from the filled RJ for day 23."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client as win32

RJ = r'K:\RJ 2026-2027\02-AVRIL 2026\Rj 23-04-2026.xls'

excel = win32.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False
excel.AskToUpdateLinks = False
try:
    wb = excel.Workbooks.Open(RJ)
    ts = wb.Sheets('transelect')
    print('=== Restaurant Section (rows 8-14) ===')
    headers = [ts.Cells(8, c).Value for c in range(1, 30)]
    print('Headers:', [h for h in headers if h])

    for r in range(9, 15):
        label = ts.Cells(r, 25).Value or ''
        v24 = ts.Cells(r, 24).Value or 0
        y = ts.Cells(r, 25).Value or 0
        total_v = ts.Cells(r, 22).Value or 0
        pos_x = ts.Cells(r, 23).Value or 0
        print(f'  row {r:2d} | V(21)={total_v:10.2f} | X(23)POS={pos_x:10.2f} | Y(24)var={v24:10.2f}')

    x14 = ts.Cells(14, 24).Value
    print(f'\nRow 14 col 24 (X14) — Restaurant TOTAL variance: {x14}')

    y14 = ts.Cells(14, 25).Value
    print(f'Row 14 col 25 (Y14): {y14}')

    print('\n=== Reception Section (rows 19-25) ===')
    for r in range(19, 26):
        try:
            label = ts.Cells(r, 1).Value
            b = ts.Cells(r, 2).Value or 0
            i = ts.Cells(r, 9).Value or 0
            p = ts.Cells(r, 16).Value or 0
            variance = ts.Cells(r, 17).Value or 0
            print(f'  row {r:2d} | label={label} | B={b:10.2f} | I={i:10.2f} | P={p:10.2f} | Q(var)={variance:10.2f}')
        except Exception as e:
            print(f'  row {r}: {e}')

    x20 = ts.Cells(20, 24).Value
    print(f'\nRow 20 col 24 (X20) — reception X24-carryover: {x20}')
    y20 = ts.Cells(20, 25).Value
    print(f'Row 20 col 25 (Y20): {y20}')

    print('\n=== Sum check ===')
    print(f'X14 (Sec1 Rest var): {x14}')
    print(f'X20 (Sec2 Recep var): {x20}')
    sec2 = 0
    for r in range(21, 25):
        v = ts.Cells(r, 17).Value or 0
        sec2 += v
    print(f'Sec2 Q sum (rows 21-24): {sec2:.2f}')

    wb.Close(False)
finally:
    excel.Quit()
