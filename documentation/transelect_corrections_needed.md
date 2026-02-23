# Corrections Nécessaires - Transelect UI

**Date:** 2025-12-25

---

## PROBLÈME ACTUEL

Le tableau Transelect dans l'UI manque des colonnes **CRITIQUES** pour la réconciliation:

### Section 1 - Restaurant/Bar (Rows 8-14)

**Colonnes actuellement présentes:**
- ✅ Terminaux B-U (20 colonnes)
- ✅ TOTAL 1 (V) - Readonly
- ❌ **TOTAL 2 (W)** - MANQUANT!
- ✅ POSITOUCH (X) - Readonly
- ❌ **VARIANCE (Y)** - MANQUANT CRITIQUE!
- ⚠️ ESCOMPTE (Z) - Présent pour VISA/MASTER/AMEX mais PAS pour DÉBIT/DISCOVER
- ⚠️ $ (AA) - Présent pour VISA/MASTER/AMEX mais PAS pour DÉBIT/DISCOVER
- ✅ NET (AB) - Readonly

### Section 2 - Réception/Chambres (Rows 20-25)

**Colonnes actuellement présentes:**
- ✅ Bank Report (B) - FreedomPay
- ❌ **Terminal 8 (C)** - MANQUANT!
- ✅ Terminal K053 (D)
- ✅ TOTAL (I) - Readonly
- ✅ Daily Revenue (P) - Readonly
- ❌ **VARIANCE (Q)** - MANQUANT CRITIQUE!
- ⚠️ ESCOMPTE% (R) - Présent mais pas dans toutes les lignes
- ✅ $ escompte (S) - Readonly
- ✅ NET GEAC (T) - Readonly

---

## EXEMPLE: Comment Row 9 (DÉBIT) DEVRAIT être

### Structure Actuelle (INCOMPLÈTE):
```html
<td class="excel-cell"><input... data-cell="V9" readonly></td>  <!-- TOTAL 1 -->
<td class="excel-cell"></td>  <!-- VIDE! Devrait être W9 -->
<td class="excel-cell"><input... data-cell="X9" readonly></td>  <!-- POSITOUCH -->
<td class="excel-cell"></td>  <!-- VIDE! Devrait être Y9 VARIANCE -->
<td class="excel-cell"></td>  <!-- VIDE! Devrait être Z9 ESCOMPTE -->
<td class="excel-cell"></td>  <!-- VIDE! Devrait être AA9 $ -->
<td class="excel-cell"><input... data-cell="AB9" readonly></td>  <!-- NET -->
```

### Structure CORRIGÉE (COMPLÈTE):
```html
<!-- V: TOTAL 1 - Auto-calculé -->
<td class="excel-cell">
  <input type="number" step="0.01" class="excel-input transelect-total1"
         data-cell="V9" data-row="9" placeholder="0.00" readonly
         style="background:#f0f0f0;">
</td>

<!-- W: TOTAL 2 - Entrée manuelle ou calculé -->
<td class="excel-cell">
  <input type="number" step="0.01" class="excel-input"
         data-cell="W9" placeholder="0.00">
</td>

<!-- X: POSITOUCH - Readonly -->
<td class="excel-cell">
  <input type="number" step="0.01" class="excel-input"
         data-cell="X9" placeholder="0.00" readonly
         style="background:#f0f0f0;">
</td>

<!-- Y: VARIANCE - Auto-calculé avec validation visuelle -->
<td class="excel-cell">
  <input type="number" step="0.01" class="excel-input transelect-variance"
         data-cell="Y9" data-row="9" placeholder="0.00" readonly
         style="background:#f0f0f0;">
</td>

<!-- Z: ESCOMPTE% - 0% pour DÉBIT -->
<td class="excel-cell">
  <input type="number" step="0.01" class="excel-input"
         data-cell="Z9" value="0" placeholder="0.00">
</td>

<!-- AA: $ escompte - Auto-calculé -->
<td class="excel-cell">
  <input type="number" step="0.01" class="excel-input transelect-escompte"
         data-cell="AA9" data-row="9" placeholder="0.00" readonly
         style="background:#f0f0f0;">
</td>

<!-- AB: NET - Auto-calculé -->
<td class="excel-cell">
  <input type="number" step="0.01" class="excel-input transelect-net"
         data-cell="AB9" data-row="9" placeholder="0.00" readonly
         style="background:#f0f0f0;">
</td>
```

---

## CORRECTIONS À FAIRE

