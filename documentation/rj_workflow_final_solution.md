# Solution Finale: Workflow RJ Automatisé

**Date:** 2026-01-02
**Statut:** Plan complet prêt pour implémentation

---

## 🎯 OBJECTIF

Simplifier le workflow quotidien:

**Avant (Manuel dans Excel):**
1. Ouvrir RJ d'hier
2. Enregistrer sous avec nouvelle date
3. Mettre à jour Controle (nom, date)
4. Cliquer sur boutons "turbo" pour effacer Recap, Transelect, GEAC
5. Remplir les nouvelles valeurs

**Après (Web App):**
1. Entrer son nom
2. Système crée automatiquement le nouveau RJ propre
3. Remplir les valeurs dans l'interface

---

## 🔍 CE QUE J'AI DÉCOUVERT

### Macros VBA "Turbo" Trouvées

J'ai extrait toutes les macros VBA du fichier RJ. Les macros d'effacement sont:

#### 1. **Recap** - 2 macros possibles

**efface_recap():**
```vba
Application.Goto Reference:="eff_recap"
Selection.ClearContents
```
Utilise une plage nommée "eff_recap"

**efface():**
```vba
Range("B6:C20").Select         ' Lecture et Corr
Selection.ClearContents
Range("D9:D10").Select         ' Certaines cellules de Net
Selection.ClearContents
Range("D12:D14").Select
Selection.ClearContents
Range("D16").Select
Selection.ClearContents
Range("D18").Select
Selection.ClearContents
```
Efface colonnes B, C et certaines cellules de D

#### 2. **Transelect**

**eff_trans():**
```vba
Range("B9:U13,X9:X13,B20:H24,J20:P24").Select
Selection.ClearContents
```
Efface les données de cartes de crédit

#### 3. **GEAC/UX**

**efface_rapport_geac():**
```vba
Range("B6:C6,E6,G6:H6,J6,B8:C8,E8,G8:H8,J8,B12:C12,E12,G12:H12,J12,B32:C32,E32,B37:C37,E37,B41:C41,G41:H41,B44:C44,J44:K44,B47:C47,E47,B50:C50,E50,B53:C53,E53").Select
Selection.ClearContents
```
Efface de nombreuses cellules spécifiques

### Autre Macro Importante

**envoie_dans_jour():**
- Copie des données dans l'onglet "jour"
- Utilise le jour du mois depuis Controle
- Colle à une plage nommée dynamiquement ("ar_1" à "ar_31")

---

## 💡 SOLUTION RECOMMANDÉE

### Approche: Template RJ Pré-nettoyé

**Pourquoi?**
1. **Simplicité:** Pas besoin de recoder 3 macros VBA complexes en Python
2. **Fiabilité:** Le template est garanti d'être correct (créé directement depuis Excel)
3. **Maintenabilité:** Un seul fichier template à maintenir
4. **Performance:** Copie instantanée vs manipulation cellule par cellule

---

## 📋 PLAN D'IMPLÉMENTATION DÉTAILLÉ

### PHASE 1: Créer le Template RJ

#### Étape 1.1: Ouvrir le RJ dans Excel

```
Fichier: Rj 12-23-2025-Copie.xls
```

#### Étape 1.2: Exécuter les Macros d'Effacement

Dans Excel, appuyer sur `Alt + F8` pour ouvrir la liste des macros, puis exécuter:

1. **efface_recap()** (ou **efface()**)
   - Efface les valeurs dans Recap
   - Garde les formules

2. **eff_trans()**
   - Efface les valeurs dans Transelect

3. **efface_rapport_geac()**
   - Efface les valeurs dans GEAC/UX

#### Étape 1.3: Vérifier que les Formules sont Intactes

- Vérifier que les totaux dans Recap affichent 0 ou #REF (normal sans données)
- Vérifier que les formules sont toujours présentes (cliquer sur les cellules de totaux)

#### Étape 1.4: Réinitialiser Controle (Optionnel)

Dans l'onglet Controle, mettre des valeurs par défaut:
- Row 2, Col B: "[NOM AUDITEUR]" (placeholder)
- Row 3, Col B: 1 (jour par défaut)
- Row 4, Col B: 1 (mois par défaut)
- Row 5, Col B: 2025 (année par défaut)

