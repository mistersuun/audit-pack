# RJ - Analysis: INPUT vs CALCULATED Fields

**Date:** 2025-12-26
**Purpose:** Identify which fields users should fill vs which Excel calculates automatically

---

## 🎯 METHODOLOGY

Based on:
1. **Excel file analysis** (Rj 12-23-2025-Copie.xls)
2. **Night audit procedure** (procedure_extracted.txt)
3. **Checklist** (checklist_back.html)
4. **Current UI implementation** (rj.html)

---

## 📋 SHEET-BY-SHEET ANALYSIS

### 1. RECAP

**Purpose:** Summary of cash deposits, checks, DueBack, and final balance

| Row | Cell | Field | Type | Notes |
|-----|------|-------|------|-------|
| 1 | E1 | Date | **INPUT** | Audit date |
| 6 | B6 | Comptant LightSpeed | **INPUT** | From Daily Revenue |
| 6 | C6 | Comptant LightSpeed Corr | **INPUT** | Correction if needed |
| 6 | D6 | Comptant LightSpeed Net | **CALCULATED** | =B6+C6 |
| 7 | B7 | Comptant Positouch | **INPUT** | From POSitouch reports |
| 7 | C7 | Comptant Positouch Corr | **INPUT** | Correction |
| 7 | D7 | Comptant Positouch Net | **CALCULATED** | =B7+C7 |
| 8 | B8 | Chèque Payment Register | **INPUT** | Checks |
| 8 | D8 | Chèque Payment Register Net | **CALCULATED** | Formula |
| 9 | B9 | Chèque Daily Revenu | **INPUT** | Checks from revenue |
| 9 | D9 | Chèque Daily Revenu Net | **CALCULATED** | Formula |
| 10 | B10, C10, D10 | **TOTAL** | **CALCULATED** | Sum of rows 6-9 |
| 10 | I10 | Balance SD (External link) | **CALCULATED** | =B23-'SD file'!E39 |
| 11 | B11 | Moins Remb. Gratuité | **INPUT** | Refund amount (negative) |
| 11 | C11 | Moins Remb. Gratuité Corr | **INPUT** | Correction |
| 11 | D11 | Moins Remb. Gratuité Net | **CALCULATED** | =B11+C11 |
| 12 | B12 | Moins Remb. Client | **INPUT** | Client refund (negative) |
| 12 | C12 | Moins Remb. Client Corr | **INPUT** | Correction |
| 12 | D12 | Moins Remb. Client Net | **CALCULATED** | =B12+C12 |
| 13 | B13, D13 | Moins Remb. Loterie | **CALCULATED?** | Check if used |
| 14 | B14, C14, D14 | **TOTAL** | **CALCULATED** | Sum of refunds |
| 15 | D15, E15 | Moins échange U.S. | **INPUT** | US exchange |
| 16 | B16 | Due Back Réception | **AUTO-FILL** | From DueBack tab |
| 16 | C16 | Due Back Réception Corr | **INPUT** | Correction |
| 16 | D16, E16 | Due Back Réception Net | **CALCULATED** | Formula |
| 17 | B17 | Due Back N/B | **AUTO-FILL** | From DueBack tab |
| 17 | C17 | Due Back N/B Corr | **INPUT** | Correction |
| 17 | D17, E17 | Due Back N/B Net | **CALCULATED** | Formula |
| 18 | B18, C18, D18 | **Total à déposer** | **CALCULATED** | Formula |
| 19 | B19, D19 | Surplus/déficit | **INPUT or CALCULATED?** | Check formula |
| 19 | E19, H19, I19, J19 | Various | **CALCULATED** | Formulas |
| 20 | B20, C20, D20 | Total dépôt net | **CALCULATED** | Formula |
| 21 | D21, E21 | Dépôt US | **INPUT** | US deposit |
| 22 | **B22, C22, D22** | **Dépôt Canadien** | **CALCULATED** | ⚠️ **FROM SD FILE** - DO NOT SHOW |
| 22 | E22 | Dépôt Canadien (other) | **CALCULATED** | Formula |
| 23 | B23, C23, D23 | **Total dépôt net** | **CALCULATED** | **BALANCE FINALE** |
| 24 | B24 | Argent Reçu | **INPUT** | Cash received |
| 26 | B26 | Préparé par | **INPUT** | Auditor name |

