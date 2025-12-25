# 📊 Guide Complet des Onglets RJ - Auditeur Back

## 🎯 Vue d'ensemble

Ce guide explique **en profondeur** chaque onglet du Revenue Journal (RJ) que vous devez balancer, les documents sources à utiliser, et comment éviter les erreurs courantes.

---

## 📑 Table des Matières

1. [Contrôle - Setup Initial](#1-contrôle---setup-initial)
2. [DueBack - Montants Dus par Réceptionnistes](#2-dueback---montants-dus-par-réceptionnistes)
3. [SD (Sommaire Dépôts) - Fichier Excel Séparé](#3-sd-sommaire-dépôts---fichier-excel-séparé)
4. [RECAP - Réconciliation Comptant](#4-recap---réconciliation-comptant)
5. [Dépôt - Montants Vérifiés](#5-dépôt---montants-vérifiés)
6. [SetD - Variances des Dépôts](#6-setd---variances-des-dépôts)
7. [TRANSELECT - Cartes de Crédit et Interac](#7-transelect---cartes-de-crédit-et-interac)
8. [GEAC/UX - Réconciliation Finale CC](#8-geacux---réconciliation-finale-cc)
9. [JOUR - Statistiques et Transfert Final](#9-jour---statistiques-et-transfert-final)
10. [Ordre de Balancement](#10-ordre-de-balancement)
11. [Erreurs Courantes à Éviter](#11-erreurs-courantes-à-éviter)

---

## 🔍 IMPORTANT: Différence entre Documents

### Cashier Details vs Server Cashout Totals

| | Cashier Details (LightSpeed) | Server Cashout Totals (POSitouch) |
|---|------------------------------|-----------------------------------|
| **Imprimé depuis** | LightSpeed (PMS) | POSitouch VNC (POS F&B) |
| **Codes** | 1-99 (réceptionnistes) | Rapport serveurs |
| **Personnes** | Araujo, Latulippe, Caron, Aguilar... | Martin, Dubois, Tremblay (serveurs) |
| **Montant montré** | DueBack (solde dû à l'hôtel) | Cash Out (montant à déposer) |
| **Utilisé pour** | **DUEBACK** (onglet RJ) | **SD** (fichier Excel séparé) |
| **Va dans RECAP comme** | Ligne "DueBack Réception" | Ligne "Surplus/Déficit" (variance) |

### Exemple Visuel:

**CASHIER DETAIL (pour DueBack):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CASHIER DETAIL - Code 1 (Araujo)
LightSpeed - Réception
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cash Received:     $2,450.00
Payments Made:     $2,350.00
───────────────────────────────────────
DUE BACK:            $100.00  ← POUR DUEBACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**SERVER CASHOUT TOTALS (pour SD):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 SERVER CASHOUT TOTALS
POSitouch VNC - F&B
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Serveur            Cash Out   Tip Out
───────────────────────────────────────
Martin, Jean       $450.75    $55.20  ← POUR SD
Dubois, Marie      $320.50    $42.00  ← POUR SD
Tremblay, Luc      $275.00    $28.50  ← POUR SD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 1. Contrôle - Setup Initial

### 🎯 Objectif
Configurer les informations de base pour l'audit de la nuit.

### 📄 Documents Sources
Aucun document externe - informations connues.

### ✍️ Comment Remplir

| Champ | Cellule | Source | Notes |
|-------|---------|--------|-------|
| **Date - Jour (DD)** | B3 | Date du jour avant minuit | Exemple: 19 |
| **Date - Mois (MM)** | B4 | Mois avant minuit | Exemple: 12 |
| **Date - Année (AAAA)** | B5 | Année | Exemple: 2024 |
| **Préparé par** | B2 | Nom de l'auditeur | Votre nom complet |
| **Température** | B6 | Température extérieure | En degrés Celsius |
| **Condition Météo** | B7 | Code météo | 1=Soleil, 2=Nuages, 3=Pluie, 4=Neige |
| **Chambres à refaire** | B9 | Nombre de chambres hors service | À vérifier avec le Front |

### ⚠️ Points Critiques
- **TOUJOURS** utiliser la date **avant minuit** (date du shift, pas du lendemain)
- Exemple: Si vous travaillez la nuit du 19 au 20, utilisez le **19**
- Effacer les onglets RECAP, TRANSELECT et GEAC/UX du RJ de la veille

### 🚫 Erreurs à Éviter
- ❌ Ne pas mettre la date du lendemain (après 00h00)
- ❌ Ne pas oublier d'effacer les onglets RECAP, TRANSELECT, GEAC/UX

---

## 2. DueBack - Montants Dus par Réceptionnistes

### 🎯 Objectif
Suivre les montants que chaque réceptionniste doit à l'hôtel suite aux transactions de la journée.

### ⚠️ NE PAS CONFONDRE AVEC SD!

| Aspect | DueBack (Onglet RJ) | SD (Fichier Excel séparé) |
|--------|---------------------|---------------------------|
| **Document principal** | **Cashier Details** (LightSpeed codes 1-99) | **Server Cashout Totals** (POSitouch VNC) |
| **Pour qui?** | **RÉCEPTIONNISTES** uniquement | **SERVEURS** (+ réceptionnistes pour dépôts) |
| **Quel montant?** | Montant que la réceptionniste **doit** à l'hôtel | Montant que le serveur **devait déposer** vs **a déposé** |
| **Type de donnée** | DueBack (solde dû) | Dépôt physique + variance |
| **Utilisé dans** | RECAP (ligne DueBack) | RECAP (ligne Surplus/Déficit) |

**Résumé simple:**
- **DueBack** = Combien Araujo **DOIT** à l'hôtel? → $100.00
- **SD** = Est-ce que Martin a **DÉPOSÉ** ce qu'il devait? → Oui/Non (variance)

### 📄 Documents Sources
1. **Cashier Details** par réceptionniste (codes 1-99) - LightSpeed
2. **Rapports de caisse** individuels des réceptionnistes

### 📐 Structure de l'Onglet

L'onglet DueBack est un tableau avec:
- **Colonnes (C à W)**: 21 réceptionnistes (Araujo, Latulippe, Caron, Aguilar, etc.)
- **Lignes**: 2 lignes par jour du mois (31 jours × 2 = 62 lignes)
  - **Ligne impaire (1ère du jour)**: Previous DueBack (montant précédent, EN NÉGATIF)
  - **Ligne paire (2ème du jour)**: Nouveau DueBack (montant du jour, EN POSITIF)

### ✍️ Comment Remplir

#### Étape 1: Imprimer les Cashier Details
```
LightSpeed → Rapports → Cashier Detail
- Imprimer codes 1-99 (chaque réceptionniste)
- Imprimer code All Sub departments
```

#### Étape 2: Localiser les Montants

Pour **chaque réceptionniste**, trouver le montant DueBack sur leur rapport de caisse:

**Exemple de rapport de caisse:**
```
===========================================
CASHIER DETAIL - Araujo (Code 1)
Date: 2024-12-19
===========================================
Cash In:           $2,450.00
Cash Out:          $2,350.00
-------------------------------------------
DUE BACK:            $100.00  ← Ce montant!
===========================================
```

#### Étape 3: Remplir le RJ

Pour le **19 décembre** (par exemple):

| Réceptionniste | Ligne 1 (Previous) | Ligne 2 (Nouveau) |
|----------------|-------------------|-------------------|
| Araujo (Col C) | -$50.00 | $100.00 |
| Latulippe (Col D) | -$0.00 | $75.50 |
| Caron (Col E) | -$25.00 | $0.00 |

**Formule DueBack total du jour:**
```
Total DueBack du jour = Somme(Ligne 2 de toutes les réceptionnistes)
```

### 🔢 Calculs Importants

**DueBack Net par employé:**
```
DueBack Net = Previous DueBack (négatif) + Nouveau DueBack (positif)
```

**Exemple:**
- Araujo: -$50.00 + $100.00 = **$50.00** (doit $50 à l'hôtel)
- Latulippe: -$0.00 + $75.50 = **$75.50** (doit $75.50)
- Caron: -$25.00 + $0.00 = **-$25.00** (l'hôtel lui doit $25)

### ⚠️ Points Critiques

1. **Previous DueBack** (1ère ligne): TOUJOURS EN NÉGATIF
   - Si hier Araujo devait $50, inscrire **-$50.00**

2. **Nouveau DueBack** (2ème ligne): TOUJOURS EN POSITIF
   - Si aujourd'hui Araujo doit $100, inscrire **$100.00**

3. **Total DueBack** sera utilisé dans le RECAP

### 🚫 Erreurs à Éviter

- ❌ Inverser les signes (positif au lieu de négatif)
- ❌ Oublier le Previous DueBack de la veille
- ❌ Inscrire le DueBack dans la mauvaise colonne (mauvais réceptionniste)
- ❌ Ne pas vérifier que le total correspond au Cashier Detail "All Sub"

### ✅ Comment Vérifier

```
Total DueBack (Ligne 2) = Somme Cashier Details individuels
```

Si ça ne balance pas:
1. Vérifier chaque montant individuellement
2. Vérifier qu'aucun réceptionniste n'a été oublié
3. Comparer avec le "All Sub departments" Cashier Detail

---

## 3. SD (Sommaire Dépôts) - Fichier Excel Séparé

### 🎯 Objectif
Réconcilier les montants que les employés (serveurs, réceptionnistes) **devaient déposer** vs ce qu'ils ont **réellement déposé** dans le coffre.

### ⚠️ DISTINCTION IMPORTANTE: SD vs DueBack

**SD (ce fichier)** = Dépôts physiques des SERVEURS
```
Question: Martin devait déposer $450.75. A-t-il déposé?
→ Oui $450.75: Variance $0.00 ✅
→ Non $440.00: Variance -$10.75 ⚠️
```

**DueBack (onglet RJ)** = Soldes dus par RÉCEPTIONNISTES
```
Question: Combien Araujo doit-elle à l'hôtel?
→ $100.00 (inscrit dans DueBack ligne 2)
```

### 📄 Documents Sources
1. **Server Cashout Totals** (POSitouch VNC) - ⚠️ SERVEURS F&B, PAS réceptionnistes!
2. **Feuille "Sommaire Journalier des Dépôts"** (pad gris) - montants déposés physiquement dans le coffre
3. **Bordereau de dépôt** des réceptionnistes (pour leurs dépôts uniquement)

### 📐 Structure du Fichier SD

Le fichier SD a un onglet par date du mois:

| Colonne | Contenu | Source |
|---------|---------|--------|
| **A** | Nom de l'employé | Liste des serveurs + réceptionnistes |
| **B** | Montant POSitouch (supposé déposer) | Server Cashout Totals |
| **C** | Montant Réel Déposé | Feuille du coffre |
| **D** | Variance (C - B) | Calculé automatiquement |

### ✍️ Comment Remplir

#### Étape 1: Imprimer Server Cashout Totals

```
VNC Viewer → Reports and batches → Sales Journal Reports
→ Date: [date avant minuit] → Deposit
→ Server Cashout Totals → Print
```

**Exemple du rapport:**
```
========================================
SERVER CASHOUT TOTALS - 2024-12-19
========================================
Serveur          Cash Out    Tip Out
----------------------------------------
Martin, Jean      $450.75    $55.20
Dubois, Marie     $320.50    $42.00
Tremblay, Luc     $275.00    $28.50
----------------------------------------
TOTAL:          $1,046.25   $125.70
========================================
```

#### Étape 2: Compléter le SD

Pour chaque employé:

| Employé | POSitouch (B) | Déposé (C) | Variance (D) |
|---------|---------------|------------|--------------|
| Martin, Jean | $450.75 | $450.75 | $0.00 ✅ |
| Dubois, Marie | $320.50 | $310.00 | **-$10.50** ⚠️ |
| Tremblay, Luc | $275.00 | $275.00 | $0.00 ✅ |

#### Étape 3: Calculer la Variance Totale

```
Variance Totale SD = Somme(Colonne D)
```

Dans l'exemple ci-dessus: **-$10.50**

### 🔢 Formule de Balancement

```
Variance SD = Montant Réel Déposé - Montant POSitouch
```

**Types de variances:**
- **Variance positive (+)**: L'employé a déposé **plus** que prévu → SURPLUS
- **Variance négative (-)**: L'employé a déposé **moins** que prévu → DÉFICIT

### ⚠️ Points Critiques

1. **NE PAS IMPRIMER LE SD TOUT DE SUITE**
   - Attendre de balancer le RECAP car vous pourriez devoir modifier le SD

2. **Variance Totale** du SD sera inscrite dans:
   - RECAP (ligne Surplus/Déficit)
   - SetD (onglet RJ)

3. Si variance importante (>$20):
   - Vérifier avec les employés
   - Documenter la raison

### 🚫 Erreurs à Éviter

- ❌ Imprimer trop tôt (avant de balancer RECAP)
- ❌ Oublier d'inclure les réceptionnistes dans le SD
- ❌ Inverser les signes des variances
- ❌ Ne pas vérifier la feuille du coffre physiquement

### ✅ Comment Vérifier

```
Total Déposé (Colonne C) + Variance Totale = Total POSitouch (Colonne B)
```

---

## 4. RECAP - Réconciliation Comptant

### 🎯 Objectif
Balancer **tout le comptant** (cash) de l'hôtel pour la journée. C'est **l'onglet le plus critique** du RJ.

### 📄 Documents Sources
1. **Daily Revenue Report** (LightSpeed) - pages 5 et 6
2. **Fichier SD** (Sommaire Dépôts) - variance totale
3. **Onglet DueBack** (RJ) - total des DueBack

### 📐 Structure du RECAP

Le RECAP a 3 colonnes principales:

| Colonne | Signification |
|---------|---------------|
| **Lecture** (B) | Montant brut du système (LightSpeed/POSitouch) |
| **Correction** (C) | Ajustements manuels (+ ou -) |
| **Net** (D) | Lecture + Correction = Montant final |

### ✍️ Comment Remplir

#### Section 1: COMPTANT (Cash)

| Ligne | Champ | Cellule Lecture | Source | Notes |
|-------|-------|-----------------|--------|-------|
| 6 | **Comptant LightSpeed** | B6 | Daily Revenue p.5 - "Cash" | Comptant des chambres |
| 7 | **Comptant POSitouch** | B7 | Daily Revenue p.5 - "POSitouch Cash" | Comptant F&B |

**Exemple:**
```
Daily Revenue - Page 5
==================================
CASH PAYMENTS
----------------------------------
LightSpeed Cash:      $1,250.75
POSitouch Cash:       $3,450.25
----------------------------------
Total Cash:           $4,701.00
==================================
```

Inscrire:
- B6 (LightSpeed Lecture) = $1,250.75
- B7 (POSitouch Lecture) = $3,450.25

#### Section 2: CHÈQUES

| Ligne | Champ | Source |
|-------|-------|--------|
| 8 | **Chèques Payment Register** | Daily Revenue - "Checks" |

#### Section 3: REMBOURSEMENTS (Déductions)

⚠️ **IMPORTANT**: Les remboursements sont en **NÉGATIF** car ils réduisent le comptant.

| Ligne | Champ | Source | Signe |
|-------|-------|--------|-------|
| 11 | **Remboursement Gratuité** | Cashier Detail 50.X | **Négatif (-)** |
| 12 | **Remboursement Client** | Cashier Detail 51.X | **Négatif (-)** |

**Exemple:**
```
Si vous avez remboursé $75.50 à un client:
→ Inscrire -$75.50 (avec le signe négatif)
```

#### Section 4: DUE BACK

| Ligne | Champ | Cellule | Source |
|-------|-------|---------|--------|
| 16 | **Due Back Réception - Lecture** | B16 | **Onglet DueBack** - Total ligne 2 |
| 17 | **Due Back N/B** | B17 | Autre DueBack (rare) |

#### Section 5: SURPLUS/DÉFICIT

| Ligne | Champ | Cellule | Source |
|-------|-------|---------|--------|
| 19 | **Surplus/Déficit - Lecture** | B19 | **Variance Totale du SD** |

⚠️ **Copier la variance du SD tel quel** (avec le signe + ou -)

#### Section 6: DÉPÔT

| Ligne | Champ | Source |
|-------|-------|--------|
| 22 | **Dépôt Canadien - Lecture** | Calculé automatiquement dans le RECAP |

### 🔢 Formule de Balancement du RECAP

```
FORMULE PRINCIPALE:

Comptant Total = Comptant LightSpeed + Comptant POSitouch + Chèques
Déductions = Remboursements (négatif)
Ajouts = DueBack + Surplus/Déficit
Résultat = Dépôt Canadien

Dépôt Canadien = Comptant Total - Déductions + Ajouts
```

### ✅ Vérification Critique

**Le RECAP doit BALANCER À ZÉRO:**

```
Différence RECAP (dernière ligne) = $0.00 ✅
```

Si différence ≠ $0.00:
1. Vérifier les montants du Daily Revenue
2. Vérifier la Variance SD
3. Vérifier le Total DueBack
4. Vérifier les remboursements (signe négatif?)

### ⚠️ Points Critiques

1. **MARQUER sur le Daily Revenue** (pages 5 et 6):
   - Total variance SD (au marqueur)
   - Total DueBack (au marqueur)

2. **NE PAS IMPRIMER** le RECAP avant qu'il balance à $0.00

3. **Corrections (Colonne C)**:
   - Utilisées seulement si erreur découverte
   - Toujours documenter la raison

4. **Après balancement**:
   - Imprimer le RECAP
   - Cliquer sur le bouton "Transférer" dans l'onglet Contrôle
   - Imprimer le SD

### 🚫 Erreurs à Éviter

- ❌ Oublier le signe négatif sur les remboursements
- ❌ Ne pas vérifier que le SD balance avant de remplir le RECAP
- ❌ Copier la mauvaise ligne du DueBack (prendre ligne 2, pas ligne 1)
- ❌ Utiliser la colonne "Correction" sans raison documentée
- ❌ Imprimer avant que ça balance

### 📊 Exemple Complet

```
RECAP - 2024-12-19
===========================================
                    Lecture     Corr    Net
-------------------------------------------
Comptant LS:       $1,250.75   $0.00   $1,250.75
Comptant POSi:     $3,450.25   $0.00   $3,450.25
Chèques:             $150.00   $0.00     $150.00
-------------------------------------------
SOUS-TOTAL:        $4,851.00

Remb. Gratuité:      -$50.00   $0.00    -$50.00
Remb. Client:        -$25.50   $0.00    -$25.50
-------------------------------------------
APRÈS REMB:        $4,775.50

DueBack Récep:       $225.50   $0.00    $225.50
DueBack N/B:          $0.00    $0.00      $0.00
-------------------------------------------
APRÈS DUEBACK:     $5,001.00

Surplus/Déficit:     -$10.50   $0.00    -$10.50
-------------------------------------------
DÉPÔT CANADIEN:    $4,990.50 ✅

DIFFÉRENCE:            $0.00 ✅✅✅
===========================================
```

---

## 5. Dépôt - Montants Vérifiés

### 🎯 Objectif
Inscrire les montants **vérifiés et validés** qui ont été déposés, après toutes les réconciliations.

### 📄 Documents Sources
1. **SD (Sommaire Dépôts)** - colonne "Montant Vérifié"

### ✍️ Comment Remplir

**APRÈS avoir balancé le RECAP et imprimé le SD:**

Copier **colonne par colonne** les montants de la colonne "Montant Vérifié" du SD dans l'onglet Dépôt du RJ.

| Employé | Montant Vérifié (SD) | → | Cellule Dépôt (RJ) |
|---------|----------------------|---|-------------------|
| Martin, Jean | $450.75 | → | [Ligne Jean] |
| Dubois, Marie | $310.00 | → | [Ligne Marie] |

### ⚠️ Points Critiques

- Faire APRÈS avoir balancé le RECAP
- Utiliser la colonne "Montant Vérifié", pas "Montant POSitouch"

---

## 6. SetD - Variances des Dépôts

### 🎯 Objectif
Documenter les **variances** (surplus ou déficits) entre ce qui devait être déposé et ce qui a été déposé.

### 📄 Documents Sources
1. **SD (Sommaire Dépôts)** - colonne "Variance"
2. **Cashier Details** - codes de remboursement (50.X, 51.X)

### 📐 Structure de l'Onglet SetD

SetD est un tableau avec:
- **Lignes**: 31 jours du mois
- **Colonnes**: Différents comptes (RJ, Comptabilité, Banquet)

### ✍️ Comment Remplir

Pour le jour actuel (ex: 19):

| Colonne | Contenu | Source |
|---------|---------|--------|
| **B (RJ)** | Variance Totale | Variance Totale du SD (avec signe) |
| **I (Comptabilité)** | Remboursements | Cashier Details 50.X + 51.X |
| **K (Banquet)** | Variance Banquet | Si applicable |

**Exemple:**
```
Jour 19:
- Variance SD = -$10.50 (déficit)
- Remboursements = $75.50

SetD:
  Colonne B (RJ): -$10.50
  Colonne I (Comptabilité): $75.50
```

### ⚠️ Points Critiques

- **Signe important**: Copier tel quel (+ ou -)
- Remplir EN MÊME TEMPS que le DueBack (au début de la nuit)

---

## 7. TRANSELECT - Cartes de Crédit et Interac

### 🎯 Objectif
Réconcilier **tous les paiements par carte de crédit et Interac** à travers les différents systèmes (POSitouch, LightSpeed, Moneris, FreedomPay).

### 📄 Documents Sources

| Document | Source | Usage |
|----------|--------|-------|
| **Rapport "Établissement"** | POSitouch VNC → CloseBATCH | Totaux POSitouch par type de carte |
| **Terminaux Moneris** | Fermetures physiques des terminaux | Totaux physiques Interac/CC |
| **Batch POSitouch** | VNC → BATCH folder | Confirmation batches fermés |
| **Payment Breakdown** | FreedomPay (après PART) | Réconciliation finale LightSpeed |
| **Daily Revenue** | LightSpeed - page 6 | Totaux LightSpeed |

### 📐 Structure du TRANSELECT

Le TRANSELECT a plusieurs sections:

```
┌──────────────────────────────────────────────────┐
│ SECTION 1: F&B (Food & Beverage)                │
│  ├─ BAR (701, 702, 703)                         │
│  ├─ SPESA (704)                                  │
│  ├─ ROOM SERVICE (705)                           │
│  └─ Réception (CC/Débit)                         │
├──────────────────────────────────────────────────┤
│ SECTION 2: TOTAUX PAR TYPE DE CARTE             │
│  ├─ Interac (+ Panne Interac)                   │
│  ├─ Visa                                         │
│  ├─ MasterCard                                   │
│  └─ American Express                             │
├──────────────────────────────────────────────────┤
│ SECTION 3: RÉCONCILIATION                       │
│  ├─ Total POSitouch                             │
│  ├─ Total Moneris                               │
│  ├─ Total LightSpeed (FreedomPay)               │
│  └─ DIFFÉRENCE (doit = $0.00)                   │
└──────────────────────────────────────────────────┘
```

### ✍️ Comment Remplir - PARTIE 1 (Avant PART 03h00)

#### Étape 1: Fermer les Terminaux Moneris

**IMPORTANT**: Fermer AVANT 03h00 (avant le PART)

Aller physiquement à chaque terminal:
1. **Réception** → Fermer batch Moneris → Imprimer
2. **Bar** → Fermer batch Moneris → Imprimer
3. **Room Service** → Fermer batch Moneris → Imprimer
4. **Banquet** (si utilisé) → Fermer batch Moneris → Imprimer

**Exemple de rapport Moneris:**
```
========================================
MONERIS - FERMETURE BATCH
Terminal: Bar (Moneris #7821)
Date: 2024-12-19 - 02:45
========================================
INTERAC:               $1,245.75  (45 trans.)
VISA:                  $2,350.25  (67 trans.)
MASTERCARD:            $1,875.50  (52 trans.)
AMERICAN EXPRESS:        $450.00  (12 trans.)
----------------------------------------
TOTAL:                 $5,921.50  (176 trans.)
========================================
```

#### Étape 2: Imprimer Rapport "Établissement" POSitouch

```
VNC Viewer → CloseBATCH
→ Sélectionner dernier document
→ Imprimer
```

⚠️ **VÉRIFIER**: Pas de lots fermés en double à une heure inhabituelle!

#### Étape 3: Remplir Section F&B du TRANSELECT

Utiliser le rapport "Établissement" pour compléter:

| Section | Colonnes | Source Document |
|---------|----------|-----------------|
| **BAR 701-703** | Interac, Visa, MC, Amex | Établissement - Section Bar |
| **SPESA 704** | Interac, Visa, MC, Amex | Établissement - Section Spesa |
| **ROOM 705** | Interac, Visa, MC, Amex | Établissement - Section Room Service |
| **Réception** | CC/Débit | Établissement - Section Front Desk |

**Exemple de remplissage:**

| Département | Interac | Visa | MC | Amex |
|-------------|---------|------|----|------|
| Bar 701 | $450.25 | $1,250.75 | $875.50 | $200.00 |
| Spesa 704 | $325.50 | $1,850.25 | $1,250.75 | $450.75 |
| Room 705 | $125.00 | $550.00 | $325.00 | $75.00 |

#### Étape 4: Compléter Colonne "POSitouch"

Dans la colonne N (POSITOUCH):

```
Interac Total = Interac + Panne Interac
Visa Total = Somme des Visa de tous les départements
MasterCard Total = Somme des MC de tous les départements
Amex Total = Somme des Amex de tous les départements
```

#### Étape 5: Compléter Totaux Moneris

Additionner les fermetures Moneris de tous les terminaux:

| Type | Réception | Bar | Room Service | Banquet | **TOTAL MONERIS** |
|------|-----------|-----|--------------|---------|------------------|
| Interac | $500.00 | $450.25 | $125.00 | $0.00 | **$1,075.25** |
| Visa | $1,200.00 | $1,250.75 | $550.00 | $0.00 | **$3,000.75** |
| MC | $950.00 | $875.50 | $325.00 | $0.00 | **$2,150.50** |
| Amex | $250.00 | $200.00 | $75.00 | $0.00 | **$525.00** |

### ✍️ Comment Remplir - PARTIE 2 (Après PART 03h00)

#### Étape 6: Imprimer Payment Breakdown (FreedomPay)

```
FreedomPay (web) → Login
→ Rapports → Transaction Reports
→ Transaction Summary by Card Type
→ Date: [date avant minuit]
→ Exécuter → Statut → Télécharger Excel
→ Imprimer
```

**Exemple Payment Breakdown:**
```
========================================
FREEDOMPAY - PAYMENT BREAKDOWN
Date: 2024-12-19
========================================
VISA:                  $3,125.75
MASTERCARD:            $2,225.50
AMERICAN EXPRESS:        $575.00
----------------------------------------
TOTAL CC:              $5,926.25
========================================
```

#### Étape 7: Compléter Section A et B du TRANSELECT

| Section | Source |
|---------|--------|
| **Section A** | Daily Revenue Report (LightSpeed) |
| **Section B** | Payment Breakdown (FreedomPay) |

#### Étape 8: Compléter Daily Revenue

Utiliser page 6 du Daily Revenue pour compléter la section "Daily Revenue" du TRANSELECT.

### 🔢 Formule de Balancement TRANSELECT

```
VÉRIFICATION 1: POSitouch vs Moneris
Total POSitouch (Interac) = Total Moneris (Interac) ± variance
Total POSitouch (Visa) = Total Moneris (Visa) ± variance
Total POSitouch (MC) = Total Moneris (MC) ± variance
Total POSitouch (Amex) = Total Moneris (Amex) ± variance

VÉRIFICATION 2: Moneris vs LightSpeed/FreedomPay
Total Moneris (toutes cartes) = Total FreedomPay ± variance

RÉSULTAT FINAL:
Différence TRANSELECT = $0.00 ✅
```

### ⚠️ Points Critiques

1. **FERMER LES TERMINAUX AVANT 03H00**
   - Après 03h00, les transactions du nouveau jour commencent

2. **Rapport "Établissement" Spesa**
   - Se ferme automatiquement à 03h00
   - Aller dans VNC → CloseBATCH pour récupérer

3. **Attention aux doubles fermetures**
   - Si un terminal a été fermé 2 fois, ça va créer une variance

4. **Variances acceptables**
   - Petites variances (<$5) sont normales
   - Grandes variances (>$20) nécessitent investigation

### 🚫 Erreurs à Éviter

- ❌ Fermer les terminaux APRÈS 03h00
- ❌ Oublier un terminal (vérifier Bar, Room Service, Banquet, Réception)
- ❌ Ne pas additionner Interac + Panne Interac
- ❌ Confondre les sections POSitouch/Moneris/FreedomPay
- ❌ Oublier d'imprimer Payment Breakdown après le PART

### ✅ Comment Vérifier

**Checklist de vérification:**

```
☐ Tous les terminaux Moneris fermés et imprimés?
☐ Rapport Établissement POSitouch imprimé?
☐ Totaux POSitouch = Totaux Moneris (± petite variance)?
☐ Payment Breakdown FreedomPay imprimé (après PART)?
☐ Daily Revenue page 6 utilisée?
☐ Différence finale = $0.00 ou variance expliquée?
```

---

## 8. GEAC/UX - Réconciliation Finale CC

### 🎯 Objectif
Faire la **réconciliation finale** des cartes de crédit en comparant 3 sources: Daily Cash Out, Daily Revenue, et Balance Sheet.

### 📄 Documents Sources

| Document | Source | Usage |
|----------|--------|-------|
| **Daily Cash Out** | LightSpeed → Rapports | Montants sortis (cash out) par type de carte |
| **Daily Revenue** | LightSpeed → Rapports (page 6) | Revenus du jour par type de carte |
| **Balance Sheet** | Généré automatiquement | Solde des comptes |

### 📐 Structure du GEAC/UX

```
┌──────────────────────────────────────────────────┐
│ SECTION 1: DAILY CASH OUT                       │
│  ├─ American Express Cash Out                   │
│  ├─ MasterCard Cash Out                         │
│  └─ Visa Cash Out                               │
├──────────────────────────────────────────────────┤
│ SECTION 2: DAILY REVENUE                        │
│  ├─ American Express Revenue                    │
│  ├─ MasterCard Revenue                          │
│  └─ Visa Revenue                                │
├──────────────────────────────────────────────────┤
│ SECTION 3: BALANCE SHEET                        │
│  └─ Soldes des comptes CC                       │
├──────────────────────────────────────────────────┤
│ SECTION 4: RÉCONCILIATION                       │
│  └─ VARIANCE (si différence, envoyer courriel)  │
└──────────────────────────────────────────────────┘
```

### ✍️ Comment Remplir

#### Étape 1: Imprimer Daily Cash Out

```
LightSpeed → Rapports → Daily Cash Out
→ Date: [date avant minuit]
→ Imprimer
```

**Exemple Daily Cash Out:**
```
========================================
DAILY CASH OUT REPORT
Date: 2024-12-19
========================================
AMERICAN EXPRESS:        $575.00
MASTERCARD:            $2,225.50
VISA:                  $3,125.75
----------------------------------------
TOTAL CASH OUT:        $5,926.25
========================================
```

#### Étape 2: Remplir Section "Daily Cash Out"

| Champ | Cellule | Source |
|-------|---------|--------|
| Amex Cash Out | B6 | Daily Cash Out - "American Express" |
| MasterCard Cash Out | G6 | Daily Cash Out - "MasterCard" |
| Visa Cash Out | J6 | Daily Cash Out - "Visa" |

#### Étape 3: Remplir Section "Daily Revenue"

Utiliser **page 6 du Daily Revenue** pour compléter:

| Champ | Source |
|-------|--------|
| Amex Revenue | Daily Revenue p.6 - "American Express" |
| MasterCard Revenue | Daily Revenue p.6 - "MasterCard" |
| Visa Revenue | Daily Revenue p.6 - "Visa" |

#### Étape 4: Remplir Balance Sheet

Les soldes des comptes CC sont généralement automatiques dans le GEAC/UX.

### 🔢 Formule de Balancement GEAC/UX

```
POUR CHAQUE TYPE DE CARTE:

Cash Out + Revenue + Balance Sheet = Variance

OBJECTIF:
Variance = $0.00 ✅

Si Variance ≠ $0.00:
→ Vérifier la saisie de données
→ Vérifier TRANSELECT (peut affecter GEAC)
→ Si toujours une variance: ENVOYER COURRIEL à Roula et Mandy
```

### ⚠️ Points Critiques

1. **Variance dans GEAC/UX**
   - **AUCUNE correction possible de votre part**
   - Si variance persiste, envoyer courriel avec détails

2. **Impression**
   - Imprimer 1 copie (2 pages)
   - Mettre face vers l'arrière sous la pile des cartes de crédit

3. **Ordre final des documents CC:**
   ```
   1. Payment Breakdown (FreedomPay) + Fermetures Moneris
   2. Settlement Details (FreedomPay)
   3. Pile LightSpeed ("Credit Card Not in BLT File" sur le dessus)
   4. 2 copies TRANSELECT (face arrière)
   5. 2 pages GEAC/UX (face arrière)
   ```
   Brocher tout ensemble (coin haut gauche)

### 🚫 Erreurs à Éviter

- ❌ Essayer de corriger une variance GEAC/UX manuellement
- ❌ Ne pas envoyer de courriel si variance persiste
- ❌ Oublier d'imprimer les 2 pages
- ❌ Mal assembler la pile finale des documents CC

### ✅ Comment Vérifier

```
☐ Daily Cash Out imprimé?
☐ Daily Revenue page 6 utilisée?
☐ Variance calculée pour chaque type de carte?
☐ Si variance ≠ $0: Double-vérification faite?
☐ Si variance persiste: Courriel envoyé à Roula et Mandy?
☐ Documents assemblés dans le bon ordre?
```

---

## 9. JOUR - Statistiques et Transfert Final

### 🎯 Objectif
Compiler **toutes les statistiques de la journée** et faire le **transfert final** des données vers tous les pigeonniers et destinataires.

### 📄 Documents Sources

| Document | Source | Usage |
|----------|--------|-------|
| **Departures/Arrivals/Stayovers** | Pile DBRS | Nombre de clients, chambres |
| **Complimentary Rooms Report** | LightSpeed | Chambres complémentaires |
| **A/R Summary Report** | LightSpeed | Transferts A/R |
| **Advance Deposit Balance Sheet** | LightSpeed | Dépôts en attente |
| **Daily Revenue** | LightSpeed (dernière page) | New Balance |
| **Sales Journal for Entire House** | POSitouch | Revenus F&B totaux |
| **Rapport Excel HP/Admin** | Bureau (dossier HP) | Hotel Promotion + Admin |

### 📐 Structure de l'Onglet JOUR

L'onglet JOUR est **TRÈS LARGE** avec plusieurs sections:

```
┌────────────────────────────────────────────────────────────┐
│ COLONNES A-D: Informations de base                        │
│  - Date, variances, transferts                            │
├────────────────────────────────────────────────────────────┤
│ COLONNES E-AJ: RESTAURATION (F&B)                         │
│  - Bar, Spesa, Room Service, Banquets                     │
│  - Par catégorie: Nourriture, Boisson, Bière, Vin, etc.  │
├────────────────────────────────────────────────────────────┤
│ COLONNES AK-BD: CHAMBRES (Rooms)                          │
│  - Room Revenue, Taxes, Parking, Internet, etc.           │
├────────────────────────────────────────────────────────────┤
│ COLONNES CO-CP: STATISTIQUES CHAMBRES                     │
│  - Occupancy, Hors Service, Complémentaires              │
├────────────────────────────────────────────────────────────┤
│ COLONNE C: DIFF CAISSE                                    │
│  - DOIT = $0.00 (si tout balance)                        │
└────────────────────────────────────────────────────────────┘
```

### ✍️ Comment Remplir - Section par Section

#### SECTION 1: Informations de Base (Colonnes A-D)

| Colonne | Champ | Source | Notes |
|---------|-------|--------|-------|
| **D** | Deposit on Hand Today | Advance Deposit Balance Sheet | En **négatif** |
| **D** | New Balance | Daily Revenue (dernière page) | + ou - |
| **CF** | Transfer to A/R | A/R Summary Report - "Total Transfers" | |

#### SECTION 2: Restauration (Colonnes E-AJ)

Utiliser **Sales Journal for Entire House** (POSitouch):

| Colonnes | Départements |
|----------|--------------|
| **E-M** | Bar (701, 702, 703) |
| **N-V** | Spesa (704) |
| **W-AE** | Room Service (705) |
| **AF-AJ** | Banquets |

Pour chaque département, remplir:
- Nourriture (Food)
- Boisson (Beverage)
- Bière (Beer)
- Vin (Wine)
- Minéraux (Soft Drinks)
- Autre (Other)
- Pourboire (Gratuity)

**IMPORTANT - SOUSTRAIRE Hotel Promotion:**

```
Revenus Net Département = Sales Journal - Rapport Excel HP/Admin

Exemple:
Sales Journal Bar Nourriture: $2,500.00
HP/Admin Bar Nourriture: -$150.00
─────────────────────────────────────
Net à inscrire: $2,350.00
```

#### SECTION 3: Onglet Diff_Forfait

⚠️ **IMPORTANT**: Compléter l'onglet **Diff_Forfait** en parallèle:

Si des frais de forfait apparaissent:
1. Noter le montant dans Diff_Forfait
2. Ajuster dans l'onglet JOUR colonne BF

#### SECTION 4: Chambres (Colonnes AK-BD)

Utiliser le **Daily Revenue**:

| Colonne | Champ | Source |
|---------|-------|--------|
| AK-AL | Room Revenue | Daily Revenue - "Room Revenue" |
| AM | Room Tax | Daily Revenue - "Room Tax" |
| AN | Parking | Daily Revenue - "Parking" |
| AW | Internet | Daily Revenue - "Internet" + Banquet Internet (si applicable) |

**Note sur Internet Banquet:**
Si des frais d'internet apparaissent dans les banquets, les ajouter à la colonne AW.

#### SECTION 5: Statistiques Chambres (Colonnes CO-CP)

| Colonne | Champ | Source |
|---------|-------|--------|
| **CO** | Nombre de clients | Departures/Arrivals/Stayovers |
| **CK** | Chambres occupées | Complimentary Rooms Report (écrit à la main) |
| **CN** | Chambres complémentaires | Complimentary Rooms Report (écrit à la main) |
| **CP** | Chambres hors service | Departures/Arrivals/Stayovers |

### 🔢 Formule de Balancement JOUR

**COLONNE C - DIFF CAISSE:**

```
OBJECTIF FINAL:
Diff. Caisse (Colonne C) = $0.00 ✅

Si Diff. Caisse ≠ $0.00, vérifier:
1. Variance dans GEAC/UX? → Affecte Diff Caisse
2. Différence dans TRANSELECT? → Affecte Diff Caisse
3. Erreur de saisie dans JOUR?
```

### ⚠️ Points Critiques

1. **TOUJOURS SOUSTRAIRE HP/ADMIN**
   - Ne JAMAIS oublier de soustraire le rapport Excel HP/Admin

2. **Internet dans Banquets**
   - Parfois des frais d'internet sont dans les banquets
   - Les ajouter à la colonne AW (Internet)

3. **Forfait Location de Salle**
   - Certains groupes ont "Forfait Location de salle"
   - Les ajouter à Location de Salle Banquets (Colonne AG)

4. **Transfert Final**
   - Après avoir complété l'onglet JOUR
   - Aller dans l'onglet **Contrôle**
   - Cliquer sur le bouton **[Transférer]**
   - Cela imprime les copies pour tous les destinataires

5. **Destinations des copies:**
   ```
   - Pigeonniers (direction)
   - Sur le classeur pour le chef (semaine seulement)
   - Bureau des superviseurs
   - Copie "Vérification" sur la pile à gauche
   ```

### 🚫 Erreurs à Éviter

- ❌ Oublier de soustraire HP/Admin
- ❌ Ne pas vérifier la colonne C (Diff Caisse)
- ❌ Oublier d'ajouter Internet des banquets
- ❌ Ne pas compléter l'onglet Diff_Forfait
- ❌ Oublier de cliquer sur "Transférer" dans l'onglet Contrôle

### ✅ Comment Vérifier

```
☐ Sales Journal for Entire House utilisé?
☐ HP/Admin soustrait de chaque département?
☐ Daily Revenue utilisé pour les chambres?
☐ Onglet Diff_Forfait complété?
☐ Statistiques chambres remplies?
☐ Colonne C (Diff Caisse) = $0.00?
☐ Bouton "Transférer" cliqué dans Contrôle?
☐ Copies imprimées et distribuées?
```

---

## 10. Ordre de Balancement

### 📊 Séquence Complète (Chronologique)

Voici l'ordre **EXACT** dans lequel balancer le RJ pour éviter les erreurs:

```
┌────────────────────────────────────────────────────────────┐
│ DÉBUT DE NUIT (23h00 - 01h00)                             │
├────────────────────────────────────────────────────────────┤
│ 1. Ouvrir RJ de la veille → Enregistrer sous (nouvelle date)
│ 2. Onglet CONTRÔLE: Date + Nom auditeur                   │
│ 3. Effacer: RECAP, TRANSELECT, GEAC/UX                    │
├────────────────────────────────────────────────────────────┤
│ TRIAGE ET DÉBUT (01h00 - 02h30)                           │
├────────────────────────────────────────────────────────────┤
│ 4. Classement factures (BACK)                             │
│ 5. Imprimer Cashier Details (codes 1-99)                  │
│ 6. ✅ DUEBACK: Remplir onglet (Previous + Nouveau)        │
│ 7. Server Cashout Totals (VNC)                            │
│ 8. ✅ SD: Commencer le fichier SD (POSitouch + Déposé)    │
│ 9. Fermer terminaux Moneris (AVANT 03h00!)               │
│ 10. Imprimer "Établissement" POSitouch                     │
│ 11. ✅ TRANSELECT (Partie 1): Sections F&B + POSitouch    │
├────────────────────────────────────────────────────────────┤
│ AVANT PART (02h30 - 03h00)                                │
├────────────────────────────────────────────────────────────┤
│ 12. HP/Admin: Compléter fichier Excel Hotel Prom          │
│ 13. Imprimer Daily Revenue (pages 5 et 6)                 │
│ 14. ✅ RECAP: Balancer le comptant                        │
│     - Marquer variance SD sur Daily Revenue                │
│     - Marquer total DueBack sur Daily Revenue              │
│     - ⚠️ DOIT BALANCER À $0.00                            │
│ 15. ✅ Finaliser SD: Balancer avec RECAP                  │
│ 16. ✅ DÉPÔT: Copier montants vérifiés du SD              │
│ 17. ✅ SETD: Transcrire variances SD                      │
│ 18. IMPRIMER: RECAP + SD                                   │
│ 19. Cliquer "Transférer" dans Contrôle                    │
├────────────────────────────────────────────────────────────┤
│ 🔄 PART - 03H00 - TOURNER LA NUIT 🔄                      │
├────────────────────────────────────────────────────────────┤
│ APRÈS PART (03h00 - 05h30)                                │
├────────────────────────────────────────────────────────────┤
│ 20. Sonifi: Comparer courriel vs Cashier Detail 35.2      │
│ 21. Internet: Compléter onglet (36.1 + 36.5)              │
│ 22. FreedomPay: Payment Breakdown (Transaction Summary)   │
│ 23. ✅ TRANSELECT (Partie 2): Section A + B + Daily Rev   │
│ 24. ✅ GEAC/UX: Cash Out + Revenue + Balance Sheet        │
│     - ⚠️ Si variance: vérifier puis email Roula/Mandy     │
│ 25. Imprimer: TRANSELECT (2 copies) + GEAC (2 pages)      │
│ 26. Assembler pile CC complète (ordre spécifique)         │
│ 27. Imprimer tous rapports VNC (Daily Sales, Batch, etc.) │
│ 28. ✅ JOUR: Compléter toutes sections                    │
│     - Statistiques chambres                                │
│     - Restauration (soustraire HP/Admin!)                  │
│     - Chambres (Daily Revenue)                             │
│     - ⚠️ Colonne C (Diff Caisse) = $0.00                  │
│ 29. Cliquer "Transférer" dans Contrôle → Imprimer tout    │
├────────────────────────────────────────────────────────────┤
│ FIN DE NUIT (05h30 - 07h00)                               │
├────────────────────────────────────────────────────────────┤
│ 30. Quasimodo: Balancer réconciliation CC                 │
│ 31. DBRS: Compléter Daily Business Review Summary         │
│ 32. Assembler enveloppe blanche (comptabilité)            │
│ 33. Assembler dossier bleu daté                           │
│ 34. Livrer documents (pigeonniers, superviseurs)          │
└────────────────────────────────────────────────────────────┘
```

### ⚠️ Points Critiques de Séquence

**DÉPENDANCES IMPORTANTES:**

1. **DUEBACK → SD → RECAP**
   ```
   DueBack doit être rempli AVANT SD
   SD doit être balancé AVANT RECAP
   RECAP utilise: Total DueBack + Variance SD
   ```

2. **RECAP → Dépôt + SetD**
   ```
   Dépôt utilise: Montants vérifiés du SD (après RECAP)
   SetD utilise: Variances du SD (après RECAP)
   ```

3. **Terminaux → TRANSELECT (Partie 1)**
   ```
   Fermer terminaux Moneris AVANT 03h00
   Remplir TRANSELECT Partie 1 AVANT le PART
   ```

4. **PART 03h00 → TRANSELECT (Partie 2) → GEAC**
   ```
   FreedomPay APRÈS le PART
   TRANSELECT Partie 2 APRÈS FreedomPay
   GEAC APRÈS TRANSELECT
   ```

5. **GEAC → JOUR**
   ```
   JOUR utilise tous les onglets précédents
   Diff Caisse (Colonne C) affecté par variances GEAC/TRANSELECT
   ```

### 🚫 Erreurs de Séquence Courantes

- ❌ Imprimer SD avant de balancer RECAP
- ❌ Remplir RECAP avant de calculer la variance SD
- ❌ Faire TRANSELECT Partie 2 avant le PART
- ❌ Compléter JOUR avant de finir GEAC
- ❌ Fermer terminaux après 03h00

---

## 11. Erreurs Courantes à Éviter

### 🔴 ERREURS CRITIQUES (À ÉVITER ABSOLUMENT)

#### 1. Signer les Mauvais Montants
```
❌ ERREUR: Signer sans vérifier
✅ CORRECT: Toujours vérifier avant de signer et encercler
```

#### 2. Oublier les Signes Négatifs
```
❌ ERREUR:
   Remboursement Client: $75.50 (positif)
   Previous DueBack: $50.00 (positif)

✅ CORRECT:
   Remboursement Client: -$75.50 (négatif)
   Previous DueBack: -$50.00 (négatif)
```

#### 3. Fermer Terminaux Après le PART
```
❌ ERREUR: Fermer à 03h15 (inclut transactions du nouveau jour)
✅ CORRECT: Fermer entre 02h45 et 02h55
```

#### 4. Oublier de Soustraire HP/Admin
```
❌ ERREUR:
   Bar Nourriture = $2,500.00 (Sales Journal)

✅ CORRECT:
   Sales Journal: $2,500.00
   HP/Admin: -$150.00
   ────────────────────
   Net: $2,350.00
```

#### 5. Imprimer Avant de Balancer
```
❌ ERREUR: Imprimer RECAP avec différence de $10.50
✅ CORRECT: Balancer à $0.00 PUIS imprimer
```

### 🟡 ERREURS FRÉQUENTES (Attention)

#### 6. Confondre les Colonnes DueBack
```
❌ ERREUR: Inscrire Araujo dans colonne Latulippe
✅ CORRECT: Vérifier le nom de chaque colonne
```

#### 7. Utiliser Mauvaise Date
```
❌ ERREUR: Date du 20 (après minuit)
✅ CORRECT: Date du 19 (avant minuit)
```

#### 8. Ne Pas Vérifier les Doubles Fermetures
```
❌ ERREUR: Ignorer rapport "Établissement" avec 2 batchs
✅ CORRECT: Vérifier heure des fermetures, alerter si anormal
```

#### 9. Copier Mauvaise Ligne DueBack
```
❌ ERREUR: Utiliser ligne 1 (Previous) dans RECAP
✅ CORRECT: Utiliser ligne 2 (Nouveau) dans RECAP
```

#### 10. Oublier Cashier Details Spécifiques
```
❌ ERREUR: Ne pas noter les codes: 1.1, 90.1, 90.2, 90.13, 90.14, 40.40, 36.5
✅ CORRECT: TOUJOURS noter ces codes (même si $0.00)
```

### 🟢 BONNES PRATIQUES

#### ✅ Vérification Croisée
```
Toujours vérifier:
1. Total individuel = Total "All Sub"
2. Variance SD dans RECAP = Variance SD dans SetD
3. Total DueBack dans RECAP = Somme ligne 2 DueBack
4. Diff Caisse JOUR = $0.00 (si tout balance)
```

#### ✅ Documentation
```
Si variance ou erreur:
1. Noter la raison sur le document
2. Encercler le montant
3. Signer + date
4. Si nécessaire: envoyer courriel
```

#### ✅ Ordre des Documents
```
Maintenir l'ordre spécifique:
- Pile gauche: Cashier Details
- Dossier bleu: Documents principaux
- Enveloppe blanche: Pour comptabilité
```

#### ✅ Sauvegarde
```
TOUJOURS:
1. Enregistrer sous (nouvelle date) au début
2. Sauvegarder régulièrement (Ctrl+S)
3. Garder copies de sauvegarde
```

---

## 📝 Checklist Finale de Validation

### Avant de Terminer l'Audit

```
☐ CONTRÔLE: Date correcte (avant minuit)? Nom inscrit?
☐ DUEBACK: Tous réceptionnistes remplis? Signes corrects?
☐ SD: Variance calculée? Correspond au RECAP?
☐ RECAP: Balance à $0.00? IMPRIMÉ?
☐ DÉPÔT: Montants vérifiés copiés?
☐ SETD: Variances transcrites?
☐ TRANSELECT: Partie 1 ET Partie 2 complètes?
☐ GEAC: Variance vérifiée? Email envoyé si nécessaire?
☐ JOUR: Diff Caisse = $0.00? HP/Admin soustrait?
☐ TRANSFERT: Bouton cliqué? Copies distribuées?
☐ DOCUMENTS: Ordre correct? Brochés? Signés?
☐ QUASIMODO: Balancé?
☐ DBRS: Complété?
☐ ENVELOPPE BLANCHE: Assemblée? Livrée?
☐ DOSSIER BLEU: Assemblé? Sur tablette?
☐ PIGEONNIERS: Tous documents livrés?
```

---

## 🆘 En Cas de Problème

### Qui Contacter?

| Problème | Contact | Quand |
|----------|---------|-------|
| **Variance GEAC/UX persiste** | Roula + Mandy (email) | Après double vérification |
| **Terminaux Moneris problème** | Superviseur réception | Immédiatement |
| **Système POSitouch down** | IT Support (tel.) | Immédiatement |
| **RECAP ne balance pas** | Superviseur + Vérifier SD/DueBack | Si >$20 variance |
| **Question procédure** | Auditeur sénior | Pendant le shift |

---

## 📚 Glossaire des Termes

| Terme | Signification |
|-------|---------------|
| **PART** | Partition à 03h00 qui sépare le jour précédent du jour actuel |
| **DueBack** | Montant qu'un employé doit à l'hôtel |
| **Variance** | Différence entre montant attendu et montant réel |
| **Cash Out** | Montant sorti (remboursé/payé) |
| **Lecture** | Montant brut du système |
| **Correction** | Ajustement manuel |
| **Net** | Montant final (Lecture + Correction) |
| **HP** | Hotel Promotion (factures promotionnelles) |
| **Admin** | Administration (factures administratives) |
| **F&B** | Food & Beverage (restauration) |
| **CC** | Cartes de crédit (Credit Cards) |
| **A/R** | Accounts Receivable (comptes clients) |

---

**Dernière mise à jour:** 2024-12-22
**Version:** 2.0
**Auteur:** Système Audit Pack - Sheraton Laval

**⚠️ IMPORTANT:** Ce guide est basé sur la procédure réelle utilisée au Sheraton Laval. Toujours se référer aux documents officiels en cas de doute.
