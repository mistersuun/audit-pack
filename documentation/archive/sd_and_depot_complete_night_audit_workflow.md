# SD and Depot - Complete Night Audit Workflow

**Date:** 2025-12-25
**Based on:** Night Audit Procedure Documents

---

## COMPLETE WORKFLOW FROM NIGHT AUDIT CHECKLIST

### Step 1: Complete SD File (Sommaire Journalier)

**Source:** "SOMMAIRE JOURNALIER DES DÉPÔTS" sheet (gray pad)

**Process:**
1. Open SD folder on desktop
2. Select the file for the current month
3. Go to the current date's tab
4. Write the date
5. Write your name at the bottom
6. For each employee who had deposits:
   - **DÉPARTEMENT:** Select department (RÉCEPTION, SPESA, RESTAURANT, BANQUET, COMPTABILITÉ)
   - **NOM:** Employee name
   - **CDN/US:** Currency
   - **MONTANT:** Amount employee said they deposited (from POSitouch reports)
   - **MONTANT VÉRIFIÉ:** ⭐ **ACTUAL amount counted/verified (what went into the safe)**
   - **REMBOURSEMENT:** Reimbursement amount if applicable
   - **VARIANCE:** Auto-calculated = MONTANT - MONTANT_VÉRIFIÉ + REMBOURSEMENT

7. Review **TOTAL MONTANT VÉRIFIÉ** - This is the KEY value!

**Note:** Don't print SD yet - need to balance RECAP first (might need modifications)

---

### Step 2: Balance Recap (Comptant)

**Process:**
1. Balance the Recap tab
2. Verify "Dépôt Canadien" matches or relates to SD total MONTANT VÉRIFIÉ
3. Make adjustments if needed

---

### Step 3: Print Recap and SD

**After balancing:**
- Print Recap
- Print SD file

---

### Step 4: Copy SD Amounts to Depot Tab

**⭐ KEY STEP:** "COPIER LES MONTANTS QUI ONT ÉTÉ DÉPOSÉ DU SD DANS L'ONGLET « DÉPÔT » DU RJ"

**Process:**
1. Open RJ file → depot tab
2. Find available space in either CLIENT 6 or CLIENT 8 columns
3. Enter **DATE** (e.g., "23 DECEMBRE")
4. Enter each **MONTANT VÉRIFIÉ** from SD as individual deposit amounts
5. System auto-calculates **TOTAL for that date**

**Important:**
- CLIENT 6 and CLIENT 8 are just **parallel logging spaces** (not different purposes)
- Use whichever has available space
- **Keep only the last 7 days** - delete or overwrite older entries
- Each SD MONTANT VÉRIFIÉ entry becomes one depot amount
- The sum of depot amounts for a date = SD's total MONTANT VÉRIFIÉ for that date

**Example:**
```
SD for Dec 23:
  Employee 1 - MONTANT VÉRIFIÉ: 48.15
  Employee 2 - MONTANT VÉRIFIÉ: 313.15
  Employee 3 - MONTANT VÉRIFIÉ: 4.70
  TOTAL MONTANT VÉRIFIÉ: 366.00

Depot entry:
  DATE: 23 DECEMBRE
  Amount 1: 48.15
  Amount 2: 313.15
  Amount 3: 4.70
  TOTAL: 366.00
```

---

### Step 5: Transcribe SD Variances to SetD Tab

**Process:**
- Copy variance values from SD file
- Enter into SetD tab of RJ

---

## DATA STRUCTURE BREAKDOWN

### SD File (Excel - Monthly)

**Purpose:** Daily summary of employee deposits and settlements

**Structure:**
- One file per month
- One tab per day (1-31)
- Each tab has the SD table with totals

**Columns:**
1. DÉPARTEMENT
2. NOM LETTRES MOULÉES
3. CDN/US
4. MONTANT (declared)
5. **MONTANT VÉRIFIÉ** ⭐ (verified - actual deposit)
6. REMBOURSEMENT
7. VARIANCE (auto-calc)

**Key Value:** Row 38, Col 4 = **TOTAL MONTANT VÉRIFIÉ**

---

### RJ File - Depot Tab

**Purpose:** 7-day rolling log of deposit entries

**Structure:**
- **CLIENT 6** (Cols 0-2): DATE, MONTANT, SIGNATURE/TOTAL
- **CLIENT 8** (Cols 8-10): DATE, MONTANT, SIGNATURE/TOTAL

**Entry Pattern:**
```
Row X:   DATE (e.g., "23 DECEMBRE")
Row X+1: MONTANT (first deposit)
Row X+2: MONTANT (second deposit)
Row X+3: MONTANT (third deposit)
Row X+4: TOTAL (sum in signature column)

Row Y:   DATE (next day)
...
```

