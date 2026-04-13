# DueBack Column Z - Structure Réelle 📊

**Date:** 2025-12-30
**Fichier analysé:** Rj 12-23-2025-Copie.xls
**Sheet:** DUBACK#

---

## 🎯 RÉPONSE À LA QUESTION

**Question:** Le total dans la colonne Z est sur une ligne ou deux?

**Réponse:** ✅ **UNE SEULE LIGNE par jour**

---

## 📐 STRUCTURE DE LA COLONNE Z

### Pattern Général

Chaque jour a **2 rows** dans Excel (comme toutes les colonnes de réceptionnistes), mais la colonne Z n'utilise que **la deuxième row** pour afficher le total.

```
Jour X:
├─ Balance Row (première ligne):    VIDE ('')
└─ Operations Row (deuxième ligne):  TOTAL ($XXX.XX)
```

### Exemple Concret - Jour 11

**Excel Rows 26-27** (0-indexed: 25-26):

```
Row 26 (Balance):    Z26 = '' (VIDE)
Row 27 (Operations): Z27 = 0.0 (TOTAL)
```

**Comparaison avec colonnes de réceptionnistes:**

| Colonne | Balance Row (26) | Operations Row (27) |
|---------|------------------|---------------------|
| C (Araujo) | 630.88 | '' (vide) |
| E (Seyfi) | 513.41 | '' (vide) |
| Z (Total) | '' (vide) | **0.0** |

**Observation:** C'est l'inverse des colonnes de réceptionnistes!
- **Réceptionnistes:** Nouveau va dans balance_row, operations_row est vide
- **Total (Z):** balance_row est vide, total va dans operations_row

---

## 📊 DONNÉES RÉELLES DU FICHIER

### Toutes les Cellules Non-Vides dans Colonne Z

| Excel Row | 0-indexed Row | Valeur | Signification |
|-----------|---------------|--------|---------------|
| Z2 | 1 | 'Total' | Header |
| Z11 | 10 | -481.91 | **Jour 3** total |
| Z17 | 16 | -200.00 | **Jour 6** total |
| Z23 | 22 | 0.03 | **Jour 9** total |
| Z45 | 44 | 100.0 | **Jour 20** total |
| Z67 | 66 | 22163.93 | **Total final** |

### Calcul du Jour depuis Row Number

Pour trouver quel jour correspond à une row:

```python
# Si on a une row avec une valeur dans Z:
operations_row = row_index  # (0-indexed)
balance_row = operations_row - 1

# Formule inverse:
day = (balance_row - 3) / 2
```

**Exemples:**
- Row 10 (Z11): balance_row=9, day=(9-3)/2 = **Jour 3**
- Row 16 (Z17): balance_row=15, day=(15-3)/2 = **Jour 6**
- Row 22 (Z23): balance_row=21, day=(21-3)/2 = **Jour 9**
- Row 44 (Z45): balance_row=43, day=(43-3)/2 = **Jour 20**

---

## 🧮 COMMENT CALCULER LE TOTAL Z

### Formule

Pour un jour donné, le total Z = somme de tous les **Nouveau** (balance_row) des réceptionnistes:

```python
def calculate_day_total(sheet, day):
    balance_row = 3 + (day * 2)

    total = 0.0
    # Colonnes C à Y (2 à 24) = 23 réceptionnistes
    for col in range(2, 25):  # C=2, Y=24
        cell = sheet.cell(balance_row, col)
        if cell.ctype in [2, 3]:  # Number or Date
            total += float(cell.value)

    return total
```

### Où Stocker le Total

```python
operations_row = balance_row + 1
Z_COL = 25  # Colonne Z

# Write total to operations_row (pas balance_row!)
sheet.write(operations_row, Z_COL, total)
```

---

## 📋 MAPPING DES ROWS PAR JOUR

| Jour | Balance Row (Excel) | Operations Row (Excel) | 0-indexed Operations | Total dans Z |
|------|---------------------|------------------------|----------------------|--------------|
| 1 | 6 | 7 | 6 | Z7 |
| 2 | 8 | 9 | 8 | Z9 |
| 3 | 10 | **11** | 10 | **Z11** (-481.91) |
| 4 | 12 | 13 | 12 | Z13 |
| 5 | 14 | 15 | 14 | Z15 |
| 6 | 16 | **17** | 16 | **Z17** (-200.00) |
| 7 | 18 | 19 | 18 | Z19 |
| 8 | 20 | 21 | 20 | Z21 |
| 9 | 22 | **23** | 22 | **Z23** (0.03) |
| 10 | 24 | 25 | 24 | Z25 |
| 11 | 26 | 27 | 26 | Z27 (0.0) |
| ... | ... | ... | ... | ... |
| 20 | 44 | **45** | 44 | **Z45** (100.0) |
| 31 | 66 | 67 | 66 | Z67 (final) |

