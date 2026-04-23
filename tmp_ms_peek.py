"""Dump Market Segment raw text (page 1 TODAY section)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber
path = r"C:\Users\Auditeur\Documents\Projects\audit-pack\.playwright-mcp\test-files\MARKET_SEGMENT.pdf"
with pdfplumber.open(path) as pdf:
    for i, p in enumerate(pdf.pages):
        if i > 1:
            break
        t = p.extract_text() or ""
        print(f"--- page {i+1} ---")
        print(t)
        print()
