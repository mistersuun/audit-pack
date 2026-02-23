# Monthly Summary Excel Export Feature

## Quick Start

The Sheraton Laval RJ Natif webapp now includes a monthly summary export endpoint that generates a professional Excel workbook with daily audit data for an entire month.

### Endpoint
```
GET /api/rj/native/export/month/<year>/<month>
```

### Example
```bash
# Export February 2025
curl http://localhost:5000/api/rj/native/export/month/2025/2 -o Sommaire_RJ_2025-02.xlsx
```

### Browser Integration
```javascript
// Add to your dashboard or admin page
function exportMonthlyReport() {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth() + 1;
  window.location = `/api/rj/native/export/month/${year}/${month}`;
}
```

## What's Included

### Four Professional Excel Sheets

1. **Sommaire** (Overview Dashboard)
   - Daily summary of all key metrics
   - 17 columns with revenues, ADR, occupancy, deposits, balances
   - Yellow highlighting for incomplete sessions

2. **F&B Détail** (Food & Beverage Breakdown)
   - Revenue by department (Café, Piazza, Spesa, Chambres Svc, Banquet)
   - Tips, tobacco sales, room rental income
   - 10 columns total

3. **Réconciliation** (Cash Reconciliation)
   - Detailed breakdown of all cash and check items
   - Lecture + Correction displayed as NET
   - Balance and variance metrics
   - 14 columns

4. **Occupation** (Room Metrics)
   - Room sales by type (Simple, Double, Suite, Comp)
   - Occupancy %, ADR, RevPAR
   - Guest count
   - 12 columns

### Professional Formatting
- Arial 10pt font
- Dark blue headers with frozen panes
- Alternating row colors (light gray)
- Currency ($#,##0.00) and percentage (0.0%) formatting
- All totals use Excel formulas (SUM, AVERAGE)
- Auto-fitted column widths
- Color-coded sheet tabs

## Documentation Files

### For API Users
- **MONTHLY_EXPORT.md** - Complete API documentation with all details

### For Developers
- **CODE_CHANGES.md** - Technical implementation details
- **IMPLEMENTATION_SUMMARY.md** - Architecture and integration notes

### For Testing
- **test_monthly_export.py** - Functional test suite (run: `python test_monthly_export.py`)

## Features

✓ One-click monthly export
✓ Professional Excel formatting
✓ Excel formulas for dynamic totals
✓ Warning highlights for incomplete audits
✓ Efficient database queries
✓ Authentication required
✓ Comprehensive error handling
✓ Production-ready code

## Database Fields Used

The endpoint automatically pulls data from these NightAuditSession fields:

**Recap (Cash):**
- cash_ls_lecture, cash_ls_corr, cash_pos_lecture, cash_pos_corr
- cheque_ar_*, cheque_dr_*, remb_gratuite_*, remb_client_*
- dueback_reception_*, dueback_nb_*
- deposit_cdn, deposit_us, recap_balance

**Jour (Daily):**
- jour_room_revenue, jour_total_fb, jour_total_revenue
- jour_adr, jour_occupancy_rate, jour_revpar
- jour_rooms_simple, jour_rooms_double, jour_rooms_suite, jour_rooms_comp
- jour_nb_clients, jour_rooms_hors_usage
- jour_*_nourriture, jour_*_boisson, jour_*_bieres, jour_*_mineraux, jour_*_vins (5 depts × 5 categories)
- jour_pourboires, jour_tabagie, jour_location_salle

**Quasimodo & Variances:**
- quasi_total, quasi_rj_total, quasi_variance
- internet_variance, sonifi_variance

**Metadata:**
- audit_date, auditor_name, status

## No Installation Required

All dependencies are already in your `requirements.txt`:
- openpyxl
- Flask
- SQLAlchemy

Just deploy the updated `routes/audit/rj_native.py` and restart the app.

## Testing

Run the test suite to verify the endpoint works:
```bash
python test_monthly_export.py
```

Expected output:
```
Creating test data...
✓ Created 28 test NightAuditSession records for February 2025

Testing export endpoint...
✓ Export endpoint returned status 200
✓ Generated valid Excel workbook
✓ Sommaire: 30 rows × 17 columns
✓ F&B Détail: 30 rows × 10 columns
✓ Réconciliation: 30 rows × 14 columns
✓ Occupation: 30 rows × 12 columns
```

## Deployment

1. Update `routes/audit/rj_native.py` with the new code
2. Restart the Flask application
3. Endpoint is immediately available at `/api/rj/native/export/month/<year>/<month>`

No database migrations needed!

## Support

For questions or issues, see the documentation files:
- `MONTHLY_EXPORT.md` for API details
- `CODE_CHANGES.md` for technical details
- `test_monthly_export.py` for examples

---

**Status:** Production Ready
**Last Updated:** February 17, 2026
