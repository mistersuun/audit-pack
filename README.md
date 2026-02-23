# RJ ETL Pipeline - Hotel Financial Data Extraction

A production-ready Python ETL pipeline for extracting, transforming, and loading hotel financial data from RJ Excel files into PostgreSQL.

## Overview

This pipeline processes daily hotel financial reports from RJ (.xls) files organized in a hierarchical folder structure and loads all data into a PostgreSQL database with comprehensive tables for analysis and auditing.

## Features

- **Multi-Sheet Processing**: Extracts data from 20 critical Excel sheets
- **Hierarchical Folder Support**: Processes `YEAR/MONTH/filename.xls` structure
- **Flexible Naming**: Handles multiple RJ filename formats
- **Batch & Single-File Modes**: Process entire 5-year archives or individual daily files
- **Comprehensive Logging**: Detailed logging with file and console output
- **Error Handling**: Robust error handling with transaction rollback
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **PostgreSQL Native**: Uses psycopg2 for direct database integration
- **Type-Safe**: Proper data type conversion and validation

## Requirements

### System Requirements
- Python 3.8+
- PostgreSQL 12+
- 50+ MB free disk space for logs and cache
- Network access to PostgreSQL database

### Python Dependencies
See `etl_requirements.txt` for complete list:
- `xlrd==2.0.1` - Excel file reading
- `psycopg2-binary==2.9.9` - PostgreSQL adapter
- `numpy==1.24.3` - Numerical operations
- `tqdm==4.65.0` - Progress bars (optional)

## Installation

### 1. Clone/Download Files
```bash
git clone <repository-url>
cd rj_etl_pipeline
```

### 2. Install Python Dependencies
```bash
pip install -r etl_requirements.txt
```

### 3. Set Up PostgreSQL Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Run the schema creation script
\i database_schema.sql

# Or from command line:
psql -U postgres -d postgres -f database_schema.sql
```

### 4. Configure Database Connection
Edit `db_config.json`:
```json
{
  "host": "your-db-host",
  "port": 5432,
  "database": "rj_hotel",
  "user": "your_username",
  "password": "your_password",
  "schema": "rj_data"
}
```

**Environment Variable Alternative:**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=rj_hotel
export DB_USER=postgres
export DB_PASSWORD=your_password
```

## Usage

### Single File Processing
Process a single RJ file:
```bash
python rj_etl_pipeline.py --mode single --file "/path/to/Rj_01-15-2024.xls"
```

### Batch Processing (5-Year Archive)
Process entire folder hierarchy:
```bash
python rj_etl_pipeline.py --mode batch --folder "/path/to/data/root"
```

Folder structure expected:
```
data/
├── 2019/
│   ├── 01/
│   │   ├── Rj_01-01-2019.xls
│   │   ├── Rj_01-02-2019.xls
│   │   └── ...
│   ├── 02/
│   └── ...
├── 2020/
└── ...
```

### Custom Configuration File
```bash
python rj_etl_pipeline.py --mode batch --folder "/data" --config "/path/to/custom_config.json"
```

### Output
```
2024-01-15 10:30:45,123 - root - INFO - Database connection established
2024-01-15 10:30:46,234 - root - INFO - Opened workbook: Rj_01-15-2024.xls
2024-01-15 10:30:47,345 - root - INFO - Parsed jour sheet with 123 columns
2024-01-15 10:30:48,456 - root - INFO - Inserted journal data for 2024-01-15
2024-01-15 10:30:49,567 - root - INFO - Successfully processed Rj_01-15-2024.xls
```

## Data Mapping

### JOUR Sheet (117 Columns)
Columns A-DK map to the following key fields:

#### Revenue Centers
- **Link Restaurant**: Columns E-I (Nouveau, Boisé, Bien, Mini, Vin varieties)
- **Piazza**: Columns J-N (Same varieties)
- **Marché**: Columns O-S
- **Service Chambres**: Columns T-X
- **Banquet**: Columns Y-AC

#### Ancillary Revenue
- **Tips/Pourboires**: AD (29)
- **Equipment/Équipement**: AE (30)
- **Miscellaneous/Divers**: AF (31)
- **Room Rentals/Location Salles**: AG (32)
- **Rooms Revenue/Chambres**: AK (36)
- **Telecommunications**: AL-AN (37-39)
- **Laundry Services**: AO (40)
- **Merchandise & Liquor**: AP (41)

#### Payment Methods (Columns BI-BN)
- Amex Elavon
- Discover
- MasterCard
- Visa
- Debit Cards
- Amex Global