---

## 🎨 IMPLICATIONS POUR LE UI

### Affichage du Total

Quand l'utilisateur sélectionne un jour:

```javascript
function getDayTotalRow(day) {
  const balanceRow = 3 + (day * 2);
  const operationsRow = balanceRow + 1;  // ← TOTAL IS HERE

  return operationsRow;  // NOT balanceRow!
}
```

### Exemple d'Affichage

```javascript
// User selects Day 11
const day = 11;
const totalRow = 3 + (day * 2) + 1;  // = 27 (0-indexed: 26)

// Read total from Z27
const total = rj_data['DUBACK#'][26][25];  // row 26, col Z (25)

// Display in UI
document.getElementById('dueback-total').textContent = formatCurrency(total);
```

---

## ⚠️ ERREURS À ÉVITER

### ❌ ERREUR 1: Chercher le total dans balance_row
```javascript
// WRONG!
const totalRow = 3 + (day * 2);
const total = sheet[totalRow][Z_COL];  // ← VIDE!
```

### ✅ CORRECT: Chercher le total dans operations_row
```javascript
// CORRECT!
const totalRow = 3 + (day * 2) + 1;
const total = sheet[totalRow][Z_COL];  // ← TOTAL IS HERE
```

### ❌ ERREUR 2: Sommer les deux rows
```javascript
// WRONG!
const total = sheet[balanceRow][Z_COL] + sheet[operationsRow][Z_COL];
// Résultat: 0 + actualTotal = actualTotal (mais confusing!)
```

### ✅ CORRECT: Lire seulement operations_row
```javascript
// CORRECT!
const total = sheet[operationsRow][Z_COL];
```

---

## 🔧 CODE À IMPLÉMENTER

### Backend (Python - utils/rj_reader.py)

```python
def get_dueback_day_total(rj_data, day):
    """
    Get total from column Z for a given day.

    Args:
        rj_data: Parsed RJ workbook data
        day: Day number (1-31)

    Returns:
        float: Total for the day from column Z
    """
    sheet = rj_data.get('DUBACK#')
    if not sheet:
        return 0.0

    # Calculate operations row (where total is stored)
    balance_row = 3 + (day * 2)
    operations_row = balance_row + 1

    # Column Z is index 25
    Z_COL = 25

    if operations_row >= len(sheet):
        return 0.0

    if Z_COL >= len(sheet[operations_row]):
        return 0.0

    cell = sheet[operations_row][Z_COL]

    # Return numeric value or 0
    if isinstance(cell, (int, float)):
        return float(cell)

    return 0.0
```

### Frontend (JavaScript)

```javascript
function updateDuebackTotal(day) {
  // Get total from backend for this day
  fetch(`/api/rj/dueback/total?day=${day}`)
    .then(res => res.json())
    .then(data => {
      const total = data.total || 0;

      // Update display
      const totalElement = document.getElementById('dueback-day-total');
      totalElement.textContent = formatCurrency(total);

      // Color coding
      if (total < 0) {
        totalElement.style.color = '#dc3545';  // Red
      } else if (total > 0) {
        totalElement.style.color = '#198754';  // Green
      } else {
        totalElement.style.color = '#6c757d';  // Gray
      }
    });
}
```

---

## 📝 RÉSUMÉ POUR LE DÉVELOPPEUR

### Ce qu'il faut retenir:

1. ✅ **Column Z a UNE ligne de total par jour** (pas deux)
2. ✅ **Le total est dans operations_row** (pas balance_row)
3. ✅ **operations_row = balance_row + 1**
4. ✅ **balance_row = 3 + (day × 2)**
5. ✅ **Le total est la somme des colonnes C à Y (balance_row)**

### Pattern inversé:

| Type | Balance Row | Operations Row |
|------|-------------|----------------|
| Réceptionniste | **Nouveau value** | vide |
| Total (Z) | vide | **Total value** |

### Formule finale:

```python
total_row_index = 3 + (day * 2) + 1  # +1 for operations row
Z_column_index = 25
total_value = sheet[total_row_index][Z_column_index]
```

---

**Document Status:** ✅ Validé avec données réelles
**Fichier analysé:** Rj 12-23-2025-Copie.xls
**Date:** 2025-12-30
