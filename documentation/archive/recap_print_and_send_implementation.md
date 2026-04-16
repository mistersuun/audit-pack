# Implémentation: Imprimer Recap et Envoyer dans RJ

**Date:** 2026-01-02
**Objectif:** Implémenter les fonctions "Imprimer Recap" et "Envoyer dans jour/RJ"

---

## 🔍 MACROS ORIGINALES

### 1. imprime_recap() - Imprimer Recap

**Code VBA:**
```vba
Sub imprime_recap()
    Range("A1:f26").Select
    ActiveWindow.SelectedSheets.PrintOut Copies:=1, Collate:=True
End Sub
```

**Ce qu'elle fait:**
- Sélectionne la plage **A1:F26** du Recap
- Imprime 1 copie

**Usage:** Bouton dans Excel pour imprimer rapidement le Recap

---

### 2. envoie_dans_jour() - Envoyer dans l'onglet "jour"

**Code VBA:**
```vba
Sub envoie_dans_jour()
    Value = InputBox("La date a-t-elle été changé o/n?")

    If Value = "o" Or Value = "O" Then
        Range("h19:n19").Select
        Selection.Copy

        Dim test
        test = Trim(Str(Worksheets("controle").Range("vjour").Value))
        test = "ar_" + test
        Application.Goto Reference:=test
        Selection.PasteSpecial Paste:=xlValues, Operation:=xlNone, SkipBlanks:=False, Transpose:=False
        Application.CutCopyMode = False
    End If
End Sub
```

**Ce qu'elle fait:**
1. Demande si la date a été changée (o/n)
2. Si oui:
   - Copie **H19:N19** (ligne de balance/résumé du Recap)
   - Récupère le jour depuis `Controle.vjour` (ex: 23)
   - Construit une référence de plage nommée: "ar_" + jour (ex: "ar_23")
   - Colle les valeurs à cette plage dans l'onglet "jour"

**Exemple:**
- Jour = 23
- Copie H19:N19 du Recap
- Colle à la plage nommée "ar_23" dans l'onglet "jour"

**Hypothèse:** L'onglet "jour" a 31 lignes (une par jour du mois) avec des plages nommées "ar_1" à "ar_31"

---

## 🎯 POUR LA WEB APP

### Option 1: Export PDF/Excel au lieu d'Imprimer

Dans une web app, on ne peut pas imprimer directement. On peut:

1. **Télécharger le RJ Excel** → L'utilisateur imprime depuis Excel
2. **Générer un PDF** → L'utilisateur télécharge et imprime le PDF

**Recommandation:** Option 1 (plus simple)

---

### Option 2: Bouton "Envoyer dans RJ" Automatique

Au lieu de demander "La date a-t-elle été changé?", la web app peut:

1. **Détecter automatiquement** si les données du Recap ont changé
2. **Copier automatiquement** vers l'onglet "jour" quand l'utilisateur clique "Enregistrer"
3. **Ou proposer un bouton** "Envoyer dans RJ" qui fait la copie

---

## 💡 IMPLÉMENTATION RECOMMANDÉE

### Backend: Fonction pour Copier Recap vers "jour"

**Fichier:** `utils/rj_writer.py`

