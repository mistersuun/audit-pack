# Detailed Column Specifications for Data Import

## 1. SD FILES - DAILY DEPOSIT SUMMARY

**File Pattern**: `RJ 2024-2025/SD YYYY/file.xls`
**Sheets**: 15 sheets named "1" through "15" (one per day of month)
**Row Range**: Row 6 headers, data starts Row 8
**Column Count**: 7 columns (A-G)

| # | Column | Excel Cell | Header Name | Data Type | Example | Notes |
|---|--------|-----------|-------------|-----------|---------|-------|
| A | Department | Col A | DÉPARTEMENT | String | RÉCEPTION, SPESA | Hotel department/section |
| B | Employee Name | Col B | NOM LETTRES MOULÉES | String | Name in capitals | Full name of handler |
| C | Currency | Col C | CDN /US | String | CDN, US | Currency type |
| D | Amount | Col D | MONTANT | Float | 0.0, 123.45 | Deposit amount |
| E | Verified Amount | Col E | MONTANT VÉRIFIÉ | Float | 0.0, 123.45 | Amount verified by manager |
| F | Reimbursement | Col F | REMBOURSEMENT | Float | 0.0 | Reimbursement amount |
| G | Variance | Col G | VARIANCE | Float | 0.0 | Difference/variance |

**Metadata Extraction**:
- **Date**: Extract from Row 4, Column A = "DATE" label, Date value in Column A Row 4
- **Sheet Name**: Numeric (1-15) = day of month
- **File Name**: Contains year information (e.g., `SD 2025/` = year 2025)

**Data Characteristics**:
- Multiple rows per department per day
- RÉCEPTION and SPESA departments most common
- Amounts are all zero in sample (vierge = blank template)
- 44 rows per sheet (7-50 approximately)

**Quality Rules**:
- Variance = Montant - Montant Vérifié (should validate)
- All amounts should be >= 0.0
- Employee name should not be empty
- Currency should be CDN or US

---

## 2. POURBOIRE FILES - TIPS/GRATUITY PAYROLL

### Format A: XLS (2022 Format)

**File Pattern**: `RJ 2024-2025/POURBOIRE YYYY/PODddmmyyyy.xls`
**Sheet**: "Feuil1" (main sheet)
**Row Range**: Row 0 headers, data starts Row 2
**Column Count**: 12 columns (A-L)

| # | Column | Excel Cell | Header Name | Data Type | Example | Notes |
|---|--------|-----------|-------------|-----------|---------|-------|
| A | Company | Col A | Compagnie | Integer | 8643 | Hotel company code |
| B | Employee ID | Col B | Matricule | Integer | 5105, 92704 | Unique employee ID |
| C | Employee Name | Col C | Nom, prénom | String | Amari Mahdi | Full employee name |
| D | Statement # | Col D | No relevé | Integer | 0 | Statement/reference number |
| E | Period | Col E | Période | Date (serial) | 44548.0, 44590.0 | Pay period date |
| F | Work Period 1 | Col F | TRAV 1 | Float | (empty) | Work code/hours period 1 |
| G | Work Period 2 | Col G | TRAV 2 | Float | (empty) | Work code/hours period 2 |
| H | Work Period 3 | Col H | TRAV 3 | Float | (empty) | Work code/hours period 3 |
| I | Work Period 4 | Col I | TRAV 4 | Float | (empty) | Work code/hours period 4 |
| J | Work Period 5 | Col J | TRAV 5 | Float | (empty) | Work code/hours period 5 |
| K | Work Period 6 | Col K | TRAV 6 | Float | (empty) | Work code/hours period 6 |
| L | Amount | Col L | G730(Montant) | Float | 7111.16, 5165.92 | Tips/gratuity amount |

**Metadata**:
- **Sheet Name**: "Feuil1" (fixed)
- **Related Sheets**: "Feuil2" (optional), "Sommaire" (summary)
- **File Name Pattern**: `POD + DDMMYYYY.xls` = date of report

**Data Characteristics**:
- Row 0 = headers
- Row 1 = "**" marker row (skip)
- Row 2+ = employee data
- Company code (8643) constant for all hotel
- Period dates are Excel serial format
- Work periods typically empty
- Amount represents tips paid to employee

### Format B: XLSX (2025 Format)

