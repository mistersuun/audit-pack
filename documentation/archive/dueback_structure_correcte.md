# DueBack# - Structure Correcte ✅

**Date:** 2025-12-30
**Statut:** VALIDÉ avec fichier Excel réel
**Fichier testé:** Rj 12-23-2025-Copie.xls

---

## 🎯 STRUCTURE VALIDÉE

### Formule Correcte (0-indexed)

```python
def get_dueback_row_for_day(day):
    balance_row = 2 + (day * 2)      # ← CORRECT!
    operations_row = balance_row + 1
    return balance_row, operations_row
```

### Exemples

| Jour | balance_row | operations_row | Excel rows |
|------|-------------|----------------|------------|
| 1 | 4 | 5 | 5, 6 |
| 11 | 24 | 25 | 25, 26 |
| 23 | 48 | 49 | 49, 50 |
| 31 | 64 | 65 | 65, 66 |

---

## 📊 CONTENU DES ROWS

### Balance Row (Première ligne du jour)

**Contient:**
- ✅ **Previous** (en négatif) dans colonnes C-Y
- ✅ **R/J** (Recap Journal) dans colonne B
- ✅ **Total Z** dans colonne Z ← **Important!**
- ✅ **DATE** = jour actuel + 1 ⚠️

**Exemple jour 11 (row 24, Excel row 25):**
```
DATE=11.0, B=-820.87, C=-273.49, E=-466.09, Q=-262.24, Z=0.0
```

### Operations Row (Deuxième ligne du jour)

**Contient:**
- ✅ **Nouveau** (en positif) dans colonnes C-Y
- ✅ **DATE** = jour actuel
- ⚠️ Colonnes B et Z sont **vides**

**Exemple jour 11 (row 25, Excel row 26):**
```
DATE=11.0, C=630.88, E=513.41, Q=755.09
```

---

## 🧮 CALCUL DU NET

Pour un réceptionniste donné un jour X:

```
Previous (jour X) = valeur dans balance_row (en négatif)
Nouveau (jour X) = valeur dans operations_row (en positif)

Net = Nouveau - abs(Previous)
```

**Exemple KRAY jour 11:**
```
balance_row (24): KRAY = -262.24  → Previous = 262.24
operations_row (25): KRAY = 755.09 → Nouveau = 755.09

Net = 755.09 - 262.24 = 492.85 (refunds du jour)
```

---

## 📍 TOTAL Z - EMPLACEMENT

### ✅ CONFIRMATION

**Le Total Z est dans balance_row, PAS operations_row!**

```python
def get_dueback_day_total(rj_data, day):
    sheet = rj_data.get('DUBACK#')

    balance_row = 2 + (day * 2)  # ← Total Z est ICI
    Z_COL = 25  # Colonne Z

    total = sheet[balance_row][Z_COL]
    return total
```

### Totaux Réels du Fichier

| Jour | Row (0-idx) | Excel Row | Total Z |
|------|-------------|-----------|---------|
| 3 | 8 | 9 | (vide) |
| 9 | 20 | 21 | (vide) |
| 10 | 22 | 23 | 0.03 |
| 11 | 24 | 25 | 0.0 |

**Note:** La plupart des jours ont Z=0.0, ce qui est normal (balance).

---

## 🔄 PATTERN DÉTAILLÉ

### Visualisation Jour 10 et 11

```
Row 22 (Excel 23): Jour 10 balance_row
├─ DATE: 10.0
├─ B (R/J): -540.63
├─ KRAY: -55.24 (Previous négatif)
└─ Z: 0.03 (Total)

Row 23 (Excel 24): Jour 10 operations_row
├─ DATE: 10.0
├─ KRAY: 262.27 (Nouveau positif)
└─ Z: vide

Row 24 (Excel 25): Jour 11 balance_row
├─ DATE: 11.0
├─ B (R/J): -820.87
├─ KRAY: -262.24 (Previous négatif)
└─ Z: 0.0 (Total)

Row 25 (Excel 26): Jour 11 operations_row
├─ DATE: 11.0
├─ KRAY: 755.09 (Nouveau positif)
└─ Z: vide
```

---

## 💻 IMPLÉMENTATION BACKEND

### Fonction pour Lire le Total

```python
# utils/rj_reader.py

def get_dueback_day_total(rj_data, day):
    """
    Get the total from column Z for a specific day.

    Args:
        rj_data: Dictionary with sheet data
        day: Day number (1-31)

    Returns:
        float: Total value from column Z balance_row
    """
    sheet = rj_data.get('DUBACK#')
    if not sheet:
        return 0.0

    # Balance row contains the Total Z
    balance_row = 2 + (day * 2)
    Z_COL = 25

    # Validate
    if balance_row >= len(sheet):
        return 0.0
    if Z_COL >= len(sheet[balance_row]):
        return 0.0

    cell = sheet[balance_row][Z_COL]

    # Return numeric value
    if isinstance(cell, (int, float)):
        return float(cell)

    return 0.0
```

