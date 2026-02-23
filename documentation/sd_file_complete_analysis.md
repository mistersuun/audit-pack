# SD File - Complete Analysis

**Date:** 2025-12-26
**File:** `SD. Novembre 2025-Copie.xls` (separate Excel file, NOT the SetD sheet in RJ)

---

## OVERVIEW

The **SD file** is a **separate Excel workbook** (not a sheet in the RJ file) that contains the **"SOMMAIRE JOURNALIER DES DÉPÔTS ET DES SURPLUS ET DÉFICIT"** (Daily Summary of Deposits, Surpluses and Deficits).

**Purpose:**
- Track daily deposits by department and employee
- Monitor variances between reported amounts and verified amounts
- Track reimbursements
- Calculate daily totals

**File Structure:**
- **31 sheets** - one for each day of the month
- Each sheet has identical structure with different data

---

## SHEET STRUCTURE

### File Information
- **Sheets:** 31 (named '1', '2', '3', ... '31' representing days of the month)
- **Rows:** 44 per sheet
- **Columns:** 7 (A through G)

### Header Section (Rows 1-7)

| Row | Column A | Column B | Purpose |
|-----|----------|----------|---------|
| 1 | (empty) | (empty) | Spacer |
| 2 | SHERATON - LAVAL | | Hotel name |
| 3 | SOMMAIRE JOURNALIER DES DÉPÔTS ET DES SURPLUS ET DÉFICIT | | Document title |
| 4 | (empty) | (empty) | Spacer |
| 5 | DATE | Excel date value (e.g., 45962.0) | Date of the summary |
| 6 | (empty) | (empty) | Spacer |
| 7 | **DÉPARTEMENT** | **NOM LETTRES MOULÉES** | **Column Headers** |

**Row 7 - Column Headers:**
- **A:** DÉPARTEMENT
- **B:** NOM LETTRES MOULÉES
- **C:** CDN /US
- **D:** MONTANT
- **E:** MONTANT VÉRIFIÉ
- **F:** REMBOURSEMENT
- **G:** VARIANCE

### Data Section (Rows 8-38)

**Department Groupings:**
Each department has multiple rows allocated:

1. **RÉCEPTION** (Rows 9-16): 8 rows
2. **SPESA** (Rows 17-20): 4 rows
3. **RESTAURANT** (Rows 21-28): 8 rows
4. **BANQUET** (Rows 29-33): 5 rows
5. **COMPTABILITÉ** (Rows 34-37): 4 rows
6. **Row 38:** (empty spacer)

### Total Row (Row 39)

| Column | Content |
|--------|---------|
| A | TOTAL |
| B | (empty) |
| C | (empty) |
| D | Sum of all MONTANT |
| E | Sum of all MONTANT VÉRIFIÉ |
| F | Sum of all REMBOURSEMENT |
| G | Sum of all VARIANCE |

### Signature Section (Rows 40-44)

| Row | Column B | Column D |
|-----|----------|----------|
| 42 | SIGNATURE AUDITEUR DE NUIT | Name (e.g., "KHALIL M") |
| 44 | SIGNATURE COMPTABILITÉ | (blank) |

---

## COLUMN DEFINITIONS

### A: DÉPARTEMENT
**Type:** Text (from fixed list)
**Values:**
- RÉCEPTION
- SPESA
- RESTAURANT
- BANQUET
- COMPTABILITÉ

**Purpose:** Categorize entries by department

---

### B: NOM LETTRES MOULÉES
**Type:** Text
**Format:** Uppercase, full name or abbreviated

**Purpose:** Employee name in capital letters

**Common Names (from example data):**
- KHALIL M
- MANON RINGROSE
- DRAGANA R
- ISABELLE LECLAIR
- MIXO 2
- CAROLINE FORGET
- RAFFI OYAN
- CUONG TRAN
- JULIE
- STEPHANE LATULIPPE

