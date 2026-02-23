# Data Source Analysis - Complete Reference

Generated: February 16, 2026

## Overview

Two comprehensive analysis documents have been created to guide database model design and data importer development:

1. **DATA_STRUCTURE_ANALYSIS.md** - High-level overview of all 4 data sources
2. **COLUMN_SPECIFICATIONS.md** - Detailed column-by-column reference

## Quick Stats

| Data Source | Files | Location | Format | Key Sheets |
|---|---|---|---|---|
| **RJ Files** | 366 | `RJ 2024-2025/RJ 2025-2026/` | XLS | EJ, Recap, depot, Diff.Caisse# |
| **SD Files** | 56 | `RJ 2024-2025/SD YYYY/` | XLS | 15 sheets (days 1-15) |
| **POURBOIRE** | 90 | `RJ 2024-2025/POURBOIRE YYYY/` | XLS/XLSX | Feuil1, Sommaire |
| **HP Files** | 54 | `RJ 2024-2025/HP YYYY-YYYY/` | XLSX | mensuel, données, Journalier |
| **QUASIMODO** | 0 | `REPORT QUASIMODO/` | N/A | (empty directory) |

## Document Structure

### DATA_STRUCTURE_ANALYSIS.md

Contains:
- Summary of all data sources
- Detailed breakdown of each source with examples
- Recommended database entities (8 models suggested)
- Import strategy and processing order
- File organization notes

**Sections**:
1. Summary
2. SD Files - Daily Deposit Summary (7 columns)
3. POURBOIRE Files - Tips/Gratuity Payroll (12-16 columns, 2 formats)
4. RJ Files - Journal Entries (38 sheets, 4 key sheets analyzed)
   - EJ: GL account entries
   - Recap: Cash reconciliation
   - depot: Bank deposits
   - Diff.Caisse#: Daily variances
5. HP Files - F&B Sales Reports (XLSX with formulas)
6. QUASIMODO Reports (empty)
7. Database Model Recommendations
8. Import Strategy

### COLUMN_SPECIFICATIONS.md

Contains precise technical specifications:

**SD Files**
- 7 columns: DÉPARTEMENT, NOM LETTRES MOULÉES, CDN/US, MONTANT, MONTANT VÉRIFIÉ, REMBOURSEMENT, VARIANCE
- Metadata extraction (date from Row 4)
- Data quality rules

**POURBOIRE Files**
- Format A (XLS 2022): 12 columns with direct values
- Format B (XLSX 2025): 16 columns with formulas and Sommaire sheet references
- Extraction strategy for both formats

**RJ Files (EJ Sheet)**
- 8 columns: GL code, Cost Center 1/2, Descriptions, Source System, Amount
- 233 GL account rows
- Date conversion from serial format
- Quality checks

**RJ Files (Other Sheets)**
- Recap: Cash reconciliation with 4 key columns
- depot: Bank deposit tracking with multi-account layout
- Diff.Caisse#: Daily variances (39 columns, days 1-30)

**HP Files**
- Monthly summary with departments (Link, Cupola, Piazza, Banquet, Serv Ch., Tabagie)
- Sales categories: NOURR, BOISSON, BIERE, VIN, MIN, POURB, TABAGIE
- Payment methods: 14 (Admin), 15 (Promo), 17 (Service), 500 (Hot rate)
- Formula-based (DSUM) with named ranges

## Key Findings

### Data Format Variety
- **XLS Format**: xlrd library (SD, POURBOIRE 2022, RJ files)
- **XLSX Format**: openpyxl library (POURBOIRE 2025, HP files)
- **Formulas**: HP and POURBOIRE XLSX use formulas; load with `data_only=True` for values

### Date Handling
- Excel serial dates (e.g., 46081.0 = Feb 15, 2026)
- Conversion: `datetime(1899, 12, 30) + timedelta(days=serial)`

### Multi-Sheet Structure
- **SD Files**: 15 sheets (one per day of month)
- **RJ Files**: 38 sheets per file (focus on EJ, Recap, depot, Diff.Caisse#)
- **HP Files**: 4 sheets per file (mensuel is main, données has raw data)

### Data Relationships
- **Date-based linking**: All files use date field
- **Employee linking**: POURBOIRE employee IDs, SD employee names
- **GL account linking**: RJ-EJ has master GL codes
- **F&B linking**: HP departments match operations

## Recommended Database Models

1. **DailyDeposit** (from SD)
2. **TipsPayroll** (from POURBOIRE)
3. **JournalEntry** (from RJ-EJ)
4. **CashReconciliation** (from RJ-Recap)
5. **BankDeposit** (from RJ-depot)
6. **CashDifference** (from RJ-Diff.Caisse#)
7. **FBSalesReport** (from HP-mensuel)
8. **GLAccount** (reference from RJ-EJ)

## Import Sequence

1. Parse RJ-EJ for GL account master
2. Process SD files for daily deposits
3. Process RJ-Recap/depot for cash reconciliation
4. Process POURBOIRE for labor costs
5. Process HP for F&B sales
6. Link all via date fields

## Quality Assurance

Each data source has specific validation rules documented:
- Amount ranges
- Required fields
- Unique constraints
- Calculated field validation
- Date range checks

## Usage

When building importers:
1. Start with COLUMN_SPECIFICATIONS.md for exact cell locations and data types
2. Reference DATA_STRUCTURE_ANALYSIS.md for context and relationships
3. Use xlrd for XLS, openpyxl for XLSX
4. Apply data quality rules before database insert
5. Handle both formats (old XLS and new XLSX) in POURBOIRE

## File Locations

- `/sessions/laughing-sharp-johnson/mnt/audit-pack/DATA_STRUCTURE_ANALYSIS.md` (11 KB)
- `/sessions/laughing-sharp-johnson/mnt/audit-pack/COLUMN_SPECIFICATIONS.md` (15 KB)
- `/sessions/laughing-sharp-johnson/mnt/audit-pack/DATA_ANALYSIS_INDEX.md` (this file)

