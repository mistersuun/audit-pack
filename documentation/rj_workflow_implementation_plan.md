# Plan d'Implémentation: Workflow RJ Automatisé

**Date:** 2026-01-02
**Objectif:** Automatiser le workflow de création d'un nouveau RJ quotidien

---

## 📋 WORKFLOW ACTUEL (MANUEL)

D'après `procedure_complete_back.pdf` et les échanges:

1. **Ouvrir le RJ d'hier**
   - Fichier Excel .xls avec 37 onglets
   - Environ 2.2 MB

2. **Enregistrer sous** avec la nouvelle date
   - Ex: "Rj 12-23-2025.xls" → "Rj 12-24-2025.xls"

3. **Mettre à jour l'onglet Controle**
   - Date (row 3, col B: jour)
   - Mois (row 4, col B: 12)
   - Année (row 5, col B: 2025)
   - Nom de l'auditeur (row 2, col B: "Khalil Mouatarif")

4. **Effacer les onglets** Recap, Transelect, GEAC/UX
   - Utilisation de boutons "turbo" (macros VBA)
   - Efface les valeurs saisies
   - Garde les formules et la structure

5. **Remplir les nouvelles valeurs**
   - Recap: Colonne B (Lecture) seulement
   - Transelect: Données de cartes de crédit
   - GEAC/UX: Données de balance

---

## 🎯 OBJECTIF DE LA WEB APP

Simplifier le workflow:

```
Utilisateur entre son nom
         ↓
Système crée automatiquement le nouveau RJ
         ↓
Utilisateur remplit seulement les valeurs
```

---

## 🔍 ANALYSE DES ONGLETS À EFFACER

### 1. Recap

**Structure:**
- Colonne A: Labels (noms des lignes)
- Colonne B: **Lecture** (VALEURS À SAISIR) ← À EFFACER
- Colonne C: Corr (jamais utilisé)
- Colonne D: Net (formule = B + C) ← GARDER
- Totaux: Formules Excel ← GARDER

**Cellules à effacer:** Colonne B (rows de données)

**Nombre de cellules:** ~23 cellules numériques

---

### 2. Transelect

**Structure:**
- Données de cartes de crédit par point de vente
- Sections:
  - BAR A, BAR B, BAR C, SPESA
  - Bank Report, Réception
  - Totaux calculés

**Cellules à effacer:** Toutes les valeurs numériques saisies

**Nombre de cellules:** ~44 cellules numériques

**Exemples:**
- B9: 381.1 (DÉBIT BAR A)
- C9: 590.86 (DÉBIT BAR B)
- B10: 673.64 (VISA BAR A)
- etc.

---

### 3. GEAC/UX

**Structure:**
- Données de balance AMEX, DINERS
- Daily Cash Out
- Daily Revenue
- Guest Ledger
- Balance Previous

**Cellules à effacer:** Toutes les valeurs numériques saisies

**Nombre de cellules:** ~21 cellules numériques

**Exemples:**
- B6: 5714.14 (AMEX Daily Cash Out)
- G6: 7394.15
- J6: 6473.46
- etc.

---

## 💡 SOLUTION PROPOSÉE: Template RJ

### Pourquoi Template?

1. **Fiabilité:** Garantit que les formules sont préservées
2. **Simplicité:** Pas besoin d'identifier précisément chaque cellule à effacer
3. **Maintenabilité:** Un seul fichier template à maintenir
4. **Performance:** Copie rapide vs lecture/écriture cellule par cellule

### Comment créer le Template?

**Option A: Manuellement**
1. Ouvrir un RJ existant dans Excel
2. Cliquer sur les boutons "turbo" pour effacer Recap, Transelect, GEAC/UX
3. Effacer les valeurs dans les autres onglets si nécessaire
4. Sauvegarder comme `RJ_TEMPLATE.xls`

**Option B: Programmatiquement**
```python
# Lire un RJ existant
# Copier la structure de tous les onglets
# Effacer toutes les valeurs numériques (sauf formules)
# Sauvegarder comme template
```

---

## 🛠️ IMPLÉMENTATION TECHNIQUE

### 1. Créer le Template

Fichier: `static/templates/RJ_TEMPLATE.xls`

**Contenu:**
- Tous les onglets avec structure complète
- Toutes les formules intactes
- **Aucune valeur saisie** dans Recap/Transelect/GEAC
- Controle avec valeurs par défaut (à remplacer)

---

### 2. Backend: Fonction de Création RJ

**Fichier:** `utils/rj_creator.py`

