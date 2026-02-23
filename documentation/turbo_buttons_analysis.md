# Analyse des Boutons "Turbo" et Workflow RJ

**Date:** 2026-01-02
**Statut:** Analyse complète - En attente de clarifications

---

## 🔍 CE QUI A ÉTÉ TROUVÉ

### 1. Codes dans Recap (Colonne F)

J'ai trouvé des codes dans la colonne F du Recap qui semblent être des **labels de référence**, pas des boutons:

| Row | Label (Colonne A) | Code (Colonne F) |
|-----|-------------------|------------------|
| E15 | Moins échange U.S. | EC |
| E16 | Due Back Réception | WR |
| E17 | Due Back N/B | WN |
| E19 | Surplus/déficit | WS |

**Hypothèse:** Ces codes sont probablement utilisés dans les formules Excel pour référencer ces cellules spécifiques.

### 2. Fichier Excel avec Macros Possibles

- **Taille du fichier:** 2,247,680 bytes (2.2 MB)
- **Nombre de sheets:** 37 onglets
- **Format:** BIFF 8.0 (Excel 97-2003)

La taille suggère qu'il pourrait contenir des macros VBA, mais **xlrd ne peut pas les lire**.

---

## 📋 WORKFLOW ACTUEL (D'APRÈS PDF PROCÉDURES)

D'après `documentation/back/procedure_complete_back.pdf`:

1. **Ouvrir le RJ d'hier**
   ```
   "Ouvrir le fichier EXCEL appelé RJ de la date d'hier,
   faire enregistrer sous et sauvegarder le document en
   changeant la date au jour actuel"
   ```

2. **Mettre à jour Controle**
   ```
   "Dans l'onglet « Contrôle » du RJ mettre à jour
   la date et le nom de l'auditeur"
   ```

3. **Effacer les onglets**
   ```
   "Effacer les onglets RECAP, TRANSELECT et GEAC/UX"
   ```

4. **Remplir les nouvelles valeurs**
   - Recap: Remplir seulement colonne B (Lecture)
   - Excel calcule automatiquement les totaux

---

## ❓ QUESTIONS POUR CLARIFICATION

### À propos des boutons "turbo":

1. **Qu'est-ce qui se passe exactement?**
   - Quand tu cliques sur un bouton "turbo", est-ce qu'il efface toutes les valeurs d'un onglet?
   - Ou seulement certaines cellules spécifiques?

2. **Où sont ces boutons?**
   - Y a-t-il un bouton par onglet (un pour Recap, un pour Transelect, un pour GEAC)?
   - Ou un seul bouton qui efface tout?

3. **Qu'est-ce qui est effacé?**
   - Seulement les **valeurs saisies** (inputs)?
   - Ou aussi les **formules calculées**?
   - Les formules restent-elles intactes?

4. **Dans quels onglets?**
   - Recap ✓
   - Transelect ✓
   - GEAC/UX ✓
   - Autres onglets?

---

## 💡 OPTIONS POUR LA WEB APP

### Option 1: Implémentation Manuelle des Boutons "Turbo"

Créer une fonction Python qui efface les cellules spécifiques:

**Recap:**
- Effacer colonne B (Lecture) - rows de données
- Garder les formules dans colonnes D et les totaux

**Transelect:**
- À déterminer quelles cellules effacer

**GEAC/UX:**
- À déterminer quelles cellules effacer

**Avantages:**
- Contrôle précis sur ce qui est effacé
- Pas besoin de macros VBA

**Inconvénients:**
- Besoin de connaître exactement quelles cellules effacer

---

### Option 2: Template RJ Vide

Créer un fichier RJ template qui contient:
- Toutes les formules
- Structure complète
- Mais **aucune valeur saisie**

**Workflow:**
1. Copier l'onglet Controle du RJ d'hier
2. Utiliser le template pour tous les autres onglets
3. Sauvegarder comme nouveau RJ

**Avantages:**
- Simple et fiable
- Garantit que les formules sont préservées

**Inconvénients:**
- Besoin de créer et maintenir le template

---

### Option 3: Copie Intelligente

Lire le RJ de la veille et copier seulement ce qui est nécessaire:

```python
def create_new_rj(previous_rj_path, auditor_name, new_date):
    # 1. Lire RJ précédent
    # 2. Copier structure de tous les onglets
    # 3. Copier formules mais pas les valeurs
    # 4. Mettre à jour Controle (date, nom)
    # 5. Sauvegarder nouveau fichier
```

**Avantages:**
- Automatisation complète
- Workflow simplifié pour l'utilisateur

**Inconvénients:**
- Plus complexe à implémenter
- Besoin de bien comprendre la structure Excel

---

## 🎯 RECOMMANDATION

**Option préférée:** Option 2 (Template RJ)

**Raison:**
- Plus simple à implémenter
- Plus fiable (pas de risque d'effacer les formules par erreur)
- Facile à maintenir

**Workflow proposé pour la web app:**

```
┌─────────────────────────────────────────┐
│  1. Utilisateur entre son nom           │
│  2. Système lit RJ d'hier (Controle)    │
│  3. Système crée nouveau RJ:             │
│     - Copie Controle avec nouveau nom   │
│     - Utilise template pour le reste    │
│  4. Utilisateur remplit les valeurs     │
│  5. Système sauvegarde le RJ du jour    │
└─────────────────────────────────────────┘
```

---

## 📊 STRUCTURE À EFFACER (HYPOTHÈSE)

### Recap
```
Colonne B (Lecture): EFFACER les valeurs saisies
Colonne C (Corr): Déjà vide (jamais utilisé)
Colonne D (Net): GARDER (formules Excel)
Totaux: GARDER (formules Excel)
```

### Transelect
```
À déterminer - besoin de voir la structure
```

### GEAC/UX
```
À déterminer - besoin de voir la structure
```

---

## 🔧 PROCHAINES ÉTAPES

1. **Clarifier avec l'utilisateur:**
   - Qu'est-ce que les boutons "turbo" font exactement?
   - Quelles cellules doivent être effacées dans chaque onglet?

2. **Analyser Transelect et GEAC:**
   - Comprendre leur structure
   - Identifier les cellules à effacer

3. **Créer Template RJ:**
   - Fichier avec formules mais sans valeurs
   - Ou implémenter la fonction d'effacement

4. **Implémenter le workflow:**
   - Interface pour entrer le nom
   - Fonction pour créer nouveau RJ
   - Fonction pour effacer les valeurs (option 1) ou utiliser template (option 2)

---

## 📝 NOTES TECHNIQUES

### Limitations de xlrd

- **Peut lire:** Données de cellules, formules (sous forme de texte), formats
- **Ne peut PAS lire:** Macros VBA, boutons de formulaire, objets graphiques, ActiveX controls

### Pour voir les macros dans Excel

1. Ouvrir le fichier dans Excel
2. Appuyer sur `Alt + F11`
3. Voir le code VBA dans l'éditeur

### Bibliothèques alternatives

- **openpyxl:** Pour fichiers .xlsx (pas .xls)
- **xlwt:** Pour écrire des fichiers .xls
- **win32com:** Pour manipuler Excel via COM (Windows seulement)

---

**Document créé:** 2026-01-02
**En attente de:** Clarifications sur les boutons "turbo"
