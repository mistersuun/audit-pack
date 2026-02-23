# RJ Sheet Parser — Archive Data Extraction

This document describes the RJ archive parsing system that extracts structured data from raw RJSheetData records and populates the database models.

## Overview

The system consists of two main components:

1. **`utils/rj_sheet_parser.py`** — Core parsing logic for three key sheets
2. **`populate_from_archives.py`** — Orchestration script to process all archives and populate models

## Files Created

### `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/rj_sheet_parser.py`

Core parser module with three main functions:

#### `parse_ej_sheet(archive: RJArchive) -> list`
**Maps:** RJSheetData sheet "EJ" → JournalEntry table

- **Input:** EJ sheet with headers: `['A/code gl', 'B/cc1', 'C/cc2', 'D/description 1', 'E/description 2', 'F/source', 'G/MONTANT']`
- **Output:** List of JournalEntry objects
- **Logic:**
  - Reads JSON array from `RJSheetData.data_json`
  - Skips header row (row 0)
  - Extracts GL code, cost centers, descriptions, source, amount from each data row
  - Uses **upsert logic**: checks if `(audit_date, gl_code)` exists before inserting
  - Unique constraint: `uq_journal_date_gl` prevents duplicates

**Example data mapping:**
```
Row: ['075001', 2, None, 'VENTES CHAMBRES', '2026-02-07', 's-ej10', 324232.11]
     ↓
JournalEntry(
  audit_date='2026-02-03',
  gl_code='075001',
  cost_center_1=2.0,
  cost_center_2=None,
  description_1='VENTES CHAMBRES',
  description_2='2026-02-07',
  source='s-ej10',
  amount=324232.11
)
```

#### `parse_salaires_sheet(archive: RJArchive) -> list`
**Maps:** RJSheetData sheet "salaires" → DailyLaborMetrics table

- **Input:** salaires sheet with data starting at row 5 (row 4 is headers)
- **Output:** List of DailyLaborMetrics objects
- **Structure:**
  - Row 4: Column headers including "Departement", "HRES SUP", "TAUX", "TOTAL HRES", "$ TOTAL"
  - Row 5+: Department rows with: `[Department, SubDept, hours, cost, ...]`
- **Logic:**
  - Aggregates hours and costs by department (in case multiple employee rows per dept)
  - Extracts `regular_hours` from column 2, `labor_cost` from column 3
  - Creates one DailyLaborMetrics record per department per date
  - Uses upsert: checks if `(date, department)` exists before inserting
  - Unique constraint: `uq_daily_labor`

**Example data mapping:**
```
Row: ['RECEPTION', 'RECEPTION', 40, 1059.28, ...]
     ↓
DailyLaborMetrics(
  date='2026-02-03',
  year=2026,
  month=2,
  department='RECEPTION',
  regular_hours=40.0,
  overtime_hours=0.0,
  employees_count=1,
  labor_cost=1059.28,
  source='rj_sheet_parser'
)
```

#### `parse_budget_sheet(archive: RJArchive) -> list`
**Maps:** RJSheetData sheet "Budget" → MonthlyBudget table

- **Input:** Budget sheet with revenue category rows
- **Output:** List of MonthlyBudget objects
- **Structure:**
  - Each row: `[Category, AnnualBudget, ..., GL_Code, MonthlyBudget, ...]`
  - Categories: "Chambres", "Nour. Piazza/Bar", "Nour. Banquet", etc.
- **Logic:**
  - Categorizes rows by keyword (chambre, nour, bar, banquet, etc.)
  - Sums up monthly budgets by category
  - Calculates total revenue budget
  - Creates one MonthlyBudget record per year/month
  - Uses upsert: checks if `(year, month)` exists before inserting
  - Unique constraint: `uq_monthly_budget`

**Categories mapped to fields:**
- "Chambres" → `room_revenue_budget`
- "Nour*", "Bar", "Banquet", "Piazza" → `fb_revenue_budget`
- Other → `other_revenue_budget`

### `/sessions/laughing-sharp-johnson/mnt/audit-pack/populate_from_archives.py`

Orchestration script that ties everything together.