```python
import xlrd
import xlwt
from xlutils.copy import copy
from datetime import datetime
import os

def create_new_rj(auditor_name, date_str=None):
    """
    Create a new RJ file for the day using the template.

    Args:
        auditor_name: Name of the auditor (e.g., "Khalil Mouatarif")
        date_str: Date string "MM-DD-YYYY" (optional, defaults to today)

    Returns:
        BytesIO: The new RJ file as bytes
    """
    if date_str is None:
        date_str = datetime.now().strftime("%m-%d-%Y")

    # Parse date
    month, day, year = date_str.split('-')

    # Load template
    template_path = 'static/templates/RJ_TEMPLATE.xls'
    rb = xlrd.open_workbook(template_path, formatting_info=True)
    wb = copy(rb)

    # Get Controle sheet
    controle = wb.get_sheet('controle')

    # Update Controle with new values
    # Row 2 (index 1): Nom de l'auditeur
    controle.write(1, 1, auditor_name)

    # Row 3 (index 2): Jour
    controle.write(2, 1, int(day))

    # Row 4 (index 3): Mois
    controle.write(3, 1, int(month))

    # Row 5 (index 4): Année
    controle.write(4, 1, int(year))

    # Save to BytesIO
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return output
```

---

### 3. Route API

**Fichier:** `routes/rj.py`

```python
@rj_bp.route('/api/rj/create-new', methods=['POST'])
@login_required
def create_new_rj():
    """
    Create a new RJ file for the day.

    Request body:
        {
            "auditor_name": "Khalil Mouatarif",
            "date": "12-24-2025"  # Optional
        }

    Returns:
        {
            "success": true,
            "filename": "Rj 12-24-2025.xls"
        }
    """
    data = request.get_json()
    auditor_name = data.get('auditor_name')
    date_str = data.get('date')  # Optional

    if not auditor_name:
        return jsonify({'success': False, 'error': 'Auditor name required'}), 400

    try:
        from utils.rj_creator import create_new_rj

        # Create new RJ
        rj_bytes = create_new_rj(auditor_name, date_str)

        # Store in session
        session_id = session.get('user_session_id', 'default')
        RJ_FILES[session_id] = rj_bytes

        # Generate filename
        if date_str:
            filename = f"Rj {date_str}.xls"
        else:
            today = datetime.now().strftime("%m-%d-%Y")
            filename = f"Rj {today}.xls"

        return jsonify({
            'success': True,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### 4. Interface Utilisateur

**Fichier:** `templates/rj.html`

Ajouter un formulaire en haut de la page:

```html
<!-- New RJ Creation Form -->
<div class="card mb-4">
  <div class="card-header bg-primary text-white">
    <h5 class="mb-0">📅 Créer un Nouveau RJ</h5>
  </div>
  <div class="card-body">
    <form id="create-rj-form">
      <div class="row">
        <div class="col-md-6 mb-3">
          <label for="auditor-name" class="form-label">Nom de l'auditeur</label>
          <input
            type="text"
            class="form-control"
            id="auditor-name"
            placeholder="Ex: Khalil Mouatarif"
            required
          >
        </div>
        <div class="col-md-4 mb-3">
          <label for="rj-date" class="form-label">Date (optionnel)</label>
          <input
            type="date"
            class="form-control"
            id="rj-date"
            placeholder="Aujourd'hui par défaut"
          >
        </div>
        <div class="col-md-2 mb-3 d-flex align-items-end">
          <button type="submit" class="btn btn-success w-100">
            ✨ Créer RJ
          </button>
        </div>
      </div>
    </form>
    <div id="create-rj-result" style="display: none;" class="alert mt-3"></div>
  </div>
