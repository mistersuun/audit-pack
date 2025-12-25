
import pandas as pd

def inspect_data_flow(file_path):
    xls = pd.ExcelFile(file_path)
    
    print("--- INSPECTING DATA FLOW & LOGIC ---")
    
    # 1. Inspect SetD to see how it relates to DUBACK#
    if 'SetD' in xls.sheet_names:
        print("\n[SetD] Structure (First 15 rows):")
        df = pd.read_excel(xls, sheet_name='SetD', header=None)
        print(df.iloc[:15].to_string())

    # 2. Inspect Depot to see its structure
    if 'depot' in xls.sheet_names:
        print("\n[depot] Structure (First 20 rows):")
        df = pd.read_excel(xls, sheet_name='depot', header=None)
        print(df.iloc[:20].to_string())

if __name__ == "__main__":
    rj_path = "documentation/back/Rj-19-12-2024.xls"
    inspect_data_flow(rj_path)

