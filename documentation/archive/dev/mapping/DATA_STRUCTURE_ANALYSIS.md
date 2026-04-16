# Data Source Structure Analysis - Sheraton Laval Audit Pack

## Summary

Analysis of 4 data sources at `/sessions/laughing-sharp-johnson/mnt/audit-pack/` covering financial and labor data:

- **RJ Files**: 366 Excel files with daily journal entries, GL codes, HR data
- **SD Files**: 56 Excel files with deposit/cash handling records  
- **POURBOIRE Files**: 90 Excel files with tips/gratuity payroll data
- **HP Files**: 54 Excel files with F&B sales reports (XLSX format)
- **QUASIMODO Reports**: 0 files (directory exists but empty)

---

## 1. SD FILES - SOMMAIRE JOURNALIER DES DÉPÔTS

**Purpose**: Daily deposit summary - tracks cash and check deposits by department

**Location**: `RJ 2024-2025/SD 2025/` (15 files) + other year folders
**Format**: Excel XLS with 15 sheets (one per day)
**File Example**: `vierge.xls`

### Sheet Structure (Sheet "1" = Day 1, "2" = Day 2, etc.)

**Columns (Row 6 header)**:
- Col A: `DÉPARTEMENT` - Department name (RÉCEPTION, SPESA, etc.)
- Col B: `NOM LETTRES MOULÉES` - Employee name
- Col C: `CDN /US` - Currency type (Canadian/US)
- Col D: `MONTANT` - Amount deposited
- Col E: `MONTANT VÉRIFIÉ` - Verified amount
- Col F: `REMBOURSEMENT` - Reimbursement amount
- Col G: `VARIANCE` - Variance/difference (numeric)

**Key Structure**:
```
Row 1: SHERATON - LAVAL
Row 2: SOMMAIRE JOURNALIER DES DÉPÔTS ET DES SURPLUS ET DÉFICIT
Row 4: DATE (cell A4)
Row 6: Column headers
Row 8+: Data rows (multiple departments per sheet)
```

**Departments Found**: RÉCEPTION, SPESA

**Data Characteristics**:
- Variance values are numeric (0.0, etc.)
- Multiple employees per department per day
- 44 rows total per sheet
- 7 columns

---

## 2. POURBOIRE FILES - TIPS/GRATUITY PAYROLL

**Purpose**: Track tips and gratuities by employee

**Location**: `RJ 2024-2025/POURBOIRE 2022-2025/` (90 total files)
**Format**: Excel XLS (2022 format) and XLSX (2025 format)
**File Examples**: 
- `POD29012022.xls` (older XLS format)
- `POD12282025.xlsx` (newer XLSX format with formulas)

### Sheet Structure - Feuil1 (Main Data Sheet)

**Columns (Row 1 header - XLS version)**:
- Col A: `Compagnie` - Company code (8643)
- Col B: `Matricule` - Employee ID
- Col C: `Nom, prénom` - Employee name
- Col D: `No relevé` - Statement number
- Col E: `Période` - Period (date serial)
- Col F-K: `TRAV 1-6` - Work periods 1-6 (appear empty in sample)
- Col L: `G730(Montant)` - Amount (tips/gratuity value)

**Columns (Row 1 header - XLSX version)**:
- Col A: `Compagnie` - Company code (8643)
- Col B: `Matricule` - Employee ID (contains formulas like `=+Sommaire!A9`)
- Col C: Calculated field (RIGHT/CONCATENATE formulas)
- Col D: `Nom, prénom` - Employee name (formula reference)
- Col E: `No relevé` - Statement number (0)
- Col F: `Période` - Period as datetime
- Col G-L: `TRAV 1-6` - Work periods (appear to be null/empty)

**Related Sheets**:
- `Sommaire` - Summary sheet containing employee master list
- `Feuil2` - Additional data (not fully analyzed)

**Data Characteristics**:
- XLS format has direct values: employee names, amounts
- XLSX format uses formulas referencing Sommaire sheet
- Employee matrix includes payroll periods
- 63 rows in sample, 16 columns (with empty trailing cols)
- Company code 8643 appears constant

---

## 3. RJ FILES - JOURNAL ENTRIES & GL RECONCILIATION

**Purpose**: Daily journal entries, GL account reconciliation, financial audit records

**Location**: `RJ 2024-2025/RJ 2025-2026/` (366 files in multiple months)
**Format**: Excel XLS
**File Structure**: 38 sheets per file (blank template shown)

### Key Sheets - RECAP (Summary)

**Purpose**: Recap of cash/payments for the day

**Structure**:
```
Row 0: Date (cell E0 = 46081.0 = Feb 15, 2026)
Row 3: "RECAP" title
Row 4: Headers - Description | Lecture | Corr. + (-) | Net
```

