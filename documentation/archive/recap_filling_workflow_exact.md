# RECAP - Workflow de Remplissage EXACT (Selon Procédure)

**Source:** Procédure Complète Back (Audition) - Mise à jour 19 décembre 2024

---

## 📋 SECTION: "BALANCER L'ONGLET RECAP DU RJ (COMPTANT)"

### Instructions de la Procédure:

> **BALANCER L'ONGLET RECAP DU RJ (COMPTANT).**
>
> 1. Imprimer les pages 5 et 6 du Daily Revenue dans LightSpeed
> 2. Marquer le total de variance (tel quel – ou +) du SD
> 3. Marquer le total de Dueback

**C'est TOUT ce qui est dit dans la procédure!** 😮

---

## 🔍 ANALYSE - Que faut-il VRAIMENT remplir?

Basé sur la procédure ET l'expérience terrain, voici ce qu'on remplit:

### ✅ CHAMPS À REMPLIR (INPUT)

#### 1. **Date (E1)**
- **Source:** Date de l'audition
- **Type:** INPUT manuel
- **Quand:** Au début

#### 2. **Comptant LightSpeed (B6)**
- **Source:** Daily Revenue pages 5-6 (LightSpeed)
- **Type:** INPUT - chercher le montant "Comptant" ou "Cash" dans le rapport
- **Note:** Procédure dit "Imprimer pages 5 et 6" - on cherche le cash total

#### 3. **Comptant Positouch (B7)**
- **Source:** Rapport POSitouch "Établissement"
- **Type:** INPUT - total comptant du rapport Établissement
- **Note:** Imprimé plus tôt dans procédure ("FERMER LES TERMINAUX...")

#### 4. **Chèques (B8, B9)** - OPTIONNEL
- **Source:** Si des chèques présents dans les rapports
- **Type:** INPUT si applicable
- **Note:** Rare - la plupart du temps = $0.00

#### 5. **Remboursement Gratuité (B11)**
- **Source:** ? (Non spécifié dans procédure)
- **Type:** INPUT
- **Note:** NÉGATIF - déductions pour gratuités

#### 6. **Remboursement Client (B12)**
- **Source:** ? (Non spécifié dans procédure)
- **Type:** INPUT
- **Note:** NÉGATIF - remboursements clients

#### 7. **Due Back Réception (B16)**
- **Source:** Total de l'onglet DueBack OU bouton WR
- **Type:** INPUT/AUTO-FILL
- **Note:** Déjà complété dans étape précédente

#### 8. **Due Back N/B (B17)**
- **Source:** Total de l'onglet DueBack OU bouton WN
- **Type:** INPUT/AUTO-FILL
- **Note:** Déjà complété dans étape précédente

#### 9. **Surplus/déficit (B19)** ⭐ IMPORTANT
- **Source:** "total de variance (tel quel – ou +) du SD"
- **Type:** INPUT - copié depuis le fichier SD
- **Note:** C'est la variance totale du SD (colonne G total)

#### 10. **Argent Reçu (B24)**
- **Source:** Montant physique compté/reçu
- **Type:** INPUT
- **Note:** Cash réellement compté dans la caisse

#### 11. **Préparé par (B26)**
- **Source:** Nom de l'auditeur
- **Type:** INPUT
- **Note:** Qui a préparé ce RECAP

### ❌ CHAMPS À NE PAS REMPLIR (CALCULATED/AUTO)

#### Colonne C - Corrections
- **C6, C7, C11, C12, C16, C17, etc.**
- **Type:** INPUT OPTIONNEL
- **Usage:** Seulement si corrections nécessaires
- **La plupart du temps:** VIDE

#### Colonne D - Net
- **D6, D7, D8, D9, D11, D12, D16, D17, D19, D20, D21, D22, D23**
- **Type:** CALCULÉ (=B + C)
- **Ne PAS remplir:** Excel calcule automatiquement

#### Lignes TOTAL
- **Row 10:** Total cash & checks (B10, C10, D10)
- **Row 14:** Total après remboursements (B14, C14, D14)
- **Row 18:** Total à déposer (B18, C18, D18)
- **Row 20:** Total dépôt net (B20, C20, D20)
- **Row 22:** Dépôt Canadien (B22, C22, D22) ⚠️ VIENT DU SD FILE!
- **Row 23:** BALANCE FINALE (B23, C23, D23) ⭐ LA PLUS IMPORTANTE!
- **Type:** TOUTES CALCULÉES - Ne PAS remplir

#### I10 - Balance SD
- **Type:** CALCULÉ - Lien externe vers SD file
- **Formule:** `=B23 - 'SD file'!E39`
- **Usage:** Vérification que RJ balance avec SD
- **Ne PAS remplir:** Excel calcule

---

## 🎯 WORKFLOW EXACT SELON PROCÉDURE

### Étape 1: Prérequis (Déjà fait avant RECAP)
✅ Onglet DueBack complété (avec rapports de caisse)
✅ Fichier SD complété (montants + variances)
✅ Rapports imprimés:
   - Daily Revenue pages 5-6 (LightSpeed)
   - Établissement (POSitouch)

