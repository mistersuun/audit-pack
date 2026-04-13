# RJ ETL Pipeline - Quick Start Guide

Get up and running with the RJ ETL Pipeline in 10 minutes!

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- RJ Excel files in YEAR/MONTH folder structure

## Step-by-Step Setup

### 1. Install Dependencies (2 minutes)

```bash
# Navigate to the pipeline directory
cd /path/to/rj_etl_pipeline

# Install required packages
pip install -r etl_requirements.txt
```

### 2. Run Interactive Setup (3 minutes)

```bash
python setup.py
```

This will guide you through:
- Configuring database connection
- Testing the connection
- Creating the database and schema
- Verifying your data folder structure

Or manually configure:

```bash
# Edit the configuration file
nano db_config.json

# Update with your PostgreSQL credentials:
{
  "host": "localhost",
  "port": 5432,
  "database": "rj_hotel",
  "user": "postgres",
  "password": "your_password"
}
```

### 3. Create Database Schema (3 minutes)

```bash
# Using psql directly
psql -U postgres -d rj_hotel -f database_schema.sql

# Or setup.py will do this automatically
python setup.py  # Select option 3 or 5
```

## First Run - Single File

Test with a single RJ file first:

```bash
python rj_etl_pipeline.py --mode single --file "/path/to/Rj_01-15-2024.xls"
```

Expected output:
```
2024-01-15 10:30:45,123 - __main__ - INFO - Database connection established
2024-01-15 10:30:46,234 - __main__ - INFO - Opened workbook: Rj_01-15-2024.xls
2024-01-15 10:30:47,345 - __main__ - INFO - Parsed jour sheet with 123 columns
2024-01-15 10:30:48,456 - __main__ - INFO - Inserted journal data for 2024-01-15
2024-01-15 10:30:49,567 - __main__ - INFO - Successfully processed Rj_01-15-2024.xls
```

## Batch Processing - Full Archive

Process all files in a 5-year archive:

```bash
# Folder structure should be: /data/YEAR/MONTH/*.xls
python rj_etl_pipeline.py --mode batch --folder "/path/to/data/root"
```

This will process all .xls files in the YEAR/MONTH hierarchy.

Typical runtime for 5 years (~1,825 files):
- **2-3 hours** with local PostgreSQL
- **3-5 hours** with remote database

### Monitor Progress

In another terminal, watch the logs:
```bash
tail -f rj_etl_pipeline.log
```

## Verify Data Loaded

Connect to database and check:

```bash
# Connect to database
psql -U postgres -d rj_hotel

# Check record count
SELECT COUNT(*) FROM rj_data.daily_journal;

# Check date range
SELECT MIN(transaction_date), MAX(transaction_date)
FROM rj_data.daily_journal;

# View sample data
SELECT transaction_date, jour, opening_balance, room_revenue
FROM rj_data.daily_journal
LIMIT 10;

# View daily summary
SELECT * FROM rj_data.daily_financial_summary LIMIT 10;
```

## Query Examples

### Daily Revenue Summary
```sql
SELECT
  transaction_date,
  jour,
  room_revenue,
  food_total,
  beverage_total,
  (room_revenue + food_total + beverage_total) as total_revenue
FROM rj_data.daily_journal
WHERE transaction_date >= '2024-01-01'
ORDER BY transaction_date DESC;
```

### Monthly YTD Analysis
```sql
SELECT
  EXTRACT(YEAR FROM transaction_date) as year,
  EXTRACT(MONTH FROM transaction_date) as month,
  COUNT(*) as days_processed,
  SUM(room_revenue) as total_rooms,
  SUM(food_total) as total_food,
  SUM(beverage_total) as total_beverage,
  AVG(guest_count) as avg_guests
FROM rj_data.daily_journal
WHERE EXTRACT(YEAR FROM transaction_date) = 2024
GROUP BY year, month
ORDER BY month;
```

### Room Occupancy Trends
```sql
SELECT
  transaction_date,
  simple_rooms,
  double_rooms,
  suite_rooms,
  (simple_rooms + double_rooms + suite_rooms) as total_occupied,
  guest_count,
  ROUND(guest_count::NUMERIC / NULLIF(simple_rooms + double_rooms + suite_rooms, 0), 2) as avg_guests_per_room
FROM rj_data.daily_journal
WHERE transaction_date >= '2024-01-01'
ORDER BY transaction_date DESC;
```

