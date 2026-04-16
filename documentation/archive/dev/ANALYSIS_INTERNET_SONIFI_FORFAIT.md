# Analysis: Internet, Sonifi, and Forfait in RJ Excel Workbook

**Analysis Date:** February 21, 2026
**RJ Files Analyzed:**
- `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Rj_03-02-2026_pour_test.xls`
- `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Rj_04-02-2026_ORIGINAL.xls`

---

## 1. JOUR SHEET COLUMNS - "Autres Revenus" Section

The JOUR sheet contains **all revenue data**, including Internet and Sonifi in the "Autres Revenus" section:

### Column AT (Index 45): **Sonifi Film**
- **Header (Row 1):** `Sonifi Film`
- **Purpose:** Sonifi (hotel entertainment system) daily revenue from film purchases
- **Data Type:** Numeric (can be positive or zero)
- **Example Values:**
  - Row 2: 22.99
  - Row 3-4: (empty)
- **Location in RJ:** Jour sheet, part of "Autres Revenus" section (column AE onwards includes other auxiliary revenues)

### Column AW (Index 48): **Internet**
- **Header (Row 1):** `Internet`
- **Purpose:** Internet sales/charges revenue (typically small, can be negative)
- **Data Type:** Numeric (can be positive, negative, or zero)
- **Example Values:**
  - Row 2: -0.27
  - Row 3: -0.7
  - Row 4: 209.11
- **Location in RJ:** Jour sheet, same "Autres Revenus" section as Sonifi

