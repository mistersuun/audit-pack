# Système de Remplissage Automatique du RJ (Revenue Journal)

## Vue d'ensemble

Le système RJ permet aux auditeurs de remplir le fichier Excel Revenue Journal de manière automatisée via une interface web, sans avoir à chercher manuellement les bonnes cellules dans Excel.

### Avantages

✅ **Gain de temps**: Plus besoin de naviguer dans 34 onglets Excel
✅ **Zéro erreur**: Les cellules sont remplies automatiquement aux bons endroits
✅ **Interface intuitive**: Formulaires clairs avec labels en français
✅ **Sauvegarde progressive**: Remplir section par section au fur et à mesure
✅ **Intégration**: Accessible directement depuis la checklist

---

## Comment ça marche

### 1️⃣ Upload du fichier RJ

Au début de votre quart, uploadez votre fichier RJ (`.xls` ou `.xlsx`):
- Soit un template vide
- Soit votre RJ en cours

Le fichier est stocké en mémoire pour votre session.

### 2️⃣ Remplir les sections

Chaque section du RJ a son propre formulaire :

#### 📊 Sections disponibles

| Section | Onglet Excel | Nombre de champs | Utilisation |
|---------|--------------|------------------|-------------|
| **Contrôle** | `controle` | 7 champs | Infos générales (date, météo, chambres) |
| **RECAP** | `Recap` | 17 champs | Réconciliation cash |
| **TRANSELECT** | `transelect` | À venir | Réconciliation CC/Interac |
| **GEAC/UX** | `geac_ux` | À venir | Réconciliation finale CC |
| **DueBack** | `DUBACK#` | À venir | Due Back par réceptionniste |
| **SetD** | `SetD` | À venir | Sommaire des dépôts |

#### Exemple: Remplir le RECAP

```
1. Cliquer sur "RECAP - Réconciliation Cash"
2. Remplir les champs:
   - Comptant LightSpeed (Lecture + Correction)
   - Comptant Positouch (Lecture + Correction)
   - Remboursements
   - Due Back
   - Dépôt
3. Cliquer "Sauvegarder RECAP dans RJ"
4. ✅ Confirmation: "10 cellules remplies dans RECAP"
```

### 3️⃣ Télécharger le RJ complété

Une fois toutes les sections remplies :
- Cliquer sur **"Télécharger le fichier RJ complété"**
- Le fichier Excel est téléchargé avec toutes vos données aux bons endroits
- Nom du fichier: `RJ_2024-12-20_filled.xls`

---

## Architecture technique

### Fichiers créés

```
routes/
  └── rj.py                    # Blueprint Flask pour le système RJ
                               # Routes: /rj, /api/rj/upload, /api/rj/fill/<sheet>

utils/
  ├── rj_mapper.py             # Configuration des mappings champs → cellules
  └── rj_filler.py             # Classe RJFiller pour remplir les cellules Excel

templates/
  └── rj.html                  # Interface web pour gérer le RJ

documentation/
  └── SYSTEME_RJ.md            # Cette documentation
```

### Mapping des cellules

Le fichier `utils/rj_mapper.py` contient tous les mappings :

```python
RECAP_MAPPING = {
    'comptant_lightspeed_lecture': 'B6',   # Cellule B6 dans onglet Recap
    'comptant_lightspeed_corr': 'C6',      # Cellule C6 dans onglet Recap
    'comptant_positouch_lecture': 'B7',
    # ... etc
}
```

### Classe RJFiller

La classe `RJFiller` gère le remplissage du fichier Excel :

```python
from utils.rj_filler import RJFiller

# Charger le fichier RJ
rj_filler = RJFiller('path/to/rj.xls')

# Remplir un onglet
data = {
    'comptant_lightspeed_lecture': 100.50,
    'comptant_positouch_lecture': 250.75,
    # ...
}
cells_filled = rj_filler.fill_sheet('Recap', data)

# Sauvegarder
rj_filler.save('output.xls')
```

---

## API Endpoints

### `POST /api/rj/upload`

Upload un fichier RJ pour la session courante.

**Request:**
```
multipart/form-data
{
  rj_file: File (.xls ou .xlsx)
}
```

**Response:**
```json
{
  "success": true,
  "message": "Fichier RJ uploadé avec succès",
  "file_info": {
    "filename": "Rj-19-12-2024.xls",
    "size": 245760
  }
}
```

---

### `POST /api/rj/fill/<sheet_name>`

Remplir un onglet spécifique du RJ.

**Sheets disponibles:**
- `controle`
- `recap`
- `transelect` (à venir)
- `geac` (à venir)