**File Pattern**: `RJ 2024-2025/POURBOIRE YYYY/PODddmmyyyy.xlsx`
**Sheets**: "Feuil1" (main), "Sommaire" (employee master)
**Row Range**: Row 1 headers, data starts Row 3
**Column Count**: 16 columns (A-P, with empty trailing)

| # | Column | Excel Cell | Header Name | Data Type | Example | Formula/Notes |
|---|--------|-----------|-------------|-----------|---------|--------|
| A | Company | Col A | Compagnie | Integer | 8643 | Constant value |
| B | Employee ID | Col B | Matricule | Formula | =+Sommaire!A9 | References Sommaire sheet |
| C | ID Formatted | Col C | (blank) | Formula | =RIGHT(CONCATENATE("000",B3),6) | Formats ID as 6-digit |
| D | Employee Name | Col D | Nom, prénom | Formula | =+Sommaire!B9 | References Sommaire sheet |
| E | Statement # | Col E | No relevé | Integer | 0 | Reference number |
| F | Period | Col F | Période | DateTime | 2026-01-10 00:00 | Python datetime object |
| G-L | Work Periods 1-6 | Col G-L | TRAV 1-6 | Empty | None | Placeholder columns |
| M-P | Empty | Col M-P | (blank) | Empty | None | Trailing empty columns |

**Sommaire Sheet Structure**:
- Contains employee master list
- Column A: Employee ID (Matricule)
- Column B: Employee Name (Nom)
- Referenced by Feuil1 formulas

**Data Characteristics**:
- Uses formulas to pull from Sommaire sheet
- When read with `data_only=False`, formulas are visible
- When read with `data_only=True`, calculated values appear
- Period stored as Python datetime when data_only=True
- 63 rows in sample file
- All TRAV columns empty (placeholders)

**Data Extraction Strategy**:
- Load with `data_only=True` to get calculated values
- Extract B column (actual IDs from Sommaire)
- Extract D column (actual names from Sommaire)
- Extract F column (period dates as datetime)
- Extract L column (amount - may need separate handling)

---

## 3. RJ FILES - JOURNAL ENTRIES & RECONCILIATION

**File Pattern**: `RJ 2024-2025/RJ 2025-2026/MM-Mois YYYY/Rj YYYY-MM-DD.xls`
**Total Sheets**: 38 sheets per file
**Format**: XLS (xlrd compatible)

### Sheet: "EJ" - General Ledger Entries

**Row Range**: Row 0 headers, data starts Row 1
**Column Count**: 8 columns (A-H)

| # | Column | Excel Cell | Header Name | Data Type | Example | Notes |
|---|--------|-----------|-------------|-----------|---------|-------|
| A | GL Code | Col A | A/code gl | String | 075001, 075022 | General Ledger account code |
| B | Cost Center 1 | Col B | B/cc1 | Float | 2.0 | Primary cost center |
| C | Cost Center 2 | Col C | C/cc2 | String | (empty) | Secondary cost center |
| D | Description 1 | Col D | D/description 1 | String | VENTES CHAMBRES | Primary account description |
| E | Description 2 | Col E | E/description 2 | Date (serial) | 46081.0 | Note: Contains date serial (Feb 15, 2026) |
| F | Source System | Col F | F/source | String | s-ej10 | System identifier |
| G | Amount | Col G | G/MONTANT | Float | 0.0 | Monetary amount |
| H | (blank) | Col H | (blank) | Empty | (empty) | Unused column |

**GL Code Range**: 075001 through 075022+ (hotel accounting codes)
- 075001-075004: Room revenue and costs
- 075010-075013: Banquet revenue and costs
- 075020-075022: Restaurant/Minibar revenue and costs
- Additional: Salaries, benefits, fixed costs

**Data Characteristics**:
- 233 rows of GL accounts
- All entries same date (from column E - see note above)
- Cost center 1 consistent at 2.0 for revenue accounts
- Source system "s-ej10" indicates source
- Amounts all 0.0 in blank template

**Extract Logic**:
```
For each row 1-232:
  gl_code = A[row]
  cost_center_1 = B[row]
  cost_center_2 = C[row]
  description = D[row]
  entry_date = convert_excel_date(E[row])
  source_system = F[row]
  amount = G[row]
```

### Sheet: "Recap" - Cash Reconciliation Summary

