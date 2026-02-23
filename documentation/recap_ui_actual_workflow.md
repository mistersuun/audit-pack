# RECAP - Workflow RÉEL (Validé par l'utilisateur)

**Date:** 2025-12-29
**Source:** Utilisateur réel + Screenshots

---

## ✅ CE QUI EST REMPLI (INPUT)

### Champs que l'utilisateur remplit manuellement:

1. **Comptant LightSpeed (B6)**
   - Source: Daily Revenue pages 5-6
   - Type: INPUT manuel
   - Toujours positif

2. **Comptant Positouch (B7)**
   - Source: Rapport POSitouch Établissement
   - Type: INPUT manuel
   - Toujours positif

3. **Chèques (B8, B9)** - SI APPLICABLE
   - B8: Chèque payment register AR
   - B9: Chèque Daily Revenu
   - Type: INPUT manuel (checkbox toggle)
   - Rare - la plupart du temps = $0.00

4. **Moins Remboursement Gratuité (B11)**
   - Type: INPUT manuel
   - TOUJOURS NÉGATIF
   - Source: À clarifier (Daily Revenue ou POSitouch?)

5. **Moins Remboursement Client (B12)**
   - Type: INPUT manuel
   - TOUJOURS NÉGATIF
   - Source: À clarifier

6. **Due Back Réception (B16)**
   - Type: INPUT manuel OU auto-fill (bouton WR)
   - Source: Onglet DueBack
   - Toujours positif

7. **Due Back N/B (B17)**
   - Type: INPUT manuel OU auto-fill (bouton WN)
   - Source: Onglet DueBack
   - Toujours positif

8. **Surplus/déficit (B19)**
   - Type: INPUT manuel OU auto-calculate (bouton WS)
   - Source: SD file (variance totale)
   - Peut être positif ou négatif

---

## ❌ CE QUI N'EST PAS REMPLI

### Champs NON utilisés en pratique:

1. **Date (E1)**
   - Auto-propagée depuis l'onglet Controle
   - Pas remplie manuellement dans Recap

2. **Argent Reçu (B24)**
   - **PAS UTILISÉ en pratique**
   - Présent dans la procédure mais pas dans le workflow réel
   - Ne PAS l'ajouter à l'UI

3. **Dépôt US (D21, E21)**
   - Rare, optionnel
   - Pas implémenté pour l'instant

4. **Dépôt Canadien (B22)**
   - CALCULÉ par Excel depuis SD file
   - Ne JAMAIS remplir manuellement
   - ✅ Déjà caché dans l'UI

---

## 📊 CE QUI EST CALCULÉ

### Totaux calculés automatiquement par Excel:

1. **Row 10: TOTAL cash & checks**
   - B10 = B6 + B7 + B8 + B9
   - C10 = C6 + C7 + C8 + C9
   - D10 = D6 + D7 + D8 + D9
   - **STATUS UI:** ❌ Pas affiché actuellement

2. **Row 14: TOTAL après remboursements**
   - B14 = B10 + B11 + B12 + B13
   - (B13 = Remb. Loterie = 0 généralement)
   - **STATUS UI:** ❌ Pas affiché actuellement

3. **Row 18: Total à déposer**
   - B18 = B14 + B15 + B16 + B17
   - (B15 = Exchange US = 0 généralement)
   - **STATUS UI:** ❌ Pas affiché actuellement

4. **Row 20: Total dépôt net**
   - B20 = B18 + B19
   - **STATUS UI:** ❌ Pas affiché actuellement

5. **Row 22: Dépôt Canadien**
   - Lien vers SD file "Montant Vérifié"
   - **STATUS UI:** ✅ Caché (correct)

6. **Row 23: BALANCE FINALE** ⭐⭐⭐
   - B23 = B20 - B21 - B22
   - **C'est le montant le plus important!**
   - Va dans SetD Column B (RJ)
   - **STATUS UI:** ⚠️ Affiché en indicateur en haut, mais pas dans tableau

7. **I10: Balance SD**
   - Formule: `=B23-'file:///K:/SD 2025/[SD Decembre.xls]23'!$E$39`
   - Devrait = $0.00 si tout balance
   - B23 (Recap) doit égaler E39 (SD file jour 23)
   - **STATUS UI:** ✅ Affiché en indicateur en haut

8. **Colonne D (Net) pour chaque row**
   - D6 = B6 + C6
   - D7 = B7 + C7
   - D8 = B8 + C8
   - D9 = B9 + C9
   - D11 = B11 + C11
   - D12 = B12 + C12
   - D16 = B16 + C16
   - D17 = B17 + C17
   - D19 = B19 + C19
   - **STATUS UI:** ❌ Jamais affichée

---

## 🎯 CHANGEMENTS NÉCESSAIRES

### Phase 1: Ajouter Colonne D (Net)

**Actuellement:**
```
| # | Description | Lecture (B) | Corr (C) | Actions |
```

**Après:**
```
| # | Description | Lecture (B) | Corr (C) | Net (D) | Actions |
```

Pour chaque row d'input (6, 7, 8, 9, 11, 12, 16, 17, 19):
- Ajouter cellule D readonly
- Afficher B + C en temps réel
- Style: fond gris, readonly

---