```python
#!/usr/bin/env python3
"""
Fonctions pour écrire dans le RJ Excel
"""

import xlrd
from xlutils.copy import copy
from io import BytesIO


def copy_recap_to_jour(rj_bytes, day):
    """
    Copy Recap summary (H19:N19) to the 'jour' sheet at the appropriate day row.

    Args:
        rj_bytes: BytesIO containing the RJ Excel file
        day: Day of the month (1-31)

    Returns:
        BytesIO: Updated RJ file

    Raises:
        ValueError: If day is not between 1-31
        Exception: If sheets not found or named range not found
    """
    if not 1 <= day <= 31:
        raise ValueError(f"Day must be between 1-31, got {day}")

    # Read RJ
    rj_bytes.seek(0)
    rb = xlrd.open_workbook(file_contents=rj_bytes.read(), formatting_info=True)
    wb = copy(rb)

    # Get sheets
    try:
        recap_read = rb.sheet_by_name('Recap')
        jour_write = wb.get_sheet('jour')
    except:
        raise Exception("Sheets 'Recap' or 'jour' not found")

    # Copy H19:N19 from Recap (row 18, cols 7-13 in 0-indexed)
    # H=7, I=8, J=9, K=10, L=11, M=12, N=13
    source_row = 18  # Row 19 in Excel (0-indexed = 18)
    source_cols = range(7, 14)  # H to N (7-13 inclusive)

    # Destination in 'jour' sheet
    # We need to find the row for this day
    # Assuming the structure is: row = 2 + (day - 1) * 2 or similar
    # This needs to be verified by analyzing the 'jour' sheet structure

    # For now, let's assume there are named ranges "ar_1" to "ar_31"
    # We need to find which row "ar_{day}" refers to

    # Since xlrd/xlwt don't easily support named ranges for writing,
    # we'll need to hardcode or parse the named ranges

    # ALTERNATIVE: Use a mapping based on day
    # Example: If each day takes 2 rows starting from row 3
    dest_row = 2 + (day - 1) * 2  # This is a guess, needs verification

    # Copy values
    for col_offset, col in enumerate(source_cols):
        value = recap_read.cell(source_row, col).value
        jour_write.write(dest_row, col, value)

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return output


def get_recap_summary_row(rj_bytes):
    """
    Get the summary row (H19:N19) from Recap.

    Args:
        rj_bytes: BytesIO containing the RJ Excel file

    Returns:
        dict: Dictionary with column names and values
    """
    rj_bytes.seek(0)
    rb = xlrd.open_workbook(file_contents=rj_bytes.read())

    try:
        recap = rb.sheet_by_name('Recap')
    except:
        raise Exception("Sheet 'Recap' not found")

    # Read row 19 (index 18), columns H-N (indices 7-13)
    row = 18
    cols = {
        'H': 7,
        'I': 8,
        'J': 9,
        'K': 10,
        'L': 11,
        'M': 12,
        'N': 13
    }

    result = {}
    for col_name, col_idx in cols.items():
        result[col_name] = recap.cell(row, col_idx).value

    return result


# For testing
if __name__ == "__main__":
    # Test getting recap summary
    rj_file = '/Users/canaldesuez/Documents/Projects/audit-pack/documentation/complete_updated_files_to_analyze/Rj 12-23-2025-Copie.xls'

    with open(rj_file, 'rb') as f:
        rj_bytes = BytesIO(f.read())

    summary = get_recap_summary_row(rj_bytes)
    print("Recap Summary (Row 19, H-N):")
    for col, value in summary.items():
        print(f"  {col}: {value}")
```

---

### Backend: Route API

**Fichier:** `routes/rj.py`

```python
@rj_bp.route('/api/rj/recap/send-to-jour', methods=['POST'])
@login_required
def send_recap_to_jour():
    """
    Copy Recap summary to 'jour' sheet for the current day.

    Request body:
        {
            "day": 23  # Day of the month (1-31)
        }

    Returns:
        {
            "success": true,
            "message": "Recap envoyé dans RJ pour le jour 23"
        }
    """
    session_id = session.get('user_session_id', 'default')
    if session_id not in RJ_FILES:
        return jsonify({'success': False, 'error': 'No RJ file uploaded'}), 400

    data = request.get_json()
    day = data.get('day', type=int)

    if not day or not 1 <= day <= 31:
        return jsonify({'success': False, 'error': 'Day must be between 1-31'}), 400

    try:
        from utils.rj_writer import copy_recap_to_jour

        # Get current RJ
        rj_bytes = RJ_FILES[session_id]

        # Copy Recap to jour
        updated_rj = copy_recap_to_jour(rj_bytes, day)

        # Update in session
        RJ_FILES[session_id] = updated_rj

        return jsonify({
            'success': True,
            'message': f'Recap envoyé dans RJ pour le jour {day}'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### Frontend: Bouton dans l'onglet Recap

**Fichier:** `templates/rj.html`

Dans la section Recap, ajouter:

```html
<!-- Bouton Envoyer dans RJ -->
<div class="mt-3">
  <button
    type="button"
    class="btn btn-success"
    id="send-recap-to-rj-btn"
    onclick="sendRecapToRJ()"
  >
    <i class="fas fa-paper-plane"></i> Envoyer dans RJ
  </button>
</div>

<!-- Message de résultat -->
<div id="send-recap-result" style="display: none;" class="alert mt-3"></div>
```

**JavaScript:**

```javascript
async function sendRecapToRJ() {
  // Get current day from Controle (if displayed) or ask user
  const day = document.getElementById('recap-day-input')?.value ||
              prompt("Quel jour du mois? (1-31)");

  if (!day || day < 1 || day > 31) {
    showSendRecapResult('error', 'Jour invalide. Doit être entre 1 et 31.');
    return;
  }

  // Show loading
  showSendRecapResult('info', 'Envoi en cours...');

  try {
    const res = await fetch('/api/rj/recap/send-to-jour', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ day: parseInt(day) })
    });

    const data = await res.json();

    if (data.success) {
      showSendRecapResult('success', data.message);
    } else {
      showSendRecapResult('error', data.error);
    }
  } catch (error) {
    showSendRecapResult('error', `Erreur: ${error.message}`);
  }
}