### 1. Row 8 (Numéros de Terminaux)

**AJOUTER:**
- Après col V: Vider W8 (pas de numéro)
- Après col X: Vider Y8, Z8, AA8 (pas de numéros pour ces colonnes)

### 2. Row 9 (DÉBIT)

**AJOUTER colonnes:**
- W9: TOTAL 2 (input editable)
- Y9: VARIANCE (readonly, auto-calculé)
- Z9: ESCOMPTE = 0 (DÉBIT n'a pas d'escompte)
- AA9: $ = 0 (auto-calculé)

### 3. Row 10 (VISA)

**AJOUTER colonnes:**
- W10: TOTAL 2 (input editable)
- Y10: VARIANCE (readonly, auto-calculé)
- **Modifier Z10:** Mettre valeur par défaut à 0.02 (0.02%)
- AA10: Déjà présent ✅

### 4. Row 11 (MASTER)

**AJOUTER colonnes:**
- W11: TOTAL 2 (input editable)
- Y11: VARIANCE (readonly, auto-calculé)
- **Modifier Z11:** Mettre valeur par défaut à 0.01 (0.01%)
- AA11: Déjà présent ✅

### 5. Row 12 (DISCOVER)

**AJOUTER colonnes:**
- W12: TOTAL 2 (input editable)
- Y12: VARIANCE (readonly, auto-calculé)
- **Modifier Z12:** Mettre valeur par défaut à 0.03 (0.03%)
- **AJOUTER AA12:** $ escompte (auto-calculé)

### 6. Row 13 (AMEX)

**AJOUTER colonnes:**
- W13: TOTAL 2 (input editable)
- Y13: VARIANCE (readonly, auto-calculé)
- **Modifier Z13:** Mettre valeur par défaut à 0.03 (0.03%)
- AA13: Déjà présent ✅

### 7. Row 14 (TOTAL)

**AJOUTER colonnes:**
- W14: TOTAL de W (auto-calculé, readonly)
- Y14: TOTAL de Y (auto-calculé, readonly)
- Z14: Vide (pas de total pour %)
- AA14: Déjà présent ✅

### 8. Section Réception - Rows 20-25

**Row 20 (DÉBIT):**
- **AJOUTER C20:** Terminal 8 input
- **AJOUTER Q20:** VARIANCE (readonly, auto-calculé)
- **AJOUTER R20:** ESCOMPTE = 0

**Row 21 (VISA):**
- **AJOUTER C21:** Terminal 8 input
- **AJOUTER Q21:** VARIANCE (readonly, auto-calculé)
- **Modifier R21:** Mettre valeur par défaut à 0.02

**Row 22 (MASTER):**
- **AJOUTER C22:** Terminal 8 input
- **AJOUTER Q22:** VARIANCE (readonly, auto-calculé)
- **Modifier R22:** Mettre valeur par défaut à 0.01

**Row 24 (AMEX):**
- **AJOUTER C24:** Terminal 8 input
- **AJOUTER Q24:** VARIANCE (readonly, auto-calculé)
- **Modifier R24:** Mettre valeur par défaut à 0.03

**Row 25 (TOTAL):**
- **AJOUTER C25:** TOTAL Terminal 8 (readonly)
- **AJOUTER Q25:** TOTAL VARIANCE (readonly)
- Vider R25 (pas de total pour %)

---

## JAVASCRIPT NÉCESSAIRE

### 1. Fonction de Calcul VARIANCE (Section Restaurant)

```javascript
function calculateTranselectRestaurantVariance(row) {
  // Récupérer les valeurs
  const total1 = parseFloat(document.querySelector(`[data-cell="V${row}"]`)?.value || 0);
  const total2 = parseFloat(document.querySelector(`[data-cell="W${row}"]`)?.value || 0);
  const positouch = parseFloat(document.querySelector(`[data-cell="X${row}"]`)?.value || 0);

  // Calculer VARIANCE = (TOTAL1 + TOTAL2) - POSITOUCH
  const variance = (total1 + total2) - positouch;

  // Afficher dans Y
  const varianceInput = document.querySelector(`[data-cell="Y${row}"]`);
  if (varianceInput) {
    varianceInput.value = variance.toFixed(2);

    // Validation visuelle
    if (Math.abs(variance) < 0.01) {
      // Balance! Vert
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
      varianceInput.style.fontWeight = '600';
    } else {
      // Ne balance pas! Rouge
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
      varianceInput.style.fontWeight = '600';
    }
  }

  return variance;
}
```