### Étape 2: Ouvrir RECAP
1. Aller dans l'onglet RECAP du RJ
2. Vérifier que la date (E1) est correcte

### Étape 3: Remplir les montants

#### A. Cash (Lignes 6-7)
```
Prendre Daily Revenue pages 5-6
Chercher ligne "Comptant" ou "Cash LightSpeed"
→ Entrer dans B6

Prendre rapport POSitouch Établissement
Chercher total comptant
→ Entrer dans B7
```

#### B. Chèques (Lignes 8-9) - Si applicable
```
Vérifier s'il y a des chèques dans les rapports
Si OUI:
  → Entrer montants dans B8 et/ou B9
Si NON:
  → Laisser vide (Excel mettra 0.00)
```

#### C. Remboursements (Lignes 11-12)
```
⚠️ ATTENTION: Valeurs NÉGATIVES!

Chercher remboursements gratuités
→ Entrer NÉGATIF dans B11 (ex: -2543.42)

Chercher remboursements clients
→ Entrer NÉGATIF dans B12 (ex: -1067.61)
```

**❓ QUESTION:** D'où viennent ces montants exactement? Procédure ne le dit pas!
- Probablement du Daily Revenue aussi?
- Ou des rapports POSitouch?
- À clarifier avec utilisateur réel

#### D. DueBack (Lignes 16-17)
```
Option 1 (Automatique):
  → Cliquer bouton WR pour B16 (Due Back Réception)
  → Cliquer bouton WN pour B17 (Due Back N/B)

Option 2 (Manuel):
  → Aller voir onglet DueBack, copier totaux
  → Entrer dans B16 et B17
```

#### E. Surplus/Déficit (Ligne 19) ⭐
```
Procédure dit: "Marquer le total de variance (tel quel – ou +) du SD"

1. Aller dans fichier SD (Excel séparé)
2. Onglet de la date courante
3. Row 39, Colonne G = Total VARIANCE
4. Copier ce montant (avec signe + ou -)
5. Entrer dans B19
```

**Exemple:**
```
SD file, onglet "23", row 39, column G = $643.99
→ Entrer 643.99 dans B19 du RECAP
```

#### F. Argent Reçu (Ligne 24)
```
Compter physiquement le cash dans la caisse
→ Entrer montant total dans B24
```

#### G. Préparé par (Ligne 26)
```
Entrer votre nom
→ B26
```

### Étape 4: Vérifier les calculs automatiques

#### ✅ Vérifications à faire:

**1. Row 10 (Total cash):**
```
Vérifier que D10 = D6 + D7 + D8 + D9
Exemple: 521.20 + 696.05 + 0 + 0 = 1217.25 ✅
```

**2. Row 14 (Après remboursements):**
```
Vérifier que D14 = D10 + D11 + D12 + D13
Exemple: 1217.25 + (-2543.42) + (-1067.61) + 0 = -2393.78 ✅
```

**3. Row 18 (Total à déposer):**
```
Vérifier que D18 = D14 + D15 + D16 + D17
Exemple: -2393.78 + 0 + 653.10 + 667.61 = -1073.07 ✅
```

**4. Row 20 (Total dépôt net):**
```
Vérifier que D20 = D18 + D19
Exemple: -1073.07 + 1532.47 = 459.40 ✅
```

**5. Row 23 (BALANCE FINALE)** ⭐⭐⭐
```
Vérifier que D23 = D20 - D21
Exemple: 459.40 - 0 = 459.40 ✅

Ce montant est CRITIQUE - il va dans SetD Column B!
```

**6. I10 (Balance SD):**
```
Devrait être $0.00 si RJ et SD sont en accord
Si ≠ 0: Il y a une erreur quelque part!
```

### Étape 5: Après RECAP complété

Selon procédure:

