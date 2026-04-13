# RJ Sheet Parser — Usage Guide

Quick reference for using the RJ archive parser scripts to extract and populate structured data from raw RJ Excel workbooks.

## Quick Start

```bash
cd /sessions/laughing-sharp-johnson/mnt/audit-pack
python populate_from_archives.py
```

That's it! The script will:
1. Find all RJArchive records in the database
2. Extract data from EJ, salaires, and Budget sheets
3. Populate JournalEntry, DailyLaborMetrics, and MonthlyBudget tables
4. Print a summary of what was inserted

## What Gets Populated

### 1. JournalEntry (from EJ sheet)

**What:** Daily general ledger entries extracted from the EJ (Entrées Journalières) sheet

**Example:**
```
audit_date: 2026-02-03
gl_code: 075001
description_1: VENTES CHAMBRES
amount: $135,881.09
source: s-ej10
```

**Count:** 191 GL codes per archive date
**Total (3 archives):** 573 records

**To query:**
```python
from database import db
from database.models import JournalEntry

# Get all JournalEntry records for 2026-02-03
entries = JournalEntry.query.filter_by(audit_date='2026-02-03').all()

# Get total room revenue for a date
room_sales = db.session.query(JournalEntry).filter(
    JournalEntry.audit_date == '2026-02-03',
    JournalEntry.gl_code == '075001'
).first()
print(f"Room Sales: ${room_sales.amount:,.2f}")

# Get total amounts by GL code
from sqlalchemy import func
gl_totals = db.session.query(
    JournalEntry.gl_code,
    JournalEntry.description_1,
    func.sum(JournalEntry.amount)
).filter(
    JournalEntry.audit_date >= '2026-02-01'
).group_by(JournalEntry.gl_code).all()
```

### 2. DailyLaborMetrics (from salaires sheet)

**What:** Daily labor hours and costs aggregated by department

**Example:**
```
date: 2026-02-03
department: RECEPTION
regular_hours: 40.0
labor_cost: $1,059.28
source: rj_sheet_parser
```

**Count:** 6 departments per archive date (from salaires parsing)
**Total (3 archives):** 18 records

**To query:**
```python
from database import db
from database.models import DailyLaborMetrics

# Get all departments' labor for a date
labor = DailyLaborMetrics.query.filter_by(
    date='2026-02-03',
    source='rj_sheet_parser'
).all()

# Total labor cost for a date
total_labor = db.session.query(
    func.sum(DailyLaborMetrics.labor_cost)
).filter(
    DailyLaborMetrics.date == '2026-02-03',
    DailyLaborMetrics.source == 'rj_sheet_parser'
).scalar()
print(f"Total Labor Cost: ${total_labor:,.2f}")

# Department breakdown
dept_breakdown = DailyLaborMetrics.query.filter_by(
    date='2026-02-03',
    source='rj_sheet_parser'
).order_by(DailyLaborMetrics.department).all()

for metric in dept_breakdown:
    print(f"{metric.department}: {metric.regular_hours} hrs @ ${metric.labor_cost:,.2f}")
```

### 3. MonthlyBudget (from Budget sheet)

**What:** Monthly revenue and cost budgets by category

**Status:** No new records inserted (they already existed from demo_seed)

**To query:**
```python
from database import db
from database.models import MonthlyBudget

# Get February 2026 budget
feb_budget = MonthlyBudget.query.filter_by(year=2026, month=2).first()
print(f"Room Revenue Budget: ${feb_budget.room_revenue_budget:,.2f}")
print(f"F&B Revenue Budget: ${feb_budget.fb_revenue_budget:,.2f}")
print(f"Labor Cost Budget: ${feb_budget.labor_cost_budget:,.2f}")
```

## Architecture

### Data Flow

```
RJArchive (database)
    ↓
    └─→ RJSheetData (raw JSON from Excel)
        ├─→ EJ sheet
        │   └─→ parse_ej_sheet()
        │       └─→ JournalEntry table
        │
        ├─→ salaires sheet
        │   └─→ parse_salaires_sheet()
        │       └─→ DailyLaborMetrics table
        │
        └─→ Budget sheet
            └─→ parse_budget_sheet()
                └─→ MonthlyBudget table
```

### Key Components

**`utils/rj_sheet_parser.py`**
- Core parsing logic
- Three main functions: `parse_ej_sheet()`, `parse_salaires_sheet()`, `parse_budget_sheet()`
- Helper function: `parse_all_sheets_for_archive()`
- Idempotent upsert logic using unique constraints

**`populate_from_archives.py`**
- Orchestration script
- Imports `parse_all_sheets_for_archive()`
- Loops through all RJArchive records
- Commits changes to database
- Prints summary

## Error Handling

If something goes wrong:

