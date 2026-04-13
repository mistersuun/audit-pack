# Depot Structure - Correct Understanding

**Date:** 2025-12-25
**Analysis based on:** SD November 2025 + RJ December 2025

---

## THE COMPLETE WORKFLOW

### 1. SD FILE (Sommaire Journalier des Dépôts)

**File structure:** One sheet per day (1-31)

**Each daily sheet contains:**

| Col | Header | Description |
|-----|--------|-------------|
| 0 | DÉPARTEMENT | Department (RÉCEPTION, SPESA, RESTAURANT, BANQUET, COMPTABILITÉ) |
| 1 | NOM LETTRES MOULÉES | Employee name |
| 2 | CDN /US | Currency (Canadian or US dollars) |
| 3 | MONTANT | Amount declared by employee |
| 4 | **MONTANT VÉRIFIÉ** | ✅ **Verified amount** (counted by auditor) |
| 5 | REMBOURSEMENT | Reimbursement |
| 6 | VARIANCE | Variance (difference) |

**Row 38: TOTAL** - Sum of all columns for the day

**Example (November 1st):**
```
Row 38:
  Col 3 (MONTANT): -462.51
  Col 4 (MONTANT VÉRIFIÉ): 497.804  ← THIS VALUE!
  Col 5 (REMBOURSEMENT): 316.32
  Col 6 (VARIANCE): 643.99
```

---

### 2. RJ RECAP SHEET

**Row 21: Dépôt Canadien**

| Col | Header | Current UI Field Name | Purpose |
|-----|--------|----------------------|---------|
| 0 | Description | Label | "Dépôt Canadien" |
| 1 | Lecture | `depot_canadien_lecture` | Initial reading |
| 2 | Corr. + (-) | `depot_canadien_corr` | Correction amount |
| 3 | Net | (auto-calc) | Lecture + Correction |
| 4 | **(NO HEADER)** | **MISSING!** | **Montant vérifié** from SD |

**Current RJ file (December 23, 2025):**
- Col 1: 459.40
- Col 2: 0.0
- Col 3: 459.40
- Col 4: **2853.18** ← This is the "Montant vérifié" from SD!

---

### 3. RJ DEPOT SHEET

**Purpose:** Detail log of all deposits by client account

**Structure:**
- **Row 5:** "COMPTE CANADIEN" headers
- **Row 6:** Client account numbers
  - Col 0: CLIENT 6 COMPTE # 1844-22
  - Col 9: CLIENT 8 COMPTE # 4743-66
- **Row 8:** Column headers (DATE, MONTANT, SIGNATURE)
- **Rows 9+:** Individual deposit entries

**Column Groups:**

**GROUP 1: CLIENT 6 (Cols 0-2)**
- Col 0: DATE
- Col 1: MONTANT
- Col 2: SIGNATURE

**GROUP 2: (Cols 4-6) - Purpose unclear, might be US account or another client**
- Col 4: DATE
- Col 5: MONTANT
- Col 6: SIGNATURE

**GROUP 3: CLIENT 8 (Cols 8-10)**
- Col 8: DATE
- Col 9: MONTANT
- Col 10: SIGNATURE

---

## THE CONNECTION

```
SD Daily Sheet
  ↓
Row 38, Col 4: TOTAL MONTANT VÉRIFIÉ (e.g., 497.804)
  ↓
RJ Recap Sheet
  ↓
Row 21, Col 4: Montant vérifié (e.g., 2853.18)
  ↓
RJ depot Sheet
  ↓
New entry with DATE, MONTANT, SIGNATURE (logged to CLIENT 6 or CLIENT 8)
```

---

## USER'S COMMENT EXPLAINED

> "normalement on remplit la feuille depot en mettant les chiffres de la colonne montant verifier dans longlet depot"

**Translation:**
"Normally we fill the depot sheet by putting the numbers from the verified amount column in the depot tab"

**This means:**
1. The "Montant vérifié" value from SD's daily summary (Row 38, Col 4)
2. Gets entered/referenced in RJ Recap Row 21, Col 4
3. And gets **logged** as an entry in the depot sheet
4. With: **DATE** + **MONTANT** (verified amount) + **SIGNATURE**

---

## WHY MY IMPLEMENTATION WAS WRONG

