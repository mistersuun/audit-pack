# 📊 Analyse de la Structure du Fichier RJ Excel

## 🎯 Objectif de cette Analyse
Comprendre la structure complète du fichier `Rj-19-12-2024.xls` pour s'assurer que l'interface web couvre TOUS les champs nécessaires.

---

## 📑 Onglets Identifiés dans le Fichier

D'après le code et la documentation, le fichier RJ contient au minimum ces onglets:

### Onglets Principaux (à remplir via web)
1. **controle** - Informations de base (date, météo, auditeur)
2. **Recap** - Réconciliation comptant (17 champs)
3. **transelect** - Réconciliation cartes de crédit/Interac (25 champs)
4. **geac_ux** - Réconciliation finale CC (15 champs)
5. **DUBACK#** - DueBack par réceptionniste (dynamique)
6. **SetD** - Variances des dépôts
7. **depot** - Montants vérifiés déposés

### Onglets Secondaires (probablement pas remplis via web)
8. **jour** - Statistiques et transfert final (très large, ~100+ colonnes)
9. **Nettoyeur** - Données nettoyage
10. **somm_nettoyeur** - Sommaire nettoyage

---

## 🔍 Structure Détaillée par Onglet

### 1. ONGLET "controle"

**Structure:**
```
Colonne A          | Colonne B
───────────────────|──────────────────
Préparé par        | [Nom auditeur] (B2)
Jour (DD)          | [1-31] (B3)
Mois (MM)          | [1-12] (B4)
Année (AAAA)       | [2024] (B5)
Température        | [°C] (B6)
Condition          | [Code] (B7)
Chambres à refaire | [Nombre] (B9)
```

**Champs dans le mapping:**
- ✅ prepare_par (B2)
- ✅ jour (B3)
- ✅ mois (B4)
- ✅ annee (B5)
- ✅ temperature (B6)
- ✅ condition (B7)
- ✅ chambres_refaire (B9)

**❓ QUESTIONS:**
- Est-ce que l'interface web doit permettre de remplir le contrôle, ou c'est fait manuellement?
- Le bouton "Transférer" dans contrôle - est-ce qu'on doit l'implémenter dans le web?

---

### 2. ONGLET "Recap"

**Structure:**
```
Colonne A (Labels) | Colonne B (Lecture) | Colonne C (Corr) | Colonne D (Net)
───────────────────|─────────────────────|──────────────────|────────────────
Date               | [E1]                |                  |
...                |                     |                  |
Comptant LS        | B6                  | C6               | D6 (calculé)
Comptant POSi      | B7                  | C7               | D7 (calculé)
Chèques            | B8                  | C8               | D8 (calculé)
...                |                     |                  |
Remb. Gratuité     | B11                 | C11              | D11 (calculé)
Remb. Client       | B12                 | C12              | D12 (calculé)
...                |                     |                  |
DueBack Réception  | B16                 | C16              | D16 (calculé)
DueBack N/B        | B17                 | C17              | D17 (calculé)
...                |                     |                  |
Surplus/Déficit    | B19                 | C19              | D19 (calculé)
...                |                     |                  |
Dépôt CAD          | B22                 | C22              | D22 (calculé)
...                |                     |                  |
Préparé par        | B26                 |                  |
```

**Champs dans le mapping (17 champs):**
- ✅ date (E1)
- ✅ comptant_lightspeed_lecture (B6)
- ✅ comptant_lightspeed_corr (C6)
- ✅ comptant_positouch_lecture (B7)
- ✅ comptant_positouch_corr (C7)
- ✅ cheque_payment_register_lecture (B8)
- ✅ cheque_payment_register_corr (C8)
- ✅ remb_gratuite_lecture (B11)
- ✅ remb_gratuite_corr (C11)
- ✅ remb_client_lecture (B12)
- ✅ remb_client_corr (C12)
- ✅ due_back_reception_lecture (B16)
- ✅ due_back_reception_corr (C16)
- ✅ due_back_nb_lecture (B17)
- ✅ due_back_nb_corr (C17)
- ✅ surplus_deficit_lecture (B19)
- ✅ surplus_deficit_corr (C19)
- ✅ depot_canadien_lecture (B22)
- ✅ depot_canadien_corr (C22)
- ✅ prepare_par (B26)

