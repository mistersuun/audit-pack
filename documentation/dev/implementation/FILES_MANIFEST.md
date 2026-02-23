# RJ ETL Pipeline - Files Manifest

Complete list and description of all files in the RJ ETL Pipeline package

## Directory Structure

```
rj_etl_pipeline/
├── rj_etl_pipeline.py          # Main ETL pipeline application
├── setup.py                     # Interactive setup utility
├── validate_data.py             # Data validation and quality checks
├── process_batch.sh             # Bash script for batch processing
├── database_schema.sql          # PostgreSQL database schema
├── db_config.json               # Database configuration file
├── etl_requirements.txt          # Python dependencies
├── README.md                     # Comprehensive documentation
├── QUICKSTART.md                # Quick start guide (10 minutes)
├── INSTALLATION.md              # Detailed installation guide
├── USAGE_EXAMPLES.md            # Practical usage examples and SQL queries
├── FILES_MANIFEST.md            # This file
└── logs/                         # (Created automatically) Log files
```

---

## Core Application Files

### rj_etl_pipeline.py
**Purpose**: Main ETL pipeline application
**Size**: ~550 KB
**Lines of Code**: 1,100+
**Language**: Python 3.8+

**Key Components**:
- `ConfigManager`: Handles database configuration
- `RJFileParser`: Parses RJ Excel files with xlrd
- `DatabaseLoader`: Loads data into PostgreSQL
- `RJETLPipeline`: Orchestrates the entire pipeline

**Key Functions**:
- `process_single_file()`: Process one RJ file
- `process_batch()`: Process files in YEAR/MONTH hierarchy
- `parse_jour_sheet()`: Extract jour sheet with 123 columns
- `parse_controle_sheet()`: Extract control metrics
- `insert_daily_journal()`: Insert into daily_journal table
- `insert_daily_control()`: Insert into daily_control table
- `insert_generic_sheet_data()`: Insert other sheet data

**Usage**:
```bash
# Single file
python rj_etl_pipeline.py --mode single --file "path/to/file.xls"

# Batch mode
python rj_etl_pipeline.py --mode batch --folder "path/to/data"

# With custom config
python rj_etl_pipeline.py --mode batch --folder "/data" --config "custom_config.json"
```

**Exit Codes**:
- `0`: Success
- `1`: Failure (check logs for details)

---

### setup.py
**Purpose**: Interactive setup and configuration wizard
**Size**: ~20 KB
**Lines of Code**: 350+
**Language**: Python 3.8+

**Features**:
- Checks Python version and dependencies
- Tests PostgreSQL installation
- Interactive configuration creation
- Database and schema creation
- Data folder structure verification

**Usage**:
```bash
# Run interactive setup
python setup.py

# Menu options:
# 1. Configure database connection
# 2. Test database connection
# 3. Create database and schema
# 4. Verify data folder structure
# 5. Run all setup steps
```

---

### validate_data.py
**Purpose**: Data quality and consistency validation
**Size**: ~25 KB
**Lines of Code**: 400+
**Language**: Python 3.8+

**Validation Checks**:
1. Table existence checks
2. Record count verification
3. Date range validation
4. NULL value detection
5. Negative value checks
6. Data completeness analysis
7. ETL processing history review

**Usage**:
```bash
# Run full validation
python validate_data.py --config db_config.json

# Output includes:
# - Pass/fail status for each check
# - Record counts and date ranges
# - Summary statistics
# - Monthly breakdown
```

---

### process_batch.sh
**Purpose**: Bash script for batch processing with logging
**Size**: ~10 KB
**Lines of Code**: 280+
**Language**: Bash

**Features**:
- Prerequisite validation
- Dry-run mode for preview
- Colored console output
- Comprehensive logging
- File counting and scanning
- User confirmation before processing

**Usage**:
```bash
# Make executable
chmod +x process_batch.sh

# Run with defaults
./process_batch.sh

# With options
./process_batch.sh --folder /data --config db_config.json

# Dry run (preview only)
./process_batch.sh --dry-run --folder /data
```

**Requirements**:
- Bash shell (macOS, Linux)
- Python 3.8+
- psql command-line tool
- Readable data folder

---

## Configuration Files

### db_config.json
**Purpose**: Database connection configuration
**Size**: <1 KB
**Format**: JSON