#### Room Inventory (Columns CK-CR)
- Simple Rooms
- Double Rooms
- Suite Rooms
- Complementary Rooms
- Guest Count
- Out of Service
- Need Cleaning
- Available Rooms

#### Beverage Breakdown (Columns DG-DM)
- Food Total
- Alcohol Total
- Beer Total
- Mineral Water Total
- Wine Total
- Total Beverages

### CONTROLE Sheet
Key cells:
- B2: Day Number (vjour)
- B3: Month (Mois)
- B4: Year (Année)
- B5: Temperature
- B9: YTD Sales (Vente dollar an a date)
- B10: LY YTD Sales (Vente dollar An dernier)
- B11: YTD Available Rooms (Ch. disponible an a date)
- B13: YTD Occupied Rooms (Ch. Occupées an a date)

### Other Sheets
All other sheets (rj, AD, salaires, Recap, DUBACK#, depot, Diff.Caisse#, transelect, geac_ux, SetD, diff_forfait, Rapp_p1/p2/p3, Etat rev, Budget, EJ, Nettoyeur, somm_nettoyeur) are stored as raw JSON in corresponding tables for flexibility and future analysis.

## Database Schema

### Main Tables

#### daily_journal
Primary table for daily financial data with 120+ columns covering:
- Revenue by department and category
- Payment methods
- Room inventory
- Beverage breakdown
- Adjustments and transfers

#### daily_control
Control metrics and validation data:
- Day/Month/Year identifiers
- Temperature tracking
- Year-to-date metrics (sales, rooms)

#### Supporting Tables
- `daily_summary` - RJ sheet data
- `fb_department` - Food & Beverage (AD sheet)
- `payroll` - Labor data (salaires sheet)
- `cash_recap` - Cash reconciliation
- `dueback` - Due back tracking
- `deposits` - Deposit information
- `cash_variance` - Cash differences
- `credit_card_terminals` - Terminal transactions
- `cc_reconciliation` - Card reconciliation
- `settlements` - Settlement data
- `packages` - Forfait differences
- `management_reports` - Rapp_p1/p2/p3 sheets
- `revenue_status` - Revenue reporting
- `budget` - Budget tracking
- `gl_journal` - General ledger entries
- `laundry` - Laundry operations
- `laundry_summary` - Laundry summary

#### Metadata Tables
- `etl_log` - Processing history and status
- `data_quality_report` - Quality check results

### Views

#### daily_financial_summary
Consolidated view with calculated totals:
- Revenue by department
- Total card payments
- Room occupancy
- YTD metrics

#### ytd_summary
Month-level aggregation:
- Total revenue by category
- Average occupancy
- Average temperature

## File Naming Conventions

The pipeline automatically detects and parses RJ filenames in multiple formats:

```
Rj MM-DD-YYYY.xls           # American format
Rj DD-MM-YYYY.xls           # European format
Rj MM-DD-YYYY-Copie.xls     # Copy with timestamp
```

Examples:
- `Rj 01-15-2024.xls` → January 15, 2024
- `Rj 15-01-2024.xls` → January 15, 2024
- `Rj 01-15-2024-Copie.xls` → January 15, 2024 (backup copy)

## Error Handling

### Connection Errors
- Database connection failures logged with full error details
- Application exits with code 1 on connection failure

### File Processing Errors
- Missing sheets logged as warnings (non-fatal)
- Invalid cell values safely converted to NULL
- Malformed rows skipped with detailed logging

### Data Type Errors
- Automatic safe conversion with fallback to NULL
- Type mismatches logged at DEBUG level

### Transaction Errors
- Automatic rollback on INSERT/UPDATE errors
- Error message logged with transaction details

## Logging

### Log Levels
- **INFO**: File processing, data insertion, summary statistics
- **DEBUG**: Cell-level data reading, type conversions
- **WARNING**: Missing sheets, unparseable data
- **ERROR**: Database errors, file access errors, fatal issues

### Log Output
Logs are written to both:
1. Console (real-time monitoring)
2. `rj_etl_pipeline.log` (persistent record)

### Example Log Entries
```
2024-01-15 10:30:45,123 - __main__ - INFO - Database connection established successfully
2024-01-15 10:30:46,234 - __main__ - INFO - Opened workbook: /data/2024/01/Rj_01-15-2024.xls, Date: 2024-01-15
2024-01-15 10:30:47,345 - __main__ - INFO - Extracted 2 rows from sheet 'jour'
2024-01-15 10:30:48,456 - __main__ - INFO - Inserted journal data for 2024-01-15
2024-01-15 10:30:49,567 - __main__ - INFO - Successfully processed /data/2024/01/Rj_01-15-2024.xls
```

## Performance Considerations

### Single File Processing
- Average time: 2-5 seconds per file
- Network latency: Database connection latency is primary factor
- File size: Most RJ files are 100-500 KB

### Batch Processing (5-Year Archive)
- ~1,825 files (365 × 5 years)
- Estimated time: 2-3 hours total
- Recommendation: Run during off-peak hours

### Database Performance
- Indexes created on all date and frequently-queried columns
- Conflict detection using UNIQUE constraints
- Transaction-based processing for data integrity

### Memory Usage
- xlrd loads entire workbook into memory (~5 MB per file)
- Suitable for standard server configurations (8 GB+ RAM)

## Troubleshooting

### Database Connection Failed
```
Error: connection failed: could not connect to server
```
**Solutions:**
- Check PostgreSQL is running: `psql -U postgres -c "SELECT 1"`
- Verify credentials in db_config.json
- Check network connectivity to database server
- Verify database exists: `psql -l`

### Sheet Not Found
```
Warning: Sheet 'jour' not found in workbook
```
**Solutions:**
- Verify Excel file is valid RJ format
- Check sheet names match exactly (case-sensitive)
- Open file in Excel to verify sheet structure

### Date Parsing Failed
```
Warning: Could not parse date from filename Rj_20240115.xls
```
**Solutions:**
- Use supported date formats: MM-DD-YYYY, DD-MM-YYYY
- Ensure filename follows "Rj PREFIX-DATE.xls" pattern
- Use consistent date formatting across all files

### Memory Error
```
MemoryError: unable to allocate memory
```
**Solutions:**
- Process files in smaller batches
- Increase available system RAM
- Check for other memory-intensive processes

### Permission Denied
```
Error: Permission denied opening file or writing to log
```
**Solutions:**
- Check file/folder permissions: `chmod 755 folder/`
- Run with appropriate user privileges
- Verify write access to current directory

## Maintenance

### Updating Data
Updates are handled automatically via ON CONFLICT clauses:
```sql
ON CONFLICT (transaction_date) DO UPDATE SET
  column = EXCLUDED.column
```

To force replace all data for a date range:
```sql
DELETE FROM daily_journal
WHERE transaction_date BETWEEN '2024-01-01' AND '2024-01-31';
```

### Archiving Old Data
```sql
-- Create archive table
CREATE TABLE daily_journal_archive AS
SELECT * FROM daily_journal
WHERE transaction_date < '2020-01-01';

-- Delete from main table
DELETE FROM daily_journal
WHERE transaction_date < '2020-01-01';
```

### Backup & Recovery
```bash
# Backup database
pg_dump -U postgres rj_hotel > rj_hotel_backup.sql

# Restore from backup
psql -U postgres -d rj_hotel < rj_hotel_backup.sql
```

## Development & Testing

### Running Tests
```bash
pytest -v
```

### Code Quality
```bash
pylint rj_etl_pipeline.py
black rj_etl_pipeline.py
flake8 rj_etl_pipeline.py
```

### Test Data Generation
```python
# Generate sample RJ file for testing
import xlwt
wb = xlwt.Workbook()
ws = wb.add_sheet('jour')
# Add test data...
wb.save('test_Rj_01-15-2024.xls')
```

## Security Considerations

### Database Credentials
- Never commit `db_config.json` with real credentials
- Use environment variables in production
- Implement database user permissions:
  ```sql
  CREATE USER rj_etl_user WITH PASSWORD 'secure_password';
  GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA rj_data TO rj_etl_user;
  GRANT USAGE ON SCHEMA rj_data TO rj_etl_user;
  ```

### File Access
- Restrict RJ file folders to authorized users only
- Use encrypted file transfers
- Audit file access logs

### Log Files
- Store logs in secure location
- Implement log rotation to prevent disk space issues
- Don't log sensitive data (passwords, PII)

## Support & Documentation

### Getting Help
1. Check logs: `tail -f rj_etl_pipeline.log`
2. Review error messages for specific guidance
3. Check database state: Query `etl_log` table
4. Review data quality reports in `data_quality_report` table

### Extended Documentation
- Database schema comments: `\d+ table_name` in psql
- View definitions: `\d+ view_name` in psql
- Full DDL export: `pg_dump -s rj_hotel > schema.sql`

## Version History

### v1.0 (Initial Release)
- Core ETL pipeline implementation
- Support for 20 critical sheets
- Batch and single-file processing modes
- Comprehensive logging and error handling
- PostgreSQL integration

## License

[Specify your license here]

## Contributors

ETL Team

## Changelog

### [1.0] - 2024-01-15
- Initial production release
- All critical sheets supported
- Cross-platform compatibility verified
- Comprehensive documentation included
