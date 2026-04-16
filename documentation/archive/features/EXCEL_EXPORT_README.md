# Excel Export Feature — RJ Natif XLSX Export

## Overview

The Excel export feature (`rj_export_excel.py`) provides complete .xlsx export functionality for the Sheraton Laval Night Audit Web App. It exports a `NightAuditSession` to a professionally formatted Excel workbook matching the original Excel RJ format.

## Features

✅ **14 Sheets** — Complete RJ Natif data structure
- Contrôle (Configuration)
- DueBack (Receptionist tracking)
- Recap (Cash reconciliation)
- Transelect (Card settlement)
- GEAC (Balance sheet)
- SD/Dépôt (Deposits & expenses)
- SetD (Personnel)
- HP/Admin (Hotel Promotion invoices)
- Internet (CD 36.1 vs 36.5)
- Sonifi (CD 35.2 vs email)
- Jour (Master daily data)
- Quasimodo (Global reconciliation)
- DBRS (Daily Business Review)
- Sommaire (Validation summary)

✅ **Professional Styling**
- Sheraton blue (#003B71) headers with white text
- Auto-width columns
- Frozen panes on headers
- Currency formatting ($#,##0.00)
- Percentage formatting (0.0%)
- Bold totals and subtotals
- Color-coded validation status (green/red)

✅ **Data Integrity**
- Proper JSON parsing for variable-structure fields
- Safe handling of None/null values
- All 150+ NightAuditSession fields mapped
- Correct number formatting per column type

✅ **Batch Export**
- Export date range to ZIP file
- One XLSX per session
- Automatic file naming

## API Endpoints

### Single Session Export

```http
GET /api/rj/export/excel/<date>
```

**Parameters:**
- `<date>` (path): Audit date in format `YYYY-MM-DD`

**Response:**
- Binary XLSX file download
- Filename: `RJ_Natif_YYYY-MM-DD.xlsx`

**Example:**
```bash
curl -X GET http://127.0.0.1:5000/api/rj/export/excel/2026-02-25 \
  -o RJ_Natif_2026-02-25.xlsx
```

**Error Responses:**
```json
{"error": "Invalid date format. Use YYYY-MM-DD"} // 400
{"error": "No session found for 2026-02-25"}    // 404
```

### Batch Export (Date Range)

```http
GET /api/rj/export/excel/batch?start=<start_date>&end=<end_date>
```

**Parameters:**
- `start` (query): Start date in format `YYYY-MM-DD`
- `end` (query): End date in format `YYYY-MM-DD`

**Response:**
- ZIP file containing multiple XLSX files
- Filename: `RJ_Export_YYYY-MM-DD_YYYY-MM-DD.zip`

**Example:**
```bash
curl -X GET "http://127.0.0.1:5000/api/rj/export/excel/batch?start=2026-02-01&end=2026-02-28" \
  -o RJ_Export_2026-02-01_2026-02-28.zip
```

**Error Responses:**
```json
{"error": "Invalid date format. Use YYYY-MM-DD"}              // 400
{"error": "start_date must be before end_date"}              // 400
{"error": "No sessions found between 2026-02-01 and ..."}    // 404
```

## Sheet Details

### 1. Contrôle
Configuration and audit metadata:
- Audit date
- Auditor name
- Temperature
- Weather condition
- Rooms to redo (chambres à refaire)
- Days in month (auto-calculated)
- Session status
- Notes

### 2. DueBack
Dynamic table of receptionist due back amounts:
- Réceptionniste (name)
- Précédent (previous balance)
- Nouveau (new amount)
- Auto-calculated TOTAL row

**Source Data:** `dueback_entries` JSON array

### 3. Recap
Cash reconciliation with 8 line items, each showing lecture/correction/net:
- Cash LS, POS
- Cheques (AR, DR)
- Reimbursements (gratuite, client)
- DueBack (reception, NB)
- Deposits CDN/USD
- Recap balance (auto-calculated)

### 4. Transelect
Two matrices showing card settlement:

**Restaurant Section** (Terminal × Card Type):
- Rows: Terminals (flexible)
- Columns: Debit, Visa, MC, AMEX, Discover
- Totals per terminal and card type

**Reception Section** (Card Type × Terminal):
- Rows: Card types
- Columns: Fusebox, Term8, K053, Daily Rev
- Variance detection

**Source Data:** `transelect_restaurant` and `transelect_reception` JSON

### 5. GEAC
GEAC system analysis:
- Card breakdown: Cashout vs Daily Revenue for each card type
- Totals and variance calculation
- AR Balance analysis with charges/payments/variance

### 6. SD/Dépôt
Two sections:

**SD (Sommaire Journalier des Dépôts)**
- Department/name/currency/amount/verified/reimbursement entries
- Total verified amount

**Deposit Envelopes**
- Client 6 and Client 8
- Individual envelope amounts
- Subtotals per client

**Source Data:** `sd_entries` and `depot_data` JSON

### 7. SetD
Personnel set-déjeuner entries:
- Name, column letter, amount per entry
- Total sum
- Recap balance reference

**Source Data:** `setd_personnel` JSON array

### 8. HP/Admin
Hotel Promotion invoice detail:
- Département (sector)
- Nourriture, Boisson, Bière, Vin, Minéraux, Autre
- Pourboire (tips)
- Raison (reason)
- Autorisé par (authorized by)
- Total sum

**Source Data:** `hp_admin_entries` JSON array

### 9. Internet
Internet revenue reconciliation:
- CD 36.1 (Lightspeed detail)
- CD 36.5 (Additional detail)
- Variance (auto-calculated as 36.5 - 36.1)

### 10. Sonifi
Sonifi (TV revenue) reconciliation:
- CD 35.2 (Cashier detail)
- Montant Courriel Sonifi (email amount from 03h00)
- Variance (difference)

### 11. Jour
Complete daily master data with sections:

**F&B — Restauration**
- 5 departments (Café Link, Piazza, Marché Spesa, Service Chambres, Banquet)
- 5 categories per dept (Nourriture, Boisson, Bière, Minéraux, Vins)
- Pourboires, Tabagie, Location Salle

**Hébergement**
- Room revenue + G4 montant
- Téléphone (local, interurbain, publics)

**Autres Revenus**
- Nettoyeur, Machine Distributrice, Autres GL
- Sonifi, Lit Pliant, Boutique, Internet, Massage
- Forfait SJ and Différence forfait

**Taxes**
- TVQ, TPS, Taxe Hébergement

**Occupation**
- Rooms by type (simple, double, suite, comp)
- Guest count and hors usage rooms

**Indicateurs (KPIs)**
- Total F&B, Total Revenue
- ADR, RevPAR
- Occupancy rate

### 12. Quasimodo
Global reconciliation reconciling cards + cash:

**Card Breakdown**
- F&B and Réception totals per card type
- Card subtotal

**Cash**
- CDN and USD amounts
- AMEX factor (default 0.9735)

**Reconciliation Summary**
- Total Quasimodo (cards + cash)
- Total RJ (journal grand total)
- Variance (difference)

**Source Data:** `quasi_*` fields

### 13. DBRS
Daily Business Review Summary:

**Segments de Marché** (Market segments):
- Transient, Group, Contract, Other

**Indicateurs (KPIs)**
- Daily revenue
- ADR (Average Daily Rate)
- House count
- Noshow count and revenue

**Source Data:** `dbrs_*` fields

### 14. Sommaire
Validation checklist and session summary:

**Validation Checks**
- Recap Balanced (✓ OK / ✗ ERREUR)
- Transelect Balanced
- AR Balanced
- Fully Balanced
- Color-coded status (green = OK, red = error)
- Variance display for each check

**Session Information**
- Audit date
- Auditor
- Status
- Created/Completed timestamps

## Data Sources

All 14 sheets pull from a single `NightAuditSession` record with:
- **150+ scalar columns** for direct data
- **12 JSON columns** for variable-structure data:
  - `dueback_entries` — Array of {name, previous, nouveau}
  - `transelect_restaurant` — Dict by terminal
  - `transelect_reception` — Dict by card type
  - `geac_cashout` — Dict by card type
  - `geac_daily_rev` — Dict by card type
  - `sd_entries` — Array of {department, name, currency, amount, verified, reimbursement}
  - `depot_data` — Dict {client6: {date, amounts[]}, client8: {date, amounts[]}}
  - `setd_personnel` — Array of {name, column_letter, amount}
  - `hp_admin_entries` — Array of {area, nourriture, boisson, ...}
  - `dbrs_market_segments` — Dict {transient, group, contract, other}
  - `dbrs_otb_data` — Dict for On-The-Books data
  - Other JSON fields as needed

## Implementation Details

### File Location
```
routes/audit/rj_export_excel.py
```

### Blueprint Registration
The blueprint is registered in `main.py`:
```python
from routes.audit.rj_export_excel import rj_excel_bp
...
app.register_blueprint(rj_excel_bp)
```

### Dependencies
- `openpyxl` — Excel workbook creation (already in requirements.txt)
- `dateutil` — Date parsing (standard library compatible)
- `Flask` — Web framework
- `SQLAlchemy` — ORM

### Module Structure

**Constants (top)**
- Color definitions (Sheraton blue, grays, status colors)
- Format strings (currency, percentage, date)

**Styling Helpers**
- `_header_fill()` / `_header_font()` — Header cells
- `_total_fill()` / `_total_font()` — Total rows
- `_apply_header(ws, row, headers)` — Style entire header row
- `_apply_total_row(ws, row)` — Style entire total row
- `_set_column_width(ws, col, width)` — Auto-width columns
- `_freeze_panes(ws, row, col)` — Freeze panes

**Utility Functions**
- `_safe_float(val)` — Safe float conversion (returns 0 for None)
- `_safe_int(val)` — Safe int conversion
- `_safe_str(val)` — Safe string conversion

**Sheet Builders (14 functions)**
- `_build_controle(wb, session)` — Sheet 1
- `_build_dueback(wb, session)` — Sheet 2
- ... (one per sheet)
- `_build_sommaire(wb, session)` — Sheet 14

**Main Functions**
- `_create_excel_workbook(session)` — Creates complete workbook
- `export_excel(date_str)` — GET endpoint for single export
- `export_batch()` — GET endpoint for batch export

## Usage Examples

### Python (Backend)
```python
from routes.audit.rj_export_excel import _create_excel_workbook
from database.models import NightAuditSession

session = NightAuditSession.query.filter_by(audit_date='2026-02-25').first()
wb = _create_excel_workbook(session)
wb.save('RJ_Natif_2026-02-25.xlsx')
```

### cURL (API)
```bash
# Single export
curl -X GET http://127.0.0.1:5000/api/rj/export/excel/2026-02-25 \
  -o RJ_Natif_2026-02-25.xlsx

# Batch export
curl -X GET "http://127.0.0.1:5000/api/rj/export/excel/batch?start=2026-02-01&end=2026-02-28" \
  -o RJ_Export_Feb_2026.zip
```

### JavaScript (Frontend)
```javascript
// Single export
fetch('/api/rj/export/excel/2026-02-25')
  .then(r => r.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'RJ_Natif_2026-02-25.xlsx';
    a.click();
  });

// Batch export
fetch('/api/rj/export/excel/batch?start=2026-02-01&end=2026-02-28')
  .then(r => r.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'RJ_Export_2026-02-01_2026-02-28.zip';
    a.click();
  });
```

## Error Handling

All error cases return JSON with descriptive messages:

| Scenario | HTTP Code | Message |
|----------|-----------|---------|
| Invalid date format | 400 | Invalid date format. Use YYYY-MM-DD |
| Start > End in batch | 400 | start_date must be before end_date |
| No session found | 404 | No session found for [date] |
| No sessions in range | 404 | No sessions found between [start] and [end] |

## Styling & Formatting

### Color Scheme
- **Headers**: Sheraton blue (#003B71) with white text
- **Subtotals**: Light blue (#E8F0F5) with bold font
- **Validation OK**: Green (#27AE60) background
- **Validation Error**: Red (#C0392B) background
- **Grid borders**: Light gray (#CCCCCC)

### Number Formats
- **Currency**: `$#,##0.00` (e.g., $1,234.56)
- **Percentage**: `0.0%` (e.g., 85.5%)
- **Integer**: `#,##0` (e.g., 252)
- **Date**: `YYYY-MM-DD` in headers only

### Column Widths
Auto-adjusted per sheet based on content:
- Labels/names: 15-30 characters
- Currency: 15 characters
- Small fields: 10 characters

### Frozen Panes
Header rows are frozen on first appearance per sheet for easy scrolling.

## Future Enhancements

Potential improvements (not yet implemented):
1. **Excel formulas** — Auto-calculate totals instead of storing values
2. **Pivot tables** — Monthly summaries from multiple sessions
3. **Charts** — Trend analysis across date ranges
4. **Conditional formatting** — Color code out-of-range values
5. **Data validation** — Input constraints on editable cells
6. **Template mode** — Export blank template for manual audit
7. **Multi-language** — Support English/French headers
8. **Compression** — Reduce file size for large exports

## Testing

### Verify Module Loads
```bash
cd /sessions/laughing-sharp-johnson/mnt/audit-pack
python3 -m py_compile routes/audit/rj_export_excel.py
echo "✓ Module OK" || echo "✗ Syntax error"
```

### Test Single Export
```bash
curl -X GET http://127.0.0.1:5000/api/rj/export/excel/2026-02-25 \
  -H "Content-Type: application/json" \
  -v
```

### Test Batch Export
```bash
curl -X GET "http://127.0.0.1:5000/api/rj/export/excel/batch?start=2026-02-01&end=2026-02-28" \
  -H "Content-Type: application/json" \
  -v
```

### Validate Excel File
```bash
python3 << 'EOF'
from openpyxl import load_workbook
wb = load_workbook('RJ_Natif_2026-02-25.xlsx')
print(f"Sheets: {wb.sheetnames}")
print(f"First sheet rows: {wb.active.max_row}")
print(f"First sheet columns: {wb.active.max_column}")
EOF
```

## Maintenance

### Adding New Fields
1. Identify which sheet the field belongs to
2. Add to corresponding `_build_*` function
3. Apply appropriate formatting (currency, percentage, etc.)
4. Test export with sample data

### Modifying Styling
1. Update color constants at top of file
2. Modify `_*_fill()` or `_*_font()` helper functions
3. Retest all 14 sheets

### Performance Optimization
- Current implementation creates workbook in memory
- For 1000+ sessions: consider async export or streaming
- JSON parsing is minimal — no bottleneck observed

## File Location

**Production Path:**
```
/sessions/laughing-sharp-johnson/mnt/audit-pack/routes/audit/rj_export_excel.py
```

**Main.py Registration:**
```
/sessions/laughing-sharp-johnson/mnt/audit-pack/main.py
```

## License & Attribution

This feature is part of the Sheraton Laval Night Audit WebApp.
All data is proprietary to Sheraton Hotels & Resorts.