### Payment Method Analysis
```sql
SELECT
  transaction_date,
  amex_elavon,
  discover,
  mastercard,
  visa,
  debit_card,
  amex_global,
  (amex_elavon + COALESCE(discover, 0) + COALESCE(mastercard, 0) +
   COALESCE(visa, 0) + COALESCE(debit_card, 0) + COALESCE(amex_global, 0)) as total_card_payments
FROM rj_data.daily_journal
WHERE transaction_date >= '2024-01-01'
ORDER BY transaction_date DESC;
```

### Cash Variance Investigation
```sql
SELECT
  transaction_date,
  opening_balance,
  cash_variance,
  (opening_balance + cash_variance) as expected_balance
FROM rj_data.daily_journal
WHERE ABS(cash_variance) > 100
ORDER BY transaction_date DESC;
```

## Troubleshooting

### "Connection refused" error
```bash
# Verify PostgreSQL is running
psql -U postgres -c "SELECT 1"

# If not running, start it:
# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# Windows: Use PostgreSQL installer or Services panel
```

### "Database does not exist"
```bash
# Create it manually:
createdb -U postgres rj_hotel

# Or re-run setup.py
python setup.py
```

### "Sheet 'jour' not found"
- Verify the Excel file is a valid RJ file
- Check sheet names in Excel file exactly match: jour, controle, etc.
- RJ files must be .xls format (not .xlsx)

### "Date parsing failed"
- File names must match format: `Rj MM-DD-YYYY.xls` or `Rj DD-MM-YYYY.xls`
- Example: `Rj 01-15-2024.xls`

### "Permission denied"
```bash
# Check folder permissions
ls -la rj_etl_pipeline.py

# Make executable if needed
chmod +x rj_etl_pipeline.py

# Ensure write access to current directory
chmod 755 .
```

## Next Steps

1. **Review the full documentation**: See `README.md` for comprehensive guide
2. **Automate processing**: Schedule batch jobs with cron or Task Scheduler
3. **Build reports**: Use the database views for BI tools (Tableau, Power BI, etc.)
4. **Monitor quality**: Check `rj_data.etl_log` table for processing status
5. **Archive old data**: Use database maintenance procedures

## Common Commands Cheat Sheet

```bash
# Single file
python rj_etl_pipeline.py --mode single --file "Rj_01-15-2024.xls"

# Batch processing
python rj_etl_pipeline.py --mode batch --folder "/data/archive"

# Custom config
python rj_etl_pipeline.py --mode batch --folder "/data" --config "config.json"

# Watch logs
tail -f rj_etl_pipeline.log

# Check PostgreSQL
psql -U postgres -l
psql -U postgres -d rj_hotel -c "SELECT COUNT(*) FROM rj_data.daily_journal"

# Interactive setup
python setup.py
```

## Performance Tips

- **First run on dedicated machine**: 5-year archive takes 2-3 hours
- **Use local PostgreSQL**: Remote database 2-3x slower
- **Run during off-peak**: Minimize impact on other systems
- **Monitor disk space**: Ensure sufficient space for logs and database
- **Validate sample data**: Check first 10 files manually before full run

## Support

- Check `rj_etl_pipeline.log` for detailed error messages
- Review `README.md` for comprehensive documentation
- Query `rj_data.etl_log` table for processing history
- Query `rj_data.data_quality_report` for data issues

## Sample Batch Script

Save as `process_archive.sh`:

```bash
#!/bin/bash
# RJ ETL Batch Processing Script

LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/batch_$(date +%Y%m%d_%H%M%S).log"

echo "Starting batch processing at $(date)" | tee "$LOG_FILE"

python rj_etl_pipeline.py \
  --mode batch \
  --folder "/data/rj_files" \
  --config "db_config.json" \
  2>&1 | tee -a "$LOG_FILE"

RESULT=$?
if [ $RESULT -eq 0 ]; then
  echo "✓ Processing completed successfully" | tee -a "$LOG_FILE"
else
  echo "✗ Processing failed with code $RESULT" | tee -a "$LOG_FILE"
fi

echo "Finished at $(date)" | tee -a "$LOG_FILE"
exit $RESULT
```

Make executable and run:
```bash
chmod +x process_archive.sh
./process_archive.sh
```

---

**Happy data processing! 🚀**

For detailed information, see the full `README.md` documentation.