**Row Range**: Row 4 headers, data starts Row 5
**Column Count**: 14 columns
**Key Row**: Row 0, Column E = Report Date (Excel serial)

| # | Column | Description | Header Name | Data Type | Example | Notes |
|---|--------|-------------|-------------|-----------|---------|-------|
| A | Description | Cash/Payment Type | Description | String | Comptant LightSpeed, Chèque | Type of cash/payment |
| B | Reading | Amount Read | Lecture | Float | 0.0 | Reading amount |
| C | Correction | Adjustment | Corr. + (-) | Float | 0.0 | Correction amount |
| D | Net Amount | Net | Net | Float | 0.0 | Final net amount |

**Key Rows**:
- Row 5: Comptant LightSpeed (Cash from POS)
- Row 6: Comptant Positouch (Cash from other POS)
- Row 7: Chèque payment register AR (Checks - payment register)
- Row 8: Chèque Daily Revenu (Checks - daily revenue)
- Row 9: **TOTAL** (Sum row)
- Row 10: Moins Remboursement Gratuité (Less tip reimbursement)
- Row 11: Moins Remboursement Client (Less customer refund)

**Data Characteristics**:
- Date in Row 0, Column E (E0)
- Multiple payment types
- Corrections allow for adjustments
- Total row provides summary

**Extract Logic**:
```
report_date = convert_excel_date(E0)
For each payment type row:
  type = A[row]
  reading = B[row]
  correction = C[row]
  net = D[row]
```

### Sheet: "depot" - Bank Deposit Records

**Row Range**: Row 8 headers, data starts Row 9
**Column Count**: 16 columns
**Key Row**: Row 3, Column B = Report Date

| # | Column | Account | Headers | Notes |
|---|--------|---------|---------|-------|
| A-C | Columns | Compte Canadien - CLIENT 6 (1844-22) | DATE, MONTANT, SIGNATURE | Left account section |
| D | Spacer | (blank) | | Separator |
| E-G | Columns | (blank) | (blank) | Middle section |
| H | Spacer | (blank) | | Separator |
| I-K | Columns | Compte Canadien - CLIENT 8 (4743-66) | DATE, MONTANT, SIGNATURE | Right account section |
| L-P | Columns | (additional account sections) | (repeating pattern) | More accounts |

**Data Characteristics**:
- Dual/multiple column layout for different bank accounts
- Row 0-2: Header information
- Row 3: DATE field
- Row 5-6: Account identification
- Row 8: Column headers
- Row 9+: Data rows (empty in template)
- Signature fields for manual authorization

**Account Information**:
- Account 1: CLIENT 6, COMPTE # 1844-22
- Account 2: CLIENT 8, COMPTE # 4743-66
- Pattern repeats for additional accounts

### Sheet: "Diff.Caisse#" - Daily Cash Differences

**Row Range**: Row 2 data starts
**Column Count**: 39 columns
**Key Info**: Row 0 = headers

| # | Column | Header Name | Data Type | Example | Notes |
|---|--------|-------------|-----------|---------|-------|
| A | Day Number | Jour | Integer | 1.0, 2.0, ... 30.0 | Day of month |
| B | Variance | (header varies) | Float | 0.0 | Cash variance/difference |
| C+ | System Data | geac ux | Float | (empty) | Multiple system columns |

**Data Characteristics**:
- 38 rows (days 1-30, plus header/footer)
- 39 columns (day + multiple system tracking)
- Day number in column A
- Variance in column B
- Repeating "geac ux" headers for system tracking

**Extract Logic**:
```
For each day 1-30:
  day = A[row]
  variance = B[row]
  # Can ignore remaining columns (system-specific)
```

---

## 4. HP FILES - F&B SALES REPORTS

**File Pattern**: `RJ 2024-2025/HP YYYY-YYYY/hp{mmdd}.xlsx`
**Format**: XLSX (openpyxl compatible with formulas)
**Sheets**: "mensuel", "données", "Journalier", "Feuil1"

### Sheet: "mensuel" - Monthly Summary Report

**Key Header**: Row 1, Column D = Month/Year (e.g., "Decembre 2024")

**Section 1: Distribution by Department (Rows 3-11)**