**⚠️ CRITICAL FINDING:**
- **Row 22 (Dépôt Canadien)** is **CALCULATED FROM SD FILE** - Should NOT be editable in UI
- **Already removed from UI** ✅

**Buttons (Column F):**
- **EC** (Row 15): Exchange Canada - Auto-fill function
- **WR** (Row 16): Fill Due Back Réception from DueBack tab
- **WN** (Row 17): Fill Due Back N/B from DueBack tab
- **WS** (Row 19): Calculate Surplus/Deficit

---

### 2. DUEBACK

**Purpose:** Track receptionist cash floats (due back amounts) daily

**Structure:**
- Row 2: Receptionist last names
- Row 3: Receptionist first names
- Row 4: Headers
- Rows 5+: Daily entries (2 rows per day)
  - Odd rows (5, 7, 9...): **Previous day's due back** (negative)
  - Even rows (6, 8, 10...): **Today's due back** (positive)

| Section | Cell | Field | Type | Notes |
|---------|------|-------|------|-------|
| Header | B2 | Date | **DISPLAY** | Shows audit date |
| Data | Column A | Day number | **AUTO** | Day of month |
| Data | Column B | R/J total | **CALCULATED?** | Check if formula |
| Data | Columns C-Z | Receptionist amounts | **INPUT** | Enter from cash reports |

**Pattern per day (example Day 9, rows 21-22):**
- Row 21: Previous DueBack (negative values)
- Row 22: Today's DueBack (positive values)

**Totals:**
- Bottom rows likely have **CALCULATED** totals per receptionist

**UI Implementation:**
- Current UI uses **search-based entry system**
- User selects date, receptionist, enters amounts
- Much better than manual Excel grid entry

---

### 3. TRANSELECT (Card Payments)

**Purpose:** Balance credit card and debit payments across all terminals

**Section A: Restaurant/Banquet Terminals (Rows 7-14)**

| Row | Section | Type | Notes |
|-----|---------|------|-------|
| 5 | B5 | Date | **INPUT** | Audit date |
| 6 | B6 | Préparé par | **INPUT** | Auditor name |
| 9-13 | Columns B-O | Terminal amounts by card type | **INPUT** | From Moneris terminals |
| 14 | Row 14 | **TOTAL** | **CALCULATED** | Sum per terminal |

**Terminals:**
- BAR A, BAR B, BAR C (columns B, C, D)
- SPESA D (E)
- ROOM E (F)
- EXTRA terminals (G, H, I)
- Banquet terminals (J-O)

**Card Types (rows 9-13):**
- DÉBIT
- VISA
- MASTER
- DISCOVER
- AMEX

**Section B: FreedomPay/Reception (Rows 18-25)**

| Row | Section | Type | Notes |
|-----|---------|------|-------|
| 20-24 | Column B | FreedomPay amounts by card type | **INPUT** | From FreedomPay report |
| 20-24 | Columns C, D | Réception 8.00 and K053 | **INPUT** | Reception terminals |
| 25 | Row 25 | **TOTAL** | **CALCULATED** | Sum |

**Section C: Summary Totals (Rows 27-40)**

| Row | Section | Type | Notes |
|-----|---------|------|-------|
| 29 | E29-I29 | **TOTAUX** | **CALCULATED** | Grand totals by card type |
| 32 | E32-I32 | **TOTAUX TRANSELE** | **CALCULATED** | Transelect totals |
| 35 | E35-I35 | **TOTAUX GEAC** | **CALCULATED** | GEAC totals |
| 38 | A38-F38 | Final summary | **CALCULATED** | All cards total |
| 40 | Various | Cross-check | **CALCULATED** | Verification formulas |

**⚠️ IMPORTANT:**
- Only **INPUT** sections should be editable
- All **TOTAL rows** are **CALCULATED** - should be readonly or hidden from form

---

### 4. GEAC/UX (Card Balance Verification)

**Purpose:** Verify card totals match between Daily Cash Out and Daily Revenue