**What I did:**
- Created a multi-entry interface with separate sections for CLIENT 6 and CLIENT 8
- Assumed users would manually add multiple deposit entries per day
- Created dynamic row addition with "Ajouter un dépôt" buttons

**Why it was wrong:**
- The depot sheet is a **DETAIL LOG**, not a data entry form
- The primary data entry happens in the **SD file** (Sommaire Journalier)
- The RJ Recap just has a **reference field** for "Montant vérifié"
- The depot sheet entries are probably added **automatically** or through a simpler workflow
- Users don't manually split amounts between CLIENT 6 and CLIENT 8 in the UI

---

## CORRECT UI IMPLEMENTATION

### Fix #1: Add "Montant vérifié" field to Recap

**In Recap Section, Row 21 (Dépôt Canadien):**

```html
<tr>
  <td class="recap-label">Dépôt Canadien</td>
  <td><input type="number" step="0.01" name="depot_canadien_lecture"
             placeholder="0.00"></td>
  <td><input type="number" step="0.01" name="depot_canadien_corr"
             placeholder="0.00"></td>
  <td><input type="number" step="0.01" name="depot_canadien_net"
             placeholder="0.00" readonly></td>
  <!-- ADD THIS: -->
  <td><input type="number" step="0.01" name="depot_canadien_verifie"
             placeholder="0.00" class="montant-verifie-highlight"></td>
</tr>
```

### Fix #2: Simplify Depot Section

**Instead of multi-entry tables, show:**

**Option A: READ-ONLY LOG VIEW**
```html
<div class="depot-section">
  <h4>Dépôt - Détail Log (Read-Only)</h4>
  <p>Les entrées de dépôt sont enregistrées automatiquement du Recap.</p>

  <table class="depot-log-table">
    <thead>
      <tr>
        <th>Client</th>
        <th>Date</th>
        <th>Montant</th>
        <th>Signature</th>
      </tr>
    </thead>
    <tbody id="depot-log-body">
      <!-- Populated from depot sheet data -->
    </tbody>
  </table>

  <div class="depot-totals">
    <p><strong>CLIENT 6 Total:</strong> <span id="client6-total">0.00</span></p>
    <p><strong>CLIENT 8 Total:</strong> <span id="client8-total">0.00</span></p>
    <p><strong>Grand Total:</strong> <span id="depot-grand-total">0.00</span></p>
  </div>
</div>
```

**Option B: SIMPLE SINGLE-ENTRY FORM (if manual entry needed)**
```html
<div class="depot-section">
  <h4>Dépôt - Ajouter une entrée</h4>

  <div class="form-group">
    <label>Client Account:</label>
    <select id="depot-client-select">
      <option value="client6">CLIENT 6 - Compte #1844-22</option>
      <option value="client8">CLIENT 8 - Compte #4743-66</option>
    </select>
  </div>

  <div class="form-group">
    <label>Date:</label>
    <input type="text" id="depot-date" placeholder="DD MOIS">
  </div>

  <div class="form-group">
    <label>Montant:</label>
    <input type="number" step="0.01" id="depot-montant" placeholder="0.00">
  </div>

  <div class="form-group">
    <label>Signature:</label>
    <input type="text" id="depot-signature" placeholder="Initiales">
  </div>

  <button onclick="addDepotEntry()">Ajouter au dépôt</button>
</div>
```

---

## RECOMMENDED APPROACH

**For now, simplest implementation:**

1. ✅ **Add "Montant vérifié" field to Recap** (Col 4)
2. ✅ **Remove the complex two-client multi-entry depot section**
3. ✅ **Replace with a READ-ONLY depot log view** that shows existing entries
4. ⏭️ **Later:** Add simple entry form if needed for manual corrections

**This matches the user's workflow:**
- Primary data entry is in SD file
- RJ Recap just has the "Montant vérifié" reference field
- depot sheet is a log/audit trail, not the main data entry point

---

## NEXT STEPS

1. Read current rj.html depot section (lines 203-370)
2. Remove incorrect two-client multi-entry implementation
3. Replace with simplified depot section
4. Update Recap section to include Col 4 ("Montant vérifié") field
5. Add visual highlighting for the "Montant vérifié" field (it's important!)