### 2. Fonction de Calcul VARIANCE (Section Réception)

```javascript
function calculateTranselectReceptionVariance(row) {
  // Récupérer TOTAL (col I) et Daily Revenue (col P)
  const total = parseFloat(document.querySelector(`[data-cell="I${row}"]`)?.value || 0);
  const dailyRev = parseFloat(document.querySelector(`[data-cell="P${row}"]`)?.value || 0);

  // Calculer VARIANCE = TOTAL - Daily Revenue (DOIT être 0!)
  const variance = total - dailyRev;

  // Afficher dans Q
  const varianceInput = document.querySelector(`[data-cell="Q${row}"]`);
  if (varianceInput) {
    varianceInput.value = variance.toFixed(2);

    // Validation visuelle
    if (Math.abs(variance) < 0.01) {
      // Balance! Vert
      varianceInput.style.backgroundColor = '#d4edda';
      varianceInput.style.color = '#155724';
      varianceInput.style.fontWeight = '600';
    } else {
      // ERREUR! Rouge vif
      varianceInput.style.backgroundColor = '#f8d7da';
      varianceInput.style.color = '#721c24';
      varianceInput.style.fontWeight = '600';
    }
  }

  return variance;
}
```

### 3. Fonction de Calcul $ Escompte et NET

```javascript
function calculateTranselectEscompte(row) {
  // Récupérer TOTAL 1 + TOTAL 2
  const total1 = parseFloat(document.querySelector(`[data-cell="V${row}"]`)?.value || 0);
  const total2 = parseFloat(document.querySelector(`[data-cell="W${row}"]`)?.value || 0);
  const totalAmount = total1 + total2;

  // Récupérer taux d'escompte (en %)
  const escompteRate = parseFloat(document.querySelector(`[data-cell="Z${row}"]`)?.value || 0);

  // Calculer $ escompte = Total × (Taux / 100)
  const escompteDollars = totalAmount × (escompteRate / 100);

  // Afficher dans AA
  const escompteInput = document.querySelector(`[data-cell="AA${row}"]`);
  if (escompteInput) {
    escompteInput.value = escompteDollars.toFixed(2);
  }

  // Calculer NET = Total - $ escompte
  const net = totalAmount - escompteDollars;

  // Afficher dans AB
  const netInput = document.querySelector(`[data-cell="AB${row}"]`);
  if (netInput) {
    netInput.value = net.toFixed(2);
  }
}
```

### 4. Event Listeners

```javascript
// Recalculer quand les valeurs changent
document.querySelectorAll('#transelect-table .excel-input').forEach(input => {
  input.addEventListener('input', function() {
    const cell = this.dataset.cell;
    const row = parseInt(cell.match(/\d+/)[0]);

    // Recalculer pour cette ligne
    if (row >= 9 && row <= 13) {
      // Section Restaurant
      calculateTranselectRestaurantVariance(row);
      calculateTranselectEscompte(row);
    } else if (row >= 20 && row <= 24) {
      // Section Réception
      calculateTranselectReceptionVariance(row);
    }
  });
});
```

---

## TAUX D'ESCOMPTE PAR DÉFAUT

| Type de Carte | Taux (%) | Colonne Z |
|---------------|----------|-----------|
| DÉBIT         | 0%       | 0         |
| VISA          | 0.02%    | 0.02      |
| MASTER        | 0.01%    | 0.01      |
| DISCOVER      | 0.03%    | 0.03      |
| AMEX          | 0.03%    | 0.03      |

---

## ESTIMATION DU TRAVAIL

**Modifications HTML:**
- Section Restaurant: ~40 ajouts de cellules (7 lignes × 2-4 colonnes manquantes)
- Section Réception: ~12 ajouts de cellules (5 lignes × 2-3 colonnes manquantes)
- **TOTAL: ~52 édits HTML**

**Modifications JavaScript:**
- 3 nouvelles fonctions de calcul
- Event listeners pour auto-calcul
- Validation visuelle VARIANCE
- **TOTAL: ~100 lignes de JS**

**Temps estimé:** 30-45 minutes de travail minutieux

---

## RECOMMANDATION

Vu l'ampleur des modifications et le risque d'erreurs avec tant d'édits manuels, je recommande:

**OPTION A:** Réécrire complètement la section Transelect avec toutes les colonnes correctes (plus rapide, moins d'erreurs)

**OPTION B:** Faire les 52 édits un par un (plus long, plus risqué)

**Quelle option préfères-tu?**