#### Étape 1.5: Sauvegarder le Template

```
Enregistrer sous: static/templates/RJ_TEMPLATE.xls
```

---

### PHASE 2: Backend Python

#### Étape 2.1: Créer le Répertoire

```bash
mkdir -p static/templates
```

#### Étape 2.2: Installer Dépendances

```bash
source .venv/bin/activate
pip install xlrd xlwt xlutils
```

Ajouter à `requirements.txt`:
```
xlrd==2.0.1
xlwt==1.3.0
xlutils==2.0.0
oletools==0.60.2
```

#### Étape 2.3: Créer `utils/rj_creator.py`

```python
#!/usr/bin/env python3
"""
Créateur de fichiers RJ pour la web app
"""

import xlrd
from xlutils.copy import copy
from datetime import datetime
from io import BytesIO
import os


def create_new_rj(auditor_name, date_str=None, template_path='static/templates/RJ_TEMPLATE.xls'):
    """
    Create a new RJ file for the day using the template.

    Args:
        auditor_name: Name of the auditor (e.g., "Khalil Mouatarif")
        date_str: Date string "MM-DD-YYYY" (optional, defaults to today)
        template_path: Path to the RJ template file

    Returns:
        BytesIO: The new RJ file as bytes

    Raises:
        FileNotFoundError: If template file doesn't exist
        ValueError: If date format is invalid
    """
    # Check if template exists
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Parse or use today's date
    if date_str is None:
        today = datetime.now()
        month, day, year = today.month, today.day, today.year
    else:
        try:
            parts = date_str.split('-')
            if len(parts) != 3:
                raise ValueError("Date must be in format MM-DD-YYYY")
            month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid date format: {date_str}. Expected MM-DD-YYYY") from e

    # Load template
    rb = xlrd.open_workbook(template_path, formatting_info=True)
    wb = copy(rb)

    # Get Controle sheet (case-sensitive!)
    controle = wb.get_sheet('controle')

    # Update Controle with new values
    # Row 2 (index 1): Nom de l'auditeur (col B = index 1)
    controle.write(1, 1, auditor_name)

    # Row 3 (index 2): Jour (col B = index 1)
    controle.write(2, 1, float(day))

    # Row 4 (index 3): Mois (col B = index 1)
    controle.write(3, 1, float(month))

    # Row 5 (index 4): Année (col B = index 1)
    controle.write(4, 1, float(year))

    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return output


def get_rj_filename(date_str=None):
    """
    Generate RJ filename based on date.

    Args:
        date_str: Date string "MM-DD-YYYY" (optional, defaults to today)

    Returns:
        str: Filename like "Rj 12-24-2025.xls"
    """
    if date_str is None:
        today = datetime.now()
        date_str = today.strftime("%m-%d-%Y")

    return f"Rj {date_str}.xls"


# For testing
if __name__ == "__main__":
    # Test creating a new RJ
    try:
        rj_bytes = create_new_rj("Khalil Mouatarif", "12-24-2025")
        filename = get_rj_filename("12-24-2025")

        # Save to test file
        with open(f"/tmp/{filename}", "wb") as f:
            f.write(rj_bytes.read())

        print(f"✅ Test successful! RJ created: /tmp/{filename}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
```

#### Étape 2.4: Ajouter Route API dans `routes/rj.py`

```python
@rj_bp.route('/api/rj/create-new', methods=['POST'])
@login_required
def create_new_rj_route():
    """
    Create a new RJ file for the day.

    Request body:
        {
            "auditor_name": "Khalil Mouatarif",
            "date": "12-24-2025"  # Optional, defaults to today
        }

    Returns:
        {
            "success": true,
            "filename": "Rj 12-24-2025.xls",
            "message": "Nouveau RJ créé avec succès"
        }
    """
    data = request.get_json()
    auditor_name = data.get('auditor_name', '').strip()
    date_str = data.get('date')  # Optional

    # Validate auditor name
    if not auditor_name:
        return jsonify({
            'success': False,
            'error': 'Le nom de l\'auditeur est requis'
        }), 400

    try:
        from utils.rj_creator import create_new_rj, get_rj_filename

        # Create new RJ
        rj_bytes = create_new_rj(auditor_name, date_str)

        # Store in session
        session_id = session.get('user_session_id', 'default')
        RJ_FILES[session_id] = rj_bytes

        # Generate filename
        filename = get_rj_filename(date_str)

        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Nouveau RJ créé pour {auditor_name}'
        })

    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'Fichier template RJ introuvable. Contactez l\'administrateur.'
        }), 500

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la création du RJ: {str(e)}'
        }), 500
```

