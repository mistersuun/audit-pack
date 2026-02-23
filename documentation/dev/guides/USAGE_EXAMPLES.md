# RJ ETL Pipeline - Usage Examples

Complete examples and recipes for using the RJ ETL Pipeline

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Batch Processing](#batch-processing)
3. [Data Validation](#data-validation)
4. [SQL Queries](#sql-queries)
5. [Automation & Scheduling](#automation--scheduling)
6. [Troubleshooting Scenarios](#troubleshooting-scenarios)

---

## Basic Usage

### Process a Single File

```bash
# Simple single file processing
python rj_etl_pipeline.py --mode single --file "Rj_01-15-2024.xls"
```

Expected output:
```
2024-01-15 10:30:45,123 - __main__ - INFO - Database connection established successfully
2024-01-15 10:30:46,234 - __main__ - INFO - Opened workbook: Rj_01-15-2024.xls, Date: 2024-01-15
2024-01-15 10:30:47,345 - __main__ - INFO - Extracted 2 rows from sheet 'jour'
2024-01-15 10:30:47,456 - __main__ - INFO - Extracted 2 rows from sheet 'controle'
2024-01-15 10:30:48,456 - __main__ - INFO - Inserted journal data for 2024-01-15
2024-01-15 10:30:49,567 - __main__ - INFO - Inserted control data for 2024-01-15
2024-01-15 10:30:50,678 - __main__ - INFO - Successfully processed Rj_01-15-2024.xls
```

### Using Custom Configuration

```bash
# Use custom database configuration
python rj_etl_pipeline.py \
  --mode single \
  --file "data/Rj_01-15-2024.xls" \
  --config "config/production.json"
```

### Processing with Error Handling

```bash
# Check exit code
python rj_etl_pipeline.py --mode single --file "Rj_01-15-2024.xls"
if [ $? -eq 0 ]; then
    echo "Processing successful"
else
    echo "Processing failed"
fi
```

---

## Batch Processing

### Process Entire Archive (5 Years)

```bash
# Batch mode processes all files in YEAR/MONTH structure
python rj_etl_pipeline.py --mode batch --folder "/data/rj_archive"
```

Folder structure expected:
```
/data/rj_archive/
├── 2019/
│   ├── 01/
│   │   ├── Rj_01-01-2019.xls
│   │   ├── Rj_01-02-2019.xls
│   │   └── ... (365 files)
│   ├── 02/
│   │   └── ... (28-29 files)
│   └── ... (12 months)
├── 2020/
│   └── ... (similar structure)
└── ... (through 2024)
```

Processing will take approximately 2-3 hours.

### Batch Processing with Progress Monitoring

```bash
# Terminal 1: Start processing
python rj_etl_pipeline.py --mode batch --folder "/data/rj_archive" &

# Terminal 2: Monitor progress in real-time
tail -f rj_etl_pipeline.log | grep "Successfully processed"
```

### Incremental Batch Processing (Resume)

```bash
# Process files for specific year
python rj_etl_pipeline.py --mode batch --folder "/data/rj_archive/2024"

# The pipeline automatically detects previously loaded dates
# and updates existing records (ON CONFLICT clause)
```

### Batch Process with Shell Script

```bash
# Make script executable
chmod +x process_batch.sh

# Run with default settings
./process_batch.sh

# Run with custom folder
./process_batch.sh --folder /data/rj_files

# Dry run to preview what would be processed
./process_batch.sh --dry-run --folder /data/rj_files

# Verbose mode with specific config
./process_batch.sh --folder /data/rj_files --config db_config.json --verbose
```

---

## Data Validation

### Run Full Data Validation

```bash
python validate_data.py --config db_config.json
```

Output example:
```
============================================================
DATA VALIDATION REPORT
============================================================

1. Table Existence Checks
------------------------------------------------------------
  daily_journal: ✓ PASS
  daily_control: ✓ PASS

2. Record Count Checks
------------------------------------------------------------
  daily_journal: ✓ PASS (1825 records)
  daily_control: ✓ PASS (1825 records)

3. Date Range Checks
------------------------------------------------------------
  daily_journal: 2019-01-01 to 2024-12-31 (2190 days)
  daily_control: 2019-01-01 to 2024-12-31 (2190 days)

4. NULL Value Checks (Critical Columns)
------------------------------------------------------------
  daily_journal.transaction_date: ✓ PASS (0 NULLs)
  daily_journal.jour: ✓ PASS (0 NULLs)
  daily_control.transaction_date: ✓ PASS (0 NULLs)

5. Negative Value Checks (Should be >= 0)
------------------------------------------------------------
  daily_journal.opening_balance: ✓ PASS
  daily_journal.room_revenue: ✓ PASS
  daily_control.sales_ytd: ✓ PASS

6. Data Completeness Checks
------------------------------------------------------------
  Unique day numbers: 31
    ✓ PASS (Good variety of days)

============================================================
VALIDATION SUMMARY
============================================================
Checks Passed: 12
Checks Failed: 0
Warnings: 0
============================================================
✓ All validation checks PASSED
```

### Validate After Each Batch Import

```bash
# Chain validation to batch processing
python rj_etl_pipeline.py --mode batch --folder "/data" && \
    python validate_data.py --config db_config.json
```

---

## SQL Queries

### Connect to Database

```bash
# Connect with psql
psql -U postgres -d rj_hotel -h localhost

# Or with password
PGPASSWORD='yourpassword' psql -U postgres -d rj_hotel -h localhost
```

### Daily Revenue Summary

```sql
-- Get daily revenue by source for a specific month
SELECT
  transaction_date,
  jour,
  room_revenue,
  food_total,
  beverage_total,
  (room_revenue + COALESCE(food_total, 0) + COALESCE(beverage_total, 0)) as total_revenue,
  guest_count,
  simple_rooms + double_rooms + suite_rooms as occupied_rooms
FROM rj_data.daily_journal
WHERE transaction_date >= '2024-01-01'
  AND transaction_date < '2024-02-01'
ORDER BY transaction_date;
```

### Monthly Financial Summary

```sql
-- Monthly aggregation with YoY comparison
SELECT
  EXTRACT(YEAR FROM j.transaction_date) as year,
  EXTRACT(MONTH FROM j.transaction_date) as month,
  COUNT(*) as operating_days,
  SUM(j.room_revenue) as total_room_revenue,
  SUM(j.food_total) as total_food_sales,
  SUM(j.beverage_total) as total_beverage_sales,
  (SUM(j.room_revenue) + SUM(j.food_total) + SUM(j.beverage_total)) as total_revenue,
  AVG(j.guest_count) as avg_daily_guests,
  AVG(j.simple_rooms + j.double_rooms + j.suite_rooms) as avg_occupied_rooms,
  SUM(j.amex_elavon + j.discover + j.mastercard + j.visa) as total_card_payments
FROM rj_data.daily_journal j
GROUP BY year, month
ORDER BY year DESC, month DESC;
```

### Year-to-Date Performance Tracking

```sql
-- YTD metrics compared to last year
SELECT
  EXTRACT(MONTH FROM transaction_date) as month,
  EXTRACT(YEAR FROM transaction_date) as year,
  SUM(room_revenue) as ytd_room_revenue,
  SUM(food_total) as ytd_food_sales,
  AVG(guest_count) as avg_guests,
  COUNT(*) as days_in_period
FROM rj_data.daily_journal
WHERE EXTRACT(YEAR FROM transaction_date) IN (2023, 2024)
GROUP BY year, month
ORDER BY year DESC, month;
```

### Payment Method Analysis

```sql
-- Payment method trends over time
SELECT
  DATE_TRUNC('month', transaction_date) as month,
  SUM(amex_elavon) as amex_elavon,
  SUM(discover) as discover_payments,
  SUM(mastercard) as mastercard_payments,
  SUM(visa) as visa_payments,
  SUM(debit_card) as debit_card_payments,
  (SUM(amex_elavon) + SUM(discover) + SUM(mastercard) +
   SUM(visa) + SUM(debit_card)) as total_card_payments,
  ROUND(
    100 * (SUM(amex_elavon) + SUM(discover) + SUM(mastercard) +
            SUM(visa) + SUM(debit_card)) /
    NULLIF(SUM(room_revenue) + SUM(food_total) + SUM(beverage_total), 0),
    2
  ) as card_payment_percent
FROM rj_data.daily_journal
GROUP BY month
ORDER BY month DESC;
```

### Room Occupancy & Performance

```sql
-- Room occupancy and revenue per room metrics
SELECT
  transaction_date,
  jour,
  simple_rooms,
  double_rooms,
  suite_rooms,
  comp_rooms,
  (simple_rooms + double_rooms + suite_rooms + comp_rooms) as total_occupied,
  guest_count,
  ROUND(guest_count::NUMERIC /
    NULLIF(simple_rooms + double_rooms + suite_rooms, 0), 2) as guests_per_room,
  room_revenue,
  ROUND(room_revenue /
    NULLIF(simple_rooms + double_rooms + suite_rooms, 0), 2) as revenue_per_occupied_room
FROM rj_data.daily_journal
WHERE transaction_date >= '2024-01-01'
ORDER BY transaction_date DESC
LIMIT 31;
```

### Cash Variance Investigation

```sql
-- Find days with significant cash discrepancies
SELECT
  transaction_date,
  jour,
  opening_balance,
  cash_variance,
  ABS(cash_variance) as abs_variance,
  ROUND(100 * ABS(cash_variance) /
    NULLIF(ABS(opening_balance), 0), 2) as variance_percent
FROM rj_data.daily_journal
WHERE ABS(cash_variance) > 50
  OR (ABS(cash_variance) / NULLIF(ABS(opening_balance), 0)) > 0.01
ORDER BY abs_variance DESC;
```

### Beverage Category Breakdown

```sql
-- Beverage sales by category
SELECT
  DATE_TRUNC('month', transaction_date) as month,
  SUM(food_total) as food_sales,
  SUM(alcohol_total) as alcohol_sales,
  SUM(beer_total) as beer_sales,
  SUM(wine_total) as wine_sales,
  SUM(mineral_total) as mineral_water_sales,
  SUM(beverage_total) as total_beverages,
  ROUND(100 * SUM(alcohol_total) / NULLIF(SUM(beverage_total), 0), 2) as alcohol_percent,
  ROUND(100 * SUM(beer_total) / NULLIF(SUM(beverage_total), 0), 2) as beer_percent,
  ROUND(100 * SUM(wine_total) / NULLIF(SUM(beverage_total), 0), 2) as wine_percent
FROM rj_data.daily_journal
GROUP BY month
ORDER BY month DESC;
```

### Restaurant Department Performance

```sql
-- Performance by restaurant department
SELECT
  DATE_TRUNC('month', transaction_date) as month,
  SUM(link_restaurant_new + link_restaurant_boi + link_restaurant_bien +
      link_restaurant_mini + link_restaurant_vin) as link_restaurant_total,
  SUM(piazza_new + piazza_boi + piazza_bien + piazza_mini + piazza_vin) as piazza_total,
  SUM(marche_new + marche_boi + marche_bien + marche_mini + marche_vin) as marche_total,
  SUM(banquet_new + banquet_boi + banquet_bien + banquet_mini + banquet_vin) as banquet_total,
  (SUM(link_restaurant_new + link_restaurant_boi + link_restaurant_bien +
       link_restaurant_mini + link_restaurant_vin) +
   SUM(piazza_new + piazza_boi + piazza_bien + piazza_mini + piazza_vin) +
   SUM(marche_new + marche_boi + marche_bien + marche_mini + marche_vin) +
   SUM(banquet_new + banquet_boi + banquet_bien + banquet_mini + banquet_vin)) as total_fb_revenue
FROM rj_data.daily_journal
GROUP BY month
ORDER BY month DESC;
```

### ETL Processing History

```sql
-- Check processing history and any errors
SELECT
  file_name,
  transaction_date,
  status,
  error_message,
  rows_processed,
  processing_time_ms,
  processed_at
FROM rj_data.etl_log
ORDER BY processed_at DESC
LIMIT 20;

-- Summary of processing results
SELECT
  status,
  COUNT(*) as file_count,
  AVG(processing_time_ms) as avg_processing_time_ms,
  MIN(processing_time_ms) as min_time_ms,
  MAX(processing_time_ms) as max_time_ms
FROM rj_data.etl_log
GROUP BY status;
```

### Missing Data Detection

```sql
-- Find dates with missing data
SELECT
  DATE_SERIES.date,
  CASE WHEN dj.transaction_date IS NOT NULL THEN 'Present'
       ELSE 'Missing' END as data_status
FROM GENERATE_SERIES(
  (SELECT MIN(transaction_date) FROM rj_data.daily_journal),
  (SELECT MAX(transaction_date) FROM rj_data.daily_journal),
  INTERVAL '1 day'
) as DATE_SERIES(date)
LEFT JOIN rj_data.daily_journal dj ON DATE_SERIES.date = dj.transaction_date
WHERE dj.transaction_date IS NULL
ORDER BY DATE_SERIES.date;
```

### Create Monthly Report View

```sql
-- Create a reusable view for monthly reporting
CREATE OR REPLACE VIEW rj_data.monthly_performance AS
SELECT
  EXTRACT(YEAR FROM j.transaction_date) as year,
  EXTRACT(MONTH FROM j.transaction_date) as month,
  TO_CHAR(j.transaction_date, 'YYYY-MM') as year_month,
  COUNT(DISTINCT j.transaction_date) as operating_days,
  SUM(j.room_revenue) as room_revenue,
  SUM(j.food_total) as food_revenue,
  SUM(j.beverage_total) as beverage_revenue,
  (SUM(j.room_revenue) + SUM(j.food_total) + SUM(j.beverage_total)) as total_revenue,
  SUM(j.amex_elavon + j.discover + j.mastercard + j.visa + j.debit_card + j.amex_global) as card_payments,
  AVG(j.guest_count) as avg_guests,
  AVG(j.simple_rooms + j.double_rooms + j.suite_rooms) as avg_occupied_rooms,
  AVG(CAST(c.temperature AS NUMERIC)) as avg_temperature,
  MAX(c.sales_ytd) as ytd_sales,
  MAX(c.occupied_rooms_ytd) as ytd_rooms
FROM rj_data.daily_journal j
LEFT JOIN rj_data.daily_control c ON j.transaction_date = c.transaction_date
GROUP BY year, month
ORDER BY year DESC, month DESC;

-- Query the view
SELECT * FROM rj_data.monthly_performance
WHERE year_month >= '2024-01'
ORDER BY year_month DESC;
```

---

## Automation & Scheduling

### Linux/macOS Cron Job

```bash
# Edit crontab
crontab -e

# Run ETL daily at 3 AM
0 3 * * * cd /home/user/rj_etl && python3 rj_etl_pipeline.py --mode batch --folder /data/rj_files >> /var/log/rj_etl.log 2>&1

# Run validation daily at 3:30 AM
30 3 * * * cd /home/user/rj_etl && python3 validate_data.py >> /var/log/rj_etl_validation.log 2>&1

# View scheduled jobs
crontab -l
```

### Windows Task Scheduler

Create a batch file `run_etl.bat`:
```batch
@echo off
cd C:\RJ_ETL_Pipeline
python rj_etl_pipeline.py --mode batch --folder C:\Data\RJ_Files --config db_config.json
if %ERRORLEVEL% EQU 0 (
    python validate_data.py --config db_config.json
) else (
    echo ETL Processing Failed >> C:\Logs\rj_etl_errors.log
)
```

Then schedule via Task Scheduler:
- Trigger: Daily at 3:00 AM
- Action: Start program `run_etl.bat`
- Advanced: Log outputs to file

### Python Scheduling (APScheduler)

```python
#!/usr/bin/env python3
"""RJ ETL Scheduler - Use APScheduler for flexible scheduling"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_batch_etl():
    """Run batch ETL process"""
    logger.info("Starting batch ETL...")
    result = subprocess.run([
        'python', 'rj_etl_pipeline.py',
        '--mode', 'batch',
        '--folder', '/data/rj_files',
        '--config', 'db_config.json'
    ])
    return result.returncode == 0

def run_validation():
    """Run data validation"""
    logger.info("Starting data validation...")
    result = subprocess.run([
        'python', 'validate_data.py',
        '--config', 'db_config.json'
    ])
    return result.returncode == 0

def main():
    scheduler = BackgroundScheduler()

    # Schedule batch ETL daily at 3 AM
    scheduler.add_job(
        run_batch_etl,
        trigger=CronTrigger(hour=3, minute=0),
        id='batch_etl_job',
        name='Daily Batch ETL'
    )

    # Schedule validation daily at 3:30 AM
    scheduler.add_job(
        run_validation,
        trigger=CronTrigger(hour=3, minute=30),
        id='validation_job',
        name='Daily Data Validation'
    )

    scheduler.start()

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()

if __name__ == '__main__':
    main()
```

### Docker Scheduling

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY etl_requirements.txt .
RUN pip install -r etl_requirements.txt

COPY . .

# Run ETL at specific time
CMD ["python", "rj_etl_pipeline.py", "--mode", "batch", "--folder", "/data"]
```

Docker compose:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rj_hotel
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  etl:
    build: .
    depends_on:
      - postgres
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: rj_hotel
      DB_USER: postgres
      DB_PASSWORD: your_password
    volumes:
      - /data/rj_files:/data:ro
    command: python rj_etl_pipeline.py --mode batch --folder /data
```

---

## Troubleshooting Scenarios

### Scenario 1: Database Connection Failed

**Problem:** Can't connect to PostgreSQL

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# If error: "could not connect to server"
# Solution 1: Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS
# Windows: Use Services panel

# Check database exists
psql -l | grep rj_hotel

# If not found, create it
createdb -U postgres rj_hotel
```

### Scenario 2: Out of Memory During Batch Processing

**Problem:** Python runs out of memory processing many files

```python
# Modify rj_etl_pipeline.py to process in smaller batches
# Add this to the process_batch method:

MAX_FILES_PER_BATCH = 50

for year_folder in sorted(root_path.iterdir()):
    for month_folder in sorted(year_folder.iterdir()):
        xls_files = sorted(month_folder.glob('*.xls'))

        # Process in batches
        for i in range(0, len(xls_files), MAX_FILES_PER_BATCH):
            batch = xls_files[i:i+MAX_FILES_PER_BATCH]
            for xls_file in batch:
                # process file
                pass
            # Force garbage collection between batches
            import gc
            gc.collect()
```

### Scenario 3: Duplicate Data Import

**Problem:** Data was imported twice causing duplicates

```sql
-- Check for duplicates
SELECT transaction_date, COUNT(*) as count
FROM rj_data.daily_journal
GROUP BY transaction_date
HAVING COUNT(*) > 1;

-- The pipeline handles this automatically via ON CONFLICT
-- But if needed, remove duplicates:
DELETE FROM rj_data.daily_journal a
WHERE a.id NOT IN (
    SELECT MAX(id)
    FROM rj_data.daily_journal b
    WHERE a.transaction_date = b.transaction_date
    GROUP BY transaction_date
);
```

### Scenario 4: Missing Sheets in File

**Problem:** Some files are missing 'jour' sheet

```bash
# The pipeline logs this as a warning
grep "Sheet 'jour' not found" rj_etl_pipeline.log

# Check which files are affected
grep -B1 "Sheet 'jour' not found" rj_etl_pipeline.log

# Verify file manually
python3 -c "
import xlrd
wb = xlrd.open_workbook('path/to/file.xls')
print('Sheets:', wb.sheet_names())
"
```

### Scenario 5: Date Parsing Issues

**Problem:** Filenames don't parse as dates

```bash
# Check log for parsing errors
grep "Could not parse date" rj_etl_pipeline.log

# Supported formats:
# Rj MM-DD-YYYY.xls (American)
# Rj DD-MM-YYYY.xls (European)
# Rj MM-DD-YYYY-Copie.xls

# Rename files if needed
mv "Rj_20240115.xls" "Rj_01-15-2024.xls"
```

### Scenario 6: Performance is Slow

**Problem:** Batch processing is taking too long

```bash
# Check if database is the bottleneck
time psql -U postgres -d rj_hotel -c "SELECT COUNT(*) FROM rj_data.daily_journal"

# Add indexes if missing (schema.sql includes them)
psql -U postgres -d rj_hotel -c "
CREATE INDEX IF NOT EXISTS idx_daily_journal_date ON rj_data.daily_journal(transaction_date);
"

# Check query plan
EXPLAIN SELECT COUNT(*) FROM rj_data.daily_journal;

# Consider using batch mode in PostgreSQL config
psql -d rj_hotel -c "ALTER SYSTEM SET work_mem = '256MB';"
sudo systemctl reload postgresql
```

---

## Advanced Recipes

### Export Data to CSV

```bash
psql -U postgres -d rj_hotel \
  -c "\COPY (
    SELECT * FROM rj_data.daily_journal
    WHERE transaction_date >= '2024-01-01'
  ) TO STDOUT WITH CSV HEADER" \
  > daily_journal_2024.csv
```

### Backup & Restore

```bash
# Backup
pg_dump -U postgres -d rj_hotel > rj_hotel_backup.sql

# Restore
psql -U postgres -d rj_hotel < rj_hotel_backup.sql
```

### Archive Old Data

```sql
-- Archive 2019-2022 data
CREATE TABLE rj_data.daily_journal_archive_2022 AS
SELECT * FROM rj_data.daily_journal
WHERE transaction_date < '2023-01-01';

-- Delete from main table
DELETE FROM rj_data.daily_journal
WHERE transaction_date < '2023-01-01';

-- Verify
SELECT MIN(transaction_date), MAX(transaction_date)
FROM rj_data.daily_journal;
```

---

This document provides practical examples for every use case of the RJ ETL Pipeline!