**Content**:
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "rj_hotel",
  "user": "rj_etl_user",
  "password": "your_password",
  "schema": "rj_data"
}
```

**Settings**:
- `host`: PostgreSQL server hostname
- `port`: PostgreSQL port (default 5432)
- `database`: Database name
- `user`: Database user account
- `password`: User password
- `schema`: Schema name (default: rj_data)

**Alternatives**:
Can use environment variables instead:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

---

## Database Files

### database_schema.sql
**Purpose**: PostgreSQL database schema and table definitions
**Size**: ~80 KB
**Lines**: 600+
**Format**: SQL (PostgreSQL 12+)

**Tables Created** (21 total):
1. `daily_journal` - Daily financial data (120+ columns)
2. `daily_control` - Control metrics
3. `daily_summary` - RJ sheet summary
4. `fb_department` - Food & Beverage (AD sheet)
5. `payroll` - Labor data (salaires sheet)
6. `cash_recap` - Cash reconciliation
7. `dueback` - Due back tracking
8. `deposits` - Deposit information
9. `cash_variance` - Cash differences
10. `credit_card_terminals` - Terminal transactions
11. `cc_reconciliation` - Card reconciliation
12. `settlements` - Settlement data
13. `packages` - Forfait differences
14. `management_reports` - Rapp_p1/p2/p3 sheets
15. `revenue_status` - Revenue reporting
16. `budget` - Budget tracking
17. `gl_journal` - General ledger entries
18. `laundry` - Laundry operations
19. `laundry_summary` - Laundry summary
20. `etl_log` - Processing history
21. `data_quality_report` - Quality check results

**Views Created** (2):
1. `daily_financial_summary` - Consolidated daily view
2. `ytd_summary` - Year-to-date aggregation

**Indexes**: 20+ indexes on frequently-queried columns

**Usage**:
```bash
# Run schema setup
psql -U postgres -d rj_hotel -f database_schema.sql