**✅ STATUT:** Tous les champs sont maintenant dans l'interface web

**❓ QUESTIONS:**
- Est-ce que la colonne D (Net) est calculée automatiquement dans Excel, ou doit-on la calculer?
- Est-ce qu'il y a une ligne "Différence" qui doit être $0.00? Si oui, où est-elle?

---

### 3. ONGLET "transelect"

**Structure (d'après le mapping):**

**SECTION 1: POSITOUCH (F&B)**
```
Row 9:  BAR 701 Débit    | BAR 702 Débit    | BAR 703 Débit    | SPESA 704 Débit
Row 10: BAR 701 Visa     | BAR 702 Visa     | BAR 703 Visa     | SPESA 704 Visa
Row 11: BAR 701 Master   | BAR 702 Master   | BAR 703 Master   | SPESA 704 Master
Row 13: BAR 701 Amex     | BAR 702 Amex     | BAR 703 Amex     | SPESA 704 Amex
Row 10: ROOM 705 Visa (Col F)
```

**SECTION 2: RÉCEPTION / BANK**
```
Row 20: Réception Débit (Col D)
Row 21: Réception Visa Terminal (Col D) | Bank Visa Fusebox (Col B)
Row 22: Réception Master Terminal (Col D) | Bank Master Fusebox (Col B)
Row 24: Réception Amex Terminal (Col D) | Bank Amex Fusebox (Col B)
```

**Champs dans le mapping (25 champs):**
- ✅ date (B5)
- ✅ prepare_par (B6)
- ✅ bar_701_debit, visa, master, amex (B9, B10, B11, B13)
- ✅ bar_702_debit, visa, master, amex (C9, C10, C11, C13)
- ✅ bar_703_debit, visa, master, amex (D9, D10, D11, D13)
- ✅ spesa_704_debit, visa, master, amex (E9, E10, E11, E13)
- ✅ room_705_visa (F10)
- ✅ reception_debit (D20)
- ✅ reception_visa_term (D21)
- ✅ reception_master_term (D22)
- ✅ reception_amex_term (D24)
- ✅ fusebox_visa (B21)
- ✅ fusebox_master (B22)
- ✅ fusebox_amex (B24)

**✅ STATUT:** Tous les champs sont maintenant dans l'interface web

**❓ QUESTIONS:**
- Est-ce qu'il y a d'autres sections dans TRANSELECT (Section A, Section B mentionnées dans le guide)?
- Est-ce qu'il y a des totaux calculés automatiquement?
- Est-ce qu'il y a une ligne "Différence" qui doit être $0.00?

---

### 4. ONGLET "geac_ux"

**Structure (d'après le mapping):**

**SECTION 1: Daily Cash Out**
```
Row 6:  Amex Cash Out (B6) | Master Cash Out (G6) | Visa Cash Out (J6)
```

**SECTION 2: Total**
```
Row 10: Amex Total (B10) | Discover Total (E10) | Master Total (G10) | Visa Total (J10)
```

**SECTION 3: Daily Revenue**
```
Row 12: Amex Daily Rev (B12) | Master Daily Rev (G12) | Visa Daily Rev (J12)
```

**SECTION 4: Balance**
```
Row 32: Balance Previous (B32)
Row 37: Balance Today (B37)
Row 53: New Balance (B53)
```

**SECTION 5: Facture Direct**
```
Row 41: Facture Direct (B41) | Facture Direct Corr (D41)
```

**SECTION 6: Adv Deposit**
```
Row 44: Adv Deposit (B44) | Adv Deposit Applied (J44)
```

**Champs dans le mapping (15 champs):**
- ✅ date (E22)
- ✅ amex_cash_out (B6)
- ✅ master_cash_out (G6)
- ✅ visa_cash_out (J6)
- ✅ amex_total (B10)
- ✅ discover_total (E10)
- ✅ master_total (G10)
- ✅ visa_total (J10)
- ✅ amex_daily_revenue (B12)
- ✅ master_daily_revenue (G12)
- ✅ visa_daily_revenue (J12)
- ✅ balance_previous (B32)
- ✅ balance_today (B37)
- ✅ facture_direct (B41)
- ✅ facture_direct_corr (D41)
- ✅ adv_deposit (B44)
- ✅ adv_deposit_applied (J44)
- ✅ new_balance (B53)

**✅ STATUT:** Tous les champs sont maintenant dans l'interface web

**❓ QUESTIONS:**
- Est-ce qu'il y a des calculs automatiques dans GEAC/UX?
- Est-ce qu'il y a une ligne "Variance" qui doit être $0.00?
- Est-ce que les balances sont calculées automatiquement ou doivent être saisies?

---

### 5. ONGLET "DUBACK#" (DueBack)

**Structure:**
```
Col A: Date (Row 1)
Col B: RJ (Row 1)
Col C-K: Réceptionnistes (21 colonnes)

Row 2: Noms de famille (Last Name)
Row 3: Prénoms (First Name)

Pour chaque jour (1-31):
  Row X (impair): Previous DueBack (en négatif)
  Row X+1 (pair): Nouveau DueBack (en positif)
```

**Calcul des lignes:**
```
Jour 1: Row 5 (Previous) + Row 6 (Nouveau)
Jour 2: Row 7 (Previous) + Row 8 (Nouveau)
...
Jour N: Row (3 + N*2) (Previous) + Row (4 + N*2) (Nouveau)
```

**Réceptionnistes (d'après DUEBACK_RECEPTIONIST_COLUMNS):**
- Araujo (Col C)
- Latulippe (Col D)
- Caron (Col E)
- Aguilar (Col F)
- Nader (Col G)
- Mompremier (Col H)
- Oppong (Col I)
- Seddik (Col J)
- Dormeus (Col K)

**❓ QUESTIONS:**
- Est-ce que les réceptionnistes sont fixes ou peuvent changer?
- Est-ce qu'il y a plus de 9 réceptionnistes (jusqu'à 21 colonnes)?
- Est-ce que la colonne B (RJ) est remplie automatiquement ou manuellement?
- Est-ce que le total DueBack est calculé quelque part?

---

### 6. ONGLET "SetD"

**Structure:**
```
Row 1: Headers (noms des comptes)
Row 2: Headers (noms des comptes)
Row 5+: Une ligne par jour (Day 1 = Row 5, Day 2 = Row 6, etc.)

Colonnes:
- Col B: RJ (variance totale)
- Col I: Comptabilité (remboursements)
- Col K: Banquet (variance banquet)
```

**❓ QUESTIONS:**
- Est-ce que SetD est rempli uniquement avec la variance du SD?
- Est-ce qu'il y a d'autres colonnes importantes à remplir?
- Est-ce que SetD est synchronisé automatiquement depuis DUBACK#?

---

### 7. ONGLET "depot"

**Structure:**
```
Row 8: Headers
Row 9+: Une ligne par dépôt

Col A: Date
Col B: Montant
```

**❓ QUESTIONS:**
- Est-ce que l'onglet depot est rempli ligne par ligne (un dépôt = une ligne)?
- Est-ce qu'on doit chercher la date dans Col A ou juste ajouter à la fin?
- Est-ce qu'il y a d'autres colonnes importantes?

---

### 8. ONGLET "jour"

**Structure (TRÈS LARGE):**
```
Colonnes A-D: Informations de base
Colonnes E-AJ: Restauration (F&B) - Bar, Spesa, Room Service, Banquets
Colonnes AK-BD: Chambres (Rooms)
Colonnes CO-CP: Statistiques chambres
Colonne C: DIFF CAISSE (doit être $0.00)
```

**❓ QUESTIONS:**
- Est-ce que l'onglet JOUR doit être rempli via le web ou c'est manuel?
- Si oui, quelles sont les colonnes les plus importantes à remplir?
- Est-ce que la colonne C (Diff Caisse) est calculée automatiquement?

---

## 🔄 Workflow et Dépendances

D'après le guide, l'ordre de remplissage est:

1. **DUEBACK** → Rempli en premier (codes 1-99 Cashier Details)
2. **SD** (fichier séparé) → Calculé avec Server Cashout Totals
3. **RECAP** → Utilise: Total DueBack + Variance SD
4. **DÉPÔT** → Utilise: Montants vérifiés du SD (après RECAP)
5. **SetD** → Utilise: Variances du SD
6. **TRANSELECT Partie 1** → Avant PART 03h00 (terminaux Moneris)
7. **TRANSELECT Partie 2** → Après PART 03h00 (FreedomPay)
8. **GEAC/UX** → Après TRANSELECT
9. **JOUR** → Dernier, utilise tout

**❓ QUESTIONS:**
- Est-ce que l'interface web doit respecter cet ordre (désactiver certains boutons)?
- Est-ce qu'on doit afficher des warnings si l'utilisateur essaie de remplir dans le mauvais ordre?

---

## 📊 Champs Calculés vs Saisis

### Champs Calculés (probablement dans Excel)
- Colonne D (Net) dans RECAP = B + C
- Totaux dans TRANSELECT
- Différence dans RECAP (doit être $0.00)
- Diff Caisse dans JOUR (doit être $0.00)

### Champs Saisis (via web)
- Toutes les colonnes B (Lecture) et C (Correction)
- Tous les montants DueBack
- Tous les montants TRANSELECT
- Tous les montants GEAC/UX

**❓ QUESTIONS:**
- Est-ce qu'on doit calculer les totaux dans le web ou laisser Excel le faire?
- Est-ce qu'on doit valider que les différences sont $0.00 avant de permettre le téléchargement?

---

## 🎯 Questions Critiques pour Finaliser l'Interface

### 1. Ordre et Validation
- ❓ Doit-on implémenter une validation d'ordre (ex: ne pas permettre RECAP avant DueBack)?
- ❓ Doit-on afficher des warnings si certaines sections ne sont pas remplies?

### 2. Calculs
- ❓ Doit-on calculer les totaux dans le web ou laisser Excel le faire?
- ❓ Doit-on valider que RECAP balance à $0.00?
- ❓ Doit-on valider que Diff Caisse (JOUR) = $0.00?

### 3. Onglet JOUR
- ❓ Est-ce que JOUR doit être rempli via le web?
- ❓ Si oui, quelles sont les colonnes prioritaires?

### 4. Onglet controle
- ❓ Est-ce que controle doit être rempli via le web?
- ❓ Le bouton "Transférer" - doit-on l'implémenter?

### 5. Synchronisation
- ❓ Est-ce que la sync DueBack → SetD est déjà implémentée? (Oui, d'après le code)
- ❓ Est-ce qu'il y a d'autres synchronisations nécessaires?

### 6. Fichier SD
- ❓ Le fichier SD est séparé - doit-on l'intégrer dans le web aussi?
- ❓ Comment gérer la variance SD qui va dans RECAP?

### 7. Validation et Erreurs
- ❓ Doit-on valider les signes (négatif pour Previous DueBack, positif pour Nouveau)?
- ❓ Doit-on valider les dates (avant minuit)?
- ❓ Doit-on afficher des messages d'erreur spécifiques?

---

## 📝 Résumé des Champs par Onglet

| Onglet | Champs dans Mapping | Champs dans Web | Statut |
|--------|---------------------|-----------------|--------|
| controle | 7 | 0 | ❓ À implémenter? |
| Recap | 20 | 20 | ✅ Complet |
| transelect | 25 | 25 | ✅ Complet |
| geac_ux | 18 | 18 | ✅ Complet |
| DUBACK# | Dynamique | Dynamique | ✅ Implémenté |
| SetD | ? | 0 | ❓ À clarifier |
| depot | ? | 1 (montant) | ⚠️ Partiel |
| jour | ? | 0 | ❓ À clarifier |

---

**Date de l'analyse:** 2024-12-XX
**Fichier analysé:** Rj-19-12-2024.xls
**Basé sur:** rj_mapper.py, rj_reader.py, GUIDE_RJ_ONGLETS.md


