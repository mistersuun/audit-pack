import pandas as pd
import os

def analyze_rj(file_path):
    print(f"Analyzing file: {file_path}")
    try:
        xls = pd.ExcelFile(file_path)
        print(f"Sheet names found: {xls.sheet_names}")
        
        sheets_to_inspect = ['Recap', 'transelect', 'geac_ux', 'jour', 'controle', 'DUBACK#', 'Nettoyeur', 'somm_nettoyeur']
        
        for sheet_name in sheets_to_inspect:
            if sheet_name in xls.sheet_names:
                print(f"\n--- Preview of Sheet: {sheet_name} ---")
                df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                # Print first 10 rows and first 10 columns to give an idea of structure
                print(df.iloc[:10, :10].to_string())
            else:
                print(f"\n[Warning] Sheet '{sheet_name}' not found in the file.")
                
    except Exception as e:
        print(f"Error analyzing Excel file: {e}")

if __name__ == "__main__":
    rj_path = "documentation/back/Rj-19-12-2024.xls"
    analyze_rj(rj_path)