**Personnel Source:**
Names can come from the 135 personnel in SetD sheet (RJ file), including:
- Martine Breton
- JEAN PHILIPPE
- Tristan Tremblay
- Mandy Le
- Frederic Dupont
- Florence Roy
- Marie Carlesso
- Patrick Caron
- KARL LECLERC
- Stéphane Latulippe
- natalie rousseau
- DAVID GIORGI
- YOUSSIF GANNI
- And 33 more...

---

### C: CDN /US
**Type:** Select (dropdown)
**Values:**
- **CDN** (Canadian Dollar) - default and most common
- **US** (US Dollar) - less common

**Purpose:** Specify currency type for the entry

**Note:** In practice, almost all entries are **CDN**

---

### D: MONTANT
**Type:** Number (decimal, 2 places)
**Format:** Currency (positive or negative)

**Purpose:** The amount reported/declared by the employee

**Can be:**
- **Positive:** Deposit amount
- **Negative:** Deficit/shortage (represented as negative values)

**Examples:**
```
$106.23    (positive deposit)
$214.64    (positive deposit)
-$740.72   (negative - deficit)
-$26.87    (negative - shortage)
-$447.80   (negative - deficit)
```

---

### E: MONTANT VÉRIFIÉ
**Type:** Number (decimal, 2 places)
**Format:** Currency (positive)
**Style:** Highlighted background (yellow #fff3cd)

**Purpose:** The verified/audited amount after night audit review

**Calculation:** Not automatically calculated - **manually entered** by auditor

**Relationship to MONTANT:**
- Should match MONTANT if everything is correct
- Small differences create variance in Column G

**Examples:**
```
$106.25    (verified amount, $0.02 variance from $106.23 montant)
$136.35    (verified amount, -$0.01 variance from $136.36 montant)
$214.70    (verified amount, $0.06 variance from $214.64 montant)
```

**Visual:** Yellow background to highlight importance

---

### F: REMBOURSEMENT
**Type:** Number (decimal, 2 places)
**Format:** Currency (positive)

**Purpose:** Reimbursement amounts paid back to employees

**When Used:**
- Employee has a deficit (negative MONTANT)
- Company reimburses the employee for the shortage

**Examples:**
```
$23.87     (reimbursement for -$26.87 montant)
$292.45    (reimbursement for -$292.45 montant)
```

**Calculation:** Usually matches negative MONTANT amounts (as positive)

---

### G: VARIANCE
**Type:** Number (decimal, 2 places)
**Format:** Currency (positive or negative)
**Style:** Read-only, calculated automatically

**Purpose:** Show difference between reported and verified amounts

**Formula:**
```
VARIANCE = MONTANT VÉRIFIÉ - MONTANT + REMBOURSEMENT
```

**Or more specifically:**
```javascript
variance = (montant_verifie || 0) - (montant || 0) + (remboursement || 0)
```

**Interpretation:**
- **0:** Perfect match ✅
- **Positive:** More verified than reported
- **Negative:** Less verified than reported (deficit)

**Examples:**
```
Row 9:  MONTANT: $3.00,      VÉRIFIÉ: $0.00,    REMB: $0.00,    VARIANCE: -$3.00
Row 17: MONTANT: $106.23,    VÉRIFIÉ: $106.25,  REMB: $0.00,    VARIANCE: $0.02
Row 18: MONTANT: $136.36,    VÉRIFIÉ: $136.35,  REMB: $0.00,    VARIANCE: -$0.01
Row 22: MONTANT: -$740.72,   VÉRIFIÉ: $0.00,    REMB: $0.00,    VARIANCE: $740.72
Row 23: MONTANT: -$26.87,    VÉRIFIÉ: $0.00,    REMB: $23.87,   VARIANCE: $3.00
Row 24: MONTANT: -$292.45,   VÉRIFIÉ: $0.00,    REMB: $292.45,  VARIANCE: $0.00
```

**Visual:** Grayed out (read-only) since it's auto-calculated

---

## EXAMPLE DATA (Day 1 - November 2025)

### RÉCEPTION Department
```
Row 9:  RÉCEPTION | KHALIL M | CDN | $3.00 | $0.00 | $0.00 | -$3.00
Rows 10-16: Empty RÉCEPTION rows
```

### SPESA Department
```
Row 17: SPESA | MANON RINGROSE | CDN | $106.23 | $106.25 | $0.00 | $0.02
Row 18: SPESA | DRAGANA R      | CDN | $136.36 | $136.35 | $0.00 | -$0.01
Rows 19-20: Empty SPESA rows
```

### RESTAURANT Department
```
Row 21: RESTAURANT | ISABELLE LECLAIR | CDN | $214.64  | $214.70 | $0.00   | $0.06
Row 22: RESTAURANT | MIXO 2           | CDN | -$740.72 | $0.00   | $0.00   | $740.72
Row 23: RESTAURANT | CAROLINE FORGET  | CDN | -$26.87  | $0.00   | $23.87  | $3.00
Row 24: RESTAURANT | RAFFI OYAN       | CDN | -$292.45 | $0.00   | $292.45 | $0.00
Row 25: RESTAURANT | CUONG TRAN       | CDN | -$447.80 | $0.00   | $0.00   | $447.80
Row 26: RESTAURANT | JULIE            | CDN | $544.68  | $0.00   | $0.00   | -$544.68
Rows 27-28: Empty RESTAURANT rows
```

### BANQUET Department
```
Row 29: BANQUET | STEPHANE LATULIPPE | CDN | $40.42 | $40.50 | $0.00 | $0.08
Rows 30-33: Empty BANQUET rows
```

### COMPTABILITÉ Department
```
Rows 34-37: Empty COMPTABILITÉ rows
```

### TOTALS (Row 39)
```
TOTAL | | | -$462.51 | $497.80 | $316.32 | $643.99
```

### Signatures
```
Row 42: SIGNATURE AUDITEUR DE NUIT | KHALIL M
Row 44: SIGNATURE COMPTABILITÉ     | (blank)
```

---

## UI IMPLEMENTATION

### Current SD Tab Features

1. **Dynamic Row Management**
   - Add unlimited SD rows
   - Delete individual rows
   - Auto-calculate totals

2. **Department Dropdown**
   - Fixed list: RÉCEPTION, SPESA, RESTAURANT, BANQUET, COMPTABILITÉ
   - Pre-selected values

3. **Personnel Name Input - ENHANCED**
   - **NEW:** Autocomplete with 46 names from SetD
   - Type to search and filter names
   - HTML5 `<datalist>` for native autocomplete
   - Can still manually enter custom names

4. **Currency Selection**
   - CDN (default)
   - US

5. **Amount Fields**
   - MONTANT (can be positive or negative)
   - MONTANT VÉRIFIÉ (highlighted in yellow)
   - REMBOURSEMENT

6. **Auto-Calculated Variance**
   - Read-only field
   - Formula: `(montant_vérifié || 0) - (montant || 0) + (remboursement || 0)`

7. **Total Row**
   - Auto-sums all columns
   - Updates in real-time

---

## WORKFLOW - NIGHT AUDITOR

**Daily Workflow for SD Entry:**

### Step 1: Select Day
- Open SD file for current day (e.g., sheet '23' for day 23)

### Step 2: Enter Deposits by Department

**For each department employee with a deposit:**

1. **Select Department:** Choose from dropdown (RÉCEPTION, SPESA, RESTAURANT, BANQUET, COMPTABILITÉ)
2. **Enter Name:** Type employee name (autocomplete will suggest from 46 names)
3. **Currency:** Leave as CDN (or select US if applicable)
4. **Enter MONTANT:** Enter declared amount (positive for deposits, negative for deficits)
5. **Enter MONTANT VÉRIFIÉ:** Enter verified amount after audit
6. **Enter REMBOURSEMENT:** If applicable (usually for negative amounts)
7. **VARIANCE:** Automatically calculated

### Step 3: Review Totals
- Check total row at bottom
- **MONTANT VÉRIFIÉ Total** should match deposits
- Review variances

### Step 4: Sign
- Name appears in signature row (Row 42)

### Step 5: Save
- Save SD file
- **IMPORTANT:** MONTANT VÉRIFIÉ total may link to other sheets (like Recap "Dépôt Canadien")

---

## INTEGRATION WITH OTHER SHEETS

### Connection to Recap Sheet (RJ File)

From earlier analysis:
```
Recap Row 22: Dépôt Canadien (B22, C22) - READ ONLY
```

The note in the UI says:
> "Le MONTANT VÉRIFIÉ total sera automatiquement transféré dans le Recap 'Dépôt Canadien'"

**This means:**
- SD total MONTANT VÉRIFIÉ → Recap B22/C22 (Dépôt Canadien)
- This is likely a formula or backend sync
- User doesn't manually enter Dépôt Canadien in Recap (it's read-only)

