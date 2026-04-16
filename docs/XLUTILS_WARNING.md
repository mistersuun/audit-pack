# xlutils.copy Limitation

## Problem
`utils/rj_filler.py` uses `xlutils.copy()` to create writable copies of .xls workbooks.
This function only preserves cell values, not:
- Formulas (DC formula, Bal_Ouv chain, escompte calcs, category totals)
- Tab colors
- VBA macros
- Cell comments

File size drops from ~2.27 MB to ~1.8 MB (470 KB of metadata lost).

## Impact
Any .xls file saved through RJFiller will have ALL formulas replaced with static values.

## Workaround
Use pywin32 Excel COM for direct writes on Windows:
```python
import win32com.client as win32
excel = win32.Dispatch('Excel.Application')
wb = excel.Workbooks.Open(path)
ws.Cells(row, col).Formula = '=value'
wb.Save()
```

## Long-term Fix
Implement RJFillerCOM class using pywin32 for .xls files, or migrate to .xlsx with openpyxl.