**Request (exemple pour RECAP):**
```json
{
  "date": "2024-12-20",
  "comptant_lightspeed_lecture": 100.50,
  "comptant_lightspeed_corr": 0.00,
  "comptant_positouch_lecture": 250.75,
  "depot_canadien_lecture": 3500.00,
  "prepare_par": "Ermika Dormeus"
}
```

**Response:**
```json
{
  "success": true,
  "message": "10 cellules remplies dans recap",
  "cells_filled": 10
}
```

---

### `GET /api/rj/download`

Télécharger le fichier RJ rempli.

**Response:**
- Fichier Excel (.xls)
- Nom: `RJ_YYYY-MM-DD_filled.xls`

---

### `GET /api/rj/status`

Vérifier si un fichier RJ est uploadé pour la session.

**Response:**
```json
{
  "uploaded": true,
  "file_size": 245760
}
```

---

## Utilisation dans le workflow

### Intégration avec la checklist

Le système RJ est accessible depuis la checklist de nuit :
1. Tâche #XX : "Commencer le Revenue Journal"
2. Bouton : **"📊 Ouvrir le système RJ"**
3. Redirection vers `/rj`

### Workflow recommandé

```
┌─────────────────────────────────────────────────────────────────┐
│ DÉBUT DE QUART                                                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Uploader le fichier RJ template                              │
│ 2. Remplir "Contrôle" (date, météo, chambres)                   │
│                                                                  │
│ PENDANT LA NUIT                                                 │
│ 3. Remplir "RECAP" après Daily Revenue                          │
│ 4. Remplir "TRANSELECT" après impressions VNC                   │
│ 5. Remplir "GEAC/UX" après vérification terminaux               │
│ 6. Remplir "DueBack" après Cashier Details                      │
│ 7. Remplir "SetD" en fin de nuit                                │
│                                                                  │
│ FIN DE QUART                                                    │
│ 8. Télécharger le RJ complété                                   │
│ 9. Vérifier dans Excel                                          │
│ 10. Sauvegarder sur le serveur/email au gestionnaire            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Sections détaillées

### 🎛️ Contrôle - Informations générales

**Onglet Excel:** `controle`
**Cellules remplies:** 7

| Champ | Cellule Excel | Description |
|-------|---------------|-------------|
| Jour (DD) | B3 | Jour du mois (1-31) |
| Mois (MM) | B4 | Mois (1-12) |
| Année (AAAA) | B5 | Année (2024, etc.) |
| Température | B6 | Température en °C |
| Condition | B7 | Code météo (1=Soleil, 4=Neige, etc.) |
| Chambres à refaire | B9 | Nombre de chambres à refaire |
| Préparé par | B2 | Nom de l'auditeur |

**Valeurs auto-remplies:**
- Date du jour pré-remplie
- Nom de l'auditeur (si connecté)

---

### 💰 RECAP - Réconciliation Cash

**Onglet Excel:** `Recap`
**Cellules remplies:** 17

#### Sous-sections

**1. Comptant**
- Comptant LightSpeed (Lecture + Correction)
- Comptant Positouch (Lecture + Correction)
- Chèque Payment Register (Lecture + Correction)

**2. Remboursements**
- Remboursement Gratuité (Lecture + Correction)
- Remboursement Client (Lecture + Correction)

**3. Due Back**
- Due Back Réception (Lecture + Correction)
- Due Back N/B (Lecture + Correction)

**4. Dépôt**
- Surplus/Déficit (Lecture + Correction)
- Dépôt Canadien (Lecture + Correction)

**Notes:**
- Champs "Lecture" : montant brut du système
- Champs "Correction" : ajustements manuels (peut être 0.00)

---

### 💳 TRANSELECT - Réconciliation CC/Interac (À VENIR)

**Onglet Excel:** `transelect`
**Cellules à remplir:** ~30

Sections prévues :
- BAR (701, 702, 703)
- SPESA (704)
- ROOM (705)
- Réception (CC/Débit)

---

### 🏦 GEAC/UX - Réconciliation finale CC (À VENIR)

**Onglet Excel:** `geac_ux`
**Cellules à remplir:** ~15

Sections prévues :
- Daily Cash Out (Amex, Master, Visa)
- Daily Revenue
- Balance Sheet

---

### 📋 DueBack - Due Back par réceptionniste (À VENIR)

**Onglet Excel:** `DUBACK#`
**Structure:** Tableau 31 jours × 9 réceptionnistes

Réceptionnistes :
- Araujo (Debby)
- Latulippe (Josée)
- Caron (Isabelle)
- Aguilar (Dayannis)
- Nader (Laeticia)
- Mompremier (Rose-Delande)
- Oppong (Zaneta)
- Seddik (Zayen)
- Dormeus (Ermika)

---

### 💵 SetD - Sommaire des dépôts (À VENIR)

**Onglet Excel:** `SetD`
**Structure:** Ligne par jour