### Phase 2: Ajouter Rows TOTAL

**Row 10 - Total Cash & Checks:**
```html
<tr class="total-row" style="background:#e7f3ff;">
  <td>10</td>
  <td>TOTAL</td>
  <td><span id="recap-b10">$0.00</span></td>
  <td><span id="recap-c10">$0.00</span></td>
  <td><span id="recap-d10">$0.00</span></td>
  <td></td>
</tr>
```

**Row 14 - Total après remboursements:**
```html
<tr class="total-row" style="background:#fff3cd;">
  <td>14</td>
  <td>TOTAL après remb.</td>
  <td><span id="recap-b14">$0.00</span></td>
  <td><span id="recap-c14">$0.00</span></td>
  <td><span id="recap-d14">$0.00</span></td>
  <td></td>
</tr>
```

**Row 18 - Total à déposer:**
```html
<tr class="total-row" style="background:#d4edda;">
  <td>18</td>
  <td>Total à déposer</td>
  <td><span id="recap-b18">$0.00</span></td>
  <td><span id="recap-c18">$0.00</span></td>
  <td><span id="recap-d18">$0.00</span></td>
  <td></td>
</tr>
```

**Row 20 - Total dépôt net:**
```html
<tr class="total-row" style="background:#cfe2ff;">
  <td>20</td>
  <td>Total dépôt net</td>
  <td><span id="recap-b20">$0.00</span></td>
  <td><span id="recap-c20">$0.00</span></td>
  <td><span id="recap-d20">$0.00</span></td>
  <td></td>
</tr>
```

**Row 23 - BALANCE FINALE:**
```html
<tr class="balance-final-row" style="background:#198754; color:white;">
  <td>23</td>
  <td>⭐ BALANCE FINALE</td>
  <td><span id="recap-b23">$0.00</span></td>
  <td><span id="recap-c23">$0.00</span></td>
  <td><span id="recap-d23">$0.00</span></td>
  <td></td>
</tr>
```

---

### Phase 3: JavaScript Calculs Temps Réel

**Fichier:** `static/js/recap-calculations.js`

**Fonctions nécessaires:**
- `getCellValue(cell)` - Lire valeur d'un input
- `formatCurrency(amount)` - Formater en $0.00
- `updateCalculatedCell(id, value)` - Mettre à jour cellule calculée
- `recalculateRecap()` - Recalculer tout
- Event listeners sur tous les inputs

**Formules:**
```javascript
// Colonne D (Net) = B + C
d6 = b6 + c6
d7 = b7 + c7
// ... etc

// Row 10 TOTAL
b10 = b6 + b7 + b8 + b9
c10 = c6 + c7 + c8 + c9
d10 = d6 + d7 + d8 + d9

// Row 14 TOTAL
b14 = b10 + b11 + b12
c14 = c10 + c11 + c12
d14 = d10 + d11 + d12

// Row 18 TOTAL
b18 = b14 + b16 + b17
c18 = c14 + c16 + c17
d18 = d14 + d16 + d17

// Row 20 TOTAL
b20 = b18 + b19
c20 = c18 + c19
d20 = d18 + d19

// Row 23 BALANCE FINALE
b23 = b20
c23 = c20
d23 = d20
```

---

## 🎨 CSS Nécessaire

```css
/* Total Rows */
.total-row {
  font-weight: 600;
  border-top: 2px solid #dee2e6;
  border-bottom: 2px solid #dee2e6;
}

/* Calculated Cells */
.calculated-cell {
  background: #f8f9fa;
  text-align: right;
  padding-right: 1rem;
  font-family: 'Courier New', monospace;
}

.calculated-value {
  font-weight: 600;
  font-size: 0.95rem;
  min-width: 80px;
  display: inline-block;
  text-align: right;
}

/* Balance Final Row */
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
```

---

## ✅ VALIDATION

### Vérifications à faire après implémentation:

1. **Colonne D affichée:** ✓
2. **D = B + C pour toutes les rows:** ✓
3. **Row 10 = somme correcte:** ✓
4. **Row 14 = somme correcte:** ✓
5. **Row 18 = somme correcte:** ✓
6. **Row 20 = somme correcte:** ✓
7. **Row 23 = B20:** ✓
8. **Calculs en temps réel:** ✓
9. **Indicateur balance en haut mis à jour:** ✓
10. **I10 devrait montrer $0.00 si SD balance:** ✓

---

## 📝 NOTES IMPORTANTES

1. **Date (E1):**
   - Vient automatiquement de l'onglet Controle
   - Pas besoin de l'ajouter manuellement dans Recap

2. **Argent Reçu (B24):**
   - PAS utilisé dans le workflow réel
   - Ne PAS l'implémenter

3. **Dépôt Canadien (B22):**
   - Déjà correctement caché ✅
   - Ne PAS permettre l'édition

4. **I10 Balance Check:**
   - Vérifie que Recap (B23) = SD file variance
   - Si ≠ 0, il y a une erreur quelque part

5. **B23 → SetD:**
   - La balance finale (B23/D23) va dans SetD Column B
   - C'est le montant RJ pour le jour en cours

---

**Document Status:** Validé par utilisateur réel
**Ready for Implementation:** Oui
**Priority:** HIGH - Améliorer visibilité des calculs
