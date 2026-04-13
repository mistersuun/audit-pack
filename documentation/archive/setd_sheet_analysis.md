# SetD Sheet - Complete Analysis

**Date:** 2025-12-26
**Purpose:** Understanding SetD structure for UI implementation

---

## OVERVIEW

The **SetD (SD)** sheet is a **monthly ledger** that tracks:
- **RJ (Revenue Journal) totals** for each day of the month (Column B)
- **Individual personnel account balances** (Columns C onwards)
- **Departmental accounts** (Accounting, Banquet, etc.)

**CRITICAL CONNECTION:**
The I10 cell in Recap sheet contains: `=B23-'file:///K:/SD 2025/[SD Decembre.xls]23'!$E$39`

This means:
- Recap B23 (Balance Finale) should match SetD day total
- I10 verifies agreement between RJ and SetD
- **I10 = 0.00** means RJ and SD are balanced

---

## SHEET STRUCTURE

### Dimensions
- **Rows:** 44
- **Columns:** 158 (A to EX)
- **Active data area:** Rows 1-40, Columns A-AX (first ~50 columns)

### Row Structure

| Row | Purpose | Description |
|-----|---------|-------------|
| **1** | Month/Year | Excel date value (46014.0 = Dec 2025), section headers |
| **2** | First Names | Personnel first names across columns |
| **3** | Last Names | Personnel last names across columns |
| **4** | Account Codes | GL account numbers (2-946000, 2-101100, 2-101701, 2-101704, etc.) |
| **5-35** | Days 1-31 | Daily transaction amounts for each person/account |
| **36** | Total | Sum of all days for each column |
| **37** | Reel | Real/actual amounts |
| **38+** | Summary | Account reconciliation rows |

### Column Structure

| Column | Name | Type | Purpose |
|--------|------|------|---------|
| **A** | Jour (Day) | Label | Day numbers 1-31, then "total", "Reel", account codes |
| **B** | RJ | **DATA ENTRY** | **Revenue Journal total for each day** |
| **C-AX** | Personnel Names | DATA ENTRY | Individual staff account amounts (46 people total) |

---

## COLUMN B - THE RJ LINK

**THIS IS THE MOST IMPORTANT COLUMN!**

```
Column B = RJ (Revenue Journal)
```

**Daily Workflow:**
1. User completes Recap sheet
2. Recap B23 (Balance Finale) is calculated
3. User enters **same value** in SetD Column B for current day
4. I10 in Recap verifies: B23 - SetD_value = 0.00 (should balance)

**Example:**
```
December 23, 2025:
- Recap B23 (Balance Finale): $1,234.56
- SetD Row 28 (day 23), Column B: $1,234.56  ← User enters this
- Recap I10: $1,234.56 - $1,234.56 = $0.00 ✅ BALANCED
```

**SetD Column B Values (from example file):**
```
Day 1:  $32.40
Day 2:  -$33.91
Day 3:  $141.41
Day 4:  $1,735.79
Day 5:  $6,170.84
Day 6:  $6,819.07
...
Day 23: $0.00
...
Total:  $34,299.06
```

---

## ALL PERSONNEL COLUMNS (C through AX)

SetD contains **135 personnel columns** representing ALL hotel staff across all departments:

### Special Accounts (Non-Personnel)
- **C: Martine Breton** (Account: 2-946000)
- **E: Petite Caisse** (Petty Cash) (Account: 2-946000)
- **F: Conc. Banc.** (Bank Reconciliation) (Account: 2-101701)
- **G: Corr. Mois suivant** (Next Month Correction) (Account: 2-101704)

### Personnel Accounts (Sample)

| Column | Full Name | First Name | Last Name | Account Code |
|--------|-----------|------------|-----------|--------------|
| H | JEAN PHILIPPE | JEAN | PHILIPPE | 2-101704 |
| I | Tristan Tremblay | Tristan | Tremblay | 2-101704 |
| J | Mandy Le | Mandy | Le | 2-101704 |
| K | Frederic Dupont | Frederic | Dupont | 2-101701 |
| L | Florence Roy | Florence | Roy | - |
| M | Marie Carlesso | Marie | Carlesso | 2-101704 |
| N | Patrick Caron | Patrick | Caron | 2-101704 |
| O | KARL LECLERC | KARL | LECLERC | 2-101704 |
| P | Stéphane Latulippe | Stéphane | Latulippe | 2-101704 |
| Q | natalie rousseau | natalie | rousseau | 2-101704 |
| ... | ... | ... | ... | ... |
| AX | spiro Katsenis | spiro | Katsenis | 2-101704 |