| Row | Cell | Field | Type | Source |
|-----|------|-------|------|--------|
| 6 | B6, G6, J6 | Daily Cash Out line 1 | **INPUT** | From Daily Cash Out report |
| 8 | G8, J8 | Daily Cash Out line 2 | **INPUT** | Additional amounts |
| 10 | B10, G10, J10 | **Daily Cash Out TOTAL** | **CALCULATED** | =B6+B8 (etc.) |
| 12 | B12, G12, J12 | Daily Revenue | **INPUT** | From Daily Revenue report |
| 14 | B14, E14, G14, J14 | **VARIANCE** | **CALCULATED** | =Daily Cash Out - Daily Revenue |

**Card Types:**
- Column B: AMEX
- Column E: DINERS (rare)
- Column G: MASTER
- Column J: VISA

**⚠️ VARIANCE ALERT:**
From procedure:
> "Vérifier si le rapport balance. S'il y a une variance, vérifier la saisie de donnée. S'il y a toujours une variance, envoyer un courriel à Roula et Mandy pour les informer. Aucune correction possible de notre part sur ce type de variance."

**UI Implementation:**
- Show variance prominently
- If variance ≠ 0, display warning message
- Row 14 (VARIANCE) should be **CALCULATED and READONLY**

---

### 5. SETD (Monthly Ledger)

**Purpose:** Monthly tracking of RJ totals and personnel account balances

| Section | Cells | Type | Notes |
|---------|-------|------|-------|
| Header | A1 | Month/Year | **DISPLAY** | Excel date |
| Names | Rows 2-3 | Personnel names | **DISPLAY** | Headers |
| Accounts | Row 4 | Account codes | **DISPLAY** | GL codes |
| Days | Column A (rows 5-35) | Day 1-31 | **DISPLAY** | Day numbers |
| **RJ Column** | **Column B (rows 5-35)** | **RJ daily total** | **INPUT** | **From Recap B23** |
| Personnel | Columns C-EI (rows 5-35) | Personnel balances | **INPUT** | Variances from SD file |
| Totals | Row 36 | **TOTAL** | **CALCULATED** | Sum of all days |

**From Procedure (line 210):**
> "Transcrire les informations au sujet des variances (et des remboursements s'il y en a) dans l'onglet SetD du RJ"

**WORKFLOW:**
1. User completes SD file (separate file)
2. SD generates variances by personnel
3. User enters **RJ total** (from Recap B23) in SetD Column B
4. User enters **variances** in respective personnel columns
5. Row 36 auto-calculates totals

**UI Implementation:**
- Need day selector (1-31)
- **Column B (RJ)** - REQUIRED input field
- Personnel columns - OPTIONAL (only if variances exist)
- Search dropdown with 135 personnel names ✅ (already implemented)

---

### 6. DEPOT (Canadian Account Deposits)

**Purpose:** Track daily deposits in Canadian bank account over 7-day period

**Structure:**
- Two parallel sections: **CLIENT 6** and **CLIENT 8**
- Each section tracks last 7 days of deposits
- Rolling 7-day window (remove oldest when adding new)

| Section | Cells | Type | Notes |
|---------|-------|------|-------|
| Date | Column A | Date | **INPUT** | Deposit date |
| Amount | Column B | Montant | **INPUT** | Deposit amount |
| Signature | Column C | Signature | **INPUT** | Who deposited |
| **TOTAL** | Column C (bottom of each date group) | **CALCULATED** | Daily total |

**CLIENT 8 Section (parallel):**
- Same structure in columns I, J, K

**From Procedure (line 208):**
> "Copier les montants de la colonne 'Montant Vérifié' du SD dans l'onglet 'Dépôt' du RJ"

**WORKFLOW:**
1. Complete SD file
2. SD generates "Montant Vérifié" totals
3. Copy those amounts into Depot tab
4. Amounts are deposits that were verified and put in safe

**UI Implementation:**
- Multi-entry system (add/remove deposit lines)
- CLIENT 6 and CLIENT 8 sections separate
- Keep last 7 days visible
- Auto-calculate daily totals
- **Total row = CALCULATED** (sum of deposits for that day)

---

## 📊 SUMMARY TABLE