**Usage:**
```bash
python populate_from_archives.py
```

**What it does:**
1. Creates Flask app context using `create_app()`
2. Queries all RJArchive records from database
3. For each archive, calls `parse_all_sheets_for_archive()` which:
   - Parses EJ sheet and inserts JournalEntry records
   - Parses salaires sheet and inserts DailyLaborMetrics records
   - Parses Budget sheet and inserts MonthlyBudget records
4. Tracks results in a summary dict
5. Commits all changes to database (or rolls back on error)
6. Prints detailed summary of what was inserted

**Output example:**
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

## Database Models

### JournalEntry
- **Table:** `journal_entries`
- **Columns:** `id`, `audit_date`, `gl_code`, `cost_center_1`, `cost_center_2`, `description_1`, `description_2`, `source`, `amount`, `created_at`
- **Unique Constraint:** `(audit_date, gl_code)` as `uq_journal_date_gl`

### DailyLaborMetrics
- **Table:** `daily_labor_metrics`
- **Columns:** `id`, `date`, `year`, `month`, `department`, `regular_hours`, `overtime_hours`, `employees_count`, `labor_cost`, `source`
- **Unique Constraint:** `(date, department)` as `uq_daily_labor`

### MonthlyBudget
- **Table:** `monthly_budgets`
- **Columns:** `id`, `year`, `month`, `room_revenue_budget`, `fb_revenue_budget`, `other_revenue_budget`, `total_revenue_budget`, `labor_cost_budget`, `operating_expense_budget`, `occupancy_budget`, `adr_budget`, `source`
- **Unique Constraint:** `(year, month)` as `uq_monthly_budget`

## Insertion Results (Feb 2026 Archives)

**JournalEntry:**
- 573 total records inserted (191 per archive date)
- 3 archive dates covered (2026-02-03, 02-04, 02-08)
- 191 unique GL codes
- Total amount: $1,536,567.08

**DailyLaborMetrics:**
- 18 total records inserted (6 per archive date)
- 3 archive dates covered
- 6 unique departments per date
- Total hours: 572.80
- Total labor cost: $21,632.09

**MonthlyBudget:**
- 0 new records inserted (upsert: already existed from demo_seed)
- Existing records: 2026-01 and 2026-02

## Idempotency

All parsers use upsert logic (check-before-insert) based on unique constraints:

- **JournalEntry:** Won't re-insert if `(audit_date, gl_code)` pair already exists
- **DailyLaborMetrics:** Won't re-insert if `(date, department)` pair already exists
- **MonthlyBudget:** Won't re-insert if `(year, month)` pair already exists

This means you can safely run `populate_from_archives.py` multiple times without duplicating data.

## Error Handling

- Each parser function catches exceptions and logs them to the summary dict
- `parse_all_sheets_for_archive()` returns a summary with `errors` list
- Main script prints errors at the end
- If commit fails, entire transaction is rolled back

## Future Improvements

1. **Departments normalization:** Some departments appear with variations (e.g., "RECEPTION" vs "RECEPTIONIST"). Add mapping table for consistency.
2. **Budget granularity:** Current budget parser sums categories. Could store individual budget line items.
3. **Overtime hours:** Salaires sheet likely contains overtime data; currently treated as 0.
4. **Validation reports:** Add pre-commit validation to flag suspicious data (e.g., negative amounts, mismatches).
5. **Audit trail:** Track which archives have been processed and when.

## Testing

To verify the data was inserted correctly:

```python
# Count records by date
from database import db
from database.models import JournalEntry, DailyLaborMetrics, MonthlyBudget

# JournalEntry count
je_count = db.session.query(JournalEntry).filter(
    JournalEntry.audit_date >= '2026-02-01'
).count()
print(f"JournalEntry records: {je_count}")  # Should be 573

# DailyLaborMetrics count
dlm_count = db.session.query(DailyLaborMetrics).filter(
    DailyLaborMetrics.date >= '2026-02-01',
    DailyLaborMetrics.source == 'rj_sheet_parser'
).count()
print(f"DailyLaborMetrics records: {dlm_count}")  # Should be 18
```