**Total: 135 personnel columns**

---

## COMPARISON: SetD vs DueBack Personnel

**SetD Personnel: 46 people (ALL departments)**
- Receptionists
- Accounting staff (Comptabilité)
- Banquet staff
- Bar/Restaurant staff (Mixologues)
- Management
- Housekeeping
- Sales
- All hotel departments

**DueBack Personnel: 23 people (RECEPTIONISTS ONLY)**
- Debby Araujo
- Josée Latulippe
- Isabelle Caron
- Laeticia Nader
- Rose-Delande Mompremier
- zaneta oppong
- ZAYEN SEDDIK
- Tavarez Kimberly
- BACHIRI AYA
- Scarpa Leo
- THANEEKAN THANKARAJAH
- PIERRE CINDY
- Cabrera Manolo
- KHALIL MOUATARIF
- VALERIE KRAY
- SAY NITHYA
- Kelly DAMAL
- LEVESQUE MAUDE
- ARHANTOU OLGA
- Pierre Sylvie
- Uwimana Emery
- Ramzi Ben mansour
- KASPERIAN ANNIE-LIS

**⚠️ IMPORTANT:** SetD and DueBack have **DIFFERENT** personnel lists!
- SetD = ALL hotel staff (46 people)
- DueBack = RECEPTION staff only (23 people)
- **NO name overlap** between the two sheets

---

## DATA ENTRY SCENARIOS

### Scenario 1: Daily RJ Entry (PRIMARY USE CASE)

**User workflow for day 23:**
1. Complete Recap sheet → B23 (Balance Finale) = $1,175.60
2. Go to SetD tab
3. Select Day 23
4. Enter $1,175.60 in Column B (RJ)
5. Return to Recap → I10 shows $0.00 ✅ (balanced)

### Scenario 2: Personnel Account Adjustment

**User needs to record staff advance/balance:**
1. Select day (e.g., Day 15)
2. Select personnel (e.g., "Tristan Tremblay", Column I)
3. Enter amount: $2,135.00
4. Amount appears in Row 19 (Day 15), Column I

**From example file:**
```
Row 19 (Day 15):
- Column A: 15 (day)
- Column B: $1,683.30 (RJ total)
- Column I: $2,135.00 (Tristan Tremblay advance)
```

### Scenario 3: Multiple Personnel Same Day

**Day 10 example:**
```
Row 14 (Day 10):
- Column A: 10
- Column B: $373.26 (RJ total)
- Column K: $6.22 (Frederic Dupont)
- Column O: $977.74 (KARL LECLERC)
```

Multiple staff can have entries on the same day.

---

## UI IMPLEMENTATION REQUIREMENTS

### 1. Day Selection
```html
<select id="setd-day-selector">
  <option value="">-- Sélectionner jour --</option>
  <option value="1">Jour 1</option>
  <option value="2">Jour 2</option>
  ...
  <option value="31">Jour 31</option>
</select>
```

### 2. RJ Entry Field (Column B) - PRIMARY
```html
<div class="setd-rj-entry">
  <label>RJ (Revenue Journal)</label>
  <input type="number"
         step="0.01"
         id="setd-rj-value"
         data-column="B"
         placeholder="0.00">
  <span class="helper-text">De Recap B23 (Balance Finale)</span>
</div>
```

### 3. Personnel Selection with Search (Columns C-AX)

**Similar to DueBack implementation:**
```html
<div class="setd-personnel-search">
  <label>Personnel (Optionnel)</label>
  <input type="text"
         id="setd-personnel-search"
         placeholder="Rechercher personnel..."
         autocomplete="off">

  <div id="setd-personnel-dropdown" class="dropdown-menu">
    <!-- Dynamically populated with 46 names -->
  </div>
</div>

<div id="setd-personnel-amount" style="display:none;">
  <label>Montant pour <span id="selected-personnel-name"></span></label>
  <input type="number"
         step="0.01"
         id="setd-personnel-value"
         data-column=""
         placeholder="0.00">
</div>
```

