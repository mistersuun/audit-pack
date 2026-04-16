# RECAP UI - Audit et Plan de Correction

**Date:** 2025-12-29
**Objectif:** Comparer l'UI actuelle avec les exigences de la procédure

---

## 📊 ÉTAT ACTUEL DE L'UI (rj.html lignes 183-360)

### ✅ Ce qui est CORRECT

1. **Balance Indicators (lignes 193-222):**
   - ✅ BALANCE FINALE RECAP affiché en haut
   - ✅ BALANCE SD (I10) affiché en haut
   - Bon format visuel, facile à voir

2. **Row 22 - Dépôt Canadien:**
   - ✅ CACHÉ du formulaire (ligne 320: commentaire seulement)
   - ✅ Sera visible seulement dans l'aperçu Excel
   - Correctement identifié comme calculé par Excel depuis SD file

3. **Boutons WR/WN/WS:**
   - ✅ WR (B16): Auto-fill Due Back Réception
   - ✅ WN (B17): Auto-fill Due Back N/B
   - ✅ WS (B19): Auto-calculate Surplus/Déficit
   - Bien placés dans colonne Actions (F)

4. **Champs Remboursement:**
   - ✅ Rouge pour indiquer négatifs
   - ✅ Attribut `data-always-negative="true"`
   - Bon style visuel (color: #dc3545)

5. **Toggle Chèques:**
   - ✅ Checkbox pour afficher/cacher rows 8-9
   - Logique: la plupart du temps pas de chèques

---

## ❌ PROBLÈMES IDENTIFIÉS

### 🚨 CRITIQUE - Champs Manquants

#### 1. **E1 - Date (MANQUANT!)**
**Gravité:** CRITIQUE
**Localisation actuelle:** Aucune
**Requis par procédure:** OUI - ligne 1 du Recap

**Devrait être:**
```html
<div class="form-group">
  <label>Date de l'audition (E1)</label>
  <input type="date" id="recap-date" data-cell="E1" data-field="date" required>
</div>
```

**Position recommandée:** AVANT le tableau, comme premier champ

---

#### 2. **B24 - Argent Reçu (MANQUANT!)**
**Gravité:** CRITIQUE
**Localisation actuelle:** Aucune
**Requis par procédure:** OUI

**De la procédure (recap_filling_workflow_exact.md ligne 192):**
> **F. Argent Reçu (Ligne 24)**
> ```
> Compter physiquement le cash dans la caisse
> → Entrer montant total dans B24
> ```

**Devrait être:**
```html
<tr>
  <td class="excel-row-header">24</td>
  <td class="excel-label">Argent Reçu</td>
  <td class="excel-cell">
    <input type="number" step="0.01" class="excel-input"
           data-cell="B24" data-field="argent_recu"
           placeholder="0.00" min="0">
  </td>
  <td class="excel-cell" colspan="2">
    <small style="color:#6c757d;">Cash physiquement compté</small>
  </td>
</tr>
```

**Position recommandée:** APRÈS Row 19, AVANT Row 26

---

#### 3. **Rows CALCULÉS - Non affichés**
**Gravité:** MOYENNE (cosmétique mais important pour transparence)
**Localisation actuelle:** Aucune (sauf balance indicators en haut)

**Rows manquants:**
- **Row 10:** Total cash & checks (B10, C10, D10)
- **Row 14:** Total après remboursements (B14, C14, D14)
- **Row 18:** Total à déposer (B18, C18, D18)
- **Row 20:** Total dépôt net (B20, C20, D20)
- **Row 21:** Dépôt US (D21, E21) - INPUT optionnel
- **Row 23:** BALANCE FINALE (B23, C23, D23) - affiché en haut mais pas dans tableau

**Impact:**
- Utilisateur ne voit pas les totaux intermédiaires
- Difficile de valider les calculs
- Pas de transparence sur la logique Excel

---

### ⚠️ MOYEN - Améliorations Nécessaires

#### 4. **Colonne D (Net) - Jamais affichée**
**Gravité:** MOYENNE
**Problème:** La colonne D (B + C) n'est JAMAIS montrée dans le tableau

**De l'analyse (rj_input_vs_calculated_fields.md ligne 90):**
> Colonne D - Net
> - D6, D7, D8, D9, D11, D12, D16, D17, D19, D20, D21, D22, D23
> - Type: CALCULÉ (=B + C)
> - Ne PAS remplir: Excel calcule automatiquement

**Options:**

**Option A (Recommandée):** Ajouter colonne D en READONLY
```html
<th class="excel-header">Net<br>(D)</th>
```
Chaque row aurait:
```html
<td class="excel-cell calculated-cell">
  <span id="recap-d6" class="calculated-value">$0.00</span>
</td>
```

**Option B:** Garder comme maintenant (pas de colonne D visible)

**Recommandation:** Option A - aide l'utilisateur à voir les calculs en temps réel

---

#### 5. **Row 21 - Dépôt US (Manquant)**
**Gravité:** FAIBLE (rare)
**Localisation actuelle:** Aucune
**Requis par procédure:** Optionnel

**De l'analyse (recap_complete_deep_dive.md):**
> Row 21: Dépôt US
> - D21: INPUT - Montant en US dollars
> - E21: CALCULATED - Conversion en CAD
> - Usage: Rare - seulement si dépôt en USD

**Devrait être:**
```html
<tr id="recap-us-deposit-row" style="display:none;">
  <td class="excel-row-header">21</td>
  <td class="excel-label">Dépôt US</td>
  <td class="excel-cell" colspan="2">
    <input type="number" step="0.01" class="excel-input"
           data-cell="D21" data-field="depot_us"
           placeholder="0.00 USD" min="0">
  </td>
  <td class="excel-cell" style="text-align:center;">
    <button onclick="toggleUSDeposit()" class="recap-macro-btn">EC</button>
  </td>
</tr>
```

**Toggle:** Checkbox "Dépôt en US dollars?" (comme pour chèques)

---

## 🎯 PLAN DE CORRECTION COMPLET

### Phase 1: Ajouts CRITIQUES (Faire en PREMIER)

#### 1.1 Ajouter Date (E1)
**Fichier:** `templates/rj.html`
**Ligne:** ~224 (avant le tableau)

**Code à ajouter:**
```html
<div class="form-group" style="margin-bottom:1.5rem;">
  <label style="font-weight:600; color:var(--text); display:block; margin-bottom:0.5rem;">
    📅 Date de l'audition (E1)
  </label>
  <input type="date"
         id="recap-date"
         class="excel-input"
         data-cell="E1"
         data-field="date"
         required
         style="max-width:200px; padding:0.5rem; border:2px solid var(--border); border-radius:6px;">
</div>
```

#### 1.2 Ajouter Argent Reçu (B24)
**Fichier:** `templates/rj.html`
**Ligne:** ~320 (après row 19, avant row 26)

**Code à ajouter:**
```html
<tr>
  <td class="excel-row-header">24</td>
  <td class="excel-label" style="font-weight:600; color:#0d6efd;">💰 Argent Reçu</td>
  <td class="excel-cell">
    <input type="number" step="0.01" class="excel-input"
           data-cell="B24"
           data-field="argent_recu"
           data-always-positive="true"
           placeholder="0.00"
           min="0"
           style="font-weight:600; font-size:1rem;">
  </td>
  <td class="excel-cell" colspan="2">
    <small style="color:#6c757d; font-style:italic;">
      💵 Cash physiquement compté dans la caisse
    </small>
  </td>
</tr>
```

#### 1.3 Mettre à jour rj_mapper.py
**Fichier:** `utils/rj_mapper.py`
**Ligne:** ~39 (après surplus_deficit_corr)

**Code à ajouter:**
```python
RECAP_MAPPING = {
    'date': 'E1',
    'comptant_lightspeed_lecture': 'B6',
    # ... existing fields ...
    'surplus_deficit_corr': 'C19',
    'argent_recu': 'B24',  # ← AJOUTER CETTE LIGNE
    'prepare_par': 'B26',
}
```

**DÉJÀ PRÉSENT** ✅ - Vérifier que la ligne existe

---

### Phase 2: Afficher les Totaux CALCULÉS (RECOMMANDÉ)

#### 2.1 Ajouter Colonne D au header
**Fichier:** `templates/rj.html`
**Ligne:** ~236

**Modifier:**
```html
<thead>
  <tr>
    <th class="excel-header excel-row-header"></th>
    <th class="excel-header">Description</th>
    <th class="excel-header">Lecture<br>(B)</th>
    <th class="excel-header">Corr. +(-)<br>(C)</th>
    <th class="excel-header">Net<br>(D)</th> <!-- AJOUTER -->
    <th class="excel-header" style="width:100px;">Actions<br>(F)</th>
  </tr>
</thead>
```

#### 2.2 Ajouter colonne D à chaque row
**Pour chaque row (6, 7, 8, 9, 11, 12, 16, 17, 19):**

**Exemple pour Row 6:**
```html
<tr>
  <td class="excel-row-header">6</td>
  <td class="excel-label">Comptant LightSpeed</td>
  <td class="excel-cell">
    <input type="number" step="0.01" class="excel-input recap-calc-input"
           data-cell="B6" data-field="comptant_lightspeed_lecture"
           data-always-positive="true" placeholder="0.00" min="0">
  </td>
  <td class="excel-cell">
    <input type="number" step="0.01" class="excel-input recap-calc-input"
           data-cell="C6" data-field="comptant_lightspeed_corr"
           placeholder="0.00">
  </td>
  <!-- AJOUTER CETTE CELLULE -->
  <td class="excel-cell calculated-cell" style="background:#f8f9fa; text-align:right; padding-right:1rem;">
    <span id="recap-d6" class="calculated-value" style="font-weight:600; color:#495057;">$0.00</span>
  </td>
  <td class="excel-cell"></td>
</tr>
```

**Répéter pour:** D7, D8, D9, D11, D12, D16, D17, D19

#### 2.3 Ajouter Rows TOTAL calculés

**Row 10 - Total Cash & Checks:**
```html
<tr class="total-row" style="background:#e7f3ff; font-weight:600;">
  <td class="excel-row-header">10</td>
  <td class="excel-label" style="font-weight:700;">TOTAL</td>
  <td class="excel-cell calculated-cell">
    <span id="recap-b10" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-c10" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-d10" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell"></td>
</tr>
```

**Row 14 - Total après remboursements:**
```html
<tr class="total-row" style="background:#fff3cd; font-weight:600;">
  <td class="excel-row-header">14</td>
  <td class="excel-label" style="font-weight:700;">TOTAL après remb.</td>
  <td class="excel-cell calculated-cell">
    <span id="recap-b14" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-c14" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-d14" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell"></td>
</tr>
```

**Row 18 - Total à déposer:**
```html
<tr class="total-row" style="background:#d4edda; font-weight:600;">
  <td class="excel-row-header">18</td>
  <td class="excel-label" style="font-weight:700;">Total à déposer</td>
  <td class="excel-cell calculated-cell">
    <span id="recap-b18" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-c18" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-d18" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell"></td>
</tr>
```

**Row 20 - Total dépôt net:**
```html
<tr class="total-row" style="background:#cfe2ff; font-weight:600;">
  <td class="excel-row-header">20</td>
  <td class="excel-label" style="font-weight:700;">Total dépôt net</td>
  <td class="excel-cell calculated-cell">
    <span id="recap-b20" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-c20" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-d20" class="calculated-value">$0.00</span>
  </td>
  <td class="excel-cell"></td>
</tr>
```

**Row 23 - BALANCE FINALE:**
```html
<tr class="total-row" style="background:#198754; color:white; font-weight:700; font-size:1.1rem;">
  <td class="excel-row-header" style="color:white;">23</td>
  <td class="excel-label" style="font-weight:700; color:white;">⭐ BALANCE FINALE</td>
  <td class="excel-cell calculated-cell">
    <span id="recap-b23" class="calculated-value" style="color:white;">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-c23" class="calculated-value" style="color:white;">$0.00</span>
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-d23" class="calculated-value" style="color:white;">$0.00</span>
  </td>
  <td class="excel-cell"></td>
</tr>
```

**Note:** Row 23 D23 va aussi dans SetD Column B pour le jour en cours

---

### Phase 3: JavaScript pour Calculs en Temps Réel

**Fichier:** Créer `static/js/recap-calculations.js`

```javascript
/**
 * Recap Real-time Calculations
 * Recalculates all Net (D) columns and TOTAL rows when inputs change
 */

function getInputValue(fieldName) {
  const input = document.querySelector(`[data-field="${fieldName}"]`);
  return input ? parseFloat(input.value) || 0 : 0;
}

function getCellValue(cell) {
  const input = document.querySelector(`[data-cell="${cell}"]`);
  return input ? parseFloat(input.value) || 0 : 0;
}

function formatCurrency(amount) {
  return '$' + amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function updateCalculatedCell(cellId, value) {
  const span = document.getElementById(cellId);
  if (span) {
    span.textContent = formatCurrency(value);

    // Color coding
    if (value < 0) {
      span.style.color = '#dc3545'; // Red
    } else if (value > 0) {
      span.style.color = '#198754'; // Green
    } else {
      span.style.color = '#495057'; // Gray
    }
  }
}

function recalculateRecap() {
  // Get all B and C values
  const b6 = getCellValue('B6');
  const c6 = getCellValue('C6');
  const b7 = getCellValue('B7');
  const c7 = getCellValue('C7');
  const b8 = getCellValue('B8');
  const c8 = getCellValue('C8');
  const b9 = getCellValue('B9');
  const c9 = getCellValue('C9');
  const b11 = getCellValue('B11');
  const c11 = getCellValue('C11');
  const b12 = getCellValue('B12');
  const c12 = getCellValue('C12');
  const b16 = getCellValue('B16');
  const c16 = getCellValue('C16');
  const b17 = getCellValue('B17');
  const c17 = getCellValue('C17');
  const b19 = getCellValue('B19');
  const c19 = getCellValue('C19');

  // Calculate D (Net) = B + C for each row
  const d6 = b6 + c6;
  const d7 = b7 + c7;
  const d8 = b8 + c8;
  const d9 = b9 + c9;
  const d11 = b11 + c11;
  const d12 = b12 + c12;
  const d16 = b16 + c16;
  const d17 = b17 + c17;
  const d19 = b19 + c19;

  // Update D column displays
  updateCalculatedCell('recap-d6', d6);
  updateCalculatedCell('recap-d7', d7);
  updateCalculatedCell('recap-d8', d8);
  updateCalculatedCell('recap-d9', d9);
  updateCalculatedCell('recap-d11', d11);
  updateCalculatedCell('recap-d12', d12);
  updateCalculatedCell('recap-d16', d16);
  updateCalculatedCell('recap-d17', d17);
  updateCalculatedCell('recap-d19', d19);

  // Row 10: Total cash & checks (B10 = B6+B7+B8+B9)
  const b10 = b6 + b7 + b8 + b9;
  const c10 = c6 + c7 + c8 + c9;
  const d10 = d6 + d7 + d8 + d9;

  updateCalculatedCell('recap-b10', b10);
  updateCalculatedCell('recap-c10', c10);
  updateCalculatedCell('recap-d10', d10);

  // Row 14: Total après remboursements (B14 = B10+B11+B12+B13)
  // Note: B13 (Remb. Loterie) = 0 for now
  const b14 = b10 + b11 + b12;
  const c14 = c10 + c11 + c12;
  const d14 = d10 + d11 + d12;

  updateCalculatedCell('recap-b14', b14);
  updateCalculatedCell('recap-c14', c14);
  updateCalculatedCell('recap-d14', d14);

  // Row 18: Total à déposer (B18 = B14+B15+B16+B17)
  // Note: B15 (Exchange US) = 0 for now
  const b18 = b14 + b16 + b17;
  const c18 = c14 + c16 + c17;
  const d18 = d14 + d16 + d17;

  updateCalculatedCell('recap-b18', b18);
  updateCalculatedCell('recap-c18', c18);
  updateCalculatedCell('recap-d18', d18);

  // Row 20: Total dépôt net (B20 = B18+B19)
  const b20 = b18 + b19;
  const c20 = c18 + c19;
  const d20 = d18 + d19;

  updateCalculatedCell('recap-b20', b20);
  updateCalculatedCell('recap-c20', c20);
  updateCalculatedCell('recap-d20', d20);

  // Row 23: BALANCE FINALE (B23 = B20-B21-B22)
  // B21 (Dépôt US) = 0 for now
  // B22 (Dépôt Canadien) = from SD file, for now = 0
  const b23 = b20;
  const c23 = c20;
  const d23 = d20;

  updateCalculatedCell('recap-b23', b23);
  updateCalculatedCell('recap-c23', c23);
  updateCalculatedCell('recap-d23', d23);

  // Update balance indicator at top
  const balanceIndicator = document.getElementById('recap-balance-value');
  if (balanceIndicator) {
    balanceIndicator.textContent = formatCurrency(d23);

    if (Math.abs(d23) < 0.01) {
      balanceIndicator.style.color = '#198754'; // Green - balanced!
    } else {
      balanceIndicator.style.color = '#dc3545'; // Red - not balanced
    }
  }

  // Update balance message
  const balanceMessage = document.getElementById('recap-balance-message');
  if (balanceMessage) {
    if (Math.abs(d23) < 0.01) {
      balanceMessage.textContent = '✅ Parfait! Le RECAP balance.';
      balanceMessage.style.color = '#198754';
    } else {
      balanceMessage.textContent = `⚠️ Différence de ${formatCurrency(d23)}`;
      balanceMessage.style.color = '#dc3545';
    }
  }
}

// Attach listeners to all recap inputs
document.addEventListener('DOMContentLoaded', function() {
  const recapInputs = document.querySelectorAll('.excel-input.recap-calc-input, [data-cell^="B"], [data-cell^="C"]');

  recapInputs.forEach(input => {
    input.addEventListener('input', recalculateRecap);
    input.addEventListener('change', recalculateRecap);
  });

  // Initial calculation
  recalculateRecap();
});
```

**Inclure dans rj.html:**
```html
<script src="{{ url_for('static', filename='js/recap-calculations.js') }}"></script>
```

---

### Phase 4: Optionnel - Dépôt US (Row 21)

**Toggle checkbox:**
```html
<div class="form-group" style="margin-bottom:1rem;">
  <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer;">
    <input type="checkbox" id="recap-has-us-deposit" onchange="toggleUSDeposit()" style="width:20px; height:20px; cursor:pointer;">
    <span>Dépôt en US dollars</span>
  </label>
</div>
```

**Row 21:**
```html
<tr id="recap-us-deposit-row" style="display:none;">
  <td class="excel-row-header">21</td>
  <td class="excel-label">Dépôt US</td>
  <td class="excel-cell" colspan="2">
    <input type="number" step="0.01" class="excel-input recap-calc-input"
           data-cell="D21" data-field="depot_us"
           placeholder="0.00 USD" min="0">
  </td>
  <td class="excel-cell calculated-cell">
    <span id="recap-e21" class="calculated-value">$0.00 CAD</span>
  </td>
  <td class="excel-cell" style="text-align:center;">
    <button onclick="calculateExchange()" class="recap-macro-btn" title="Convertir USD → CAD" style="background:#ffc107; color:#000;">
      EC
    </button>
  </td>
</tr>
```

**JavaScript:**
```javascript
function toggleUSDeposit() {
  const checkbox = document.getElementById('recap-has-us-deposit');
  const row = document.getElementById('recap-us-deposit-row');
  row.style.display = checkbox.checked ? 'table-row' : 'none';

  if (!checkbox.checked) {
    // Clear value
    const input = document.querySelector('[data-cell="D21"]');
    if (input) input.value = '';
  }

  recalculateRecap();
}

function calculateExchange() {
  const usdAmount = getCellValue('D21');
  if (usdAmount > 0) {
    const rate = prompt('Taux de change USD → CAD:', '1.35');
    if (rate && !isNaN(rate)) {
      const cadAmount = usdAmount * parseFloat(rate);
      updateCalculatedCell('recap-e21', cadAmount);

      // Update B21 for calculations
      // Store in hidden field or update directly
      alert(`${formatCurrency(usdAmount)} USD = ${formatCurrency(cadAmount)} CAD`);
    }
  } else {
    alert('Entrez d\'abord le montant en USD');
  }
}
```

---

## 📋 CHECKLIST DE MISE EN ŒUVRE

### ✅ Phase 1 - CRITIQUE (À faire IMMÉDIATEMENT)

- [ ] Ajouter Date (E1) avant le tableau
- [ ] Ajouter Argent Reçu (B24) entre row 19 et row 26
- [ ] Vérifier que `argent_recu` est dans RECAP_MAPPING
- [ ] Tester sauvegarde avec les nouveaux champs

### ✅ Phase 2 - RECOMMANDÉ (Important pour transparence)

- [ ] Ajouter colonne D (Net) au header du tableau
- [ ] Ajouter cellule D calculée pour chaque row (6,7,8,9,11,12,16,17,19)
- [ ] Ajouter Row 10 TOTAL (cash & checks)
- [ ] Ajouter Row 14 TOTAL (après remboursements)
- [ ] Ajouter Row 18 TOTAL (à déposer)
- [ ] Ajouter Row 20 TOTAL (dépôt net)
- [ ] Ajouter Row 23 BALANCE FINALE (déjà affiché en haut, aussi dans tableau)
- [ ] Style CSS pour `.total-row` et `.calculated-cell`

### ✅ Phase 3 - JavaScript

- [ ] Créer `static/js/recap-calculations.js`
- [ ] Implémenter `recalculateRecap()`
- [ ] Ajouter event listeners sur tous les inputs
- [ ] Tester calculs en temps réel
- [ ] Valider formules contre Excel

### ✅ Phase 4 - OPTIONNEL

- [ ] Ajouter checkbox "Dépôt US"
- [ ] Ajouter Row 21 (caché par défaut)
- [ ] Implémenter bouton EC (Exchange Canada)
- [ ] Mettre à jour calculs pour inclure B21

---

## 🎨 CSS NÉCESSAIRE

```css
/* Total Rows Styling */
.total-row {
  font-weight: 600;
  border-top: 2px solid #dee2e6;
  border-bottom: 2px solid #dee2e6;
}

.total-row td {
  padding: 0.75rem 0.5rem !important;
}

/* Calculated Cells (Read-only, gray background) */
.calculated-cell {
  background: #f8f9fa;
  text-align: right;
  padding-right: 1rem;
  font-family: 'Courier New', monospace;
}

.calculated-value {
  font-weight: 600;
  font-size: 0.95rem;
  display: inline-block;
  min-width: 80px;
  text-align: right;
}

/* Balance Final Row (Row 23) - Special */
.balance-final-row {
  background: linear-gradient(135deg, #198754 0%, #0f5132 100%) !important;
  color: white !important;
  font-size: 1.1rem;
  font-weight: 700;
}

.balance-final-row .calculated-value {
  color: white !important;
  font-size: 1.2rem;
}

/* Recap Input Focus */
.recap-calc-input:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
  outline: none;
}
```

---

## 🧪 TESTS À EFFECTUER

### Test 1: Champs Requis
- [ ] Date (E1) ne peut pas être vide
- [ ] Argent Reçu (B24) sauvegarde correctement
- [ ] Préparé par (B26) fonctionne

### Test 2: Calculs Automatiques
- [ ] D6 = B6 + C6 ✓
- [ ] D7 = B7 + C7 ✓
- [ ] B10 = B6+B7+B8+B9 ✓
- [ ] B14 = B10+B11+B12 ✓
- [ ] B18 = B14+B16+B17 ✓
- [ ] B20 = B18+B19 ✓
- [ ] B23 = B20 ✓

### Test 3: Validation
- [ ] Remboursements (B11, B12) deviennent négatifs automatiquement
- [ ] DueBack (B16, B17) toujours positifs
- [ ] Boutons WR/WN remplissent correctement
- [ ] Balance indicator change couleur si ≠ 0

### Test 4: Excel Export
- [ ] Date exporté correctement dans E1
- [ ] Argent Reçu exporté dans B24
- [ ] Dépôt Canadien (B22) reste vide (Excel le calculera)
- [ ] Formules Excel préservées

---

## ❓ QUESTIONS À CLARIFIER AVEC UTILISATEUR

### 1. Sources des Remboursements
**Question:** D'où viennent exactement B11 (Remb. Gratuité) et B12 (Remb. Client)?
- Daily Revenue?
- Rapport POSitouch?
- Autre rapport?

**Action:** Ajouter tooltip explicatif dans l'UI

### 2. Utilisation de la Colonne C
**Question:** Quand utilise-t-on les Corrections (Colonne C)?
- Erreurs de saisie?
- Ajustements après vérification?

**Action:** Comprendre pour mieux guider l'utilisateur

### 3. Bouton WS (Surplus/Déficit)
**Question:** La procédure dit de copier depuis SD. Le bouton WS fait quoi exactement?
- Auto-calculate depuis le tableau?
- Fetch depuis SD file?

**Action:** Clarifier la logique

---

## 📊 RÉSUMÉ DES CHANGEMENTS

| Élément | État Actuel | État Après Corrections | Priorité |
|---------|-------------|------------------------|----------|
| **Date (E1)** | ❌ Manquant | ✅ Champ date requis | CRITIQUE |
| **Argent Reçu (B24)** | ❌ Manquant | ✅ Input number | CRITIQUE |
| **Colonne D (Net)** | ❌ Cachée | ✅ Affichée en readonly | RECOMMANDÉ |
| **Row 10 Total** | ❌ Caché | ✅ Affiché calculé | RECOMMANDÉ |
| **Row 14 Total** | ❌ Caché | ✅ Affiché calculé | RECOMMANDÉ |
| **Row 18 Total** | ❌ Caché | ✅ Affiché calculé | RECOMMANDÉ |
| **Row 20 Total** | ❌ Caché | ✅ Affiché calculé | RECOMMANDÉ |
| **Row 21 Dépôt US** | ❌ Manquant | ⚠️ Optionnel (toggle) | OPTIONNEL |
| **Row 22 Dépôt Can.** | ✅ Caché | ✅ Reste caché | OK |
| **Row 23 Balance** | ⚠️ Indicateur seulement | ✅ Dans tableau aussi | RECOMMANDÉ |
| **JS Calculations** | ❌ Aucun | ✅ Temps réel | RECOMMANDÉ |

---

**Document Status:** Complet - Prêt pour implémentation
**Prochaine Étape:** Implémenter Phase 1 (CRITIQUE) en premier
**Temps Estimé Phase 1:** 30 minutes
**Temps Estimé Phase 2-3:** 2 heures
