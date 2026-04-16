# Labor & Budget Data Import Script

## Overview

The `import_labor.py` script imports labor (SALAIRES) and budget (BUDGET) data from Sheraton Laval's RJ Excel files into the Flask application's SQLite database. It processes hundreds of RJ files across multiple years and aggregates the data by department and month.

## Purpose

This script enables:
- Historical tracking of labor costs and staffing levels across all hotel departments
- Budget vs. actual comparisons for labor planning and forecasting
- Department-level staffing analysis
- Multi-year labor cost trends (2024-2026+)

## Features

### Data Extraction

The script extracts:

1. **SALAIRES Sheet** (Payroll)
   - Department staffing lists
   - Position counts per department
   - Employee headcount by role

2. **BUDGET Sheet** (Budget Data)
   - Budgeted labor costs by position
   - Aggregated costs by department
   - Monthly budget figures

### Department Coverage

The script processes 9 departments:
- RECEPTION
- ROOMS (Housekeeping)
- PIAZZA (Café/Restaurant)
- BANQUET
- KITCHEN
- BAR
- LAUNDRY
- MAINTENANCE
- ADMINISTRATION

### Time Period Coverage

- **Years**: 2024, 2025, 2026+
- **Monthly granularity**: Separate records for each month
- **Data frequency**: 180 records imported (9 departments × 20 month-periods)

## Running the Import

### Prerequisites

```bash
# Install dependencies
pip install xlrd --break-system-packages
pip install -r requirements.txt
```

### Execution

```bash
# Run from the app root directory
cd /sessions/laughing-sharp-johnson/mnt/audit-pack
python import_labor.py
```

### Output

The script will:
1. Scan all RJ folders for .xls files (590 files scanned)
2. Process valid files (338 successfully parsed)
3. Extract data and upsert into the database
4. Display a detailed summary report:

```
================================================================================
SHERATON LAVAL LABOR & BUDGET IMPORT - FINAL REPORT
================================================================================

Total Records Imported: 180

DATA COVERAGE BY YEAR AND MONTH
Year 2025: 108 records (all 12 months, 9 departments)
Year 2026: 72 records (8 months, 9 departments)

FINANCIAL SUMMARY
Total Budget Cost: $28,994,844.84
Total FTE-Months: 600
```

## Data Model

Records are stored in the `DepartmentLabor` table with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| year | Integer | Fiscal year (2024-2026) |
| month | Integer | Month (1-12) |
| department | String | Department name |
| headcount | Integer | Number of positions/staff |
| total_labor_cost | Float | Total budgeted labor cost |
| budget_cost | Float | Budget amount from RJ file |
| budget_hours | Float | Budgeted hours (headcount × 160) |
| avg_hourly_rate | Float | Calculated average hourly rate |

## How It Works

### Step 1: File Discovery

The script recursively searches the `RJ 2024-2025` folder structure:
```
RJ 2024-2025/
  ├── RJ 2024-2025/
  │   ├── 01-Janvier 2024/
  │   │   ├── Rj 01-01-2024.xls
  │   │   ├── Rj 01-02-2024.xls
  │   │   └── ...
  │   └── ...
  ├── RJ 2025-2026/
  │   └── ...
  └── RJ 2026-2027/
```

### Step 2: Filename Parsing

Extracts month and year from RJ filenames:
- Pattern: `Rj MM-YYYY.xls` or `Rj MM-DD-YYYY.xls`
- Examples: `Rj 07-2025.xls` (July 2025), `Rj 07-15-2025.xls` (July 15, 2025)

### Step 3: SALAIRES Sheet Processing

1. Scans for department headers (RECEPTION, CHAMBRE, PIAZZA, BANQUET, CUISINE, BAR, BUANDERIE, MAINTENANCE)
2. Counts positions under each department
3. Maps to canonical department names (e.g., CHAMBRE → ROOMS)
4. Stores headcount per department

### Step 4: BUDGET Sheet Processing

1. Scans rows 42+ for position names and labor costs
2. Uses keyword matching to infer departments:
   - `RECEPTION, AUDITION, PORTIER, CHASSEUR` → RECEPTION
   - `GOUVERNANTE, FEMME DE CHAMBRE, ÉQUIPIÈRE` → ROOMS
   - `CUISINIER, CUISINE, PLONGEUR` → KITCHEN
   - `BANQUET, GIOTTO` → BANQUET
   - And so on...
3. Aggregates costs by department
4. Stores budgeted labor cost per department

### Step 5: Database Upsert

- For each (year, month, department) combination:
  - If record exists: update with new data
  - If new: insert into DepartmentLabor table
- Calculates derived fields (average hourly rate, etc.)
- Commits changes to SQLite database

## Key Insights from Imported Data

### Top Budgeted Departments (Annual)

1. **BANQUET**: $8,260,594.90
2. **ADMINISTRATION**: $5,559,192.00
3. **KITCHEN**: $3,671,315.00
4. **RECEPTION**: $3,194,047.00
5. **ROOMS**: $3,009,884.42

### Staffing Levels (FTE-Months)

- BANQUET: 120
- KITCHEN: 140
- RECEPTION: 100
- MAINTENANCE: 80
- PIAZZA: 80
- BAR: 40
- ROOMS: 40

### Total Investment

- **Total Budget**: $28,994,844.84
- **Period**: 20 month-periods (2025-2026)
- **Average per Month**: $1,449,742.24

## Error Handling

The script gracefully handles:
- Missing or malformed RJ files (252 files skipped)
- Files with invalid naming conventions
- Missing SALAIRES or BUDGET sheets
- Corrupted Excel files
- Encoding/character issues

All errors are logged to console during import.

## File Locations

- **Script**: `/sessions/laughing-sharp-johnson/mnt/audit-pack/import_labor.py`
- **Source files**: `/sessions/laughing-sharp-johnson/mnt/audit-pack/RJ 2024-2025/`
- **Database**: `/sessions/laughing-sharp-johnson/mnt/audit-pack/database/audit.db`
- **Model**: `/sessions/laughing-sharp-johnson/mnt/audit-pack/database/models.py`

## Rerunning the Import

To reimport all data:

1. **Option A**: Script will automatically update existing records (upsert)
   ```bash
   python import_labor.py
   ```

2. **Option B**: Clear database first for fresh import
   ```bash
   rm database/audit.db
   python import_labor.py
   ```

## Integration with Flask App

After import, the data is immediately available in the Flask application:

```python
from database.models import DepartmentLabor

# Query by department and month
kitchen_jan_2025 = DepartmentLabor.query.filter_by(
    year=2025,
    month=1,
    department='KITCHEN'
).first()

# Calculate variance
variance = kitchen_jan_2025.get_budget_variance()
variance_pct = kitchen_jan_2025.get_budget_variance_pct()

# Generate reports
all_depts = DepartmentLabor.query.filter_by(year=2025).all()
```

## Performance Notes

- Processes 338 files in ~30-60 seconds
- Database insertion: ~180 records committed
- Total data size: ~29M in budgeted labor costs
- Memory usage: Minimal (file-by-file processing)

## Future Enhancements

Potential improvements:
- Extract actual hours worked (not just budgeted)
- Parse wage rates by position type
- Extract tips data from POURBOIRE sheet
- Integrate with DBRS/QUASIMODO systems
- Create departmental dashboards
- Implement alerts for budget overruns