**Search functionality:**
- Type to filter 135 personnel names
- Click to select
- Enter amount for selected personnel
- Can add multiple personnel for same day

### 4. Visual Layout

```
┌─────────────────────────────────────────────────────────┐
│ SetD - Sommaire Dépôt (Monthly Ledger)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Jour: [Dropdown: 1-31]                                 │
│                                                         │
│ ┌───────────────────────────────────────────────────┐  │
│ │ RJ (Revenue Journal) - REQUIS                     │  │
│ │ [Input: $______]                                   │  │
│ │ ℹ️ Entrer le montant de Recap B23 (Balance Finale)│  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
│ ┌───────────────────────────────────────────────────┐  │
│ │ Personnel (Optionnel)                              │  │
│ │ [Search: Rechercher personnel...]                  │  │
│ │                                                     │  │
│ │ [Dropdown with 46 names appears when typing]       │  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
│ [Ajouter Entrée] [Annuler]                            │
│                                                         │
│ ┌───────────────────────────────────────────────────┐  │
│ │ Entrées pour Jour 23:                              │  │
│ │ • RJ: $1,234.56                                    │  │
│ │ • Tristan Tremblay: $2,135.00                      │  │
│ │ • KARL LECLERC: $977.74                            │  │
│ └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## CELL MAPPING FOR BACKEND

### Dynamic Cell Calculation

**For a given day and column:**
```python
def get_setd_cell(day, column_letter):
    """
    Get Excel cell reference for SetD entry.

    Args:
        day (int): Day of month (1-31)
        column_letter (str): Column letter ('B' for RJ, 'C'-'AX' for personnel)

    Returns:
        str: Excel cell reference (e.g., 'B5', 'I19', 'O14')
    """
    row = 4 + day  # Row 5 = Day 1, Row 6 = Day 2, ..., Row 35 = Day 31
    return f"{column_letter}{row}"

# Examples:
# Day 1, RJ (Column B): get_setd_cell(1, 'B') → 'B5'
# Day 23, RJ (Column B): get_setd_cell(23, 'B') → 'B27'
# Day 15, Tristan Tremblay (Column I): get_setd_cell(15, 'I') → 'I19'
# Day 10, KARL LECLERC (Column O): get_setd_cell(10, 'O') → 'O14'
```

### Personnel Column Mapping

```python
SETD_PERSONNEL_COLUMNS = {
    'Martine Breton': 'C',
    'Petite Caisse': 'E',
    'Conc. Banc.': 'F',
    'Corr. Mois suivant': 'G',
    'JEAN PHILIPPE': 'H',
    'Tristan Tremblay': 'I',
    'Mandy Le': 'J',
    'Frederic Dupont': 'K',
    'Florence Roy': 'L',
    'Marie Carlesso': 'M',
    'Patrick Caron': 'N',
    'KARL LECLERC': 'O',
    'Stéphane Latulippe': 'P',
    'natalie rousseau': 'Q',
    'DAVID GIORGI': 'R',
    'YOUSSIF GANNI': 'S',
    'MYRLENE BELIVEAU': 'T',
    'EMMANUELLE LUSSIER': 'U',
    'DANIELLE BELANGER': 'V',
    'VALERIE GUERIN': 'W',
    'Youri Georges': 'X',
    'Alexandre Thifault': 'Y',
    'Julie Dagenais': 'Z',
    'PATRICK MARTEL': 'AA',
    'Nelson Dacosta': 'AB',
    'NAOMIE COLIN': 'AC',
    'SOPHIE CHIARUCCI': 'AD',
    'CHRISTOS MORENTZOS': 'AE',
    'WOODS John': 'AF',
    'MARCO Sabourin': 'AG',
    'sachetti francois': 'AH',
    'caouette Phillipe': 'AI',
    'Caron Patrick': 'AJ',
    'MIXOLOGUE': 'AK',
    'GIOVANNI TOMANELLI': 'AL',
    'Mathieu Guerit': 'AN',
    'Marie Eve': 'AO',
    'CARL Tourangeau': 'AP',
    'MAUDE GAUTHIER': 'AQ',
    'Stephane Bernachez': 'AR',
    'Jonathan Samedy': 'AS',
    'NICOLAS Bernatchez': 'AT',
    'JULIEN BAZAGLE': 'AU',
    'Panayota Lappas': 'AV',
    'PLINIO TESTA Campos': 'AW',
    'spiro Katsenis': 'AX',
}
```

---

## TYPICAL NIGHT AUDIT WORKFLOW

**Step-by-step for completing RJ for December 23:**

1. **Complete all RJ tabs:**
   - Controle ✅
   - Recap ✅ → B23 (Balance Finale) = $1,175.60
   - Transelect ✅
   - GEAC_UX ✅
   - DueBack ✅

2. **Go to SetD tab:**
   - Select "Jour 23"
   - Enter RJ: $1,175.60 (from Recap B23)
   - Optionally add personnel amounts if needed
   - Save

3. **Verify balance:**
   - Return to Recap tab
   - Check I10 indicator at top
   - **I10 = $0.00** ✅ GREEN → RJ and SetD are balanced!
   - **I10 ≠ $0.00** ❌ RED → Mismatch! Check entries

---

## BACKEND REQUIREMENTS

### Reading SetD Data
```python
# Read RJ value for day 23
cell_ref = get_setd_cell(23, 'B')  # Returns 'B27'
rj_value = read_excel_cell('SetD', cell_ref)  # Returns float

