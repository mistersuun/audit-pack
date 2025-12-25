
import pandas as pd

def inspect_sd_file(file_path):
    print(f"--- INSPECTING SD FILE: {file_path} ---")
    try:
        df = pd.read_excel(file_path, header=None)
        
        # Search for keywords like "Montant", "Verifie", "Total"
        print("\nSearching for keywords in first 20 rows/cols...")
        for r in range(min(20, len(df))):
            for c in range(min(20, len(df.columns))):
                val = str(df.iloc[r, c]).lower()
                if any(k in val for k in ['montant', 'verifie', 'vérifié', 'total']):
                    print(f"Found '{df.iloc[r,c]}' at Row {r}, Col {c}")
                    
        # Print a small block around where we find interesting data
        # Let's assume the data starts around row 5 based on previous peek
        print("\nBlock Preview (Rows 0-10):")
        print(df.iloc[0:10].to_string())
        
    except Exception as e:
        print(f"Error reading SD file: {e}")

if __name__ == "__main__":
    sd_path = "documentation/back/Sommaire journalier des dépôts.xls"
    inspect_sd_file(sd_path)