**Rows 5-11 (Data)**:
- Row 5: Comptant LightSpeed | 0.0 | | 0.0
- Row 6: Comptant Positouch | | | 0.0
- Row 7: Chèque payment register AR | 0.0 | | 0.0
- Row 8: Chèque Daily Revenu | 0.0 | | 0.0
- Row 9: **Total** | 0.0 | 0.0 | 0.0
- Row 10: Moins Remboursement Gratuité | | | 0.0
- Row 11: Moins Remboursement Client | | | 0.0

**Data Characteristics**:
- 26 rows, 14 columns
- Main reconciliation values in columns B (Lecture) and C (Correction)

### Key Sheets - DEPOT (Deposit Records)

**Purpose**: Bank deposit tracking with signatures

**Structure**:
```
Row 0: GROUPE HÔTELIER GRAND CHÂTEAU INC
Row 1: HOTEL SHERATON LAVAL
Row 3: DATE: 46081.0
Row 5: COMPTE CANADIEN (header)
Row 6: CLIENT 6 COMPTE # 1844-22 (left side) | CLIENT 8 COMPTE # 4743-66 (right side)
Row 8: Column headers - DATE | MONTANT | SIGNATURE (repeated for multiple accounts)
```

**Data Characteristics**:
- 54 rows, 16 columns
- Multiple bank accounts tracked side-by-side
- Dual-column layout for different account sections
- Signature fields for authorization

### Key Sheets - EJ (GL Journal Entries)

**Purpose**: General Ledger account entries by GL code

**Structure**:
```
Row 0: Headers - A/code gl | B/cc1 | C/cc2 | D/description 1 | E/description 2 | F/source | G/MONTANT
```

**Sample Entries (Rows 1-11)**:
```
075001 | 2.0 | | VENTES CHAMBRES | 46081.0 | s-ej10 | 0.0
075002 | 2.0 | | SALAIRES CHAMBRES | 46081.0 | s-ej10 | 0.0
075003 | 2.0 | | BENEFICES MARGINAUX | 46081.0 | s-ej10 | 0.0
...
075021 | 2.0 | | SALAIRES RESTAURATION | 46081.0 | s-ej10 | 0.0
075022 | 2.0 | | BEN MARGINAUX | 46081.0 | s-ej10 | 0.0
```

**Data Characteristics**:
- 233 rows of GL accounts
- 8 columns
- GL codes: 075001-075022+ (hotel accounting code range)
- Cost center 1 (cc1) = 2.0 (appears constant for room revenue)
- Date stored as serial (46081.0)
- Amount column (G) is the monetary value

### Key Sheets - DIFF.CAISSE# (Daily Cash Differences)

**Purpose**: Track daily cash variances/discrepancies

**Structure**:
```
Row 0: Jour | (blank) | geac ux (repeating columns)
Row 2+: 
  1.0 | 0.0 | (repeating values)
  2.0 | 0.0 |
  3.0 | 0.0 |
  ...
  30.0 | 0.0 |
```

**Data Characteristics**:
- 38 rows (for days in month), 39 columns
- Day number in column A (1-30)
- Variance/difference value in column B
- Multiple system tracking columns (geac ux)

### Other Sheets (Not analyzed in detail)

The RJ file contains 38 sheets including:
- `rj` - Main journal sheet
- `jour` - Daily summary
- `salaires` - Salary/payroll info
- `controle` - Control/verification
- `autre GL` - Other GL accounts
- `Analyse 101100 autre`, `Analyse 100401` - GL account analysis
- Payment methods: `Sonifi`, `Internet`, `SOCAN`, `résonne`, `Vestiaire#`, `DUBACK#`
- Labor: `somm_nettoyeur`, `Nettoyeur`, `AD`, `Massage`
- Reports: `Rapp_p1`, `Rapp_p2`, `Rapp_p3`, `Etat rev`, `Budget`

---

## 4. HP FILES - F&B SALES REPORTS

**Purpose**: Food & Beverage sales analysis and reconciliation

**Location**: `RJ 2024-2025/HP 2024-2025/` (17 .xlsx files), `HP 2025-2026/` (1 file)
**Format**: Excel XLSX (formulas used)
**File Examples**: 
- `hp1224.xlsx` (Dec 2024 report)
- `hp0124.xlsx` (Jan 2024)

### Sheet "mensuel" (Monthly Report)

**Structure**:
```
Row 1: RAPPORT AJUSTEMENT HP POUR LE MOIS | (col D) Decembre 2024
Row 3: Distribution des ventes par département
Row 4: Headers - DEPARTEMENT | NOURR | BOISSON | BIERE | VIN | MIN | POURB | TABAGIE | TOTAL
```

