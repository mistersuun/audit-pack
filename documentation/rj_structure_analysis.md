# RJ (Revenue Journal) File Structure Analysis

**Date:** 2025-12-25
**Source File:** `documentation/back/RJ_TEST_OUTPUT.xls`
**Total Sheets:** 34 sheets

---

## 1. DUBACK# Sheet (67 rows x 23 cols)

### Structure
This sheet tracks receptionist due back balances using a **two-row-per-day pattern**:

**Header Rows:**
- **Row 1:** Receptionist last names (columns 2-21)
  - Araujo, Latulippe, Caron, Aguilar, Nader, Mompremier, oppong, SEDDIK, ERMIKA, AYA, Innocent, MAGDA, THANKARAJAH, KRAY, DAMAS, MAUDE, Stephanie, Ben mansour, Simon, Evelyne
- **Row 2:** Receptionist first names
  - Debby, Josée, Isabelle, Dayannis, Laeticia, Rose-Delande, zaneta, ZAYEN, DORMEUS, BACHIRI, Marly, ROCHE, THANEEKAN, VALERIE, Kelly, LEVESQUE, Durocher, Ramzi, Jessica, Mathieu

**Column Layout:**
- **Column 0:** DATE (day number 1-31)
- **Column 1:** R/J (previous total dueback balance)
- **Columns 2-21:** 20 receptionist columns
- **Column 22:** Total

### Daily Entry Pattern
Each day uses **TWO rows**:

1. **First row (even):** Previous DueBack balances being cleared
   - Col 1: Previous total (usually negative)
   - Receptionist cols: Adjustments/corrections

2. **Second row (odd):** New DueBack amounts
   - Col 1: Empty
   - Receptionist cols: New dueback amounts

**Example - Day 1:**
```
Row 4: ['1', '-1636.30', ...]  → Clearing previous total of -1636.30
Row 5: ['1', '', '', '', '', '', '', '', '1.01', '', '', '800.04', '', '150.80', '', '', '', '684.45', ...]
       → New dueback: oppong=1.01, AYA=800.04, MAGDA=150.80, MAUDE=684.45
```

**Bottom Row (66):** Monthly totals for each receptionist

### UI Requirements
- Display all 20 receptionist names (last + first)
- For each day, allow entry of:
  - Previous dueback corrections (if needed)
  - New dueback amounts for each receptionist
- Show running totals
- Auto-calculate total column

---

## 2. Recap Sheet (26 rows x 14 cols)

### Structure
Daily cash reconciliation summary

**Key Fields:**
| Row | Description | Columns |
|-----|-------------|---------|
| 5 | Comptant LightSpeed | Lecture, Corr. +(-), Net |
| 6 | Comptant Positouch | Lecture, Corr. +(-), Net |
| 7 | Chèque payment register AR | Net |
| 8 | Chèque Daily Revenu | Net |
| 9 | Total | |
| 10 | Moins Remboursement Gratuité | |
| 11 | Moins Remboursement Client | |
| 12 | Moins Remboursement Loterie | |
| 13 | Total reimbursements | |
| 14 | Moins échange U.S. | |
| 15 | Due Back Réception | Lecture, Corr., Net, WR code |
| 16 | Due Back N/B | Lecture, Corr., Net, WN code |
| 17 | Total à déposer | |
| 18 | Surplus/déficit (+ ou -) | Multiple calculations |
| 19 | Total dépôt net | |
| 20 | Depot US | |
| 21 | Dépôt Canadien | |
| 23 | Argent Reçu | Total |
| 25 | Préparé par | Auditor name |