</div>
```

**JavaScript:**

```javascript
// Create new RJ
document.getElementById('create-rj-form').addEventListener('submit', async function(e) {
  e.preventDefault();

  const auditorName = document.getElementById('auditor-name').value;
  const dateInput = document.getElementById('rj-date').value;

  // Convert date from YYYY-MM-DD to MM-DD-YYYY if provided
  let dateStr = null;
  if (dateInput) {
    const [year, month, day] = dateInput.split('-');
    dateStr = `${month}-${day}-${year}`;
  }

  const resultDiv = document.getElementById('create-rj-result');
  resultDiv.style.display = 'none';

  try {
    const res = await fetch('/api/rj/create-new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        auditor_name: auditorName,
        date: dateStr
      })
    });

    const data = await res.json();

    if (data.success) {
      resultDiv.className = 'alert alert-success mt-3';
      resultDiv.innerHTML = `
        ✅ Nouveau RJ créé: <strong>${data.filename}</strong><br>
        Vous pouvez maintenant remplir les valeurs dans les onglets ci-dessous.
      `;
      resultDiv.style.display = 'block';
    } else {
      resultDiv.className = 'alert alert-danger mt-3';
      resultDiv.textContent = `❌ Erreur: ${data.error}`;
      resultDiv.style.display = 'block';
    }
  } catch (error) {
    resultDiv.className = 'alert alert-danger mt-3';
    resultDiv.textContent = `❌ Erreur: ${error.message}`;
    resultDiv.style.display = 'block';
  }
});
```

---

## 📦 DÉPENDANCES

Ajouter à `requirements.txt`:

```
xlrd==2.0.1
xlwt==1.3.0
xlutils==2.0.0
```

Installation:

```bash
source .venv/bin/activate
pip install xlrd xlwt xlutils
```

---

## 🧪 TESTS

### 1. Créer le Template

**Manuellement:**
1. Ouvrir `Rj 12-23-2025-Copie.xls` dans Excel
2. Cliquer sur les boutons "turbo" (ou effacer manuellement)
3. Sauvegarder comme `static/templates/RJ_TEMPLATE.xls`

**Vérifier:**
- Recap colonne B est vide
- Transelect valeurs numériques sont vides
- GEAC/UX valeurs numériques sont vides
- Les formules sont toujours présentes

---

### 2. Tester la Création

```bash
# Démarrer l'app
source .venv/bin/activate
python main.py
```

1. Aller sur http://127.0.0.1:5000
2. Entrer le PIN
3. Cliquer "Gestion Revenue Journal"
4. Entrer nom: "Khalil Mouatarif"
5. Cliquer "Créer RJ"
6. Vérifier le message de succès
7. Tester les onglets Recap, DueBack, etc.

---

### 3. Vérifier le Fichier Créé

**Via l'interface:**
- Télécharger le RJ créé
- Ouvrir dans Excel
- Vérifier:
  - Controle a le bon nom et la bonne date
  - Recap colonne B est vide
  - Les formules fonctionnent
  - Les totaux s'affichent

---

## ✅ AVANTAGES DE CETTE APPROCHE

1. **Simple:** Un seul template à maintenir
2. **Fiable:** Les formules Excel sont garanties
3. **Rapide:** Copie instantanée du template
4. **UX Amélioré:** L'utilisateur entre seulement son nom
5. **Pas de macros:** Pas besoin de VBA ou de boutons turbo

---

## 🔄 WORKFLOW FINAL

```
┌─────────────────────────────────────────────────────┐
│  1. Utilisateur arrive sur la page RJ               │
│                                                     │
│  2. Entre son nom: "Khalil Mouatarif"              │
│     (Optionnel: sélectionne une date)              │
│                                                     │
│  3. Clique "Créer RJ"                              │
│                                                     │
│  4. Système:                                       │
│     - Charge le template RJ_TEMPLATE.xls           │
│     - Copie la structure complète                  │
│     - Met à jour Controle (nom, date)              │
│     - Stocke le nouveau RJ en session              │
│                                                     │
│  5. Message de succès affiché                      │
│     "Nouveau RJ créé: Rj 12-24-2025.xls"           │
│                                                     │
│  6. Utilisateur remplit les valeurs:               │
│     - Recap: Colonne Lecture                       │
│     - DueBack: Previous et Nouveau                 │
│     - Transelect: Données cartes                   │
│     - etc.                                         │
│                                                     │
│  7. Clique "Télécharger RJ" quand terminé          │
│                                                     │
│  8. Fichier sauvegardé localement                  │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 PROCHAINES ÉTAPES

### Phase 1: Préparation du Template
- [ ] Créer `static/templates/` directory
- [ ] Créer `RJ_TEMPLATE.xls` manuellement ou programmatiquement
- [ ] Vérifier que toutes les formules sont intactes

### Phase 2: Backend
- [ ] Créer `utils/rj_creator.py`
- [ ] Installer dépendances `xlrd`, `xlwt`, `xlutils`
- [ ] Implémenter fonction `create_new_rj()`
- [ ] Créer route API `/api/rj/create-new`
- [ ] Tester avec Postman ou curl

### Phase 3: Frontend
- [ ] Ajouter formulaire de création dans `templates/rj.html`
- [ ] Ajouter JavaScript pour appeler l'API
- [ ] Ajouter messages de succès/erreur
- [ ] Tester l'interface complète

### Phase 4: Tests et Validation
- [ ] Tester création avec différents noms
- [ ] Tester avec différentes dates
- [ ] Vérifier que les formules Excel fonctionnent
- [ ] Télécharger et vérifier le fichier créé dans Excel
- [ ] Valider avec l'utilisateur

---

**Document créé:** 2026-01-02
**Prêt pour implémentation:** En attente de validation utilisateur
**Temps estimé:** 2-3 heures d'implémentation + tests
