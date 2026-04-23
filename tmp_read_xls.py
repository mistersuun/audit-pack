import xlrd
import sys

files = {
    'Daily_Rev': r'K:\Audition\03 - March\01-03-2026\Daily_Rev_1th.xls',
    'Departure_Arr_Stay': r'K:\Audition\03 - March\01-03-2026\Departure_Arr_Stay_1th.xls',
    'GLedger': r'K:\Audition\03 - March\01-03-2026\GLedger_1st_Mar.xls',
    'Market_Segment': r'K:\Audition\03 - March\01-03-2026\Market_Segment_Analysis_1th_March.xls',
    'Advance_Dep': r'K:\Audition\03 - March\01-03-2026\Advance_Dep_1st_March.xls',
    'AR_Summary': r'K:\Audition\03 - March\01-03-2026\AR_Summary_1th.xls',
    'RJ': r'K:\Audition\03 - March\01-03-2026\Rj 01-03-2026.xls',
}

for name, path in files.items():
    print(f'\n{"="*80}')
    print(f'FILE: {name}')
    print(f'{"="*80}')
    try:
        wb = xlrd.open_workbook(path, formatting_info=(name != 'RJ'))
        for sheet_name in wb.sheet_names():
            sh = wb.sheet_by_name(sheet_name)
            max_rows = 80 if name != 'RJ' else 5
            print(f'\nSheet: {sheet_name} ({sh.nrows} rows x {sh.ncols} cols)')
            print('-'*60)
            for r in range(min(sh.nrows, max_rows)):
                row = []
                for c in range(sh.ncols):
                    v = sh.cell_value(r, c)
                    if v != '' and v != 0.0 and v != 0:
                        row.append(f'[{c}]{v}')
                if row:
                    print(f'  R{r}: {" | ".join(row)}')
            if sh.nrows > max_rows:
                print(f'  ... ({sh.nrows - max_rows} more rows)')
    except Exception as e:
        print(f'  ERROR: {e}')