**Data Rows (Rows 5-11)**:
```
Link      | =DSUM(...) | =DSUM(...) | ... | =SUM(B5:H5)
Cupola    | =DSUM(...) | =DSUM(...) | ... | =SUM(B6:H6)
Piazza    | =DSUM(...) | =DSUM(...) | ... | =SUM(B7:H7)
Banquet   | =DSUM(...) | =DSUM(...) | ... | =SUM(B8:H8)
Serv Ch.  | =DSUM(...) | =DSUM(...) | ... | =SUM(B9:H9)
Tabagie   | =DSUM(...) | =DSUM(...) | ... | =SUM(B10:H10)
TOTAL     | =SUM(...)  | =SUM(...)  | ... | =SUM(...)
```

**Payment Method Section (Rows 15-19)**:
```
Row 15: Headers - DEPARTEMENT | NOURR | BOISSON | BIERE | VIN | MIN | TABAGIE | (blank) | TOTAL
Row 16: Administartion (14) | DSUM formulas...
Row 17: Hotel promotion (15) | DSUM formulas...
Row 18: Promesse service | DSUM formulas...
Row 19: 50% Hot rate | DSUM formulas...
```

**Data Characteristics**:
- 45 rows max_row, 9 columns max_col
- 4 sheets per file: `mensuel`, `données`, `Journalier`, `Feuil1`
- Uses DSUM() and Database named range for dynamic calculations
- References criteria ranges (crit_Link, crit_cupola, etc.)
- Department codes: Link, Cupola, Piazza, Banquet, Serv Ch., Tabagie
- Payment method codes: 14 (Admin), 15 (Promo), 17 (Service), 500 (Hot rate)

**Sales Categories**:
- NOURR (Food)
- BOISSON (Beverage)
- BIERE (Beer)
- VIN (Wine)
- MIN (Minibar)
- POURB (Tips/Gratuity)
- TABAGIE (Tobacco)

### Other Sheets

- `données` - Raw transaction data with Database named range
- `Journalier` - Daily breakdown (not analyzed)
- `Feuil1` - Additional data sheet

---

## 5. QUASIMODO REPORTS

**Location**: `REPORT QUASIMODO/`
**Status**: Directory exists but contains 0 files
**Purpose**: Unknown (likely legacy or future feature)

---

## Database Model Recommendations

### Entities to Create

1. **DailyDeposit** (from SD files)
   - date
   - department
   - employee_name
   - currency (CDN/US)
   - amount
   - amount_verified
   - reimbursement
   - variance

2. **TipsPayroll** (from POURBOIRE files)
   - employee_id
   - employee_name
   - company_code (8643)
   - period_date
   - statement_number
   - amount
   - work_periods (TRAV 1-6)

3. **JournalEntry** (from RJ-EJ sheet)
   - date
   - gl_code
   - cost_center_1
   - cost_center_2
   - description_1
   - description_2
   - source_system
   - amount

4. **CashReconciliation** (from RJ-RECAP sheet)
   - date
   - cash_type (Comptant LightSpeed, Positouch, Chèque, etc.)
   - reading_amount
   - correction_amount
   - net_amount

5. **DailyDeposit_Bank** (from RJ-DEPOT sheet)
   - date
   - account_number
   - account_name
   - deposit_date
   - amount
   - signature

6. **CashDifference** (from RJ-DIFF.CAISSE# sheet)
   - date
   - day_number (1-30)
   - variance
   - system

7. **FBSalesReport** (from HP files)
   - report_date
   - month
   - department
   - nourr_amount
   - boisson_amount
   - biere_amount
   - vin_amount
   - min_amount
   - pourb_amount
   - tabagie_amount
   - total_amount
   - payment_method

8. **GLAccount** (Reference data from RJ-EJ)
   - gl_code
   - description
   - department
   - category

---

## Import Strategy

### File Format Handling
- **XLS files**: Use `xlrd` library
- **XLSX files**: Use `openpyxl` library (with `data_only=True` if values needed)
- **Date conversion**: Use Excel serial date format (e.g., 46081.0 = datetime)

### Processing Order
1. Parse RJ-EJ sheet for GL account master data
2. Process SD files for daily deposits
3. Process RJ-RECAP/DEPOT for cash reconciliation
4. Process POURBOIRE files for labor costs
5. Process HP files for F&B sales
6. Link via date fields

### File Organization
```
/data_sources/
  /RJ/                    # 366 files
    /monthly_folders/     # Organized by month
  /SD/                    # 56 files
    /yearly_folders/      # Organized by year
  /POURBOIRE/             # 90 files
    /yearly_folders/
  /HP/                    # 54 files (xlsx)
    /yearly_folders/
```

