# Current RJ File Structure Analysis

**Date:** December 25, 2025
**Source File:** `Rj 12-23-2025-Copie.xls`
**Total Sheets:** 38

---

## DUBACK# Sheet - Current Active Structure

### Dimensions
- **67 rows × 26 columns**
- **23 receptionists** (columns 2-24)
- Column 0: DATE (day 1-31)
- Column 1: R/J (previous total)
- Column 25: Total

### Current Receptionists (23 total)

| Col | Last Name | First Name |
|-----|-----------|------------|
| 2 | Araujo | Debby |
| 3 | Latulippe | Josée |
| 4 | Caron | Isabelle |
| 5 | Nader | Laeticia |
| 6 | Mompremier | Rose-Delande |
| 7 | oppong | zaneta |
| 8 | SEDDIK | ZAYEN |
| 9 | Kimberly | Tavarez |
| 10 | AYA | BACHIRI |
| 11 | Leo | Scarpa |
| 12 | THANKARAJAH | THANEEKAN |
| 13 | CINDY | PIERRE |
| 14 | Manolo | Cabrera |
| 15 | MOUATARIF | KHALIL |
| 16 | KRAY | VALERIE |
| 17 | NITHYA | SAY |
| 18 | DAMAL | Kelly |
| 19 | MAUDE | LEVESQUE |
| 20 | OLGA | ARHANTOU |
| 21 | Sylvie | Pierre |
| 22 | Emery | Uwimana |
| 23 | Ben mansour | Ramzi |
| 24 | ANNIE-LIS | KASPERIAN |

### Daily Entry Pattern

Each day uses **TWO rows**:

**Example - Day 1 (Dec 23, 2025):**

```
Row 4: ['1', '-675.18', '', '', '0', '', '', '', '', '', '', '', '', '', '', '', '-697.88', '', '', '', '', '', '', '', '', '0']
       ↑    ↑           Previous DueBack being cleared (Caron: 0, KRAY: -697.88)

Row 5: ['1', '', '', '', '419.82', '', '', '', '', '', '', '18.40', '934.84', '', '', '', '', '', '', '', '']
       ↑    ↑  New DueBack amounts (Caron: 419.82, MOUATARIF: 18.40, KRAY: 934.84)
```

**Row Pattern:**
- **Even rows (4, 6, 8, ...):** Previous DueBack corrections/clearing
  - Often negative values
  - Column 1 shows previous total balance
- **Odd rows (5, 7, 9, ...):** New DueBack amounts
  - Positive values for new due back
  - Column 1 is empty

**Example - Day 11:**
```
Row 24: ['11', '-820.87', '-273.49', '', '-466.09', '', '', '', '', '', '', '', '', '', '', '-611.19', '-262.24', '', '', '', '', '', '', '', '', '0']
        ↑     ↑         Clearing: Araujo: -273.49, Caron: -466.09, MOUATARIF: -611.19, KRAY: -262.24

Row 25: ['11', '', '630.88', '', '513.41', '', '', '', '', '', '', '', '', '', '', '534.50', '755.09', '', '', '', '', '', '', '', '', '']
        ↑     ↑   New: Araujo: 630.88, Caron: 513.41, MOUATARIF: 534.50, KRAY: 755.09
```

### Bottom Row (Row 66)
Contains monthly totals for each receptionist

---

## Other Key Sheets