| Sheet | Total Fields | INPUT Fields | CALCULATED Fields | Current UI Status |
|-------|--------------|--------------|-------------------|-------------------|
| **Recap** | ~20 | ~12 | ~8 | ⚠️ Need to verify all calculated fields are readonly |
| **DueBack** | ~200+ | ~200+ | ~10 | ✅ Using search-based entry (good) |
| **Transelect** | ~100+ | ~30 | ~70 | ⚠️ Need to hide/readonly all totals |
| **GEAC/UX** | ~15 | ~7 | ~8 | ⚠️ Variance must be readonly |
| **SetD** | ~4000+ | ~400 | ~3600 | ✅ Search dropdown implemented |
| **Depot** | ~50 | ~40 | ~10 | ⚠️ Need multi-entry with calculated totals |

---

## 🚨 CRITICAL ISSUES TO FIX

### Issue 1: Recap - Dépôt Canadien (Row 22)
**Status:** ✅ **FIXED** - Removed from UI (hidden, only visible in preview)

### Issue 2: Recap - Total Rows (Rows 10, 14, 18, 20, 23)
**Status:** ⚠️ **NEED TO VERIFY** - Are these shown as readonly?
**Action:** Make sure all total rows are **CALCULATED and READONLY** or **HIDDEN from form**

### Issue 3: Recap - I10 (Balance SD)
**Status:** ✅ **HANDLED** - Shown as balance indicator at top, not editable

### Issue 4: Recap - Due Back Auto-Fill (B16, B17)
**Status:** ⚠️ **NEED TO CHECK** - WR/WN buttons should auto-fill from DueBack tab
**Action:** Verify WR/WN buttons are functional or remove if not implemented

### Issue 5: Transelect - All Total Rows
**Status:** ⚠️ **NEED TO VERIFY** - Rows 14, 25, 29, 32, 35, 38, 40 should be readonly
**Action:** Make all calculated totals **READONLY** or **HIDDEN from form**

### Issue 6: GEAC/UX - Variance Row (Row 14)
**Status:** ⚠️ **NEED TO VERIFY** - Should be calculated and readonly
**Action:** Make variance row **CALCULATED and READONLY**

### Issue 7: Depot - Total Rows
**Status:** ⚠️ **NEED TO VERIFY** - Daily totals should be calculated
**Action:** Implement calculated daily totals per CLIENT section

---

## ✅ RECOMMENDED UI CHANGES

### 1. **Hide ALL calculated fields from data entry forms**
- Show them only in **Excel preview** (inline preview)
- Users should never type into calculated fields

### 2. **Make Total Rows readonly with visual distinction**
- If shown in form, make them:
  - `readonly` attribute
  - Gray background (`background: #e9ecef`)
  - `cursor: not-allowed`
  - Maybe bold text to distinguish

### 3. **Group fields logically**
- **INPUT section:** User fills these
- **CALCULATED section:** View-only, grayed out
- **PREVIEW section:** Full Excel view with all formulas

### 4. **Add validation**
- Prevent editing of calculated fields
- Highlight required INPUT fields
- Validate number formats

### 5. **Add helpful indicators**
- 🟢 INPUT fields: Normal input styling
- 🔵 AUTO-FILL fields: Blue border (filled from other tabs)
- ⚪ CALCULATED fields: Gray background, readonly
- 🔴 ERRORS: Red border if validation fails

---

## 📝 NEXT STEPS

1. **Audit current UI implementation** (rj.html)
   - Check each tab's rendered fields
   - Identify which calculated fields are currently editable
   - Create list of fields to make readonly/hide

2. **Update field mappings** (rj_mapper.py)
   - Add flag: `is_calculated: True/False`
   - Frontend can use this to determine readonly state

3. **Update frontend rendering** (rj.html)
   - Add conditional readonly rendering
   - Style calculated fields differently
   - Hide unnecessary calculated fields

4. **Add validation logic** (JavaScript)
   - Prevent manual editing of calculated fields
   - Show warning if user tries to edit
   - Auto-calculate totals in real-time for immediate feedback

5. **Test thoroughly**
   - Verify all INPUT fields are editable
   - Verify all CALCULATED fields are protected
   - Test with real data from procedure examples

---

**Document Status:** Complete
**Ready for Implementation:** Yes
**Priority:** HIGH - Prevent users from editing calculated fields
