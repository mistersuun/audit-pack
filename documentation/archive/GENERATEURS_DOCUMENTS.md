# Générateurs de Documents Automatiques

## Vue d'ensemble

Le système de génération automatique de documents permet aux employés de l'audit de nuit de télécharger des documents pré-remplis avec un minimum d'effort. Les générateurs sont intégrés directement dans l'interface de checklist.

## Documents Générés

### 1. Séparateur Date (Task #6)
**Endpoint:** `/api/generators/separateur-date`

**Automatisation:** 100% automatique
- Date du jour insérée automatiquement
- Téléchargement en 1 clic

**Format de sortie:** Word (.docx)
- Date formatée en français: "Lundi le 20 Décembre 2025"
- Police: 18pt, gras, centré

**Utilisation dans le workflow:**
1. L'employé clique sur la tâche #6
2. Voit le guide avec le bouton "Télécharger le document"
3. Un clic télécharge le document avec la date du jour

---

### 2. Checklist Tournée des Étages (Task #7)
**Endpoint:** `/api/generators/checklist-tournee`

**Automatisation:** 100% automatique
- Date du jour insérée automatiquement dans le titre
- Téléchargement en 1 clic

**Format de sortie:** Excel (.xlsx)
- Template: `Checklist Tournée Étages.xlsx`
- Cellule A1 mise à jour avec: "liste des vérifications pour auditeur de nuit MM/DD/YYYY"

**Utilisation dans le workflow:**
1. L'employé clique sur la tâche #7
2. Un clic télécharge la checklist avec la date du jour

---

### 3. Feuille d'Entretien Hiver (Task #8)
**Endpoint:** `/api/generators/entretien-hiver`

**Automatisation:** 100% automatique avec capture météo
- Date du jour insérée automatiquement
- **Capture automatique des prévisions météo** depuis Environment Canada
- Téléchargement en 1 clic

**Format de sortie:** Word (.docx)
- Template: `Entretien Sheraton Laval Hiver.docx`
- Date formatée en français dans l'en-tête
- Screenshot météo inséré (6 pouces de largeur)
- Prévisions pour 6-7 jours avec conditions actuelles

**Capture météo:**
- **Source primaire:** MétéoMédia (peut timeout)
- **Source fallback:** Environment Canada (fiable)
- **URL utilisée:** `https://www.meteo.gc.ca/fr/location/index.html?coords=45.585,-73.751`
- **Technique:** Playwright (navigateur headless) capture `.center` de la page
- **Taille screenshot:** 1400x1000 pixels
- **Informations capturées:**
  - Conditions actuelles (température, vent, humidité, visibilité)
  - Prévisions 6 jours (température min/max, conditions, icônes météo)
  - En français

**Utilisation dans le workflow:**
1. L'employé clique sur la tâche #8
2. Un clic lance la génération (prend ~5-10 secondes pour capturer la météo)
3. Document téléchargé automatiquement avec météo incluse

**Note technique:** Le document généré fait ~600 KB avec l'image météo incluse.

---

### 4. Clés Banquets (Task #19)
**Endpoint:** `/api/generators/cles-banquets`

**Automatisation:** Semi-automatique
- Date du jour insérée automatiquement
- **Formulaire dynamique pour les événements:**
  - Nom du salon
  - Nom de la compagnie
  - Heures (ex: "08:00-13:00")
  - Personne responsable
- Possibilité d'ajouter plusieurs événements

**Format de sortie:** Word (.docx)
- Template: `CLES BANQUETS.doc`
- Date formatée: "DATE : 20 DÉCEMBRE 2025"
- Tableau rempli avec les événements saisis

**Utilisation dans le workflow:**
1. L'employé clique sur la tâche #19
2. Voit un formulaire pour entrer les événements du jour
3. Peut ajouter plusieurs événements
4. Clique "Générer et télécharger"
5. Document généré avec tous les événements dans le tableau

---

## Architecture Technique

### Structure des fichiers

```
routes/
  └── generators.py          # Blueprint avec tous les endpoints API

utils/
  ├── weather_capture.py     # Capture météo avec Playwright
  └── weather_api.py         # (Non utilisé - API rate-limited)

static/
  └── templates/             # Documents templates Word/Excel
      ├── CLES BANQUETS.doc
      ├── Checklist Tournée Étages.xlsx
      ├── Entretien Sheraton Laval Hiver.docx
      └── separateur_date_comptabilité.docx

templates/
  └── checklist.html         # UI intégrée avec générateurs
```

### Intégration Frontend

Les générateurs sont intégrés dans `templates/checklist.html`:

