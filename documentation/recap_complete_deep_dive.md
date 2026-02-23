# RECAP - Complete Deep Dive Analysis

**Date:** 2025-12-26
**Purpose:** Understand RECAP sheet completely before making any UI changes

---

## 📊 OVERVIEW

**RECAP = "Récapitulatif"** - Summary sheet that calculates the final cash balance for the night audit.

**Primary Purpose:**
- Calculate how much cash should be deposited
- Track cash, checks, refunds, and DueBack amounts
- Verify the balance matches what was physically received
- Feed data into other sheets (SetD, Depot)

**Dimensions:** 26 rows × 15 columns (active area: A1:J26)

---

## 🏗️ STRUCTURE - 6 MAIN SECTIONS

### Section 1: HEADER (Rows 1-5)

| Cell | Content | Type | Purpose |
|------|---------|------|---------|
| **D1** | "Date:" | Label | Date label |
| **E1** | `46014.0` | **INPUT** | Audit date (Excel date format) |
| **A4** | "RECAP" | Label | Sheet title |
| **A5** | "Description" | Label | Column header |
| **B5** | "Lecture" | Label | Reading/declared amounts |
| **C5** | "Corr. + (-)" | Label | Corrections |
| **D5** | "Net" | Label | Net result |

---

### Section 2: CASH & CHECKS (Rows 6-10)

**Purpose:** Total up all cash and check receipts

#### Row 6: Comptant LightSpeed

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A6** | "Comptant LightSpeed" | Label | - | - |
| **B6** | `521.20` | **INPUT** | - | Daily Revenue page 5/6 |
| **C6** | (empty) | **INPUT** | - | Correction if needed |
| **D6** | `521.20` | **CALCULATED** | `=B6+C6` | Auto |

**Workflow:**
1. User prints Daily Revenue pages 5-6 from LightSpeed
2. Finds "Comptant LightSpeed" total
3. Enters in B6
4. D6 auto-calculates

#### Row 7: Comptant Positouch

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A7** | "Comptant Positouch" | Label | - | - |
| **B7** | `696.05` | **INPUT** | - | POSitouch reports |
| **C7** | (empty) | **INPUT** | - | Correction if needed |
| **D7** | `696.05` | **CALCULATED** | `=B7+C7` | Auto |

**Workflow:**
1. User uses POSitouch "Établissement" report
2. Finds cash total
3. Enters in B7
4. D7 auto-calculates

#### Row 8: Chèque payment register AR

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A8** | "Chèque payment register AR" | Label | - | - |
| **B8** | (empty) | **INPUT** | - | Check from payment register |
| **C8** | (empty) | **INPUT** | - | Correction |
| **D8** | `0.00` | **CALCULATED** | `=IF(B8="",0,B8+C8)` | Auto |

**Usage:** Rarely used - only if there are checks

#### Row 9: Chèque Daily Revenu

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A9** | "Chèque Daily Revenu" | Label | - | - |
| **B9** | (empty) | **INPUT** | - | Checks from daily revenue |
| **C9** | (empty) | **INPUT** | - | Correction |
| **D9** | `0.00` | **CALCULATED** | `=IF(B9="",0,B9+C9)` | Auto |

**Usage:** Checks received during the day (rare)

#### Row 10: TOTAL (First Total Row) ⚡

| Cell | Value | Type | Formula (inferred) |
|------|-------|------|-------------------|
| **A10** | "Total" | Label | - |
| **B10** | `1217.25` | **CALCULATED** | `=SUM(B6:B9)` or `=B6+B7+B8+B9` |
| **C10** | `0.00` | **CALCULATED** | `=SUM(C6:C9)` or `=C6+C7+C8+C9` |
| **D10** | `1217.25` | **CALCULATED** | `=SUM(D6:D9)` or `=B10+C10` |
| **I10** | `0.00` | **CALCULATED** | `=B23-'SD file'!E39` (external link!) |

**⚠️ SPECIAL: I10 - Balance SD**
- **Formula:** `=B23-'file:///K:/SD 2025/[SD Decembre.xls]23'!$E$39`
- **Purpose:** Verify RJ balance matches SD file
- **Should be:** $0.00 when everything balances
- **UI:** Shown as indicator at top, NOT editable

**Math Check:**
```
B10 = B6 + B7 + B8 + B9 = 521.20 + 696.05 + 0 + 0 = 1217.25 ✅
D10 = B10 + C10 = 1217.25 + 0 = 1217.25 ✅
```

