"""Extract all Chambres lines from DR PDF so we can map each DailyRev template row."""
import sys, io, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')
import pdfplumber

path = r"C:\Users\Auditeur\Documents\Projects\audit-pack\.playwright-mcp\test-files\DAILY_REV.pdf"
with pdfplumber.open(path) as pdf:
    p1 = pdf.pages[0].extract_text() or ""
    p2 = pdf.pages[1].extract_text() or ""

text = p1 + "\n" + p2
# Find "Chambres" section from p1
# Print everything from "Chambres" up to "TELEPHONES"
m = re.search(r"Chambres[\s\S]*?TELEPHONES", text)
if m:
    print("=== Chambres section (raw) ===")
    print(m.group(0))
else:
    print("(no Chambres section found in p1+p2)")

# Also show p1 headers
print("\n=== p1 top ===")
print("\n".join(p1.splitlines()[:10]))