```javascript
const generators = {
    6: { // Séparateur Daté
        endpoint: '/api/generators/separateur-date',
        autoDate: true,
        fields: `<input type="hidden" name="date" value="${today}">
                 <p class="generator-auto-info">📅 Document généré automatiquement avec la date d'aujourd'hui</p>`
    },
    7: { // Checklist Tournée
        endpoint: '/api/generators/checklist-tournee',
        autoDate: true,
        // ...
    },
    8: { // Entretien Hiver
        endpoint: '/api/generators/entretien-hiver',
        autoDate: true,
        // ...
    },
    19: { // Clés Banquets
        endpoint: '/api/generators/cles-banquets',
        autoDate: false,
        // Formulaire dynamique pour événements
    }
}
```

### Dépendances Python

```python
from docx import Document              # Manipulation Word documents
from docx.shared import Pt, Inches     # Formatage
from openpyxl import load_workbook     # Manipulation Excel
from playwright.sync_api import sync_playwright  # Capture météo
from PIL import Image                  # Traitement d'images
```

### Sécurité

- Tous les endpoints protégés par `@login_required`
- Validation des entrées utilisateur
- Timeouts sur les captures météo (30 secondes)
- Gestion d'erreurs avec messages fallback

---

## Guide de Déploiement

### Prérequis

1. **Installer Playwright:**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Vérifier les templates:**
   - Les 4 fichiers doivent être dans `static/templates/`
   - Permissions de lecture correctes

3. **Test de capture météo:**
   ```bash
   python -c "from utils.weather_capture import get_weather_screenshot; \
              img = get_weather_screenshot(); \
              print('✅ OK' if img else '❌ Failed')"
   ```

### Utilisation en Production

L'application fonctionne en mode local seulement (`127.0.0.1:5000`) pour raisons de sécurité.

**Lancement:**
```bash
python main.py
```

**Accès:**
1. Navigateur → http://127.0.0.1:5000
2. Entrer le PIN configuré dans `.env`
3. Commencer une nouvelle nuit d'audit
4. Cliquer sur les tâches 6, 7, 8, ou 19
5. Utiliser les générateurs intégrés

---

## Dépannage

### La capture météo échoue

**Symptômes:** Message "⚠️ Prévisions météo temporairement indisponibles"

**Solutions:**
1. Vérifier la connexion Internet
2. Vérifier que Playwright est installé: `playwright install chromium`
3. Augmenter le timeout dans `weather_capture.py` ligne 61
4. Tester manuellement la capture (voir commande ci-dessus)

### Le document n'a pas la météo

**Vérifications:**
1. Taille du fichier téléchargé (~600 KB avec météo, ~50 KB sans)
2. Vérifier les logs Flask: chercher "✅ Weather forecast screenshot added"
3. Tester la capture météo indépendamment

### Erreur "Template not found"

**Solution:**
1. Vérifier que les fichiers sont dans `static/templates/`
2. Vérifier les noms de fichiers (sensible à la casse)
3. Permissions de lecture sur les fichiers

### Erreur de date dans Clés Banquets

**Cause:** Bug corrigé - caractère tab dans format de date
**Solution:** Mise à jour déjà appliquée dans `generators.py` ligne 246

---

## Performance

### Temps de génération estimés

- **Séparateur Date:** ~0.5 secondes
- **Checklist Tournée:** ~0.5 secondes
- **Entretien Hiver (avec météo):** ~8-12 secondes
  - Capture météo: 6-10 secondes
  - Génération document: 1-2 secondes
- **Clés Banquets:** ~0.5-1 seconde

### Optimisations possibles

1. **Cache météo:** Cacher la capture pour 1 heure (même météo pour plusieurs générations)
2. **Pre-warming:** Lancer Playwright au démarrage de l'app
3. **Compression image:** Réduire la taille du screenshot (actuellement 1400x1000)

---

## Améliorations Futures

### Court terme
- [ ] Ajouter un indicateur de progression pour la capture météo
- [ ] Cache météo (1 heure de validité)
- [ ] Prévisualisation du document avant téléchargement

### Long terme
- [ ] Support pour autres templates dynamiques
- [ ] Historique des documents générés
- [ ] Email automatique des documents au gestionnaire
- [ ] API pour d'autres sources météo (redondance)

---

## Changelog

### Version 1.0 (2025-12-20)
- ✅ Implémentation des 4 générateurs de documents
- ✅ Intégration complète dans l'interface checklist
- ✅ Capture automatique météo avec Playwright
- ✅ Système de fallback MétéoMédia → Environment Canada
- ✅ Automatisation 100% pour 3 documents sur 4
- ✅ Formulaire dynamique pour Clés Banquets
- ✅ Correction bug date dans Clés Banquets
- ✅ Tests de génération complets

---

## Support

Pour toute question ou problème:
1. Vérifier cette documentation
2. Consulter les logs Flask en mode debug
3. Tester les composants individuellement (capture météo, imports, etc.)
4. Vérifier les templates et leurs permissions