---

### Section 3: REFUNDS (Rows 11-14)

**Purpose:** Subtract refunds/reimbursements from cash total

#### Row 11: Moins Remboursement Gratuité

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A11** | "Moins Remboursement Gratuité" | Label | - | - |
| **B11** | `-2543.42` | **INPUT** | - | Complimentary refunds (NEGATIVE) |
| **C11** | (empty) | **INPUT** | - | Correction |
| **D11** | `-2543.42` | **CALCULATED** | `=B11+C11` | Auto |

**Note:** Always NEGATIVE (it's a refund/deduction)

#### Row 12: Moins Remboursement Client

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A12** | "Moins Remboursement Client" | Label | - | - |
| **B12** | `-1067.61` | **INPUT** | - | Client refunds (NEGATIVE) |
| **C12** | (empty) | **INPUT** | - | Correction |
| **D12** | `-1067.61` | **CALCULATED** | `=B12+C12` | Auto |

**Note:** Always NEGATIVE (it's a refund/deduction)

#### Row 13: Moins Remboursement Loterie

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A13** | "Moins Remboursement Loterie" | Label | - | - |
| **B13** | (empty) | **INPUT** | - | Lottery refunds (rare) |
| **C13** | (empty) | **INPUT** | - | Correction |
| **D13** | `0.00` | **CALCULATED** | `=IF(B13="",0,B13+C13)` | Auto |

**Usage:** Rarely used

#### Row 14: TOTAL (Second Total Row) ⚡

| Cell | Value | Type | Formula (inferred) |
|------|-------|------|-------------------|
| **A14** | "Total" | Label | - |
| **B14** | `-2393.78` | **CALCULATED** | `=SUM(B11:B13)` or `=B11+B12+B13` |
| **C14** | `0.00` | **CALCULATED** | `=SUM(C11:C13)` |
| **D14** | `-2393.78` | **CALCULATED** | `=SUM(D11:D13)` or `=B14+C14` |

**Math Check:**
```
B14 = B11 + B12 + B13 = -2543.42 + (-1067.61) + 0 = -3611.03
Wait... Excel shows -2393.78 🤔
Let me check: -2543.42 + (-1067.61) = -3611.03
But Excel shows: -2393.78

Actually looking at the data:
B11 = -2543.42
B12 = -1067.61
Total should be -3611.03, but shows -2393.78

This suggests B14 might NOT be SUM(B11:B13), but rather something else.
Let me recalculate:
-2543.42 - 1067.61 = -3611.03
But actual B14 = -2393.78

Difference: -3611.03 - (-2393.78) = -1217.25 (which is B10!)

So the formula might be: B14 = B11 + B12 + B13 - B10? No wait...
Or maybe: B14 = -(B11 + B12) where B11 and B12 are already negative?

Actually, looking again:
If B11 = -2543.42 and B12 = -1067.61
Then -2543.42 + (-1067.61) = -3611.03

But B14 shows -2393.78

Hmm, let me think differently. Maybe the formula is:
B14 = B10 + B11 + B12 + B13
= 1217.25 + (-2543.42) + (-1067.61) + 0
= 1217.25 - 3611.03
= -2393.78 ✅

So B14 is the NET after refunds: Cash IN (B10) - Refunds OUT (B11+B12+B13)
```

**Corrected Understanding:**
- **B14 = B10 + B11 + B12 + B13** (Running total, not just refunds)
- This is the NET CASH after refunds are deducted

---

### Section 4: DUE BACK & US EXCHANGE (Rows 15-18)

**Purpose:** Handle DueBack (receptionist floats) and US exchange

#### Row 15: Moins échange U.S.

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A15** | "Moins échange U.S." | Label | - | - |
| **B15** | (empty) | **INPUT** | - | US exchange amount |
| **C15** | (empty) | **INPUT** | - | Correction |
| **D15** | `0.00` | **CALCULATED** | `=IF(B15="",0,B15+C15)` | Auto |
| **E15** | `0.00` | **CALCULATED** | Related calculation | Auto |
| **F15** | "EC" | **BUTTON** | Macro button | Exchange Canada |

**Usage:** Rare - only if there are US dollar exchanges

**EC Button:** Auto-fill function (macro) - may not be needed in web UI

#### Row 16: Due Back Réception

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A16** | "Due Back Réception" | Label | - | - |
| **B16** | `653.10` | **INPUT/AUTO** | - | From DueBack tab OR manual |
| **C16** | (empty) | **INPUT** | - | Correction |
| **D16** | `653.10` | **CALCULATED** | `=B16+C16` | Auto |
| **E16** | `-653.10` | **CALCULATED** | `=-D16` | Negative for transfer |
| **F16** | "WR" | **BUTTON** | Macro button | Fill from DueBack |

**WR Button:** Should auto-fill B16 from DueBack tab total

**From Procedure:**
> "Sur la 1e ligne de la date, inscrire le dueback précédant de chaque employé (en négatif)"
> "Sur la 2e ligne de la date, inscrire le dueback d'aujourd'hui, soit total de chaque employé (en positif)"

So DueBack tab tracks daily amounts, and this row gets the TOTAL.

#### Row 17: Due Back N/B

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A17** | "Due Back N/B" | Label | - | - |
| **B17** | `667.61` | **INPUT/AUTO** | - | From DueBack tab OR manual |
| **C17** | (empty) | **INPUT** | - | Correction |
| **D17** | `667.61` | **CALCULATED** | `=B17+C17` | Auto |
| **E17** | `-667.61` | **CALCULATED** | `=-D17` | Negative for transfer |
| **F17** | "WN" | **BUTTON** | Macro button | Fill from DueBack |

**WN Button:** Should auto-fill B17 from DueBack tab total

**Question:** What's the difference between "Réception" and "N/B"?
- Likely: Réception = Reception floats, N/B = Night/Back office floats?

#### Row 18: Total à déposer ⚡

| Cell | Value | Type | Formula (inferred) |
|------|-------|------|-------------------|
| **A18** | "Total à déposer" | Label | - |
| **B18** | `-1073.07` | **CALCULATED** | `=B14+B15+B16+B17` |
| **C18** | `0.00` | **CALCULATED** | `=C14+C15+C16+C17` |
| **D18** | `-1073.07` | **CALCULATED** | `=D14+D15+D16+D17` or `=B18+C18` |

**Math Check:**
```
B18 = B14 + B15 + B16 + B17
= -2393.78 + 0 + 653.10 + 667.61
= -2393.78 + 1320.71
= -1073.07 ✅
```

**Meaning:** This is the amount that should be deposited (negative means we owe money back to floats/refunds)

---

### Section 5: BALANCE & DEPOSITS (Rows 19-23)

**Purpose:** Calculate final balance and deposits

#### Row 19: Surplus/déficit (+ ou -) ⚡⚡⚡

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A19** | "Surplus/déficit  (+ ou -)" | Label | - | - |
| **B19** | `1532.47` | **INPUT?** | Maybe calculated? | Unclear |
| **C19** | (empty) | **INPUT** | - | Correction |
| **D19** | `1532.47` | **CALCULATED** | `=B19+C19` | Auto |
| **E19** | `-1532.47` | **CALCULATED** | `=-D19` | Negative |
| **F19** | "WS" | **BUTTON** | Macro button | Calculate surplus |
| **H19** | `4070.43` | **CALCULATED** | Related | ? |
| **I19** | `-1067.61` | **CALCULATED** | Reference to B12? | Remb Client |
| **J19** | `-2543.42` | **CALCULATED** | Reference to B11? | Remb Gratuité |

**⚠️ CRITICAL - Need to understand B19:**
- Is it INPUT (user enters) or CALCULATED?
- WS button suggests it can be auto-calculated
- H19 value (4070.43) appears also in B24 (Argent Reçu)

**Hypothesis:**
- B19 might be: `=B24 - B18` (Argent Reçu - Total à déposer)
- Let's check: 4070.43 - (-1073.07) = 4070.43 + 1073.07 = 5143.50 ❌ (not 1532.47)

**Alternative hypothesis:**
- Maybe from SD variances?
- Need to check procedure more carefully

**From Procedure (line 174):**
> "BALANCER L'ONGLET RECAP DU RJ (COMPTANT)."
> "Marquer le total de variance (tel quel – ou +) du SD"
> "Marquer le total de Dueback"

So B19 (Surplus/déficit) comes from **SD variance total**!

#### Row 20: Total dépôt net ⚡

| Cell | Value | Type | Formula (inferred) |
|------|-------|------|-------------------|
| **A20** | "Total dépôt net" | Label | - |
| **B20** | `459.40` | **CALCULATED** | `=B18+B19` |
| **C20** | `0.00` | **CALCULATED** | `=C18+C19` |
| **D20** | `459.40` | **CALCULATED** | `=D18+D19` or `=B20+C20` |

**Math Check:**
```
B20 = B18 + B19 = -1073.07 + 1532.47 = 459.40 ✅
```

**Meaning:** This is the NET amount to deposit after accounting for surplus/deficit

#### Row 21: Dépôt US

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A21** | "Depot US" | Label | - | - |
| **B21** | (empty) | **INPUT** | - | US deposit amount |
| **C21** | (empty) | **INPUT** | - | Correction |
| **D21** | `0.00` | **CALCULATED** | `=IF(B21="",0,B21+C21)` | Auto |
| **E21** | `0.00` | **CALCULATED** | Related | Auto |

**Usage:** Rare - only if there are US dollar deposits

#### Row 22: Dépôt Canadien ⚡⚡⚡ **CRITICAL**

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A22** | "Dépôt Canadien" | Label | - | - |
| **B22** | `459.40` | **CALCULATED** | `=B20-B21` | From SD file |
| **C22** | `0.00` | **CALCULATED** | `=C20-C21` | Auto |
| **D22** | `459.40` | **CALCULATED** | `=D20-D21` or `=B22+C22` | Auto |
| **E22** | `2853.18` | **CALCULATED** | From SD/Depot? | ? |

**From Procedure (line 208):**
> "Copier les montants de la colonne 'Montant Vérifié' du SD dans l'onglet 'Dépôt' du RJ"

And from SD analysis:
> "Le MONTANT VÉRIFIÉ total sera automatiquement transféré dans le Recap 'Dépôt Canadien'"

**⚠️ SO B22 IS CALCULATED FROM SD FILE!**

**Current UI Status:** ✅ Already removed from form (readonly/hidden)

#### Row 23: Total dépôt net (BALANCE FINALE) ⚡⚡⚡

| Cell | Value | Type | Formula (inferred) |
|------|-------|------|-------------------|
| **A23** | "Total dépôt net" | Label | - |
| **B23** | `459.40` | **CALCULATED** | `=B20-B21` or `=B22` |
| **C23** | `0.00` | **CALCULATED** | `=C20-C21` or `=C22` |
| **D23** | `459.40` | **CALCULATED** | `=D20-D21` or `=D22` or `=B23+C23` |

**Math Check:**
```
B23 = B20 - B21 = 459.40 - 0 = 459.40 ✅
B23 = B22 (same value) ✅
```

**⚠️ CRITICAL - B23 IS THE BALANCE FINALE!**
- This value goes to **SetD Column B** (RJ total for the day)
- This is THE most important calculated value in the entire sheet
- Used for I10 formula: `I10 = B23 - SD_file!E39`

---

### Section 6: FOOTER (Rows 24-26)

#### Row 24: Argent Reçu

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A24** | "Argent Reçu :" | Label | - | - |
| **B24** | `4070.43` | **INPUT** | - | Cash physically received |

**Purpose:** Enter the actual cash amount received/counted

**Note:** This value also appears in H19, suggesting a relationship

#### Row 26: Préparé par

| Cell | Value | Type | Formula (inferred) | Source |
|------|-------|------|-------------------|--------|
| **A26** | "Préparé par :" | Label | - | - |
| **B26** | "Khalil Mouatarif" | **INPUT** | - | Auditor name |

**Purpose:** Who prepared this recap

---

## 🔄 COMPLETE WORKFLOW

### Step 1: Gather Source Documents
1. **LightSpeed Daily Revenue** pages 5-6 → Comptant LightSpeed (B6)
2. **POSitouch Établissement** report → Comptant Positouch (B7)
3. **Check amounts** (if any) → B8, B9
4. **Refund amounts** → B11, B12, B13 (negative values!)
5. **DueBack tab totals** → B16, B17 (or use WR/WN buttons)
6. **SD file variance total** → B19 (Surplus/déficit)
7. **Physical cash counted** → B24 (Argent Reçu)

### Step 2: Fill INPUT Fields
- E1: Date
- B6: Comptant LightSpeed
- B7: Comptant Positouch
- B8, B9: Checks (if any)
- B11: Remb. Gratuité (negative!)
- B12: Remb. Client (negative!)
- B16: Due Back Réception (or click WR)
- B17: Due Back N/B (or click WN)
- B19: Surplus/déficit (from SD variance, or click WS?)
- B24: Argent Reçu
- B26: Auditor name

### Step 3: Excel Auto-Calculates
- All D columns (Net = Lecture + Correction)
- All Total rows (10, 14, 18, 20, 22, 23)
- I10 (Balance with SD file)
- E columns (transfers/negatives)

### Step 4: Verify Balance
- Check **I10** = should be $0.00 (RJ matches SD)
- Check **B23** (Balance Finale) - this is THE number
- Print Recap for filing

### Step 5: Transfer Data
- **B23 → SetD Column B** (for current day)
- **Variance data → SetD personnel columns** (if any)
- **SD Montant Vérifié totals → Depot tab**

---

## 📋 CURRENT UI STATUS

Looking at `/templates/rj.html` (Recap section):

### ✅ CORRECT in Current UI:
1. **Row 22 (Dépôt Canadien)** - Removed/hidden ✅
2. **I10 Balance indicator** - Shown at top as indicator ✅
3. **Row 11-12 red text** - Remboursements in red ✅
4. **Row 9 added** - Chèque Daily Revenu ✅

### ⚠️ NEEDS FIXING in Current UI:

#### 1. **All "Net" columns (Column D) - Should be READONLY**
- D6, D7, D8, D9 (calculated from B+C)
- Currently: Probably shown as inputs? ❌
- Should: Be readonly with gray background ✅

#### 2. **All TOTAL rows - Should be READONLY or HIDDEN**
- Row 10 (B10, C10, D10)
- Row 14 (B14, C14, D14)
- Row 18 (B18, C18, D18)
- Row 20 (B20, C20, D20)
- Row 23 (B23, C23, D23)
- Currently: Shown as inputs? ❌
- Should: Be readonly OR completely hidden from form ✅

#### 3. **B19 (Surplus/déficit) - Needs Clarification**
- Is it INPUT or CALCULATED?
- WS button suggests auto-fill from somewhere
- From procedure: comes from SD variance total
- Should: Make it INPUT with helpful note: "From SD variance total"

#### 4. **Macro Buttons (EC, WR, WN, WS)**
- Currently: May not be functional
- EC (Row 15): Exchange Canada - probably not needed
- WR (Row 16): Should fill B16 from DueBack total
- WN (Row 17): Should fill B17 from DueBack total
- WS (Row 19): Should fill B19 from SD variance (unclear exactly how)
- Should: Implement WR/WN to auto-fill from DueBack, or remove if too complex

#### 5. **Corrections columns (Column C) - Optional INPUTs**
- C6, C7, C11, C12, C16, C17
- Should allow input but default to empty
- If empty, doesn't affect Net calculation

---

## 🎯 RECOMMENDED UI CHANGES FOR RECAP

### Priority 1: Make Calculated Fields Readonly

**All Column D cells (Net):**
```html
<!-- BEFORE (wrong) -->
<input type="number" data-cell="D6">

<!-- AFTER (correct) -->
<input type="number" data-cell="D6" readonly
       style="background: #e9ecef; cursor: not-allowed; font-weight: 600;">
```

**All TOTAL rows:**
Option A: Make readonly
```html
<input type="number" data-cell="B10" readonly
       style="background: #e9ecef; cursor: not-allowed; font-weight: 700;">
```

Option B: Hide from form entirely (better!)
```html
<!-- Don't show in form at all, only in Excel preview -->
```

### Priority 2: Group Sections Visually

```html
<!-- Section 1: Cash & Checks -->
<div class="recap-section">
  <h4>💵 Comptant et Chèques</h4>
  <!-- Rows 6-9 inputs -->
  <div class="recap-total-row">
    <!-- Row 10 total - READONLY -->
  </div>
</div>

<!-- Section 2: Refunds -->
<div class="recap-section">
  <h4>💸 Remboursements</h4>
  <!-- Rows 11-13 inputs -->
  <div class="recap-total-row">
    <!-- Row 14 total - READONLY -->
  </div>
</div>

<!-- Section 3: DueBack -->
<div class="recap-section">
  <h4>🔄 Due Back</h4>
  <!-- Rows 16-17 inputs with WR/WN buttons -->
  <div class="recap-total-row">
    <!-- Row 18 total - READONLY -->
  </div>
</div>

<!-- Section 4: Balance Final -->
<div class="recap-section">
  <h4>✅ Balance Finale</h4>
  <!-- Row 19-20-23 -->
  <div class="recap-balance-finale">
    B23: <strong>$459.40</strong>
  </div>
</div>
```

### Priority 3: Add Real-Time Calculations (JavaScript)

```javascript
// Auto-calculate Net columns
function updateRecapNet(row) {
  const lecture = parseFloat(document.querySelector(`[data-cell="B${row}"]`).value) || 0;
  const corr = parseFloat(document.querySelector(`[data-cell="C${row}"]`).value) || 0;
  const net = lecture + corr;
  document.querySelector(`[data-cell="D${row}"]`).value = net.toFixed(2);
}

// Auto-calculate totals
function updateRecapTotals() {
  // Row 10: Sum of rows 6-9
  const b10 = sumCells(['B6', 'B7', 'B8', 'B9']);
  const c10 = sumCells(['C6', 'C7', 'C8', 'C9']);
  const d10 = b10 + c10;

  // Row 14: Net after refunds
  const b14 = b10 + sumCells(['B11', 'B12', 'B13']);
  const c14 = c10 + sumCells(['C11', 'C12', 'C13']);
  const d14 = b14 + c14;

  // Row 18: Total à déposer
  const b18 = b14 + sumCells(['B15', 'B16', 'B17']);
  const c18 = c14 + sumCells(['C15', 'C16', 'C17']);
  const d18 = b18 + c18;

  // Row 20: Total dépôt net
  const b20 = b18 + getCell('B19');
  const c20 = c18 + getCell('C19');
  const d20 = b20 + c20;

  // Row 23: BALANCE FINALE
  const b23 = b20 - getCell('B21');
  const c23 = c20 - getCell('C21');
  const d23 = b23 + c23;

  // Update all calculated fields
  setCell('B10', b10);
  setCell('D10', d10);
  setCell('B14', b14);
  setCell('D14', d14);
  setCell('B18', b18);
  setCell('D18', d18);
  setCell('B20', b20);
  setCell('D20', d20);
  setCell('B23', b23);
  setCell('D23', d23);
}
```

### Priority 4: Add Validation & Warnings

```javascript
// Warn if refunds are positive (should be negative)
if (parseFloat(getCell('B11')) > 0) {
  showWarning('B11', 'Remboursement Gratuité devrait être négatif!');
}

if (parseFloat(getCell('B12')) > 0) {
  showWarning('B12', 'Remboursement Client devrait être négatif!');
}

// Warn if I10 is not zero
const i10 = parseFloat(getCell('I10')) || 0;
if (Math.abs(i10) > 0.01) {
  showWarning('I10', `⚠️ Balance SD n'est pas à $0.00! Vérifier RJ et SD.`);
}
```

---

## 📊 FORMULA SUMMARY

| Cell | Formula (inferred) | Purpose |
|------|-------------------|---------|
| **D6-D9** | `=B{row}+C{row}` | Net = Lecture + Correction |
| **B10** | `=SUM(B6:B9)` | Total cash & checks |
| **D10** | `=B10+C10` | Net total |
| **I10** | `=B23-'SD file'!E39` | Balance check with SD |
| **D11-D13** | `=B{row}+C{row}` | Net refunds |
| **B14** | `=B10+B11+B12+B13` | Net after refunds |
| **D14** | `=B14+C14` | Net total |
| **D16-D17** | `=B{row}+C{row}` | Net DueBack |
| **E16-E17** | `=-D{row}` | Negative for transfer |
| **B18** | `=B14+B15+B16+B17` | Total to deposit |
| **B19** | INPUT? or from SD? | Surplus/Deficit |
| **B20** | `=B18+B19` | Net deposit |
| **B22** | `=B20-B21` or from SD | Canadian deposit |
| **B23** | `=B20-B21` or `=B22` | **BALANCE FINALE** |

---

## ✅ ACTION ITEMS

1. **Read current UI implementation** - Check which fields are currently editable
2. **Make all D columns readonly** - They're calculated (B+C)
3. **Hide or readonly all TOTAL rows** - Rows 10, 14, 18, 20, 23
4. **Clarify B19 (Surplus/déficit)** - Is it INPUT or CALCULATED?
5. **Implement WR/WN buttons** - Auto-fill from DueBack tab totals
6. **Add JavaScript auto-calculations** - Real-time feedback
7. **Add validation** - Warn about negative refunds, I10 balance
8. **Style sections** - Group logically with visual separators
9. **Test with real data** - Use example from procedure

---

**Document Status:** Complete
**Next Step:** Audit current UI implementation and fix identified issues
**Priority:** HIGH - This is the core calculation sheet