function showSendRecapResult(type, message) {
  const resultDiv = document.getElementById('send-recap-result');

  const alertClass = {
    'success': 'alert-success',
    'error': 'alert-danger',
    'info': 'alert-info'
  }[type] || 'alert-info';

  resultDiv.className = `alert ${alertClass}`;
  resultDiv.textContent = message;
  resultDiv.style.display = 'block';

  // Auto-hide after 5 seconds
  setTimeout(() => {
    resultDiv.style.display = 'none';
  }, 5000);
}
```

---

## ⚠️ IMPORTANT: Structure de l'onglet "jour"

**Il faut d'abord analyser l'onglet "jour" pour comprendre:**

1. Quelle est la structure (combien de lignes par jour?)
2. Où se trouvent les plages nommées "ar_1" à "ar_31"?
3. À quelle row correspond chaque jour?

**Script d'analyse:**

```python
#!/usr/bin/env python3
"""
Analyser l'onglet 'jour' pour comprendre sa structure
"""

import xlrd

rj_file = '/Users/canaldesuez/Documents/Projects/audit-pack/documentation/complete_updated_files_to_analyze/Rj 12-23-2025-Copie.xls'
workbook = xlrd.open_workbook(rj_file, formatting_info=False)

try:
    jour = workbook.sheet_by_name('jour')

    print("=" * 100)
    print("ANALYSE DE L'ONGLET 'JOUR'")
    print("=" * 100)
    print(f"\nDimensions: {jour.nrows} rows x {jour.ncols} columns\n")

    # Show first 50 rows, columns A-N
    print("{:<10} {:<15} {:<15} {:<15} {:<15} {:<15}".format(
        "Row", "A", "B", "C", "D", "H"
    ))
    print("-" * 100)

    for row in range(min(50, jour.nrows)):
        a_val = jour.cell(row, 0).value if 0 < jour.ncols else ''
        b_val = jour.cell(row, 1).value if 1 < jour.ncols else ''
        c_val = jour.cell(row, 2).value if 2 < jour.ncols else ''
        d_val = jour.cell(row, 3).value if 3 < jour.ncols else ''
        h_val = jour.cell(row, 7).value if 7 < jour.ncols else ''

        # Only print rows with data
        a_str = str(a_val)[:15] if a_val != '' else '---'
        b_str = str(b_val)[:15] if b_val != '' else '---'
        c_str = str(c_val)[:15] if c_val != '' else '---'
        d_str = str(d_val)[:15] if d_val != '' else '---'
        h_str = str(h_val)[:15] if h_val != '' else '---'

        if any(v != '---' for v in [a_str, b_str, c_str, d_str, h_str]):
            print("{:<10} {:<15} {:<15} {:<15} {:<15} {:<15}".format(
                f"Row {row}",
                a_str,
                b_str,
                c_str,
                d_str,
                h_str
            ))

    # Try to find named ranges
    print("\n" + "=" * 100)
    print("PLAGES NOMMÉES")
    print("=" * 100)

    for name_obj in workbook.name_obj_list:
        if name_obj.name.startswith('ar_'):
            print(f"{name_obj.name}: {name_obj}")

except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
```

---

## 📋 CHECKLIST D'IMPLÉMENTATION

### Analyse
- [ ] Exécuter le script d'analyse de l'onglet "jour"
- [ ] Comprendre la structure (rows par jour)
- [ ] Identifier les plages nommées "ar_1" à "ar_31"
- [ ] Vérifier ce qui est copié (H19:N19 du Recap)

### Backend
- [ ] Créer `utils/rj_writer.py`
- [ ] Implémenter `copy_recap_to_jour()`
- [ ] Tester la fonction avec un fichier RJ
- [ ] Ajouter route `/api/rj/recap/send-to-jour`
- [ ] Tester l'API avec curl

### Frontend
- [ ] Ajouter bouton "Envoyer dans RJ" dans Recap
- [ ] Ajouter JavaScript `sendRecapToRJ()`
- [ ] Tester l'interface
- [ ] Vérifier que les données sont bien copiées

### Validation
- [ ] Télécharger le RJ modifié
- [ ] Ouvrir dans Excel
- [ ] Vérifier que l'onglet "jour" contient les bonnes données
- [ ] Valider avec l'utilisateur

---

## 🎯 ALTERNATIVE SIMPLE

Si l'analyse de l'onglet "jour" est trop complexe, on peut:

1. **Laisser l'utilisateur faire la copie dans Excel** après avoir téléchargé le RJ
2. **Ou automatiser seulement lors du téléchargement final** (copier automatiquement avant de sauvegarder)

**Recommandation:** D'abord analyser l'onglet "jour" pour comprendre, puis décider.

---

**Document créé:** 2026-01-02
**Prêt pour analyse:** ✅
**Nécessite:** Analyse de l'onglet "jour" en premier