### Sheet 27: Recap (26 rows × 14 cols)
Daily cash reconciliation summary with:
- Cash readings (LightSpeed, Positouch)
- Checks
- Reimbursements
- Due Back totals (links to DUBACK#)
- Deposit calculations

### Sheet 25: transelect (40 rows × 32 cols)
Credit card terminal reconciliation:
- Restaurant/Bar terminals section
- Reception/Rooms terminals section
- Card type breakdowns (DEBIT, VISA, MASTER, DISCOVER, AMEX)

### Sheet 28: geac_ux (58 rows × 11 cols)
GEAC/UX system reconciliation:
- Daily Cash Out vs Daily Revenue
- Variance calculations

### Sheet 12: depot (54 rows × 16 cols)
Bank deposit tracking:
- Canadian account entries
- US account entries
- Daily deposit logs

### Sheet 22: SetD (44 rows × 158 cols)
Employee settlement tracking:
- 44 days × ~40+ employee columns
- Daily settlement balances
- Department groupings

---

## UI Requirements for DUBACK# Entry

The RJ management UI needs a **DueBack Entry Section** with:

### 1. Receptionist Name Display
- Show all 23 current receptionists
- Display format: "Last Name, First Name" or "First Name Last Name"
- Should be dynamically read from the RJ file (rows 1-2)

### 2. Daily Entry Interface
For each day (1-31), provide inputs for:

**Previous DueBack (Row 1 for that day):**
- Input field for each receptionist's previous balance correction
- Usually negative values
- Auto-calculate total in column 1 (R/J)

**New DueBack (Row 2 for that day):**
- Input field for each receptionist's new due back amount
- Positive values
- Leave column 1 empty

### 3. Visual Layout Options

**Option A: Horizontal Grid**
```
Day | R/J Total | Araujo | Latulippe | Caron | ... | Total
 1  | -675.18   | Prev:  | Prev:     | Prev: 0|   |
    |           | New:   | New:      | New: 419.82|  |
 2  | -1227.76  | Prev:  | Prev:     | Prev: -419.82|
    |           | New:   | New:      | New: 855.49|  |
```

**Option B: Expandable Day Cards**
```
[Day 1] [Previous: -675.18] [New: 1373.06] [▼]
  Previous DueBack:
    - Caron: 0
    - KRAY: -697.88
  New DueBack:
    - Caron: 419.82
    - MOUATARIF: 18.40
    - KRAY: 934.84
```

**Option C: Two-Column Layout**
```
Previous DueBack               New DueBack
┌─────────────────────┐       ┌─────────────────────┐
│ Araujo:        0.00 │       │ Araujo:      630.88 │
│ Latulippe:     0.00 │       │ Latulippe:     0.00 │
│ Caron:      -466.09 │       │ Caron:       513.41 │
│ ...                 │       │ ...                 │
└─────────────────────┘       └─────────────────────┘
```

### 4. Auto-Calculations
- **Previous total:** Sum of all previous corrections
- **New total:** Sum of all new dueback amounts
- **Running balance:** Track cumulative for each receptionist
- **Variance warnings:** Flag unusual amounts

### 5. Data Validation
- Warn if previous + new don't balance
- Highlight negative new dueback (unusual)
- Verify totals match column 1 and column 25

---

## Current Implementation Status

**Existing UI has:**
✅ File upload
✅ Reset/Sync automation
✅ Basic Recap entry
✅ Transelect entry
✅ GEAC/UX entry
✅ Live preview

**Missing:**
❌ **DueBack entry interface** (23 receptionists)
❌ Previous vs New dueback input separation
❌ Receptionist name dynamic loading
❌ Day-by-day dueback entry
❌ Auto-calculations for dueback totals

---

## Implementation Priority

**CRITICAL:** Add DueBack entry section to `/templates/rj.html` with:
1. Load receptionist names from DUBACK# sheet rows 1-2
2. Create input grid for all 23 receptionists
3. Implement two-row-per-day data structure
4. Add auto-calculation for totals
5. Backend API endpoint: `/api/rj/fill/dueback` to write data
6. Frontend validation and visual feedback

**File to modify:**
- `/Users/canaldesuez/Documents/Projects/audit-pack/templates/rj.html`
- Backend: Add DUBACK# sheet handler in RJ routes

**Data structure for API:**
```json
{
  "day": 1,
  "previous": {
    "Caron": 0,
    "KRAY": -697.88
  },
  "new": {
    "Caron": 419.82,
    "MOUATARIF": 18.40,
    "KRAY": 934.84
  }
}
```