### Column BF (Index 57): **Difference forfait**
- **Header (Row 1):** `Difference forfait`
- **Purpose:** Forfait (meal plan) variance - shows negative amounts for forfait deductions
- **Data Type:** Numeric (typically negative, as it's a cost/deduction)
- **Example Values:**
  - Row 2: -1181.23
  - Row 3: -83.85
  - Row 4: -142.81
- **Location in RJ:** Jour sheet, in the main F&B reconciliation section (columns BF-BJ area)

---

## 2. INTERNET SHEET - Data Entry & Reconciliation

The **Internet** sheet is a standalone reconciliation tab that:

### Structure
- **Dimensions:** 41 rows × 94 columns
- **Purpose:** Reconcile Internet CD (charge detail) against Jour sheet
- **Data Layout:**

```
Row 0-2: Header info (hotel name, report number, report date)
Row 3: Date (45809.0 = Excel date serial)
Row 6: Column headers:
  - A: JOUR (day number)
  - B: Rapport LightSpeed (LS report value)
  - C: Ajustement Chambre (room adjustment)
  - D: BANQUETS (banquet adjustment)
  - E: SPESA (market adjustment)
  - F: ADJ MARRIOTT (Marriott adjustment)
  - G: Forfait BNC (BNC forfait)
  - H: forfait internet (internet forfait)
  - I: (adjustment total)
  - J: R.J (Jour sheet value - pulled from Jour!AW{row})
  - K: Variance (calculated: = J - I)

Row 7-41: Data rows (1 row per day of month)
```

### Formula Pattern
Column J should contain formula references to Jour sheet column AW, but in this test file, the values appear pre-calculated rather than formula-based. The structure suggests:
- **Expected Formula (not visible in xlrd):** `=+jour!AW{row}`
- **Actual Pattern:** Values are static numbers
- **Variance Calculation:** Column K = Column J (Jour value) - Column I (Adjusted LS report)

### Example Row (Day 1):
```
A1=1, B1="", C="", D="", E="", F="", G="", H="", I=0.0, J=-0.27, K=0.27
```

**Interpretation:**
- Jour sheet shows Internet = -0.27
- Adjusted LS report shows 0.0
- Variance = -0.27 (explains discrepancy)

---

## 3. SONIFI SHEET - Data Entry & Reconciliation

The **Sonifi** sheet is similar to Internet but specifically for Sonifi (hotel entertainment):

### Structure
- **Dimensions:** 65 rows × 94 columns
- **Purpose:** Reconcile Sonifi CD (charge detail) against Jour sheet
- **Data Layout:**

```
Row 0-3: Header info (hotel name, "RECONCILIATION", date serial, month)
Row 4: Column headers with price points:
  - Col L-S: Product price points ($8.95, $9.95, $10.95, etc.)
  - Col T: (blank)
  - Col U: RAPPORTS - InnVue label
  - Col V: Ajustement FILMS $ (adjustment)
  - Col W: TOTAL APRES AJUST. (total after adjustment)
  - Col X: TOTAL RJ (Jour sheet value - pulled from Jour!AT{row})
  - Col Y: DIFF (variance)

Row 5: Sub-header labels
Row 6-40: Data rows (1 row per day)
```

### Formula Pattern
Column X should reference Jour sheet column AT (Sonifi Film), following same pattern as Internet:
- **Expected Formula:** `=+jour!AT{row}`
- **Actual Pattern:** Values are static (e.g., 22.99 in Row 6)
- **Variance Calculation:** Column Y = Column X (Jour value) - Column W (Adjusted total)

### Example Row (Day 1):
```
Row 6: ... Col S=22.99 (customer pay), Col T=, Col U=, Col V="", Col W=22.99, Col X=22.99, Col Y=""
```

**Interpretation:**
- Customer payment = 22.99
- Adjusted total = 22.99
- Jour sheet = 22.99
- Variance = 0 (balanced)

---

## 4. SALES JOURNAL PARSER - Payment Method Extraction

File: `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/parsers/sales_journal_parser.py`

### A. COMPTANT (Cash) Extraction

**YES - Comptant is extracted:**

```python
# Line 333-334 in sales_journal_parser.py:
'comptant': r'COMPTANT\s+(\d+\.\d+)',

# Line 584:
'comptant_lightspeed': payments.get('comptant', 0.0),
```

**Test Data Confirmation** (`Sales_Journal_4th_Feb.rtf`):
```
Line 53: COMPTANT                                737.99
```
✓ Successfully parsed: $737.99

**RJ Mapping:**
- Stores in `parsed_result['rj_mapping']['recap']['comptant_lightspeed']`
- Maps to Recap sheet, column for Positouch cash

### B. FORFAIT Extraction

**YES - Forfait is extracted:**

```python
# Line 378 in sales_journal_parser.py:
'forfait': r'FORFAIT\s+(\d+\.\d+)',

# Lines 375-381 (adjustment parsing):
adjustment_items = {
    'administration': r'ADMINISTRATION\s+(\d+\.\d+)',
    'hotel_promotion': r'HOTEL PROMOTION\s+(\d+\.\d+)',
    'forfait': r'FORFAIT\s+(\d+\.\d+)',
    'empl_30': r'EMPL 30%\s+(\d+\.\d+)',
    'pourboire_charge': r'POURBOIRE CHARGE\s+(\d+\.\d+)',
}
```

**Test Data Confirmation** (`Sales_Journal_4th_Feb.rtf`):
```
Line 71: FORFAIT                     58.65
```
✓ Successfully parsed: $58.65 (debits column, line 71, page 2)

**Storage:**
- Stores in `parsed_result['extracted_data']['adjustments']['forfait']`
- Currently **NOT included** in the RJ mapping (line 570-606)

### C. All Payment Methods Extracted

The parser extracts these payment methods (lines 332-340):

```python
'comptant': r'COMPTANT\s+(\d+\.\d+)',           # Cash
'visa': r'VISA\s+(\d+\.\d+)',                   # Visa credit card
'mastercard': r'MASTERCARD\s+(\d+\.\d+)',       # Mastercard
'amex': r'AMEX\s+(\d+\.\d+)',                   # American Express
'interac': r'INTERAC\s+(\d+\.\d+)',             # Interac debit
'chambre': r'CHAMBRE\s+(\d+\.\d+)',             # Room charges
'correction': r'CORRECTION\s+(\d+\.\d+)',       # Correction adjustments
```

**Test Data Results:**
| Payment Method | Amount | Line | Status |
|---|---|---|---|
| COMPTANT | 737.99 | 53 | ✓ |
| VISA | 2344.84 | 55 | ✓ |
| MASTERCARD | 807.83 | 56 | ✓ |
| AMEX | 496.53 | 57 | ✓ |
| INTERAC | 880.15 | 58 | ✓ |
| CHAMBRE | 13265.41 | 59 | ✓ |
| CORRECTION | 11176.96 | 60 | ✓ |

---

## 5. DIFF_FORFAIT SHEET - Forfait Variance Tracking

**Purpose:** Detailed daily forfait (meal plan) variance reconciliation

### Structure
- **Dimensions:** 44 rows × 92 columns
- **Row 0:** Hotel header: "Hôtel Sheraton"
- **Row 1:** Title: "Vérification di[fference] [forfait]"
- **Row 2:** Column headers:
  - Col A: JOUR (day number)
  - Col B: 12.0 (month identifier)
  - Col C-L: Various forfait types and allocations
    - "Allocation Club"
    - "Facture restaur" (restaurant invoice)
    - "FORFAIT 75$"
    - "coupon restaura"
    - "Forfait 63$"
    - "Forfait BRUNCH"
    - "Forfait 87$"
    - "FORFAIT 90$"
    - "FORFAIT 98$ Wur"
    - "ADPQ ADE29A"
- **Row 3+:** Day numbers (45809.0 onwards = Excel date serial numbers)

### Function
This sheet tracks individual forfait meal plan entries by:
1. Date/day (column A)
2. Type of meal plan (columns C-L with different forfait price points)
3. Allowing manual entry of forfait adjustments per day

---

## 6. FEUIL1 SHEET - Labor Hours Tracking

**Purpose:** Daily labor hours by department/position

### Structure
- **Dimensions:** 40 rows × 98 columns
- **Row 0:** Column headers (labor categories)
  - REC_ADM (Reception Admin)
  - REC_PROM (Reception Promotion)
  - REC_AUDIT (Reception Audit)
  - REC_SERV (Reception Service)
  - REC_PORTIER (Doorman)
  - REC_CLUB (Reception Club)
  - GOUVERNANTE (Housekeeper)
  - FDC (Front Desk Clerk)
  - etc.

- **Row 1:** "JOUR" label with daily hours
- **Row 6:** Second set of headers repeated
- **Rows 7+:** Daily hours by position

### Function
Tracks daily staffing hours for payroll/labor cost analysis. Not directly related to Internet, Sonifi, or Forfait revenue.

---

## 7. KEY FINDINGS & RELATIONSHIPS

### A. Internet and Sonifi Data Flow

```
Sales Journal (POS)
    ↓ (reported by POS system)
    ├─→ Jour sheet, Column AW (Internet revenue)
    └─→ Jour sheet, Column AT (Sonifi revenue)
         ↓
    Internet/Sonifi tabs (reconciliation)
         ├─→ Pull from Jour via formula: =jour!AW{row} and =jour!AT{row}
         ├─→ Compare against LightSpeed CD (charge details)
         ├─→ Calculate variance to identify discrepancies
         └─→ Allow manual adjustments for special items/forfaits
```

### B. Forfait (Meal Plan) Data Flow

```
Sales Journal (POS)
    ├─→ Adjustments section, "FORFAIT" line ($58.65 in test data)
    └─→ Currently EXTRACTED but NOT MAPPED to RJ sheet
         ↓
Jour sheet, Column BF (Difference forfait)
    ├─→ Stores daily forfait variance (negative amounts)
    ├─→ Example: -1181.23, -83.85, -142.81
    └─→ Used in reconciliation against expected vs actual
         ↓
diff_forfait sheet
    └─→ Detailed daily breakdown by meal plan type
        (75$, 63$, 87$, 90$, 98$ Wurst, Brunch, etc.)
```

### C. Comptant (Cash - POS) Extraction

```
Sales Journal (POS)
    └─→ Payment Methods section, "COMPTANT" line
         ↓ (Parser extracts: $737.99)
         ↓
RJ Mapping: recap['comptant_lightspeed']
    └─→ Maps to Recap sheet for cash reconciliation
         (currently shows as part of recap extraction)
```

---

## 8. COLUMN REFERENCE SUMMARY

| Sheet | Column | Index | Header | Purpose | Data Type |
|-------|--------|-------|--------|---------|-----------|
| jour | AT | 45 | Sonifi Film | Hotel entertainment revenue | Numeric (positive) |
| jour | AW | 48 | Internet | Internet sales revenue | Numeric (pos/neg) |
| jour | BF | 57 | Difference forfait | Meal plan variance | Numeric (negative) |
| Internet | J | 9 | R.J | Jour value reference | Formula: =jour!AW{row} |
| Internet | K | 10 | Variance | Discrepancy | Calculated: J - I |
| Sonifi | X | 23 | TOTAL RJ | Jour value reference | Formula: =jour!AT{row} |
| Sonifi | Y | 24 | DIFF | Discrepancy | Calculated: X - W |

---

## 9. FORMULAS NOT DIRECTLY VISIBLE IN XLRD

**Note:** The xlrd library does not expose Excel formulas directly. However, based on the column structure and data patterns:

- **Internet Sheet, Column J:** Should contain `=+jour!AW{row}` to pull Internet values
- **Sonifi Sheet, Column X:** Should contain `=+jour!AT{row}` to pull Sonifi values

These are standard Excel cross-sheet references that calculate cell-by-cell reconciliation.

---

## 10. SALES JOURNAL PARSER - SUMMARY

| Item | Extracted | Mapped to RJ | Notes |
|------|-----------|--------------|-------|
| COMPTANT (Cash) | ✓ Yes | ✓ Yes | Stores as `recap['comptant_lightspeed']` |
| VISA | ✓ Yes | ✓ Yes | Stores as `transelect['visa']` |
| MASTERCARD | ✓ Yes | ✓ Yes | Stores as `transelect['mastercard']` |
| AMEX | ✓ Yes | ✓ Yes | Stores as `transelect['amex']` |
| INTERAC | ✓ Yes | ✓ Yes | Stores as `transelect['interac']` |
| CHAMBRE | ✓ Yes | ✗ No | Not in current RJ mapping |
| CORRECTION | ✓ Yes | ✗ No | Not in current RJ mapping |
| FORFAIT | ✓ Yes | ✗ No | **Extracted but NOT mapped** (in `adjustments['forfait']`) |
| HOTEL PROMOTION | ✓ Yes | ✓ Yes | Stores as `hp['hotel_promotion']` |
| ADMINISTRATION | ✓ Yes | ✗ No | Not in current RJ mapping |

---

## 11. IMPLICATIONS FOR WEBAPP

### For Internet & Sonifi Tabs:
- Values pull from `Jour!AW` and `Jour!AT` respectively
- These should auto-populate when Jour tab is completed
- Variance columns show discrepancies vs LightSpeed CD reports

### For Forfait Handling:
- **Currently:** Forfait extracted from Sales Journal but not auto-filled in RJ
- **Recommendation:** Consider mapping `forfait` from Sales Journal to `Jour!BF` (Difference forfait) column
- **Alternative:** Keep manual entry in diff_forfait sheet for granular daily tracking

### For Comptant Positouch:
- **Comptant is successfully extracted** from Sales Journal
- Should auto-fill in Recap sheet as cash validation
- Matches POS reported cash against manual count

---

## Test Data Files Used

1. **RJ Excel Workbook:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Rj_03-02-2026_pour_test.xls`
2. **Sales Journal:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Sales_Journal_4th_Feb.rtf`

All analysis based on February 3-4, 2026 data from Sheraton Laval.