# Read personnel value for day 15, Tristan Tremblay
cell_ref = get_setd_cell(15, 'I')  # Returns 'I19'
personnel_value = read_excel_cell('SetD', cell_ref)  # Returns 2135.0
```

### Writing SetD Data
```python
# Write RJ value for day 23
cell_ref = get_setd_cell(23, 'B')  # 'B27'
write_excel_cell('SetD', cell_ref, 1175.60)

# Write personnel value for day 10, KARL LECLERC
cell_ref = get_setd_cell(10, 'O')  # 'O14'
write_excel_cell('SetD', cell_ref, 977.74)
```

### Updating I10 Balance Indicator
```python
# After saving SetD data, read I10 from Recap
i10_value = read_excel_cell('Recap', 'I10')

# Send to frontend to update balance indicator
return jsonify({
    'success': True,
    'i10_balance': i10_value,
    'message': 'SetD mis à jour'
})
```

---

## VALIDATION RULES

### Required Fields
- **Day:** Must be selected (1-31)
- **RJ (Column B):** Must be entered (primary purpose of SetD)

### Optional Fields
- **Personnel amounts:** Only enter if needed for staff advances/balances

### Balance Check
- **I10 = 0.00:** ✅ RJ and SetD are in agreement
- **I10 ≠ 0.00:** ⚠️ Mismatch detected - check Recap B23 vs SetD Column B

---

## SUMMARY

**SetD Purpose:**
- Monthly ledger tracking daily RJ totals and personnel accounts
- **Primary use:** Record RJ (Recap B23 Balance Finale) for each day in Column B
- **Secondary use:** Record personnel advances/balances if needed

**Key Points:**
1. SetD has 135 personnel columns (ALL hotel staff, not just reception)
2. Column B (RJ) is the critical link to Recap sheet
3. I10 in Recap verifies RJ and SetD are balanced (should = $0.00)
4. Days 1-31 = Rows 5-35
5. Search dropdown needed for easy personnel selection (46 names)

**Implementation Priority:**
1. ✅ Day selector (1-31)
2. ✅ RJ input field (Column B) - **MOST IMPORTANT**
3. ✅ Personnel search dropdown (46 names)
4. ✅ Personnel amount input (optional)
5. ✅ Multi-entry support (multiple personnel per day)
6. ✅ Backend cell mapping with `get_setd_cell(day, column)`

---

**Document Status:** Complete
**Ready for Implementation:** Yes
**Next Step:** Build SetD UI tab with search functionality