Comptes :
- RJ (colonne B)
- Comptabilité (colonnes I, J)
- Banquet (colonne K)

---

## Tests

### Test manuel via interface web

1. Démarrer l'application : `python main.py`
2. Ouvrir http://127.0.0.1:5000/rj
3. Uploader `documentation/back/Rj-19-12-2024.xls`
4. Remplir le formulaire RECAP
5. Télécharger le fichier
6. Ouvrir dans Excel pour vérifier

### Test automatisé

```bash
python << 'EOF'
from utils.rj_filler import RJFiller

# Charger
rj = RJFiller('documentation/back/Rj-19-12-2024.xls')

# Remplir
data = {
    'jour': 20,
    'mois': 12,
    'annee': 2024,
    'temperature': -5.0,
    'chambres_refaire': 243
}
cells = rj.fill_sheet('controle', data)
print(f"✅ {cells} cellules remplies")

# Sauvegarder
rj.save('test_output.xls')
EOF
```

---

## Dépannage

### Erreur: "No RJ file uploaded"

**Cause:** Aucun fichier uploadé pour cette session
**Solution:** Uploader le fichier RJ d'abord

### Erreur: "Unknown sheet: xyz"

**Cause:** Nom de sheet invalide
**Solution:** Utiliser: `controle`, `recap`, `transelect`, `geac`

### Les cellules ne sont pas remplies correctement

**Cause:** Mapping incorrect
**Solution:** Vérifier `utils/rj_mapper.py` et ajuster les cellules

### Fichier Excel corrompu après remplissage

**Cause:** xlutils a des limitations avec les fichiers .xls complexes
**Solution:**
1. Utiliser un fichier .xls simple comme template
2. Ou migrer vers openpyxl pour fichiers .xlsx

---

## Améliorations futures

### Court terme (Sprint 1)
- [ ] Ajouter formulaire TRANSELECT
- [ ] Ajouter formulaire GEAC/UX
- [ ] Ajouter formulaire DueBack
- [ ] Ajouter formulaire SetD
- [ ] Validation des montants (balancement RECAP)

### Moyen terme (Sprint 2)
- [ ] Auto-calcul des totaux
- [ ] Validation croisée entre onglets
- [ ] Import des données depuis LightSpeed/VNC
- [ ] Prévisualisation Excel dans le navigateur

### Long terme
- [ ] Historique des RJ complétés
- [ ] Comparaison avec RJ de la veille
- [ ] Alertes sur écarts significatifs
- [ ] Export vers système comptable
- [ ] API pour intégration avec autres systèmes

---

## Changelog

### Version 1.0 (2024-12-20)

✅ **Implémenté:**
- Système d'upload de fichier RJ
- Mapping des cellules pour contrôle et Recap
- Formulaires web pour contrôle (7 champs) et Recap (17 champs)
- API endpoints: upload, fill, download, status
- Tests automatisés

🚧 **En cours:**
- Formulaires TRANSELECT, GEAC/UX, DueBack, SetD

📋 **Planifié:**
- Intégration avec checklist
- Validation des données
- Auto-calculs

---

## Support

### Documentation
- Cette page : `/documentation/SYSTEME_RJ.md`
- Mapping des cellules : `/utils/rj_mapper.py`
- Code remplissage : `/utils/rj_filler.py`

### Tests
- Test manuel : http://127.0.0.1:5000/rj
- Test automatisé : Voir section "Tests" ci-dessus

### Problèmes
Pour tout problème :
1. Vérifier les logs Flask
2. Tester avec le fichier RJ exemple
3. Vérifier que xlrd et xlutils sont installés
4. Consulter la section Dépannage

---

## Notes techniques

### Dépendances Python

```bash
pip install xlrd       # Lecture fichiers .xls
pip install xlutils    # Modification fichiers .xls
```

### Limitations connues

1. **Format .xls seulement** : xlutils ne supporte que l'ancien format Excel
   - Solution future : migrer vers openpyxl pour .xlsx

2. **Formatage perdu** : Les styles Excel peuvent être perdus
   - Solution : Utiliser un template pré-formaté

3. **Formules Excel** : Les formules ne sont pas préservées
   - Solution : Écrire seulement dans les cellules de données

4. **Session-based storage** : RJ stocké en mémoire (perdu au redémarrage)
   - Solution future : Stockage fichier ou base de données

### Sécurité

- ✅ Tous les endpoints protégés par `@login_required`
- ✅ Validation des types de fichiers (.xls, .xlsx seulement)
- ✅ Validation des noms de sheets
- ✅ Stockage en session (isolé par utilisateur)
- ✅ Pas d'exécution de code dans Excel (pas de macros)

---

**Dernière mise à jour:** 2024-12-20
**Version:** 1.0
**Auteur:** Système d'automatisation Sheraton Laval