| # | Column | A | B | C | D | E | F | G | H | I |
|---|--------|---|---|---|---|---|---|---|---|---|
| Header (Row 4) | DEPARTEMENT | NOURR | BOISSON | BIERE | VIN | MIN | POURB | TABAGIE | TOTAL |
| Row 5 | Link | Formula | Formula | Formula | Formula | Formula | Formula | Formula | =SUM(B5:H5) |
| Row 6 | Cupola | Formula | Formula | Formula | Formula | Formula | Formula | Formula | =SUM(B6:H6) |
| Row 7 | Piazza | Formula | Formula | Formula | Formula | Formula | Formula | Formula | =SUM(B7:H7) |
| Row 8 | Banquet | Formula | Formula | Formula | Formula | Formula | Formula | Formula | =SUM(B8:H8) |
| Row 9 | Serv Ch. | Formula | Formula | Formula | Formula | Formula | Formula | Formula | =SUM(B9:H9) |
| Row 10 | Tabagie | Formula | Formula | Formula | Formula | Formula | Formula | Formula | =SUM(B10:H10) |
| Row 11 | TOTAL | =SUM(B5:B10) | =SUM(C5:C10) | =SUM(D5:D10) | =SUM(E5:E10) | =SUM(F5:F10) | =SUM(G5:G10) | =SUM(H5:H10) | =SUM(I5:I10) |

**Departments**:
- Link: POS system Link
- Cupola: Restaurant area
- Piazza: Restaurant area
- Banquet: Banquet/private events
- Serv Ch.: Room service
- Tabagie: Tobacco/retail shop

**Sales Categories** (Columns B-H):
- B: NOURR (Food)
- C: BOISSON (Beverage - non-alcoholic)
- D: BIERE (Beer)
- E: VIN (Wine)
- F: MIN (Minibar)
- G: POURB (Tips/Gratuity)
- H: TABAGIE (Tobacco products)
- I: TOTAL (Sum of B-H)

**Section 2: Distribution by Payment Method (Rows 14-19)**

| # | Column | A | B-G | H | I |
|---|--------|---|-----|---|---|
| Row 15 | Headers | DEPARTEMENT | Category columns | (blank) | TOTAL |
| Row 16 | Administartion (14) | Code | DSUM formulas | | =SUM(B16:G16) |
| Row 17 | Hotel promotion (15) | Code | DSUM formulas | | =SUM(B17:G17) |
| Row 18 | Promesse service | Code | DSUM formulas | | =SUM(B18:G18) |
| Row 19 | 50% Hot rate | Code | DSUM formulas | | =SUM(B19:G19) |

**Payment Method Codes**:
- 14: Administration (employee/house use)
- 15: Hotel promotion (promotional discount)
- 17: Service promise (complimentary/promise)
- 500: 50% Hot rate (special rate)

**Formula Pattern**:
```
=DSUM(_xlnm.Database, {column_number}, crit_{dept_name})
```

**Data Extraction Strategy**:
- Load with `data_only=True` to get calculated values
- Extract rows 5-10 (departments)
- Row 11 = Total row
- Extract rows 16-19 (payment methods)
- Column B-I = numeric sales values
- Use row 1, column D for report date

### Sheet: "données" - Raw Transaction Data

**Purpose**: Source data for DSUM formulas in mensuel sheet
**Structure**: Database named range with transaction details
**Columns**: Not fully analyzed but referenced by formulas

---

## Excel Date Serial Conversion

**Formula**: Serial date number = days since January 0, 1900
- 46081.0 = February 15, 2026
- 44548.0 = January 1, 2022

**Python Conversion**:
```python
from datetime import datetime, timedelta

def excel_to_date(excel_serial):
    return datetime(1899, 12, 30) + timedelta(days=excel_serial)
```

---

## Data Quality Checks

### By File Type

**SD Files**:
- Variance should equal |Montant - Montant Vérifié|
- All amounts >= 0
- Department not empty
- One entry per employee per day

**POURBOIRE Files**:
- Employee ID unique per file (mostly)
- Period dates in reasonable range
- Amount >= 0
- Company code = 8643

**RJ-EJ Files**:
- GL codes follow pattern (075xxx)
- Cost centers are valid numbers
- Date consistent across file
- Source system populated

**RJ-RECAP Files**:
- Reading amount >= 0
- Correction may be positive/negative
- Net amount = Reading + Correction
- Total row sums correctly

**HP Files**:
- Amounts all >= 0
- Department names consistent
- Sales categories match column headers
- TOTAL rows sum correctly