### UI Requirements
- Cash readings section (LightSpeed, Positouch, Checks)
- Corrections column for adjustments
- Auto-calculated reimbursements section
- Due Back entry (matches DUBACK# totals)
- Auto-calculated deposit totals
- Surplus/deficit calculation

---

## 3. Transelect Sheet (40 rows x 32 cols)

### Structure
Credit card terminal reconciliation - **TWO sections**:

#### Section 1: Restaurant/Bar Terminals (Rows 6-13)
**Columns:**
- TYPE (row 6): Terminal purposes
- Row 7: Terminal IDs (701, 702, 703, 704, 705, etc.)
- Rows 8-12: Card types (DEBIT, VISA, MASTER, DISCOVER, AMEX)
- Row 13: TOTAL
- Last columns: TOTAL 1, TOTAL 2, POSITOUCH, VARIANCE

**Terminals:**
- **BAR:** 701, 702, 703
- **SPESA:** 704
- **ROOM:** 705
- **EXTRA:** A0774167, B0774167, DG531139
- **Banquet:** DN531139, DL531139, CK531139, BU531139, BS531139, BR531139, BO531139, CX531139, DJ531139, DI531139

#### Section 2: Reception/Rooms Terminals (Rows 17-24)
**Columns:**
- Bank Report (FuseBoxe)
- Réception terminals (8, K053)
- TOTAL, Daily Revenue, VARIANCE
- ESCOMPTE (discount), NET GEAC

**Card types:** DÉBIT, VISA, MASTER, DISCOVER, AMEX

### UI Requirements
- Restaurant terminals grid: terminals × card types
- Reception terminals grid: terminals × card types
- Auto-calculate totals and variances
- Discount calculations
- GEAC net amounts

---

## 4. geac_ux Sheet (58 rows x 11 cols)

### Structure
GEAC/UX system reconciliation

**Key Rows:**
- Row 4: Daily Cash Out (AMEX, MASTER, VISA)
- Row 7: (Additional amounts)
- Row 9: Daily totals
- Row 11: Daily Revenue
- Row 13: Variances

**Columns:** AMEX, DINERS, MASTER, VISA

### UI Requirements
- Cash out entry (3 card types)
- Daily revenue comparison
- Variance calculation (should be 0)
- Warning if amounts don't balance

---

## 5. depot Sheet (99 rows x 256 cols)

### Structure
Bank deposit tracking log - **TWO sections**:

#### Canadian Account (Columns 0-7)
- CLIENT 6 COMPTE # 1844-22
- Columns: DATE, MONTANT, SIGNATURE

#### American Account (Columns 8-15)
- CLIENT 8 COMPTE # 4743-66
- Columns: DATE, MONTANT, SIGNATURE

**Pattern:**
Each deposit day shows:
- Date
- Multiple deposit amounts (one per row)
- Subtotal for that day
- Signature column

### UI Requirements
- Date entry
- Multiple deposit lines per day
- Auto-calculated daily totals
- Separate Canadian and US sections

---

## 6. SetD Sheet (44 rows x 127 cols)

### Structure
Daily settlement tracking for multiple employees/accounts

**Header Rows:**
- Row 0: Department labels (COMPTAB, BANQUET, etc.)
- Row 1: Employee names
- Row 2: Employee last names
- Row 3: GL account codes (2-946000, 2-101100, 2-101701, 2-101704)

**Employees tracked (partial list):**
- Martine Breton, Olga Arhontou, Mandy Le, Frederic Dupont, Marie Carlesso, Patrick Fournier, Karl Leclerc, Stéphane Latulippe, and many more (~25+ employees)

**Daily rows (4-43):**
- Column 0: Day number (1-31)
- Column 1: RJ balance (can be negative = "débiteur")
- Columns 2+: Individual employee settlements

### UI Requirements
- Employee columns grid (25+ employees)
- Daily settlement entries
- Department grouping
- GL account code display
- Negative value handling (debit balances)

---

## Summary: Required UI Components

Based on this analysis, the RJ management UI needs:

### 1. DueBack Entry Section
- 20 receptionist columns with full names
- Previous/New dueback input for each day
- Auto-calculated totals

### 2. Recap Section
- Cash readings (LightSpeed, Positouch)
- Corrections column
- Reimbursements
- Due Back totals (linked to DUBACK#)
- Deposit calculations

### 3. Transelect Section
- Restaurant terminals grid
- Reception terminals grid
- Card type breakdowns
- Variance calculations

### 4. Deposit Section
- Canadian account entries
- US account entries
- Multiple deposits per day

### 5. GEAC/UX Section
- Card type reconciliation
- Cash out vs Revenue comparison

### 6. SetD Section
- Employee settlement grid
- Daily balances

---

## Current Implementation Gap

The current RJ UI (as of Dec 25, 2025) has:
- ✅ File upload
- ✅ Reset/Sync automation
- ✅ Basic Recap entry
- ✅ Transelect entry
- ✅ GEAC/UX entry
- ✅ Live preview

**Missing:**
- ❌ **DueBack entry interface** (20 receptionists × previous/new amounts)
- ❌ Individual receptionist name display
- ❌ Previous vs New dueback separation
- ❌ Complete depot entry UI
- ❌ SetD employee settlements UI

**Priority:** Implement DueBack entry section with all 20 receptionist columns.