---

### PHASE 3: Frontend

#### Étape 3.1: Ajouter Formulaire dans `templates/rj.html`

Ajouter ce code au début de la page (après le header):

```html
<!-- Formulaire de Création de Nouveau RJ -->
<div class="card mb-4" style="border-left: 4px solid #0d6efd;">
  <div class="card-header" style="background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%); color: white;">
    <h5 class="mb-0">
      <i class="fas fa-plus-circle"></i> Créer un Nouveau RJ
    </h5>
  </div>
  <div class="card-body">
    <form id="create-rj-form">
      <div class="row align-items-end">
        <!-- Nom de l'auditeur -->
        <div class="col-md-5 mb-3">
          <label for="auditor-name" class="form-label fw-bold">
            Nom de l'auditeur <span class="text-danger">*</span>
          </label>
          <input
            type="text"
            class="form-control"
            id="auditor-name"
            placeholder="Ex: Khalil Mouatarif"
            required
          >
          <small class="form-text text-muted">
            Votre nom sera inscrit dans l'onglet Controle
          </small>
        </div>

        <!-- Date (optionnel) -->
        <div class="col-md-4 mb-3">
          <label for="rj-date" class="form-label fw-bold">
            Date (optionnel)
          </label>
          <input
            type="date"
            class="form-control"
            id="rj-date"
          >
          <small class="form-text text-muted">
            Laissez vide pour aujourd'hui
          </small>
        </div>

        <!-- Bouton Créer -->
        <div class="col-md-3 mb-3">
          <button type="submit" class="btn btn-primary w-100" style="height: 38px;">
            <i class="fas fa-magic"></i> Créer RJ
          </button>
        </div>
      </div>
    </form>

    <!-- Résultat -->
    <div id="create-rj-result" style="display: none;" class="mt-3"></div>
  </div>
</div>
```

#### Étape 3.2: Ajouter JavaScript

Ajouter dans la section `<script>`:

```javascript
// ========================================
// CREATE NEW RJ
// ========================================

document.getElementById('create-rj-form').addEventListener('submit', async function(e) {
  e.preventDefault();

  const auditorName = document.getElementById('auditor-name').value.trim();
  const dateInput = document.getElementById('rj-date').value;

  if (!auditorName) {
    showCreateRjResult('error', 'Le nom de l\'auditeur est requis');
    return;
  }

  // Convert date from YYYY-MM-DD to MM-DD-YYYY if provided
  let dateStr = null;
  if (dateInput) {
    const [year, month, day] = dateInput.split('-');
    dateStr = `${month}-${day}-${year}`;
  }

  // Show loading
  showCreateRjResult('info', 'Création du RJ en cours...');

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
      showCreateRjResult('success', `
        <i class="fas fa-check-circle"></i>
        <strong>${data.message}</strong><br>
        Fichier: <strong>${data.filename}</strong><br>
        <small>Vous pouvez maintenant remplir les valeurs dans les onglets ci-dessous.</small>
      `);

      // Optionnel: Rafraîchir l'interface pour montrer le nouveau RJ chargé
      // (Dépend de comment vous gérez l'état du RJ chargé)

    } else {
      showCreateRjResult('error', data.error || 'Erreur inconnue');
    }
  } catch (error) {
    showCreateRjResult('error', `Erreur réseau: ${error.message}`);
  }
});

function showCreateRjResult(type, message) {
  const resultDiv = document.getElementById('create-rj-result');

  const alertClass = {
    'success': 'alert-success',
    'error': 'alert-danger',
    'info': 'alert-info'
  }[type] || 'alert-info';

  resultDiv.className = `alert ${alertClass}`;
  resultDiv.innerHTML = message;
  resultDiv.style.display = 'block';

  // Auto-hide after 10 seconds for success
  if (type === 'success') {
    setTimeout(() => {
      resultDiv.style.display = 'none';
    }, 10000);
  }
}
```