### Connection to Depot Sheet

The SD data may also feed into the "Depot" (Dépôt) sheet which tracks Canadian account deposits over 7 days.

---

## BACKEND REQUIREMENTS

### Data Structure

```python
sd_entry = {
    'day': 1-31,                    # Which day sheet (1-31)
    'departement': 'RÉCEPTION',     # Department name
    'nom': 'KHALIL M',              # Employee name
    'devise': 'CDN',                # Currency
    'montant': 3.00,                # Declared amount
    'montant_verifie': 0.00,        # Verified amount
    'remboursement': 0.00,          # Reimbursement
    'variance': -3.00               # Calculated variance
}
```

### Cell Mapping

**For day N (sheet '1' through '31'):**

**Data rows start at row 9 (first RÉCEPTION entry)**

```python
def get_sd_row(department, index):
    """
    Get Excel row for SD entry based on department and index.

    Department ranges:
    - RÉCEPTION: rows 9-16 (8 rows)
    - SPESA: rows 17-20 (4 rows)
    - RESTAURANT: rows 21-28 (8 rows)
    - BANQUET: rows 29-33 (5 rows)
    - COMPTABILITÉ: rows 34-37 (4 rows)
    """
    dept_ranges = {
        'RÉCEPTION': (9, 16),
        'SPESA': (17, 20),
        'RESTAURANT': (21, 28),
        'BANQUET': (29, 33),
        'COMPTABILITÉ': (34, 37)
    }

    start_row, end_row = dept_ranges.get(department, (9, 16))
    row = start_row + index

    if row > end_row:
        raise ValueError(f"Too many entries for {department}")

    return row
```