**Rules:**
1. CLIENT 6 and CLIENT 8 are interchangeable (just two spaces)
2. Write wherever there's available space
3. Keep only 7 days of data
4. Each date gets: DATE → amounts → TOTAL

---

### RJ File - Recap Tab

**Purpose:** Daily cash reconciliation summary

**Row 21: Dépôt Canadien**
- Col 1 (Lecture): Initial reading
- Col 2 (Corr): Correction
- Col 3 (Net): Lecture + Corr
- Col 4: Should relate to SD's MONTANT VÉRIFIÉ total

---

## UI IMPLEMENTATION MATCHES WORKFLOW

### ✅ SD Section
- Multi-entry table with all required columns
- Auto-calculates VARIANCE
- Highlights MONTANT VÉRIFIÉ column (yellow)
- Shows TOTAL MONTANT VÉRIFIÉ prominently

### ✅ Depot Section
- Separate CLIENT 6 and CLIENT 8 areas
- DATE field for each client
- Multi-entry amounts
- Auto-calculates TOTAL DU JOUR
- Note explaining CLIENT 6/8 are just parallel spaces
- Reminder to keep only 7 days

### ✅ Connection
- SD MONTANT VÉRIFIÉ values → copied to depot as individual amounts
- Depot TOTAL for date = SD TOTAL MONTANT VÉRIFIÉ for that date

---

## WHY THIS MATTERS

### For Night Auditor:
1. **Accountability:** Each employee's deposits are verified and tracked
2. **Reconciliation:** VARIANCE shows discrepancies between declared vs actual
3. **Audit Trail:** 7-day depot log for accounting verification
4. **Cash Management:** Admins know exactly when deposits were made

### For Accounting:
1. **Deposit Verification:** Can verify actual deposits made to bank
2. **Employee Tracking:** Know which employees had discrepancies
3. **Date Tracking:** Know which dates had which deposit amounts
4. **Reconciliation:** Can cross-reference with bank statements

---

## VALIDATION RULES

### SD Validation:
- ✅ All employees with deposits are entered
- ✅ MONTANT VÉRIFIÉ matches actual counted amounts
- ✅ VARIANCE is reviewed (should be minimal)
- ✅ TOTAL MONTANT VÉRIFIÉ is highlighted

### Depot Validation:
- ✅ DATE matches current audit date
- ✅ Individual amounts match SD MONTANT VÉRIFIÉ entries
- ✅ TOTAL matches SD total MONTANT VÉRIFIÉ
- ✅ Old data (>7 days) is removed

### Cross-Validation:
- ✅ SD Total MONTANT VÉRIFIÉ = Depot Total for that date
- ✅ Recap "Dépôt Canadien" relates to SD total
- ✅ No missing dates in 7-day window

---

## BACKEND REQUIREMENTS

### 1. Read SD File
- Determine which SD file to read (current month)
- Extract MONTANT VÉRIFIÉ values
- Pre-populate depot amounts (optional convenience)

### 2. Write SD File
- Create/update daily tab in monthly SD file
- Save all employee entries
- Calculate totals

### 3. Write Depot Tab
- Find available space in CLIENT 6 or CLIENT 8
- Write DATE + amounts + total
- Clean up entries older than 7 days

### 4. Auto-Cleanup
- On save, check all depot entries
- Remove any entries with dates older than 7 days
- Warn user if depot is getting full

---

## CURRENT STATUS

✅ **UI Complete**
- SD section with all columns
- Depot section with DATE fields
- Auto-calculations working
- Visual notes and guidance

⏭️ **Backend Pending**
- API endpoints for SD
- API endpoints for depot
- Data loading from existing files
- 7-day cleanup logic

---

## TESTING CHECKLIST

- [ ] Fill SD with 3+ employee entries
- [ ] Verify TOTAL MONTANT VÉRIFIÉ calculates correctly
- [ ] Copy MONTANT VÉRIFIÉ values to depot
- [ ] Enter DATE in depot
- [ ] Add amounts (matching SD values)
- [ ] Verify depot TOTAL matches SD total
- [ ] Add entries to CLIENT 6
- [ ] Add entries to CLIENT 8
- [ ] Verify TOTAL GÉNÉRAL = CLIENT 6 + CLIENT 8
- [ ] Test with data >7 days old (cleanup)

---

## NEXT DEVELOPMENT STEPS

1. **Create backend API for SD write**
2. **Create backend API for depot write**
3. **Implement 7-day cleanup logic**
4. **Add data loading from existing RJ/SD files**
5. **Add cross-validation warnings**
6. **Add one-click "Copy SD to Depot" feature**
