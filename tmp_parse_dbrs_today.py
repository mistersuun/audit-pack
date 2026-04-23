"""Parse Apr 21 DR + MS PDFs and dump parser output."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Auditeur\Documents\Projects\audit-pack')

from utils.parsers.daily_revenue_parser import DailyRevenueParser
from utils.parsers.market_segment_parser import MarketSegmentParser

DR_PATH = r"C:\Users\Auditeur\Documents\Projects\audit-pack\.playwright-mcp\test-files\DAILY_REV.pdf"
MS_PATH = r"C:\Users\Auditeur\Documents\Projects\audit-pack\.playwright-mcp\test-files\MARKET_SEGMENT.pdf"

# Fallback to K drive if those aren't the today files
import os
if not os.path.exists(DR_PATH):
    DR_PATH = r"K:\Audition\04 - April\21-04-2026\DAILY_REV.pdf"
MS_K = r"K:\Audition\04 - April\21-04-2026\MARKET_SEGMENT.pdf"

print(f"DR: {DR_PATH}")
print(f"MS: {MS_PATH if os.path.exists(MS_PATH) else MS_K}")

with open(DR_PATH, "rb") as f:
    dr_bytes = f.read()
ms_path = MS_PATH if os.path.exists(MS_PATH) else MS_K
with open(ms_path, "rb") as f:
    ms_bytes = f.read()

print("\n" + "=" * 80)
print("DailyRevenueParser")
print("=" * 80)
dr = DailyRevenueParser(dr_bytes, filename="DAILY_REV.pdf")
dr.parse()
dr.validate()
print(f"Confidence: {dr.confidence}")
print(f"Validation errors: {dr.validation_errors}")
print(f"Validation warnings: {dr.validation_warnings}")
print(f"Parsed keys: {list(dr.extracted_data.keys())}")
# Dump revenue/non_revenue in full
print("\n--- revenue ---")
print(json.dumps(dr.extracted_data.get("revenue", {}), indent=2, default=str))
print("\n--- non_revenue ---")
print(json.dumps(dr.extracted_data.get("non_revenue", {}), indent=2, default=str))
print("\n--- settlements ---")
print(json.dumps(dr.extracted_data.get("settlements", {}), indent=2, default=str))
print("\n--- balance ---")
print(json.dumps(dr.extracted_data.get("balance", {}), indent=2, default=str))

print("\n--- get_fillable_data ---")
try:
    fd = dr.get_fillable_data()
    print(json.dumps(fd, indent=2, default=str))
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 80)
print("MarketSegmentParser")
print("=" * 80)
ms = MarketSegmentParser(ms_bytes, filename="MARKET_SEGMENT.pdf")
ms.parse()
ms.validate()
print(f"Confidence: {ms.confidence}")
print(f"Validation errors: {ms.validation_errors}")
print(f"Validation warnings: {ms.validation_warnings}")
print(f"Parsed keys: {list(ms.extracted_data.keys())}")
print(f"\nSegments count: {len(ms.segments)}")
for seg in ms.segments:
    print(f"  {seg['code']:4} {seg['name'][:20]:20} rooms_today={seg['today_rooms']:4} rev_today={seg['today_revenue']:10.2f}")

print("\n--- extracted_data totals ---")
for k in ('today_guests', 'today_rooms', 'today_revenue', 'today_avg_rate', 'today_occupancy',
          'mtd_guests', 'mtd_rooms', 'mtd_revenue',
          'transient_rooms', 'transient_revenue', 'group_rooms', 'group_revenue',
          'contract_rooms', 'contract_revenue', 'complimentary_rooms_today'):
    print(f"  {k}: {ms.extracted_data.get(k)}")

print("\n--- get_fillable_data ---")
try:
    fd = ms.get_fillable_data()
    print(json.dumps(fd, indent=2, default=str))
except Exception as e:
    print(f"ERROR: {e}")
