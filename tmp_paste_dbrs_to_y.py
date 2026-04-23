"""Paste-only: reads DBRS Insertion B2:B89 from the already-filled staging file
and pastes into Y:\\2026DBR MasterSheraton.xls for Apr 21.
"""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.dbrs_filler import DBRSFiller

import win32com.client as win32


AUDIT_DATE = date(2026, 4, 21)
Y_MASTER = r'Y:\2026DBR MasterSheraton.xls'


def read_insertion():
    """Read DBRS Insertion B2:B89 from the staging workbook."""
    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.AskToUpdateLinks = False
    try:
        wb = excel.Workbooks.Open(DBRSFiller.DBRS_PATH)
        ws = wb.Sheets('DBRS Insertion')
        data = {}
        for r in range(2, 90):
            val = ws.Cells(r, 2).Value
            if val is not None and val != 0:
                data[r] = val
        wb.Close(False)
        return data
    finally:
        excel.Quit()


def main():
    insertion = read_insertion()
    print(f'Read {len(insertion)} non-zero rows from DBRS Insertion')

    filler = DBRSFiller()
    result = filler.paste_to_master(
        audit_date=AUDIT_DATE,
        insertion_values=insertion,
        master_path=Y_MASTER,
    )
    print(f'\n=== PASTE DONE ===')
    print(f'Master:      {Y_MASTER}')
    print(f'Month tab:   {result["month_tab"]}')
    print(f'Day column:  {result["day_column"]}')
    print(f'Rows pasted: {result["rows_written"]}')


if __name__ == '__main__':
    main()