**Column mapping:**
```python
SD_COLUMNS = {
    'departement': 'A',
    'nom': 'B',
    'devise': 'C',
    'montant': 'D',
    'montant_verifie': 'E',
    'remboursement': 'F',
    'variance': 'G'
}
```

**Write SD entry:**
```python
def write_sd_entry(day, department, index, entry_data):
    """
    Write SD entry to specific day sheet.

    Args:
        day (int): Day of month (1-31)
        department (str): Department name
        index (int): Entry index within department (0-based)
        entry_data (dict): Entry data
    """
    sheet_name = str(day)  # '1', '2', ..., '31'
    row = get_sd_row(department, index)

    # Write each field
    write_excel_cell(sheet_name, f"A{row}", entry_data['departement'])
    write_excel_cell(sheet_name, f"B{row}", entry_data['nom'])
    write_excel_cell(sheet_name, f"C{row}", entry_data['devise'])
    write_excel_cell(sheet_name, f"D{row}", entry_data['montant'])
    write_excel_cell(sheet_name, f"E{row}", entry_data['montant_verifie'])
    write_excel_cell(sheet_name, f"F{row}", entry_data['remboursement'])
    # Variance (G) is auto-calculated by Excel formula
```

**Read SD totals:**
```python
def read_sd_totals(day):
    """
    Read SD totals from row 39.

    Args:
        day (int): Day of month (1-31)

    Returns:
        dict: Total amounts
    """
    sheet_name = str(day)

    return {
        'total_montant': read_excel_cell(sheet_name, 'D39'),
        'total_verifie': read_excel_cell(sheet_name, 'E39'),
        'total_remboursement': read_excel_cell(sheet_name, 'F39'),
        'total_variance': read_excel_cell(sheet_name, 'G39')
    }
```