### Fonction pour Lire Previous et Nouveau

```python
def get_dueback_entry(rj_data, day, receptionist_col):
    """
    Get Previous and Nouveau for a receptionist on a given day.

    Args:
        rj_data: Dictionary with sheet data
        day: Day number (1-31)
        receptionist_col: Column index (2-24 for C-Y)

    Returns:
        dict: {'previous': float, 'nouveau': float, 'net': float}
    """
    from utils.rj_mapper import get_dueback_row_for_day

    sheet = rj_data.get('DUBACK#')
    if not sheet:
        return {'previous': 0.0, 'nouveau': 0.0, 'net': 0.0}

    balance_row, operations_row = get_dueback_row_for_day(day)

    # Previous is in balance_row (negative)
    previous_cell = sheet[balance_row][receptionist_col]
    previous = abs(float(previous_cell)) if isinstance(previous_cell, (int, float)) else 0.0

    # Nouveau is in operations_row (positive)
    nouveau_cell = sheet[operations_row][receptionist_col]
    nouveau = float(nouveau_cell) if isinstance(nouveau_cell, (int, float)) else 0.0

    # Net = refunds made today
    net = nouveau - previous

    return {
        'previous': previous,
        'nouveau': nouveau,
        'net': net
    }
```

---

## 🎨 IMPLÉMENTATION FRONTEND

### Afficher le Total Z

```javascript
function updateDuebackTotal(day) {
    fetch(`/api/rj/dueback/total?day=${day}`)
        .then(res => res.json())
        .then(data => {
            const total = data.total || 0;

            const elem = document.getElementById('dueback-day-total');
            elem.textContent = formatCurrency(total);

            // Color coding
            if (Math.abs(total) < 0.01) {
                elem.style.color = '#198754';  // Green (balanced)
            } else if (total < 0) {
                elem.style.color = '#dc3545';  // Red (negative)
            } else {
                elem.style.color = '#0d6efd';  // Blue (positive)
            }
        });
}
```

### Route API

```python
# routes/rj.py

@rj_bp.route('/api/rj/dueback/total', methods=['GET'])
def get_dueback_total():
    """Get DueBack total for a specific day from column Z."""
    from utils.rj_reader import get_dueback_day_total

    try:
        day = int(request.args.get('day', 1))

        rj_data = session.get('rj_data')
        if not rj_data:
            return jsonify({'error': 'No RJ file loaded'}), 400

        total = get_dueback_day_total(rj_data, day)

        return jsonify({
            'total': total,
            'day': day
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## ⚠️ ERREURS CORRIGÉES

### ❌ ERREUR 1: Mauvaise Formule

**Ancien code (FAUX):**
```python
balance_row = 3 + (day * 2)  # ❌ FAUX
```

**Nouveau code (CORRECT):**
```python
balance_row = 2 + (day * 2)  # ✅ CORRECT
```

### ❌ ERREUR 2: Total Z dans operations_row

**Ancienne compréhension (FAUSSE):**
> "Le total Z est dans operations_row (deuxième ligne)"

**Compréhension correcte:**
> "Le total Z est dans balance_row (première ligne)"

### ❌ ERREUR 3: Mauvais Mapping des Rows

**Ancien mapping:**
- Jour 1: rows 5, 6 ❌
- Jour 11: rows 25, 26 ❌

**Mapping correct:**
- Jour 1: rows 4, 5 ✅
- Jour 11: rows 24, 25 ✅

---

## ✅ CHECKLIST DE VALIDATION

- [x] Formule corrigée dans `utils/rj_mapper.py`
- [x] Validé avec fichier Excel réel (Rj 12-23-2025-Copie.xls)
- [x] Total Z confirmé dans balance_row
- [x] Pattern Previous/Nouveau confirmé
- [x] Documentation mise à jour
- [ ] Tests avec plusieurs jours
- [ ] Implémentation dans routes/rj.py
- [ ] Implémentation dans templates/rj.html

---

## 📝 NOTES IMPORTANTES

1. **DATE Column Quirk**: La balance_row contient DATE=jour actuel, mais la valeur représente le Previous du jour précédent + R/J

2. **Previous est Négatif**: Dans Excel, le Previous est stocké en négatif pour faciliter les calculs de somme

3. **Total Z Calculation**: On ne calcule PAS le total Z - on le LIT depuis Excel. Excel a sa propre formule pour le calculer.

4. **Empty Cells**: Si un réceptionniste n'a pas de DueBack pour un jour, les cellules sont vides (pas 0)

---

**Document créé:** 2025-12-30
**Fichier corrigé:** utils/rj_mapper.py
**Statut:** ✅ VALIDÉ et CORRIGÉ