> **FINIR LES ONGLETS RECAP, DÉPÔT, SETD ET LE FICHIER SD**
>
> 1. Imprimer le RECAP
> 2. Transférer les informations du RECAP dans le restant du RJ en cliquant sur [bouton]
> 3. Imprimer le fichier SD
> 4. Mettre les copies imprimées du RECAP (Top) et du fichier SD (2e) sur le dessus des caisses
> 5. **Copier les montants de la colonne « Montant Vérifié » du SD dans l'onglet « Dépôt » du RJ**
> 6. **Transcrire les informations au sujet des variances (et des remboursements s'il y en a) dans l'onglet SetD du RJ**

**Donc:**
- **RECAP B23** → **SetD Column B** (pour le jour en cours)
- **SD "Montant Vérifié"** → **Onglet Dépôt**
- **SD variances** → **SetD autres colonnes** (personnel)

---

## ❓ QUESTIONS NON RÉSOLUES

### 1. Remboursements - Source exacte?
**Question:** D'où viennent exactement les montants B11 et B12?
- Daily Revenue?
- Rapport POSitouch?
- Cashier Details?

**À clarifier avec utilisateur réel!**

### 2. Colonne C - Corrections
**Question:** Quand utilise-t-on les corrections (colonne C)?
- Si erreur de saisie?
- Si ajustement nécessaire après vérification?

**Usage:** Probablement rare - la plupart du temps vide

### 3. Boutons WR/WN/WS/EC
**Question:** Fonctionnent-ils dans Excel? Ou juste placeholders?
- WR: Fill Due Back Réception from DueBack tab
- WN: Fill Due Back N/B from DueBack tab
- WS: Calculate Surplus/Déficit (mais procédure dit de le prendre du SD?)
- EC: Exchange Canada (US dollar exchange)

**À tester:** Est-ce que ces macros fonctionnent?

---

## 🎨 UI IMPLICATIONS

### Champs à montrer comme INPUT (11 champs):
1. ✅ E1 - Date
2. ✅ B6 - Comptant LightSpeed
3. ⚠️ C6 - Correction (optionnel, rare)
4. ✅ B7 - Comptant Positouch
5. ⚠️ C7 - Correction (optionnel, rare)
6. ⚠️ B8 - Chèque payment register (rare)
7. ⚠️ B9 - Chèque Daily Revenu (rare)
8. ✅ B11 - Remb. Gratuité (NÉGATIF!)
9. ⚠️ C11 - Correction (optionnel)
10. ✅ B12 - Remb. Client (NÉGATIF!)
11. ⚠️ C12 - Correction (optionnel)
12. ✅ B16 - Due Back Réception (ou bouton WR)
13. ⚠️ C16 - Correction (optionnel)
14. ✅ B17 - Due Back N/B (ou bouton WN)
15. ⚠️ C17 - Correction (optionnel)
16. ✅ B19 - Surplus/déficit (du SD)
17. ✅ B24 - Argent Reçu
18. ✅ B26 - Préparé par

**Total:** 18 champs INPUT possibles (dont 7 optionnels/rares)

### Champs à CACHER ou READONLY (30+ champs):
- **Toute colonne D** (Net = B + C)
- **Toutes lignes TOTAL** (10, 14, 18, 20, 22, 23)
- **I10** (Balance SD - lien externe)
- **E16, E17, E19** (Calculs négatifs)
- **E21, E22** (Calculs dépôt)

### Boutons à implémenter (optionnel):
- **WR** - Auto-fill B16 from DueBack
- **WN** - Auto-fill B17 from DueBack
- **WS** - ??? (Pas clair - procédure dit de prendre du SD)
- **EC** - Rare - Exchange US (peut ignorer)

---

## ✅ RECOMMANDATIONS UI

### Option A: UI Minimaliste (Recommandé)
**Montrer SEULEMENT les champs essentiels:**

```
RECAP - Comptant

📅 Date: [____]

💵 Comptant
  LightSpeed:  [______] (Daily Revenue)
  Positouch:   [______] (Rapport Établissement)

💸 Remboursements (toujours négatifs!)
  Gratuité:    [______]
  Client:      [______]

🔄 Due Back
  Réception:   [______] [WR button]
  N/B:         [______] [WN button]

📊 Surplus/Déficit: [______] (du SD variance)

💰 Argent Reçu:     [______]

✍️ Préparé par:     [______]

━━━━━━━━━━━━━━━━━━━━━━━
BALANCE FINALE: $459.40 (calculé)
━━━━━━━━━━━━━━━━━━━━━━━

[Enregistrer RECAP]
```

**Avantages:**
- Simple, clair
- Seulement ce qu'on remplit vraiment
- Pas de confusion avec champs calculés

### Option B: UI Complète avec Sections Readonly
**Montrer TOUT mais griser les champs calculés:**

```
RECAP - Vue Complète

[Sections INPUT avec fonds blancs]
[Sections CALCULÉES avec fonds gris + readonly]
[Totaux en gras avec icône calculatrice]
```

**Avantages:**
- Voir tous les calculs en temps réel
- Transparence totale
- Peut valider les totaux immédiatement

**Inconvénients:**
- Plus complexe
- Risque de confusion (essayer de remplir readonly)

---

## 🔧 ACTIONS IMMÉDIATES

1. **Clarifier sources manquantes:**
   - D'où viennent B11 et B12 (remboursements)?
   - Demander à l'utilisateur

2. **Simplifier l'UI actuelle:**
   - Retirer/cacher tous les champs calculés
   - Garder seulement les 11 INPUT essentiels
   - Montrer les totaux en READONLY visuel

3. **Implémenter boutons WR/WN:**
   - Auto-fill depuis onglet DueBack
   - Ou retirer si trop complexe

4. **Ajouter aide contextuelle:**
   - "D'où vient ce montant?"
   - Tooltips sur chaque champ
   - Exemple: "B6: Chercher 'Comptant' dans Daily Revenue pages 5-6"

---

**Document Status:** Complete
**Questions Pending:** Sources exactes pour B11, B12
**Next Step:** Lire l'UI actuelle et identifier changements nécessaires
