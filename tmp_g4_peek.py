"""Peek at G4.pdf."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber
path = r"C:\Users\Auditeur\Documents\Projects\audit-pack\.playwright-mcp\test-files\G4.pdf"
with pdfplumber.open(path) as pdf:
    print(f"pages: {len(pdf.pages)}")
    for i, p in enumerate(pdf.pages):
        t = p.extract_text() or ""
        print(f"--- page {i+1} ---")
        print(t[:2500])