---

### PHASE 4: Tests

#### Test 1: Créer le Template

```bash
# Dans Excel:
# 1. Ouvrir Rj 12-23-2025-Copie.xls
# 2. Alt + F8
# 3. Exécuter efface_recap(), eff_trans(), efface_rapport_geac()
# 4. Sauvegarder comme static/templates/RJ_TEMPLATE.xls
```

#### Test 2: Tester le Backend

```bash
source .venv/bin/activate
python utils/rj_creator.py
```

Devrait créer `/tmp/Rj 12-24-2025.xls`

Ouvrir dans Excel et vérifier:
- Controle a "Khalil Mouatarif" et date 12-24-2025
- Recap est vide (sauf formules)
- Transelect est vide
- GEAC/UX est vide

#### Test 3: Tester l'API

```bash
# Démarrer l'app
python main.py

# Dans un autre terminal:
curl -X POST http://127.0.0.1:5000/api/rj/create-new \
  -H "Content-Type: application/json" \
  -d '{"auditor_name": "Test User", "date": "12-25-2025"}'
```

Devrait retourner:
```json
{
  "success": true,
  "filename": "Rj 12-25-2025.xls",
  "message": "Nouveau RJ créé pour Test User"
}
```

#### Test 4: Tester l'Interface

1. Ouvrir http://127.0.0.1:5000
2. Entrer PIN
3. Cliquer "Gestion Revenue Journal"
4. Entrer nom: "Khalil Mouatarif"
5. Cliquer "Créer RJ"
6. Vérifier message de succès
7. Remplir quelques valeurs dans Recap
8. Télécharger le RJ
9. Ouvrir dans Excel et vérifier

---

## ✅ CHECKLIST FINALE

### Préparation
- [ ] Extraire macros VBA (FAIT ✅)
- [ ] Analyser les macros (FAIT ✅)
- [ ] Créer plan d'implémentation (FAIT ✅)

### Template
- [ ] Ouvrir RJ dans Excel
- [ ] Exécuter efface_recap()
- [ ] Exécuter eff_trans()
- [ ] Exécuter efface_rapport_geac()
- [ ] Vérifier que les formules sont intactes
- [ ] Sauvegarder comme static/templates/RJ_TEMPLATE.xls

### Backend
- [ ] Créer répertoire static/templates/
- [ ] Installer xlrd, xlwt, xlutils
- [ ] Créer utils/rj_creator.py
- [ ] Ajouter route /api/rj/create-new dans routes/rj.py
- [ ] Tester création RJ via script Python
- [ ] Tester API avec curl

### Frontend
- [ ] Ajouter formulaire dans templates/rj.html
- [ ] Ajouter JavaScript pour appeler l'API
- [ ] Ajouter messages de succès/erreur
- [ ] Tester l'interface complète
- [ ] Vérifier UX et styling

### Validation
- [ ] Créer un RJ via l'interface
- [ ] Remplir des valeurs
- [ ] Télécharger le RJ
- [ ] Ouvrir dans Excel
- [ ] Vérifier que tout fonctionne
- [ ] Valider avec l'utilisateur

---

## 🎉 RÉSULTAT FINAL

### Avant
```
Utilisateur ouvre Excel manuellement
  ↓
Enregistre sous nouvelle date
  ↓
Met à jour Controle
  ↓
Clique 3 boutons turbo
  ↓
Remplit les valeurs
```

### Après
```
Utilisateur entre son nom dans la web app
  ↓
Clique "Créer RJ"
  ↓
Remplit les valeurs dans l'interface
  ↓
Télécharge le RJ complété
```

**Gain de temps:** ~5 minutes par jour
**Moins d'erreurs:** Pas de risque d'oublier d'effacer un onglet
**Plus simple:** Workflow en 3 clics au lieu de 10+

---

**Document créé:** 2026-01-02
**Prêt pour implémentation:** ✅
**Temps estimé:** 3-4 heures total
