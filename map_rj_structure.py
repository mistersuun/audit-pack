
import pandas as pd

def map_rj_locations(file_path):
    xls = pd.ExcelFile(file_path)
    
    print("--- MAPPING LOCATIONS IN RJ FILE ---")
    
    # Map DUBACK# (Staff Names)
    if 'DUBACK#' in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name='DUBACK#', header=None)
        print("\n[DUBACK#] Staff Locations (Row 2):")
        # Assuming names are in the 3rd row (index 2) based on previous preview
        row_index = 2
        for col_index, cell_value in enumerate(df.iloc[row_index]):
            if pd.notna(cell_value):
                print(f"  - {cell_value}: Column {col_index} ({chr(65+col_index)})")

    # Map Transelect (Payment Types)
    if 'transelect' in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name='transelect', header=None)
        print("\n[transelect] Payment Types (Column A):")
        # Look for payment types in the first column
        for row_index, cell_value in enumerate(df.iloc[:, 0]):
            if pd.notna(cell_value) and isinstance(cell_value, str):
                if cell_value.upper() in ['DEBIT', 'VISA', 'MASTER', 'AMEX', 'DISCOVER']:
                     print(f"  - {cell_value}: Row {row_index + 1}")

    # Map Transelect (Revenue Centers)
    if 'transelect' in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name='transelect', header=None)
        print("\n[transelect] Revenue Centers (Row 7):")
        row_index = 6 # Row 7
        for col_index, cell_value in enumerate(df.iloc[row_index]):
             if pd.notna(cell_value):
                print(f"  - {cell_value}: Column {col_index} ({chr(65+col_index)})")

if __name__ == "__main__":
    rj_path = "documentation/back/Rj-19-12-2024.xls"
    map_rj_locations(rj_path)