```bash
# Check console output for error details
python populate_from_archives.py 2>&1 | tee parser.log

# Query what was actually inserted
python3 << 'EOF'
from main import create_app
from database.models import JournalEntry, DailyLaborMetrics

app = create_app()
with app.app_context():
    je_count = JournalEntry.query.filter(
        JournalEntry.audit_date >= '2026-02-01'
    ).count()
    print(f"JournalEntry: {je_count}")

    dlm_count = DailyLaborMetrics.query.filter(
        DailyLaborMetrics.date >= '2026-02-01'
    ).count()
    print(f"DailyLaborMetrics: {dlm_count}")
EOF
```

## Idempotency & Re-running

All parsers use upsert logic. You can safely run the script multiple times:

```bash
python populate_from_archives.py  # First run: inserts 573 JournalEntry, 18 DailyLaborMetrics
python populate_from_archives.py  # Second run: inserts 0 (already exist, skipped by upsert)
```

The unique constraints prevent duplicates:
- **JournalEntry:** `(audit_date, gl_code)` must be unique
- **DailyLaborMetrics:** `(date, department)` must be unique
- **MonthlyBudget:** `(year, month)` must be unique

## Advanced Usage

### Parsing a Single Archive

```python
from main import create_app
from database import db
from database.models import RJArchive
from utils.rj_sheet_parser import parse_all_sheets_for_archive

app = create_app()
with app.app_context():
    archive = RJArchive.query.filter_by(audit_date='2026-02-03').first()
    summary = parse_all_sheets_for_archive(archive)

    print(f"Inserted {summary['journal_entries']} JournalEntry records")
    print(f"Inserted {summary['daily_labor_metrics']} DailyLaborMetrics records")
    print(f"Inserted {summary['monthly_budgets']} MonthlyBudget records")

    db.session.commit()
```

### Parsing Only One Sheet Type

```python
from main import create_app
from database import db
from database.models import RJArchive
from utils.rj_sheet_parser import parse_ej_sheet

app = create_app()
with app.app_context():
    archive = RJArchive.query.filter_by(audit_date='2026-02-03').first()

    # Parse only EJ sheet
    je_records = parse_ej_sheet(archive)
    print(f"Found {len(je_records)} JournalEntry records")

    db.session.commit()
```

### Debugging Raw Data

```python
from main import create_app
from database import db
from database.models import RJSheetData
import json

app = create_app()
with app.app_context():
    # Get raw EJ sheet data
    ej_data = RJSheetData.query.filter_by(
        sheet_name='EJ',
        audit_date='2026-02-03'
    ).first()

    rows = json.loads(ej_data.data_json)
    print(f"Total rows: {len(rows)}")
    print(f"Headers: {rows[0]}")
    print(f"First data row: {rows[1]}")
```

## Performance

- **Processing time:** < 1 second per archive (typical)
- **Database commits:** Single transaction for all 3 archives
- **Memory:** < 50 MB for all parsing operations

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError: No module named 'main'" | Ensure you're in `/sessions/laughing-sharp-johnson/mnt/audit-pack/` directory |
| "No RJArchive records found" | Check if RJ files have been uploaded to the database |
| "JournalEntry duplicate" | Run `parse_ej_sheet()` directly to see which dates/GL codes are being processed |
| "ZeroDivisionError" | Check for empty sheet data in RJSheetData.data_json |

## Output Examples

### Successful run:
```
Found 3 archive(s) to process.

Processing archive: 2026-02-03 (Rj 03-02-2026.xls)
  Archive ID: 2
  Journal Entries added: 191
  Labor Metrics added: 6
  Monthly Budgets added: 0

Processing archive: 2026-02-04 (Rj 04-02-2026.xls)
  Archive ID: 3
  Journal Entries added: 191
  Labor Metrics added: 6
  Monthly Budgets added: 0

Processing archive: 2026-02-08 (2026-02-08.xls)
  Archive ID: 1
  Journal Entries added: 191
  Labor Metrics added: 6
  Monthly Budgets added: 0

======================================================================
SUMMARY
======================================================================
Archives processed: 3
Total JournalEntry records added: 573
Total DailyLaborMetrics records added: 18
Total MonthlyBudget records added: 0

No errors!

Commit successful!
```

## Next Steps

1. **Verify data quality:**
   - Run queries to inspect the parsed data
   - Check for unexpected null values or negative amounts
   - Validate GL codes against your chart of accounts

2. **Automate updates:**
   - Add a cron job to run `populate_from_archives.py` when new RJ archives are uploaded
   - Set up alerts if parsing fails

3. **Enhance parsing:**
   - Add more sheet types (Nettoyeur, Internet, Sonifi, etc.)
   - Implement reconciliation between parsed data and NightAuditSession
   - Generate reports from parsed data

## Files

- **Parser module:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/rj_sheet_parser.py` (12 KB)
- **Population script:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/populate_from_archives.py` (2.8 KB)
- **Documentation:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/RJ_PARSER_README.md` (8.2 KB)
- **This guide:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/PARSER_USAGE_GUIDE.md`