# Or via setup.py
python setup.py  # Select option 3
```

**Execution Time**: ~5 seconds
**Data Size**: ~0 MB (schema only, no data)

---

## Documentation Files

### README.md
**Purpose**: Comprehensive project documentation
**Size**: ~30 KB
**Sections**:
- Overview and features
- Requirements and installation
- Usage instructions (single & batch)
- Data mapping and schema
- Error handling
- Logging configuration
- Performance considerations
- Troubleshooting guide
- Maintenance procedures
- Development & testing
- Security considerations
- Support & documentation

**Audience**: All users
**Read Time**: 30-45 minutes
**Critical Sections**: Installation, Usage, Troubleshooting

---

### QUICKSTART.md
**Purpose**: Get started in 10 minutes
**Size**: ~15 KB
**Sections**:
- Prerequisites checklist
- Step-by-step setup (7 steps)
- First run - single file
- Batch processing
- Data verification
- Query examples
- Common commands cheat sheet

**Audience**: New users
**Read Time**: 10-15 minutes
**Next Step**: Full README.md for detailed information

---

### INSTALLATION.md
**Purpose**: Complete installation guide for all platforms
**Size**: ~40 KB
**Sections**:
- System requirements
- Windows installation (step-by-step)
- macOS installation
- Linux installation (Ubuntu, CentOS)
- Cloud database setup (AWS RDS, Azure)
- Common issues and solutions
- Verification and testing
- Docker installation
- Performance tuning

**Audience**: DevOps, system administrators
**Read Time**: 45-60 minutes
**Platform Coverage**: Windows, macOS, Linux, Docker

---

### USAGE_EXAMPLES.md
**Purpose**: Practical examples and recipes
**Size**: ~50 KB
**Sections**:
- Basic usage examples
- Batch processing recipes
- Data validation procedures
- 25+ SQL query examples
- Automation with cron/Task Scheduler
- Python scheduling examples
- Docker orchestration
- Troubleshooting scenarios
- Advanced recipes (backup, archive, export)

**Audience**: Developers, data analysts, administrators
**Read Time**: 60+ minutes
**Includes**: Copy-paste ready examples

---

### FILES_MANIFEST.md
**Purpose**: This file - complete file inventory
**Size**: ~20 KB
**Sections**:
- Directory structure
- File descriptions
- File purposes and sizes
- Usage instructions
- Configuration details

**Audience**: All users
**Reference**: Use as index to find what you need

---

## Dependencies File

### etl_requirements.txt
**Purpose**: Python package dependencies
**Size**: ~1 KB
**Format**: pip requirements format

**Core Packages**:
- `xlrd==2.0.1` - Excel file reading (CRITICAL)
- `psycopg2-binary==2.9.9` - PostgreSQL adapter (CRITICAL)
- `numpy==1.24.3` - Numerical operations

**Optional Packages**:
- `tqdm==4.65.0` - Progress bars
- `pandera==0.15.1` - Data validation
- `openpyxl==3.1.2` - XLSX support

**Development Packages**:
- `pytest==7.4.0` - Testing
- `pylint==2.17.5` - Code quality
- `black==23.7.0` - Code formatting

**Installation**:
```bash
pip install -r etl_requirements.txt
```

**Package Count**: 14 packages (9 optional/dev)
**Total Size**: ~150 MB (installed)

---

## Generated Files (Automatic)

### rj_etl_pipeline.log
**Purpose**: Application logs
**Location**: Current working directory
**Format**: Text, timestamped entries
**Rotation**: Manual (no auto-rotation configured)

**Log Levels**:
- INFO: Processing status, summaries
- DEBUG: Detailed cell-level operations
- WARNING: Missing sheets, parsing issues
- ERROR: Database errors, file errors

**Example Entry**:
```
2024-01-15 10:30:45,123 - __main__ - INFO - Database connection established successfully
```

**Retention**: Keep indefinitely for audit trail

### logs/ directory
**Purpose**: Store batch processing logs
**Created By**: process_batch.sh
**Format**: batch_YYYYMMDD_HHMMSS.log

**Contents**: Full processing output
**Retention**: Keep for audit purposes

---

## File Statistics Summary

| Category | Count | Total Size | Purpose |
|----------|-------|-----------|---------|
| Python Scripts | 3 | ~595 KB | Core application |
| Setup/Utility | 2 | ~40 KB | Installation & validation |
| Configuration | 1 | <1 KB | Database settings |
| Database Schema | 1 | ~80 KB | Table definitions |
| Documentation | 5 | ~155 KB | User guides |
| **TOTAL** | **12** | **~870 KB** | Complete pipeline |

---

## Platform Compatibility

### Windows
- ✓ rj_etl_pipeline.py
- ✓ setup.py
- ✓ validate_data.py
- ✗ process_batch.sh (use batch file alternative)
- ✓ database_schema.sql
- ✓ All documentation

### macOS
- ✓ rj_etl_pipeline.py
- ✓ setup.py
- ✓ validate_data.py
- ✓ process_batch.sh
- ✓ database_schema.sql
- ✓ All documentation

### Linux
- ✓ rj_etl_pipeline.py
- ✓ setup.py
- ✓ validate_data.py
- ✓ process_batch.sh
- ✓ database_schema.sql
- ✓ All documentation

### Docker
- ✓ All Python files
- ✓ All scripts
- ✓ Schema execution
- ✓ All documentation

---

## Getting Started Guide

### For New Users
1. Read: **QUICKSTART.md** (10 minutes)
2. Run: `python setup.py`
3. Test: `python validate_data.py`
4. Try: `python rj_etl_pipeline.py --mode single --file "test.xls"`

### For Administrators
1. Read: **INSTALLATION.md** (platform-specific)
2. Install dependencies and PostgreSQL
3. Configure: `db_config.json`
4. Initialize: Database schema setup
5. Schedule: Cron jobs or Task Scheduler

### For Data Analysts
1. Review: **USAGE_EXAMPLES.md**
2. Connect: `psql -d rj_hotel`
3. Query: Use provided SQL examples
4. Analyze: Daily financial summary views

### For Developers
1. Review: **README.md** (Architecture section)
2. Study: `rj_etl_pipeline.py` source code
3. Extend: Add custom parsing logic
4. Test: Using `pytest` framework

---

## Version Information

**Package Version**: 1.0
**Release Date**: 2024-01-15
**Python**: 3.8 - 3.12
**PostgreSQL**: 12 - 15+
**xlrd Version**: 2.0.1
**psycopg2 Version**: 2.9.9

---

## Support and Documentation

- **Main Documentation**: README.md
- **Quick Start**: QUICKSTART.md
- **Installation Help**: INSTALLATION.md
- **Code Examples**: USAGE_EXAMPLES.md
- **File Index**: FILES_MANIFEST.md (this file)

**For Issues**:
1. Check INSTALLATION.md troubleshooting section
2. Review rj_etl_pipeline.log for error messages
3. Run validate_data.py to check data integrity
4. Query rj_data.etl_log table for processing history

---

## License and Attribution

License: [Specify your license]
Author: ETL Team
Created: 2024-01-15
Last Updated: 2024-01-15

---

**Start Here**: QUICKSTART.md → README.md → INSTALLATION.md