---

## VALIDATION RULES

### Required Fields
- **Département:** Must be selected from dropdown
- **Nom:** Should be entered (can be autocompleted or manual)
- **Devise:** Defaults to CDN

### Optional Fields
- **Montant:** Enter if there's an amount
- **Montant Vérifié:** Enter after verification
- **Remboursement:** Only if applicable

### Calculated Fields
- **Variance:** Auto-calculated, read-only

### Business Rules
1. **Each department has limited rows:**
   - RÉCEPTION: max 8 entries
   - SPESA: max 4 entries
   - RESTAURANT: max 8 entries
   - BANQUET: max 5 entries
   - COMPTABILITÉ: max 4 entries

2. **Variance should be small:** Large variances indicate problems

3. **Negative MONTANT usually requires REMBOURSEMENT**

4. **Total MONTANT VÉRIFIÉ** syncs to Recap "Dépôt Canadien"

---

## COMPARISON: SD FILE vs SETD SHEET

| Feature | SD File | SetD Sheet |
|---------|---------|------------|
| **Location** | Separate Excel file | Sheet in RJ Excel file |
| **Sheets** | 31 (one per day) | 1 (all days in rows) |
| **Purpose** | Daily deposit summary by employee | Monthly ledger with RJ totals + personnel accounts |
| **Structure** | Rows grouped by department | Days in rows, personnel in columns |
| **Personnel** | Any employee (typed or selected) | Fixed 46 columns |
| **Columns** | 7 (Dept, Name, Currency, amounts) | 158 (Day + 135 personnel + accounts) |
| **Primary Use** | Track daily deposits & variances | Track RJ balance + personnel balances |
| **Link to RJ** | MONTANT VÉRIFIÉ → Recap Dépôt Canadien | Column B (RJ) links to Recap B23 |

---

## PERSONNEL AUTOCOMPLETE IMPLEMENTATION

### HTML5 Datalist (Current Implementation)

**Advantages:**
- Native browser support
- Simple implementation
- No extra JavaScript needed
- Works across all browsers

**Code:**
```html
<!-- Input field with list attribute -->
<input type="text"
       class="excel-input sd-nom"
       placeholder="Rechercher nom..."
       list="sd-personnel-list"
       autocomplete="off">

<!-- Datalist with 46 names -->
<datalist id="sd-personnel-list">
  <option value="Martine Breton">
  <option value="JEAN PHILIPPE">
  <option value="Tristan Tremblay">
  <!-- ... 43 more names ... -->
</datalist>
```

**User Experience:**
1. User clicks in name field
2. Types any part of a name (e.g., "steph")
3. Browser shows matching options:
   - "Stéphane Latulippe"
   - "Stephane Bernachez"
4. User clicks or arrows to select
5. Name is filled in

**Fallback:**
- User can still type any custom name if not in list

---

## SUMMARY

**SD File Purpose:**
- Daily deposit tracking by department and employee
- Variance monitoring between declared and verified amounts
- Reimbursement tracking
- Integration with Recap (Dépôt Canadien)

**Key Features:**
1. **31 daily sheets** (one per day of month)
2. **5 departments** (RÉCEPTION, SPESA, RESTAURANT, BANQUET, COMPTABILITÉ)
3. **135 personnel names** available for autocomplete (from SetD)
4. **Auto-calculated variance** column
5. **Total row** with sums
6. **Integration** with Recap sheet

**Current UI Status:**
- ✅ Department dropdown
- ✅ **Personnel autocomplete with 46 names** (NEW!)
- ✅ Currency selection
- ✅ Amount entry fields
- ✅ Auto-calculated variance
- ✅ Dynamic row management
- ✅ Total calculations
- ⚠️ Backend integration pending

**Next Steps:**
1. Backend route to save SD data
2. Excel write integration for SD file
3. Link MONTANT VÉRIFIÉ total to Recap Dépôt Canadien
4. Day selector if multiple days need to be edited

---

**Document Status:** Complete
**Implementation Status:** UI enhanced with autocomplete, backend pending
