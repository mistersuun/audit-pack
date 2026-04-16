# Quick Start — Excel Export Feature

## 30-Second Overview

The Sheraton Laval Night Audit app now exports audit sessions to professional Excel (.xlsx) files with 14 pre-formatted sheets matching the original RJ workbook.

## Installation

✓ Already installed! Files are in place.

```
routes/audit/rj_export_excel.py  ← Main module (1,104 lines)
main.py                           ← Blueprint registered
```

## API Usage

### Export Single Session

```bash
# Get XLSX file for specific date
curl -X GET http://127.0.0.1:5000/api/rj/export/excel/2026-02-25 \
  -o RJ_Natif_2026-02-25.xlsx
```

**Response:** Binary XLSX file download
**Error:** 404 if no session exists for that date

### Export Date Range to ZIP

```bash
# Get ZIP containing all sessions for date range
curl -X GET "http://127.0.0.1:5000/api/rj/export/excel/batch?start=2026-02-01&end=2026-02-28" \
  -o RJ_Export_Feb_2026.zip
```

**Response:** ZIP file with multiple XLSX files
**Error:** 404 if no sessions exist in range

## What's Included

14 Excel sheets covering all RJ Natif data:

1. **Contrôle** — Audit date, auditor, weather
2. **DueBack** — Receptionist balances
3. **Recap** — Cash reconciliation
4. **Transelect** — Card settlement
5. **GEAC** — Balance sheet analysis
6. **SD/Dépôt** — Deposits and expenses
7. **SetD** — Personnel entries
8. **HP/Admin** — Hotel Promotion invoices
9. **Internet** — CD 36.1 vs 36.5 variance
10. **Sonifi** — CD 35.2 vs email variance
11. **Jour** — Master daily data (F&B, taxes, KPIs)
12. **Quasimodo** — Global reconciliation
13. **DBRS** — Daily Business Review
14. **Sommaire** — Validation checklist

## Features

✓ **Professional formatting**
- Sheraton blue headers (#003B71)
- Currency/percentage formatting
- Color-coded validation status
- Auto-width columns

✓ **Data integrity**
- All 150+ NightAuditSession fields mapped
- Proper JSON parsing
- Safe null handling
- Correct number formats

✓ **Flexible export**
- Single session or batch
- Automatic file naming
- ZIP compression for batches
- Error messages in JSON

## JavaScript Example

```javascript
// Export button click handler
async function exportToExcel(auditDate) {
  const response = await fetch(`/api/rj/export/excel/${auditDate}`);
  if (!response.ok) {
    alert('Export failed');
    return;
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `RJ_Natif_${auditDate}.xlsx`;
  a.click();
  URL.revokeObjectURL(url);
}

// Batch export example
async function exportBatch(startDate, endDate) {
  const url = `/api/rj/export/excel/batch?start=${startDate}&end=${endDate}`;
  const response = await fetch(url);
  const blob = await response.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `RJ_Export_${startDate}_${endDate}.zip`;
  a.click();
}
```

## Testing

### Quick Test with Sample Data

```bash
cd /sessions/laughing-sharp-johnson/mnt/audit-pack

# Create sample session and export it
python3 test_excel_export.py --create-sample --export 2026-02-25

# Verify the file was created
ls -lh RJ_Natif_2026-02-25.xlsx
```

### Validate Excel Structure

```bash
python3 << 'EOF'
from openpyxl import load_workbook

wb = load_workbook('RJ_Natif_2026-02-25.xlsx')
print(f"Total sheets: {len(wb.sheetnames)}")  # Should be 14
print(f"Sheet names: {wb.sheetnames}")
print(f"First sheet rows: {wb.active.max_row}")
print(f"First sheet columns: {wb.active.max_column}")
EOF
```

## HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success — file download |
| 400 | Invalid date format or invalid params |
| 404 | No session found for given date(s) |

## Error Responses

```json
{"error": "Invalid date format. Use YYYY-MM-DD"}
{"error": "No session found for 2026-02-25"}
{"error": "start_date must be before end_date"}
{"error": "No sessions found between 2026-02-01 and 2026-02-28"}
```

## Date Format

**Always use ISO 8601 format:** `YYYY-MM-DD`

✓ Correct:
```
2026-02-25
2026-02-01
```

✗ Wrong:
```
02/25/2026
25-02-2026
Feb 25, 2026
```

## File Sizes

- **Single XLSX:** ~100-200 KB (typical)
- **ZIP (10 sessions):** ~300-500 KB
- **ZIP (30 sessions):** ~1-2 MB

## Colors Used

| Element | Color | Code |
|---------|-------|------|
| Headers | Sheraton Blue | #003B71 |
| Subtotals | Light Blue | #E8F0F5 |
| OK Status | Green | #27AE60 |
| Error Status | Red | #C0392B |
| Borders | Gray | #CCCCCC |

## Number Formatting

| Type | Format | Example |
|------|--------|---------|
| Currency | $#,##0.00 | $1,234.56 |
| Percentage | 0.0% | 78.5% |
| Integer | #,##0 | 252 |

## Common Tasks

### Add Export Button to UI

```html
<!-- In your template -->
<a href="/api/rj/export/excel/{{ session.audit_date }}"
   class="btn btn-primary"
   download>
  📥 Télécharger Excel
</a>
```

### Export All Sessions This Month

```bash
# Get first and last day of current month
START=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d)
END=$(date +%Y-%m-%d)

curl "http://127.0.0.1:5000/api/rj/export/excel/batch?start=$START&end=$END" \
  -o "RJ_Export_$(date +%Y%m).zip"
```

### Batch Export in Python

```python
import requests
from dateutil.parser import parse as parse_date

start = '2026-02-01'
end = '2026-02-28'

url = f'http://127.0.0.1:5000/api/rj/export/excel/batch?start={start}&end={end}'
response = requests.get(url)

if response.status_code == 200:
    with open(f'RJ_Export_{start}_{end}.zip', 'wb') as f:
        f.write(response.content)
    print("✓ Export successful")
else:
    print(f"✗ Error: {response.json()['error']}")
```

## Troubleshooting

### "No session found for [date]"

- Verify the session exists in database
- Check date format is YYYY-MM-DD
- Try another date with known data

### "Invalid date format"

- Use YYYY-MM-DD format only
- Check for typos
- Avoid spaces or special characters

### File download not starting

- Check browser console for errors
- Verify HTTP response code is 200
- Try a different browser

### Excel file won't open

- Download may have been corrupted
- Try exporting again
- Check file size is >10 KB

## Module Location

```
/sessions/laughing-sharp-johnson/mnt/audit-pack/routes/audit/rj_export_excel.py
```

## Documentation

- **Full Details:** EXCEL_EXPORT_README.md
- **Implementation:** IMPLEMENTATION_SUMMARY.md
- **Testing:** test_excel_export.py
- **This Guide:** QUICK_START_EXCEL_EXPORT.md

## Support

For detailed information, see:
1. EXCEL_EXPORT_README.md (comprehensive API reference)
2. IMPLEMENTATION_SUMMARY.md (technical architecture)
3. test_excel_export.py (working examples)

---

**Status:** ✓ Ready for Production
**Version:** 1.0.0
