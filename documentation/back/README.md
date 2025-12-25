# 📊 Sheraton Laval — Procédures Back (Auditeur de Nuit)

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Documents de référence](#documents-de-référence)
3. [Systèmes utilisés](#systèmes-utilisés)
4. [Flux de travail complet](#flux-de-travail-complet)
5. [Procédures détaillées par étape](#procédures-détaillées-par-étape)
6. [Fichiers Excel et Templates](#fichiers-excel-et-templates)
7. [Impressions et Rapports](#impressions-et-rapports)
8. [Réconciliations critiques](#réconciliations-critiques)
9. [Check-lists de contrôle](#check-lists-de-contrôle)
10. [Dépannage et erreurs courantes](#dépannage-et-erreurs-courantes)
11. [Glossaire](#glossaire)
12. [Notes d'intégration webapp](#notes-dintégration-webapp)

---

## 🎯 Vue d'ensemble

Cette documentation rassemble **toutes les procédures d'audit de nuit Back** pour le Sheraton Laval. L'auditeur Back est responsable de la réconciliation financière complète de l'hôtel incluant:

- **Front Desk:** Réception, cashiers, due backs
- **F&B (Food & Beverage):** Restaurants, bars, room service, banquets
- **Systèmes de paiement:** Cartes de crédit, Interac, comptant
- **Réconciliations:** POSitouch, Moneris, FreedomPay, LightSpeed
- **Rapports:** DBRS, Revenue Journal, Quasimodo, HP/Admin
- **Remises:** Enveloppes comptabilité, pigeonniers direction

### Durée estimée de l'audit Back
- **Nuit normale:** 6-7 heures (23h00 → 06h00)
- **Nuit avec problèmes:** 7-8 heures
- **Formation nouvel auditeur:** 3-4 nuits d'observation + 2 semaines accompagnement

### Moment critique
⚠️ **03h00** - Heure du PART (partition LightSpeed) - sépare les opérations du jour précédent et du jour actuel.

---

## 📚 Documents de référence

### Documents principaux

| Fichier | Type | Taille | Description | Dernière MAJ |
|---------|------|--------|-------------|--------------|
| `2025-02 - Procédure Complete Back (Audition).docx` | Word | 36 MB | **Document maître** - Procédure complète avec captures d'écran détaillées | 2024-12-19 |
| `2024-12 - Check List Back (Audition).docx` | Word | 19 KB | Check-list condensée pour audit quotidien | 2024-12 |
| `Formation Auditeurs Back.pdf` | PDF | 4.5 MB | Guide de formation (scanné, nécessite OCR) | - |
| `Formation Auditeurs Back.docx` | Word | 8.6 MB | Version Word du guide de formation | 2024 |

### Guides spécialisés

| Fichier | Sujet | Usage |
|---------|-------|-------|
| `print_VNC.docx` | Rapports POSitouch/VNC | Liste complète des rapports à imprimer |
| `print_VNC_SHORT.docx` | Rapports POSitouch/VNC | Version condensée des rapports essentiels |
| `QUASIMODO.docx` | Réconciliation Quasimodo | Guide complet du fichier de réconciliation |
| `Back - Quasimodo.docx` | Réconciliation Quasimodo | Version alternative du guide |
| `HP explication.docx` | HP/Admin | Saisie factures Hotel Promotion et Administration |

### Fichiers Excel de travail

| Fichier | Usage | Sauvegarde |
|---------|-------|------------|
| `Rj-[DATE].xls` | **Revenue Journal** - Fichier principal de réconciliation | Quotidienne (Enregistrer sous) |
| `Sommaire journalier des dépôts.xls` | **SD** - Réconciliation des dépôts cash par employé | Quotidienne |
| `RAPPORT DE CAISSE.xlsx` | Rapports de caisse par département | Mensuelle |
| `DBRS_formule.2023_corriger copie.xlsm` | DBRS (Daily Business Review Summary) | À la fin de chaque audit |

---

## 💻 Systèmes utilisés

### Systèmes principaux

#### 1. **LightSpeed (Galaxy)**
- **Fonction:** PMS (Property Management System) - Gestion hôtelière
- **Usage:**
  - Impression Cashier Details (rapports de caisse)
  - Folio des chambres
  - Payment Breakdown (CC)
  - Daily Revenue Report
  - Guest Ledger Summary
  - Room Post Audit
- **Accès:** Workstation principale
- **PART:** 03h00 (partition jour précédent/jour actuel)

#### 2. **POSitouch (VNC Viewer)**
- **Fonction:** POS (Point of Sale) - Système de vente F&B
- **Usage:**
  - Daily Sales Report (DSR)
  - Paiement par Département
  - Sales Journal Reports
  - Memo Listings
  - Server Cashout Totals
  - Server Productivities
- **Accès:** VNC Viewer → Reports and batches → Sales Journal Reports
- **IP/Connexion:** (configuré dans VNC)

#### 3. **Moneris**
- **Fonction:** Terminaux de paiement par carte
- **Terminaux:**
  - Réception (Front Desk)
  - Bar
  - Room Service
  - Banquet
- **Usage:** Fermeture de batch (End of Day), rapports de réconciliation
- **Horaire:** Fermer AVANT le PART (03h00)

#### 4. **FreedomPay**
- **Fonction:** Processeur de paiement par carte (backend Marriott)
- **Usage:** Payment Breakdown pour réconcilier cartes de crédit
- **Accès:** Interface web (login requis)

#### 5. **Empower**
- **Fonction:** Système Marriott (Mobile Check-in, etc.)
- **Usage:** Contrôle mobile check-in, statuts chambres
- **Accès:** Application web

#### 6. **Sonifi**
- **Fonction:** Système de divertissement in-room
- **Usage:** Revenus films/jeux pay-per-view
- **Rapport:** Courriel automatique à 03h00
- **Réconciliation:** Cashier Detail 35.2 vs courriel Sonifi

#### 7. **Call Accounting**
- **Fonction:** Système de téléphonie
- **Usage:** Revenus appels téléphoniques
- **Rapport:** Call Accounting Exception Report
- **Réconciliation:** Cashier Detail 30.1/30.2

### Fichiers Excel locaux

#### **Revenue Journal (RJ)**
- **Localisation:** Lecteur partagé / Bureau
- **Onglets principaux:**
  - `Contrôle` - Date, auditeur, bouton transfert
  - `RECAP` - Réconciliation comptant
  - `TRANSELECT` - Réconciliation CC/Interac
  - `GEAC/UX` - Réconciliation finale cartes
  - `Dépôt` - Montants des dépôts validés
  - `SetD` - Variances dépôts
  - `DueBack` - Montants dûs par employés
  - `SONIFI` - Revenus Sonifi
  - `INTERNET` - Revenus internet
  - `Jour` - Statistiques quotidiennes & transfert final
  - `Diff Forfait` - Différences forfaits chambres

##### Analyse RJ (d’après la procédure complète 2025-02)
- **Contrôle** : date/auditeur, boutons macros pour transferts; réinitialiser RECAP/TRANSELECT/GEAC au début.  
- **DueBack** : ligne -(veille) et +(jour) par employé depuis Cashier Details réception; alimente RECAP comptant.  
- **Nettoyeur / Somm_Nettoyeur / Valet** : si nettoyage à sec/valet (Daoust), valeurs pour RJ et justificatifs.  
- **SD / Dépôt / SetD** : SD (fichier séparé) produit montants vérifiés → onglet Dépôt; variances/rbt → SetD.  
- **RECAP (comptant)** : balance comptant avec Daily Revenue p.5-6, DueBack, variances SD; imprimé puis transfert via bouton.  
- **Transelect** : cartes Interac/CC (POSitouch Établissement col. N, batchs Moneris, FreedomPay Payment Breakdown); imprimer x2 (face inversée).  
- **POSitouch chambres** : rapprocher Memo Listings (Chambre + Panne Lien) avec Cashier Detail dept 4-28 (ajustements LS si besoin).  
- **Internet (onglet jaune)** : montants avant taxes via Cashier Detail 36.1 (LS) et 36.5 (ajustements Marriott).  
- **SONIFI** : Cashier Detail 35.2 pré-PART vs courriel PDF 03h00; brocher ensemble.  
- **Diff Forfait** : écarts forfaits/banquets (colonnes dédiées dans Jour).  
- **GEAC/UX** : Daily Cash Out + Daily Revenue p.6; variance doit = 0 (sinon alerter).  
- **Jour** : stats CK/CN/CO/CP (DBRS pile), Transfer to A/R (A/R Summary), Advance Deposit (négatif) + New Balance, revenus F&B colonnes E–AJ/AU/AX/AY/BF/BQ/BR, internet banquets, variance caisse (col. C) attendu 0; bouton transfert avant impression/distribution.  
- **Quasimodo** (fichier séparé) : montants Transelect (F&B/réception/tablettes), AMEX net ×0.9735, comptant CAD/USD depuis RJ; variance cible ±0.01 et concordance RJ (montant négatif).  
- **Sorties papier** : RECAP, SD, Transelect x2, GEAC/UX x2, pile CC, RJ vérif, Daily Revenue, Advance Deposit, Complimentary/Room Type Production, Sales Journal Entire House, HP/Admin pack, Cashier Details brochés, DBRS, enveloppe blanche + dossier bleu/pigeonniers.

#### **Sommaire Dépôts (SD)**
- **Fonction:** Réconciliation des dépôts cash par employé
- **Colonnes:**
  - Nom employé
  - Montant déclaré
  - Montant compté
  - Variance
  - Signatures

#### **HP-ADMIN**
- **Fonction:** Suivi factures Hotel Promotion & Administration
- **Onglets:**
  - Saisie (filtrer Date = VIDE)
  - Journalier (rapport quotidien)
- **Champs:** Date, Area, Nourriture, Boisson, Bière, Vin, Minéraux, Autre, Pourboire, Paiement, Raison, Autorisé par

#### **DBRS (Daily Business Review Summary)**
- **Fonction:** Rapport de performance quotidienne Marriott
- **Fichiers:**
  - `DBRS_formule` (calculs)
  - `DBRS master` (historique)
- **Sections:**
  - Market Segment rooms
  - Daily Revenue
  - ADR (Average Daily Rate)
  - House Count
  - OTB (On The Books)
  - No-Show revenus

---

## 🔄 Flux de travail complet

### ⚠️ IMPORTANT: Flux réel de travail

Le workflow ci-dessous reflète la **pratique réelle** sur le terrain, pas un ordre strictement linéaire. Plusieurs tâches peuvent être faites en parallèle ou pendant les temps d'attente.

### Vue chronologique (flux réel optimisé)

```
┌─────────────────────────────────────────────────────────────────┐
│ DÉBUT DE QUART (23h00)                                          │
├─────────────────────────────────────────────────────────────────┤
│ 1. Setup poste de travail                    [15 min]           │
│    ├─ Ouvrir systèmes (LightSpeed, Empower, Excel)             │
│    ├─ Ouvrir RJ d'hier → "Enregistrer sous" RJ du jour         │
│    ├─ Mettre à jour onglet Contrôle (date, auditeur)           │
│    └─ Réinitialiser onglets (RECAP, TRANSELECT, GEAC, etc.)    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ DÉBUT DES OPÉRATIONS (23h15)                                   │
├─────────────────────────────────────────────────────────────────┤
│ 2. Classement factures (FONCTION BACK)       [15 min]           │
│    ├─ Récupérer TOUTES les factures/documents                  │
│    ├─ Séparer Réception vs F&B                                  │
│    ├─ Classer F&B par mode paiement:                            │
│    │  • Débit (Interac)                                         │
│    │  • Visa                                                    │
│    │  • MasterCard                                              │
│    │  • Amex                                                    │
│    │  • Forfait/Admin/HP                                        │
│    ├─ Organiser par département (Restaurant, Bar, etc.)         │
│    └─ Créer piles de travail pour traitement                    │
├─────────────────────────────────────────────────────────────────┤
│ 3. Cashier Details + DueBack + SD            [45 min]           │
│    ├─ Imprimer TOUS les Cashier Details réception              │
│    ├─ Vérifier et noter TOUS les ajustements:                  │
│    │  • Code 50+ (tous)                                         │
│    │  • TOUJOURS noter: 1.1, 90.2, 90.1, 90.13, 90.14,         │
│    │    40.40, 36.5 (même si pas 50+)                           │
│    ├─ Encercler totaux, initialer pages                         │
│    ├─ Extraire Interac/chèques                                  │
│    │                                                             │
│    ├─ ** EN PARALLÈLE **                                        │
│    ├─ Compléter onglet DueBack (RJ)                             │
│    └─ Faire SD (Sommaire Dépôts) en même temps                  │
│       ├─ Compter dépôts coffre                                  │
│       ├─ Comparer avec montants POSitouch                       │
│       ├─ Calculer variances                                     │
│       └─ Signatures (auditeur + superviseur si variance)        │
├─────────────────────────────────────────────────────────────────┤
│ 4. RECAP - Commencer                         [20 min]           │
│    ├─ Entrer infos dès que SD/DueBack complétés                │
│    ├─ Commencer réconciliation comptant                         │
│    └─ (Sera finalisé plus tard avec Daily Revenue)             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ IMPRESSIONS VNC (pendant temps morts/attente) [30-45 min]      │
├─────────────────────────────────────────────────────────────────┤
│ 5. Rapports POSitouch/VNC - ORDRE SPÉCIFIQUE                   │
│    ├─ 1. Daily Sales (EN PREMIER)                               │
│    │    ├─ 1× 9 pages (comptabilité)                            │
│    │    └─ 1× page 1 (pigeonnier M. Pazzi)                      │
│    │                                                             │
│    ├─ 2. Sales Report Journal Memo Listing (ensuite)            │
│    │    └─ Trier par mode (chambre, panne lien, etc.)           │
│    │                                                             │
│    ├─ 3. Acheteur.bat                                           │
│    │    ├─ 1× Christophe Chanvillard                            │
│    │    └─ 1× Restaurant Manager                                │
│    │                                                             │
│    └─ 4. Auditeur.bat                                           │
│         └─ Séparer "Server Sales and Tips" pour paie            │
├─────────────────────────────────────────────────────────────────┤
│ 6. Fermeture terminaux Moneris               [15 min]           │
│    ├─ (Faire quand les terminaux sont libres)                   │
│    ├─ Réception, Bar, Room Service, Banquet                     │
│    └─ Récupérer rapports batch                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TEMPS FLEXIBLE (peut être fait n'importe quand)                │
├─────────────────────────────────────────────────────────────────┤
│ 7. HP/Admin - MOMENT OPTIMAL                 [20 min]           │
│    ├─ ** MEILLEUR MOMENT: Pendant que Front run PART 2 **      │
│    ├─ (PART 2 prend du temps)                                  │
│    │                                                             │
│    ├─ Filtrer Date = VIDE                                       │
│    ├─ Saisir factures Admin/Hotel Promotion                     │
│    ├─ Rafraîchir onglet Journalier                              │
│    └─ Imprimer et assembler pack                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  PART 1 - ~01h30 - NE PAS TRAVAILLER SUR LIGHTSPEED        │
│ ⚠️  PART 2 - ~03h00 - NE PAS TRAVAILLER SUR LIGHTSPEED        │
│                                                                 │
│ PENDANT PART 2:                                                 │
│ - Front run le PART (prend du temps)                            │
│ - Back peut faire HP/Admin, finaliser impressions VNC           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ APRÈS PART 2 (quand Front a fini)            [1h30-2h00]        │
├─────────────────────────────────────────────────────────────────┤
│ 8. Recevoir rapports du Front                [5 min]            │
│    ├─ Front fournit documents imprimés                          │
│    ├─ Back vérifie complétude                                   │
│    └─ Back organise/classe par type (si nécessaire)             │
├─────────────────────────────────────────────────────────────────┤
│ 9. Transelect (CC/Interac)                   [40 min]           │
│    ├─ Reporter POSitouch Établissement                          │
│    ├─ Reporter Moneris (4 terminaux)                            │
│    ├─ Reporter FreedomPay Payment Breakdown                     │
│    ├─ Balancer par type de carte                                │
│    └─ Variance acceptable: ±0.01$ par type                      │
├─────────────────────────────────────────────────────────────────┤
│ 10. GEAC/UX (réconciliation finale CC)      [20 min]           │
│     ├─ Copier depuis Transelect                                 │
│     ├─ Settlement Details                                       │
│     ├─ Credit Card Not in BLT File                              │
│     └─ Doit balancer: 0.00$                                     │
├─────────────────────────────────────────────────────────────────┤
│ 11. Onglet Jour (RJ)                         [30 min]           │
│     ├─ Statistiques: départs/arrivées/stayovers                 │
│     ├─ Rooms OOO, comp rooms                                    │
│     ├─ Revenus F&B (depuis rapports POSitouch)                  │
│     ├─ Dépôts on hand                                           │
│     ├─ Forfaits/différences                                     │
│     ├─ Variance caisse = 0 (attendu)                            │
│     ├─ ** BOUTON TRANSFERT ** (action finale RJ)                │
│     └─ Distribuer copies (pigeonniers)                          │
├─────────────────────────────────────────────────────────────────┤
│ 12. Quasimodo                                [15 min]           │
│     ├─ Copier fichier modèle, dater                             │
│     ├─ Montants depuis Transelect (F&B, réception)              │
│     ├─ AMEX ×0.9735                                             │
│     ├─ Cash depuis RECAP                                        │
│     └─ Vérifier balance avec RJ (±0.01$)                        │
├─────────────────────────────────────────────────────────────────┤
│ 13. DBRS                                     [20 min]           │
│     ├─ Market Segment, Daily Revenue, ADR                       │
│     ├─ Copier vers master                                       │
│     ├─ House Count, OTB, No-Shows                               │
│     └─ Déposer sur bureau superviseurs                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ FIN DE NUIT - ASSEMBLAGE FINAL               [30-45 min]        │
├─────────────────────────────────────────────────────────────────┤
│ 14. Séparation et assemblage documents                          │
│     ├─ ** C'EST ICI qu'on sépare les documents **               │
│     ├─ (Beaucoup ont été imprimés PENDANT la nuit)              │
│     │                                                            │
│     ├─ Enveloppe blanche (comptabilité):                        │
│     │  ├─ Daily Sales Report (9p)                               │
│     │  ├─ Paiement par Département                              │
│     │  ├─ Tous Cashier Details                                  │
│     │  ├─ Rapports POSitouch (memo listings, etc.)              │
│     │  ├─ Pile CC complète                                      │
│     │  ├─ RECAP + SD signés                                     │
│     │  ├─ RJ (onglets pertinents imprimés)                      │
│     │  ├─ HP/Admin pack                                         │
│     │  ├─ DBRS                                                  │
│     │  └─ Quasimodo                                             │
│     │                                                            │
│     ├─ Pigeonniers:                                             │
│     │  ├─ M. Pazzi (DSR page 1)                                 │
│     │  ├─ Christophe (Acheteur.bat)                             │
│     │  ├─ Restaurant (Acheteur.bat copy 2)                      │
│     │  └─ Superviseurs (copies RJ, DBRS)                        │
│     │                                                            │
│     └─ Porter enveloppe à comptabilité                          │
├─────────────────────────────────────────────────────────────────┤
│ 15. Courriels & fin de quart                [15 min]           │
│     ├─ Envoyer courriels (contrôleur, GM, superviseurs)         │
│     ├─ Balances finales                                         │
│     ├─ Recharger papier imprimantes                             │
│     └─ Notes pour prochain shift                                │
└─────────────────────────────────────────────────────────────────┘

TOTAL ESTIMÉ: 6h00 - 7h00 (selon complexité de la nuit)
```

### 🔑 Points clés du flux réel

**Ce qui peut être fait TÔT (début de quart):**
- ✅ **Classement factures** (FONCTION BACK - pas Front!)
  - Séparer Réception vs F&B
  - Classer par mode paiement (Débit, Visa, MC, Amex, Forfait/Admin/HP)
  - Organiser par département
- ✅ **DueBack** (dès impression Cashier Details)
- ✅ **SD** (en même temps que DueBack)
- ✅ **RECAP** (commencer avec SD/DueBack, finaliser avec Daily Revenue)

**Codes Cashier Details à TOUJOURS noter:**
- Tous codes 50+ (ajustements)
- **Codes spécifiques:** 1.1, 90.1, 90.2, 90.13, 90.14, 40.40, 36.5

**Impressions VNC (pendant temps morts):**
1. Daily Sales (EN PREMIER - toujours)
2. Sales Report Journal Memo Listing
3. Acheteur.bat
4. Auditeur.bat

**HP/Admin (flexible):**
- Moment optimal: Pendant PART 2 du Front
- Peut être fait n'importe quand

**Après PART 2:**
- Recevoir rapports du Front (imprimés)
- Back vérifie et organise si nécessaire
- Transelect → GEAC/UX → Onglet Jour → Quasimodo → DBRS

**Séparation documents:**
- À la FIN (pas au début!)
- Assemblage final enveloppe blanche + pigeonniers
- Beaucoup imprimé PENDANT la nuit

┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  PART - 03h00 - NE PAS TRAVAILLER SUR LIGHTSPEED           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ POST-PART (03h15 - 06h00)                                      │
├─────────────────────────────────────────────────────────────────┤
│ 9. Copier SD → RJ                            [10 min]           │
│    ├─ Copier montants validés SD → onglet Dépôt RJ             │
│    └─ Copier variances → onglet SetD                            │
├─────────────────────────────────────────────────────────────────┤
│ 10. Transelect (CC/Interac)                  [40 min]           │
│     ├─ Onglet Transelect dans RJ                                │
│     ├─ Reporter POSitouch Établissement (col. N)                │
│     ├─ Reporter terminaux Moneris (batchs)                      │
│     ├─ Reporter FreedomPay (Payment Breakdown)                  │
│     └─ Ranger relevés fermetures Moneris                        │
├─────────────────────────────────────────────────────────────────┤
│ 11. POSitouch détails & chambres             [30 min]           │
│     ├─ Imprimer/trier Sales Journal Memo Listings               │
│     ├─ Comparer Chambre + Panne Lien avec Cashier Detail 4-28   │
│     └─ Brocher quand balancé                                    │
├─────────────────────────────────────────────────────────────────┤
│ 12. Téléphone & Sonifi                       [20 min]           │
│     ├─ Imprimer Cashier Detail 30.1/30.2                        │
│     ├─ Imprimer Call Accounting Exception                       │
│     ├─ Imprimer Cashier Detail 35.2 (pré-PART)                  │
│     ├─ Récupérer courriel Sonifi 03h00                          │
│     ├─ Compléter onglet SONIFI du RJ                            │
│     └─ Brocher 35.2 + rapport Sonifi                            │
├─────────────────────────────────────────────────────────────────┤
│ 13. Internet                                  [10 min]           │
│     ├─ Cashier Detail 36.1 (LightSpeed)                         │
│     ├─ Cashier Detail 36.5 (ajustements Marriott)               │
│     └─ Compléter onglet INTERNET (montants avant taxes)         │
├─────────────────────────────────────────────────────────────────┤
│ 14. Pile finale CC                           [20 min]           │
│     ├─ Assembler Payment Breakdown                              │
│     ├─ Fermetures Moneris                                       │
│     ├─ Settlement Details                                       │
│     ├─ CC LightSpeed (Not in BLT File)                          │
│     ├─ 2× Transelect imprimé (face arrière)                     │
│     ├─ 2× GEAC/UX                                               │
│     └─ Brocher ensemble                                         │
├─────────────────────────────────────────────────────────────────┤
│ 15. Onglet Jour du RJ                        [30 min]           │
│     ├─ Statistiques (départs/arrivées/stayovers)                │
│     ├─ Rooms OOO, comp rooms, transfers A/R                     │
│     ├─ Dépôts on hand                                           │
│     ├─ Revenus F&B (colonnes E-BQ)                              │
│     ├─ Forfaits/diff forfait                                    │
│     ├─ Internet banquets                                        │
│     ├─ Variance caisse = 0 (attendu)                            │
│     ├─ Bouton de transfert depuis onglet Contrôle               │
│     └─ Distribuer copies (pigeonniers, superviseurs)            │
├─────────────────────────────────────────────────────────────────┤
│ 16. Quasimodo                                 [15 min]           │
│     ├─ Copier fichier modèle du mois                            │
│     ├─ Dater cellules A2/D1                                     │
│     ├─ Montants Transelect (F&B, réception, tablettes)          │
│     ├─ AMEX net (×0.9735)                                       │
│     ├─ Comptant (CAD/USD) depuis RJ                             │
│     ├─ Ajuster variance ≤0.01                                   │
│     └─ Vérifier concordance RJ (montant négatif)                │
├─────────────────────────────────────────────────────────────────┤
│ 17. Enveloppe blanche & dossier bleu         [30 min]           │
│     ├─ Assembler toutes les piles (voir détails §8)             │
│     ├─ Vérifier check-list complétude                           │
│     └─ Porter à la comptabilité                                 │
├─────────────────────────────────────────────────────────────────┤
│ 18. DBRS                                      [20 min]           │
│     ├─ Ouvrir DBRS_formule + DBRS master                        │
│     ├─ Compléter Market Segment (rooms)                         │
│     ├─ Daily Rev (Today)                                        │
│     ├─ Vérifier ADR                                             │
│     ├─ Copier vers master via bouton                            │
│     ├─ Compléter House Count/OTB/allotements/NoShow             │
│     ├─ Ajuster prévisions                                       │
│     └─ Déposer pile DBRS sur bureau superviseurs                │
├─────────────────────────────────────────────────────────────────┤
│ 19. Courriels & fin de quart                 [15 min]           │
│     ├─ Envoyer courriels requis (direction, superviseurs)       │
│     ├─ Balances finales                                         │
│     ├─ Préparer pigeonnier mobile                               │
│     └─ Recharger papier imprimantes                             │
└─────────────────────────────────────────────────────────────────┘

TOTAL ESTIMÉ: 6h30 - 7h00
```

---

## 📝 Procédures détaillées par étape

### ÉTAPE 1: Setup poste de travail (15 min)

**Objectif:** Préparer l'environnement de travail et créer le Revenue Journal du jour.

**Actions:**

1. **Connexion systèmes**
   - Allumer workstation principale
   - Ouvrir LightSpeed Galaxy
   - Ouvrir Empower (Mobile Check-in)
   - Ouvrir VNC Viewer

2. **Création Revenue Journal**
   ```
   - Localiser RJ d'hier: lecteur partagé/Bureau
   - Ouvrir le fichier: Rj-[DATE-HIER].xls
   - Fichier → Enregistrer sous...
   - Nom: Rj-[DATE-AUJOURD'HUI].xls
   - Exemple: Rj-20-12-2024.xls
   ```

3. **Mise à jour onglet Contrôle**
   - Cliquer sur onglet `Contrôle`
   - Cellule Date: entrer date du jour
   - Cellule Auditeur: entrer nom de l'auditeur
   - **NE PAS CLIQUER** sur bouton "Transfert" maintenant

4. **Réinitialisation onglets**
   - Onglet `RECAP`: vider toutes les cellules de montants
   - Onglet `TRANSELECT`: vider colonnes de montants
   - Onglet `GEAC/UX`: vider
   - Onglets `SONIFI`, `INTERNET`, `Diff Forfait`: vérifier vides

5. **Organisation espace physique**
   - Préparer 6 zones de tri (piles):
     1. Réception (enveloppes grises/brunes)
     2. F&B Débit
     3. F&B Visa
     4. F&B MasterCard
     5. F&B Amex
     6. F&B Forfait/Admin/HP
   - Préparer agrafeuse, surligneur, stylos

**Vérification:**
- [ ] RJ du jour créé et daté
- [ ] Onglet Contrôle à jour
- [ ] Tous les onglets de montants vides
- [ ] Espace de travail organisé

**Système utilisé:** LightSpeed, Excel, Empower, VNC

**Durée:** 15 minutes

---

### ÉTAPE 2: Triage papiers & documents (20 min)

**Objectif:** Organiser tous les documents de la journée par type et mode de paiement pour faciliter le traitement.

**Actions:**

1. **Récupération documents**
   - **Réception:**
     - Enveloppes grises/brunes (shift day/evening)
     - Feuilles d'ajustement
     - Relevés de caisse
   - **F&B:**
     - Enveloppes bleues (restaurants, bars, room service, banquets)
     - Rapports serveurs
     - Bordereaux de dépôt

2. **Séparation Réception vs F&B**
   ```
   RÉCEPTION (pile 1)
   ├─ Cashier Details imprimés
   ├─ Feuilles d'ajustement
   ├─ Relevés terminaux Moneris
   ├─ Folio chambres problématiques
   └─ Notes superviseurs

   F&B (piles 2-6)
   ├─ Par mode de paiement:
   │  ├─ Débit (Interac)
   │  ├─ Visa
   │  ├─ MasterCard
   │  ├─ Amex
   │  └─ Forfait/Admin/HP
   └─ Documents:
      ├─ Rapports serveurs (tips, sales)
      ├─ Factures POSitouch
      └─ Bordereaux dépôt cash
   ```

3. **Classification F&B détaillée**
   - **Par département:**
     - Restaurant (dept 4)
     - Bar (dept 10)
     - Room Service (dept 12)
     - Banquet (dept 28)
   - **Par type:**
     - Factures clients
     - Rapports de ventes
     - Tips sheets
     - Dépôts cash

4. **Documents spéciaux**
   - **Caisses:** Séparer par département et employé
   - **Relevés Moneris:** Par terminal (réception, bar, room service, banquet)
   - **Folio problématiques:** Marquer avec post-it pour révision
   - **Ajustements:** Vérifier signatures et autorisations

5. **Vérification complétude**
   - Compter nombre d'enveloppes F&B (noter sur feuille)
   - Vérifier présence bordereaux dépôt pour chaque caisse
   - Confirmer ajustements signés
   - Noter documents manquants sur feuille de notes

**Vérification:**
- [ ] Réception séparée de F&B
- [ ] F&B classé par mode de paiement
- [ ] Tous les documents présents (ou manquants notés)
- [ ] Piles organisées et étiquetées

**Documents produits:** Aucun

**Système utilisé:** Aucun (travail manuel)

**Durée:** 20 minutes

---

### ÉTAPE 3: Caisses & DueBack (30 min)

**Objectif:** Réconcilier les caisses de réception, traiter les paiements Interac/chèques, et compléter les montants dus par les employés (DueBack).

**Actions:**

1. **Impression Cashier Details - Réception**
   ```
   LightSpeed → Reports → Cashier Reports

   IMPRIMER:
   - Cashier Detail par département:
     ├─ Dept 2 (Front Desk - General)
     ├─ Dept 90.1 (Réceptionniste A)
     ├─ Dept 90.2 (Réceptionniste B)
     └─ Dept 90.3 (Réceptionniste C)

   - Cashier Detail 40.52 (Dépôt Restaurant)
   - Feuilles d'ajustement (si applicable)
   ```

2. **Traitement Cashier Details**
   - **Pour CHAQUE Cashier Detail:**
     - Encercler le total général (en bas)
     - Initialer chaque page
     - **Noter TOUS les ajustements:**
       ```
       CODES À TOUJOURS NOTER:

       1. Tous les codes 50+ (ajustements):
          - 50.x, 51.x, 52.x, etc.
          - Tous sont des ajustements qui doivent être vérifiés

       2. CODES SPÉCIFIQUES (même si < 50):
          - 1.1   (TOUJOURS noter)
          - 90.1  (si présent - TOUJOURS noter)
          - 90.2  (TOUJOURS noter)
          - 90.13 (TOUJOURS noter)
          - 90.14 (TOUJOURS noter)
          - 40.40 (TOUJOURS noter)
          - 36.5  (TOUJOURS noter - ajustements Marriott Internet)

       FORMAT DE NOTE:
       Dept [CODE] - Montant: $XXX.XX - Description
       Exemple: Dept 90.2 - Montant: $125.50 - Réceptionniste B
       ```
     - Surligner anomalies (montants négatifs, ajustements non signés)
     - Comparer total avec bordereau de dépôt

3. **Extraction paiements Interac & Chèques**
   - Parcourir chaque Cashier Detail ligne par ligne
   - Noter sur feuille séparée:
     ```
     INTERAC:
     - Folio #: _______
     - Montant: _______
     - Employé: _______

     CHÈQUES:
     - Folio #: _______
     - Montant: _______
     - Nom: _______
     - Banque: _______
     ```
   - Reporter dans onglet `Transelect` du RJ (section Interac)

4. **Onglet DueBack dans RJ**
   ```
   Onglet: DueBack

   STRUCTURE:
   - Ligne 1: DueBack jour précédent (négatif = dette employé)
   - Ligne 2: DueBack du jour actuel (positif = dû par employé)

   COLONNES (par employé):
   - A: Nom employé
   - B: DueBack précédent (copier depuis hier)
   - C: Montant département (depuis Cashier Detail)
   - D: Interac extrait
   - E: Chèques extraits
   - F: Ajustements
   - G: Total DueBack = B + C - D - E + F
   ```

   **Exemple:**
   ```
   Employé: Marie Tremblay
   - DueBack hier: -50.00 (elle devait 50$)
   - Département aujourd'hui: 1,250.00
   - Interac: -200.00
   - Chèques: -100.00
   - Ajustements: +15.00 (over/short)
   - Total DueBack: -50 + 1250 - 200 - 100 + 15 = 915.00
   ```

5. **Fermeture folio Dépôt Restaurant (40.52)**
   - LightSpeed → Folio Search
   - Chercher département 40.52
   - Vérifier balance = 0.00$
   - Si balance ≠ 0:
     - Créer ajustement avec code appropriate
     - Obtenir signature superviseur
     - Documenter raison
   - Imprimer folio final
   - Imprimer Cashier Detail 40.52

6. **Complétude documents Nettoyeur/Valet**
   - **Si applicable (vérifier avec superviseur):**
     ```
     NETTOYEUR:
     - Imprimer rapport nettoyeur
     - Compléter formulaire "Somm Nettoyeur"
     - Faire signer employé(s)

     VALET:
     - Imprimer rapport valet parking
     - Compléter formulaire valet
     - Comparer avec cash reçu
     ```

**Vérification:**
- [ ] Tous Cashier Details imprimés, encerclés, initialisés
- [ ] Interac/chèques extraits et notés
- [ ] Onglet DueBack complété et balancé
- [ ] Folio 40.52 = 0.00$
- [ ] Nettoyeur/Valet complétés (si applicable)

**Documents produits:**
- Cashier Details réception (multiples)
- Cashier Detail 40.52 + folio
- Feuille extraction Interac/Chèques
- Formulaires Nettoyeur/Valet (si applicable)

**Système utilisé:** LightSpeed, Excel (RJ onglet DueBack)

**Durée:** 30 minutes

---

### ÉTAPE 4: Fermeture terminaux Moneris (15 min)

**Objectif:** Fermer tous les terminaux de paiement Moneris et récupérer les rapports de batch pour réconciliation.

**⚠️ CRITIQUE:** Cette étape DOIT être complétée AVANT 03h00 (PART).

**Actions:**

1. **Localisation terminaux**
   ```
   TERMINAUX MONERIS (4 au total):
   1. Front Desk (Réception principale)
   2. Bar (Lounge)
   3. Room Service (Cuisine/Service)
   4. Banquet (Salle événements)
   ```

2. **Procédure de fermeture POUR CHAQUE terminal**
   ```
   ÉTAPES SUR TERMINAL MONERIS:

   1. Appuyer sur bouton ADMIN (ou F4)
   2. Enter → mot de passe (si demandé): [CONFIDENTIEL]
   3. Sélectionner: "4 - Fermeture de Lot" (ou "Batch Close" / "End of Day")
   4. Confirmer: OUI
   5. ATTENDRE impression du rapport (15-30 secondes)
   6. Récupérer le rapport imprimé

   RAPPORT CONTIENT:
   - Date/heure de fermeture
   - Numéro de batch
   - Nombre de transactions
   - Total Visa
   - Total MasterCard
   - Total Amex
   - Total Débit (Interac)
   - Total général
   ```

3. **Traitement des rapports**
   - **Pour CHAQUE rapport Moneris:**
     - Encercler:
       - Numéro de batch
       - Total général
       - Détail par type de carte
     - Annoter en haut:
       - Nom du terminal (ex: "RÉCEPTION")
       - Date
       - Heure de fermeture
     - Stapler multiple pages ensemble si applicable

4. **Organisation des rapports**
   ```
   PILE "MONERIS":
   ├─ Rapport Réception (en haut)
   ├─ Rapport Bar
   ├─ Rapport Room Service
   └─ Rapport Banquet (en bas)

   ORDRE: du plus gros volume au plus petit
   ```

5. **Entrée dans feuille de travail temporaire**
   - Créer feuille Excel temporaire ou noter sur papier:
   ```
   MONERIS - [DATE]

   RÉCEPTION:
   - Batch #: _______
   - Visa: _______
   - MC: _______
   - Amex: _______
   - Débit: _______
   - TOTAL: _______

   BAR:
   - [même structure]

   ROOM SERVICE:
   - [même structure]

   BANQUET:
   - [même structure]

   GRAND TOTAL:
   - Visa: _______
   - MC: _______
   - Amex: _______
   - Débit: _______
   - TOTAL: _______
   ```

6. **Vérification synchronisation**
   - Confirmer que TOUS les 4 terminaux sont fermés
   - Vérifier que batch# sont séquentiels
   - Vérifier aucune transaction en attente
   - Si erreur sur un terminal:
     - Noter erreur
     - Appeler support Moneris si nécessaire: 1-866-319-7450
     - Documenter actions prises

**Vérification:**
- [ ] 4 terminaux fermés (Réception, Bar, Room Service, Banquet)
- [ ] 4 rapports de batch récupérés
- [ ] Totaux encerclés et annotés
- [ ] Rapports organisés en pile
- [ ] Montants notés dans feuille temporaire

**Documents produits:**
- 4 rapports de fermeture Moneris
- Feuille de travail Moneris (temporaire)

**Système utilisé:** Terminaux Moneris

**Durée:** 15 minutes (4-5 min par terminal)

**Notes:**
- Si terminal ne répond pas: débrancher/rebrancher, attendre 30 sec
- Si erreur persiste: contacter superviseur immédiatement
- Les montants Moneris seront utilisés dans ÉTAPE 10 (Transelect)

---

### ÉTAPE 5: Rapports POSitouch/VNC (pré-PART) (45 min)

**Objectif:** Imprimer tous les rapports POSitouch nécessaires via VNC Viewer pour la réconciliation F&B.

**⚠️ NOTE:** Certains rapports doivent être imprimés AVANT le PART (03h00), d'autres APRÈS.

**Actions:**

1. **Connexion VNC Viewer**
   ```
   - Ouvrir VNC Viewer
   - Connexion: [IP serveur POSitouch]
   - Mot de passe: [CONFIDENTIEL]
   - Attendre chargement interface POSitouch
   ```

2. **Vérification CloseBATCH automatique**
   - Si Spesa configuré pour batch automatique 03h00:
     - Aller dans: Reports and batches → CloseBATCH
     - Vérifier dernier batch = hier 03h00
     - Noter batch #: ___________
   - Si batch auto n'a pas fonctionné:
     - Lancer manuellement: "Close Current Batch"
     - Attendre confirmation
     - Noter nouveau batch #

3. **Impression Établissement + Spesa (PRÉ-PART)**
   ```
   VNC → Reports and batches → Sales Journal Reports

   SÉLECTIONNER:
   - Report: "Paiement par Établissement"
   - Date: HIER (date du shift en cours)
   - Options: All locations

   IMPRIMER: 1 copie

   ENSUITE:
   - Report: "Utilisateurs Spesa"
   - Date: HIER
   - Options: Summary

   IMPRIMER: 1 copie
   ```

4. **Impression Server Cashout Totals (PRÉ-PART)**
   ```
   VNC → Reports and batches → Sales Journal Reports

   SÉLECTIONNER:
   - Report: "Server Cashout Totals"
   - Date Range: HIER 00:00 à HIER 23:59
   - Group by: Server
   - Include: Tips

   IMPRIMER: 1 copie
   ```

5. **Impression Daily Sales Report - DSR (PRÉ-PART)**
   ```
   VNC → Reports and batches → Sales Journal Reports

   SÉLECTIONNER:
   - Report: "Daily Sales Report"
   - Date: HIER
   - Options: Full report (9 pages)

   IMPRIMER:
   - 1× 9 pages complètes (pour enveloppe blanche comptabilité)
   - 1× page 1 seulement (pour pigeonnier M. Pazzi)

   PAGES DU DSR:
   Page 1: Summary totals
   Page 2: Sales by category
   Page 3: Sales by time period
   Page 4: Server sales summary
   Page 5: Payment types (IMPORTANT pour RECAP)
   Page 6: Payment details (IMPORTANT pour RECAP)
   Page 7: Discounts and voids
   Page 8: Tax summary
   Page 9: Memo/Notes
   ```

6. **Impression Paiement par Département (PRÉ-PART)**
   ```
   VNC → Reports and batches → Sales Journal Reports

   SÉLECTIONNER:
   - Report: "Paiement par Département"
   - Date: HIER
   - Format: Horizontal landscape

   IMPRIMER: 1 copie (recto-verso si possible)

   ACTION: Brocher immédiatement à l'arrière de la copie 9 pages du DSR
   ```

7. **Impression Batchs ACHETEUR (PRÉ-PART)**
   ```
   VNC → Reports and batches → Batch Reports

   SÉLECTIONNER BATCH: "ACHETEUR.BAT"

   CONTENU:
   - Item Sales Trend Analysis (2 copies)
     Copy 1: Pour Christophe Chanvillard (Acheteur)
     Copy 2: Pour Restaurant Manager

   IMPRIMER: 2 copies

   ACTIONS:
   - Mettre copie 1 dans pigeonnier "Christophe Chanvillard"
   - Mettre copie 2 dans pigeonnier "Restaurant"
   ```

8. **Impression Batch AUDIT (PRÉ-PART)**
   ```
   VNC → Reports and batches → Batch Reports

   SÉLECTIONNER BATCH: "AUDIT.BAT"

   CONTENU:
   - Sales Journal Report for [DATE]
   - Includes: All memo listings

   ACTIONS:
   1. Imprimer batch complet
   2. RETIRER: Page "Server Sales and Tips" → pour département paie
   3. RESTE: Brocher ensemble pour enveloppe comptabilité
   ```

9. **Organisation rapports PRÉ-PART**
   ```
   PILE POSitouch (PRÉ-PART):
   ├─ DSR 9 pages + Paiement par Dept (brochés ensemble)
   ├─ DSR page 1 seule (séparé pour M. Pazzi)
   ├─ Établissement
   ├─ Utilisateurs Spesa
   ├─ Server Cashout Totals
   ├─ ACHETEUR.BAT (2 copies)
   └─ AUDIT.BAT (page Server Sales mise de côté)
   ```

10. **Notes pour rapports POST-PART (à faire après 03h15)**
    - Sales Journal Memo Listings (par mode)
    - Manager Reports
    - Server Productivities
    - Detail Ticket Reports
    - **Ces rapports seront imprimés dans ÉTAPE 11**

**Vérification:**
- [ ] VNC connecté et opérationnel
- [ ] Batch fermé/vérifié
- [ ] DSR 9 pages + page 1 séparée imprimés
- [ ] Paiement par Dept broché avec DSR
- [ ] Établissement + Spesa imprimés
- [ ] Server Cashout Totals imprimé
- [ ] ACHETEUR.BAT (2 copies) imprimé → pigeonniers
- [ ] AUDIT.BAT imprimé → Server Sales séparé
- [ ] Tous rapports PRÉ-PART organisés en pile

**Documents produits:**
- Daily Sales Report (9 pages) + Paiement par Dept
- Daily Sales Report (page 1 seule)
- Paiement par Établissement
- Utilisateurs Spesa
- Server Cashout Totals
- ACHETEUR.BAT (2 copies)
- AUDIT.BAT (moins Server Sales)
- Server Sales and Tips (séparé pour paie)

**Système utilisé:** VNC Viewer → POSitouch

**Durée:** 45 minutes

**Notes importantes:**
- NE PAS fermer VNC - sera réutilisé POST-PART
- Pages 5-6 du DSR sont CRITIQUES pour RECAP (ÉTAPE 8)
- Vérifier qualité d'impression (lisibilité des chiffres)
- Si imprimante jam: attendre, ne pas réimprimer avant vérification

---

### ÉTAPE 6: HP/Admin (20 min)

**Objectif:** Saisir et imprimer les factures Hotel Promotion et Administration dans le fichier Excel HP-ADMIN.

**Contexte:** Hotel Promotion (HP) et Administration (Admin) sont des départements internes qui consomment nourriture/boissons sans payer - ces coûts doivent être suivis et approuvés.

**Actions:**

1. **Ouverture fichier HP-ADMIN**
   ```
   Localisation: Lecteur partagé → Comptabilité → HP-ADMIN.xlsx

   OU: Bureau → HP-ADMIN.xlsx

   - Double-cliquer pour ouvrir
   - Attendre chargement (fichier peut être lent)
   ```

2. **Récupération factures physiques**
   - Dans pile F&B triée (ÉTAPE 2):
     - Chercher enveloppe "Admin"
     - Chercher enveloppe "Hotel Promotion"
   - Compter nombre de factures: _______
   - Trier par date si désorganisées

3. **Filtrage colonne Date**
   ```
   Excel HP-ADMIN:

   1. Cliquer sur onglet: "Saisie"
   2. Cliquer sur en-tête colonne "Date"
   3. Cliquer sur icône filtre ▼
   4. Décocher "Sélectionner tout"
   5. Cocher SEULEMENT: "(Vides)"
   6. Cliquer OK

   RÉSULTAT: Affiche seulement les lignes vides (prêtes pour saisie)
   ```

4. **Saisie des factures**

   **POUR CHAQUE facture:**

   ```
   COLONNES À REMPLIR:

   A. Date
      - Format: JJ/MM/AAAA
      - Exemple: 20/12/2024
      - Date de la facture (pas date du jour)

   B. Area
      - Hotel Promotion
      OU
      - Administration

   C. Nourriture
      - Montant AVANT taxes
      - Exemple: 45.50

   D. Boisson
      - Montant AVANT taxes
      - Inclut: cocktails, spiritueux, liqueurs

   E. Bière
      - Montant AVANT taxes
      - Séparé de "Boisson"

   F. Vin
      - Montant AVANT taxes
      - Séparé de "Boisson"

   G. Minéraux
      - Eau, sodas, jus
      - Montant AVANT taxes

   H. Autre
      - Items non classifiables
      - Exemples: location salle, équipement

   I. Pourboire (TIP)
      - Montant du pourboire (si applicable)
      - Généralement 15-18%

   J. Paiement
      - TOUJOURS écrire:
        "Administration" (si facture Admin)
        OU
        "Promotion" (si facture Hotel Prom)

   K. Raison
      - Pourquoi cette dépense?
      - Exemples:
        • "Réunion managers"
        • "Formation employés"
        • "Événement client VIP"
        • "Repas employé malade"

   L. Autorisé par
      - Nom de la personne qui a approuvé
      - Vérifier signature sur facture
      - Si manquant: écrire "À confirmer" et noter sur feuille
   ```

   **Exemple de saisie:**
   ```
   Date: 19/12/2024
   Area: Administration
   Nourriture: 125.00
   Boisson: 0.00
   Bière: 35.00
   Vin: 0.00
   Minéraux: 12.50
   Autre: 0.00
   Pourboire: 25.88
   Paiement: Administration
   Raison: Lunch réunion département ventes
   Autorisé par: Marie Lavoie (GM)
   ```

5. **Vérification et total**
   - Après saisie de TOUTES les factures:
   - Vérifier nombre de lignes saisies = nombre de factures
   - Vérifier aucune cellule vide dans colonnes obligatoires
   - Compter total montant (Excel calcule automatiquement en bas)

6. **Onglet Journalier - Rafraîchir**
   ```
   1. Cliquer sur onglet: "Journalier"
   2. Cliquer sur: Données → Actualiser tout
      OU
      Clic droit dans tableau → Actualiser
   3. Attendre recalcul (5-10 secondes)
   ```

7. **Sélection date et impression**
   ```
   Onglet Journalier:

   1. Chercher filtre "Date" en haut du tableau
   2. Cliquer sur ▼
   3. Sélectionner: DATE DU JOUR (19/12/2024)
   4. Cliquer OK

   AFFICHAGE: Toutes les factures saisies aujourd'hui

   IMPRESSION:
   1. Fichier → Mise en page
   2. Orientation: Paysage (Landscape)
   3. Ajuster: Tenir sur 1 page de largeur
   4. Imprimer: 1 copie
   ```

8. **Impression vue "Date Vide" (si demandé)**
   - Retourner onglet "Saisie"
   - Filtre Date → (Vides)
   - Si lignes présentes (factures non datées):
     - Imprimer cette vue
     - Ajouter note: "Factures à dater"

9. **Sauvegarde**
   ```
   1. Ctrl+S (ou Fichier → Enregistrer)
   2. Confirmer écrasement du fichier
   3. Attendre confirmation
   ```

10. **Assemblage pack HP/Admin pour comptabilité**
    ```
    ORDRE (de haut en bas):

    1. Page Excel "Journalier" (imprimée)
    2. Page Excel "Date Vide" (si applicable)
    3. TOUTES les factures physiques dans l'ordre de saisie
    4. Agrafer ensemble (coin supérieur gauche)

    ANNOTER sur page Excel:
    "HP/ADMIN - [DATE] - [Nombre] factures - [Total $]"
    ```

**Vérification:**
- [ ] Toutes factures Admin/HP saisies
- [ ] Colonnes obligatoires remplies (Date, Area, Paiement, Raison, Autorisé par)
- [ ] Onglet Journalier rafraîchi
- [ ] Rapport journalier imprimé
- [ ] Factures physiques attachées
- [ ] Pack HP/Admin assemblé et agrafé
- [ ] Fichier sauvegardé

**Documents produits:**
- Rapport Journalier HP/Admin (1 page Excel)
- Rapport Date Vide (si applicable)
- Pack complet (Excel + factures physiques)

**Système utilisé:** Excel (HP-ADMIN.xlsx)

**Durée:** 20 minutes

**Erreurs courantes:**
- Oublier de filtrer "Date Vide" → saisie dans mauvaises lignes
- Confondre "Boisson" et "Bière/Vin" → fausse la comptabilité
- Ne pas vérifier signature "Autorisé par" → problème audit
- Oublier de rafraîchir onglet Journalier → rapport incomplet
- Montants AVEC taxes → erreur (toujours AVANT taxes)

---

### ÉTAPE 7: Sommaire Dépôts - SD (30 min)

**Objectif:** Compter les dépôts cash du coffre, comparer avec les montants POSitouch par employé, calculer variances, et obtenir signatures.

**Contexte:** Chaque employé F&B dépose son cash de la journée dans le coffre avec un bordereau. L'auditeur doit vérifier que le montant déclaré = montant compté = montant POSitouch.

**Actions:**

1. **Ouverture fichier SD**
   ```
   Localisation: Bureau → Sommaire journalier des dépôts.xls

   OU: Lecteur partagé → Comptabilité → SD.xls

   - Ouvrir le fichier
   - Enregistrer sous: SD-[DATE].xls
   - Exemple: SD-20-12-2024.xls
   ```

2. **Récupération dépôts du coffre**
   - Ouvrir le coffre (code: [CONFIDENTIEL])
   - Récupérer TOUS les dépôts cash de la journée
   - Chaque dépôt a:
     - Enveloppe
     - Bordereau (nom, montant, signature)
     - Cash/chèques
   - Compter nombre de dépôts: _______
   - Organiser par employé

3. **Structure du fichier SD**
   ```
   COLONNES:

   A. Nom Employé
      - Nom complet
      - Département (serveur, barman, etc.)

   B. Montant POSitouch
      - Depuis Daily Sales Report page 5
      - Section "Cash by Server"
      - AVANT tips

   C. Montant Déclaré (Bordereau)
      - Ce que l'employé a écrit sur bordereau
      - Vérifier signature employé

   D. Montant Compté
      - Ce que l'auditeur compte physiquement
      - Recompter 2× si ≠ déclaré

   E. Variance Comptage
      - = D - C
      - Montant compté - Montant déclaré
      - Positif = surplus
      - Négatif = manquant

   F. Variance POSitouch
      - = D - B
      - Montant compté - Montant POSitouch
      - Acceptable: ±5.00$ (tips, arrondissements)

   G. Status
      - OK (variance ≤ 5.00$)
      - À RÉVISER (variance > 5.00$)
      - CRITIQUE (variance > 20.00$)

   H. Notes
      - Explications variances
      - Actions prises

   I. Signature Auditeur
   J. Signature Superviseur
   ```

4. **Comptage des dépôts**

   **POUR CHAQUE employé:**

   ```
   PROCÉDURE DE COMPTAGE:

   1. Ouvrir enveloppe de l'employé
   2. Sortir bordereau → noter montant déclaré
   3. Sortir cash
   4. Trier par coupures:
      - 100$: _____ × 100 = _____
      - 50$:  _____ × 50  = _____
      - 20$:  _____ × 20  = _____
      - 10$:  _____ × 10  = _____
      - 5$:   _____ × 5   = _____
      - 2$:   _____ × 2   = _____
      - 1$:   _____ × 1   = _____
      - 0.25$: _____ × 0.25 = _____
      - Autres: _____
   5. Total compté: _________
   6. RECOMPTER si ≠ déclaré
   7. Remettre cash dans enveloppe
   8. Agrafer bordereau sur enveloppe
   ```

5. **Récupération montants POSitouch**
   - Aller chercher DSR (imprimé à ÉTAPE 5)
   - Page 5: "Cash by Server" OU "Server Sales Summary"
   - Pour chaque serveur, noter montant CASH (pas tips)

   **Exemple DSR page 5:**
   ```
   SERVER SALES SUMMARY

   Marie Tremblay
   - Food Sales: 1,250.00
   - Beverage: 450.00
   - Total Sales: 1,700.00
   - CASH: 350.00    ← PRENDRE CE MONTANT
   - Credit: 1,200.00
   - Tips: 150.00
   ```

6. **Saisie dans fichier SD**
   ```
   Exemple ligne:

   A. Marie Tremblay (Serveuse - Restaurant)
   B. 350.00         (POSitouch DSR page 5)
   C. 345.00         (Déclaré sur bordereau)
   D. 348.50         (Compté par auditeur)
   E. +3.50          (348.50 - 345.00 = +3.50 surplus)
   F. -1.50          (348.50 - 350.00 = -1.50 vs POSitouch)
   G. OK             (variance ≤ 5.00$)
   H. "Tips non déclarés estimés ~2$"
   I. [Signature auditeur]
   J. [Signature superviseur requis si variance]
   ```

7. **Gestion des variances**

   **Si variance ≤ 5.00$:**
   - Status: OK
   - Pas d'action requise
   - Tips expliquent généralement la différence

   **Si variance 5.01$ - 20.00$:**
   - Status: À RÉVISER
   - Actions:
     1. Recompter le cash (erreur de comptage?)
     2. Vérifier DSR (bon employé? bon montant?)
     3. Vérifier bordereau (bien rempli?)
     4. Appeler superviseur → signature requis
     5. Noter explication dans colonne "Notes"

   **Si variance > 20.00$:**
   - Status: CRITIQUE
   - Actions:
     1. ARRÊTER le traitement de ce dépôt
     2. Appeler superviseur IMMÉDIATEMENT
     3. Superviseur doit recompter avec auditeur
     4. Vérifier si tips non déclarés
     5. Vérifier si erreur système POSitouch
     6. Compléter rapport d'incident
     7. Superviseur doit signer + justifier
     8. Photocopier bordereau + rapport

8. **Totaux et réconciliation RECAP**
   - En bas du fichier SD:
   ```
   TOTAUX:
   - Total POSitouch:    _________
   - Total Déclaré:      _________
   - Total Compté:       _________
   - Variance Totale:    _________
   ```

   - Comparer avec RECAP (ÉTAPE 8):
   - Total Compté SD doit égaler ligne "CASH" du RECAP
   - Si ≠ → investiguer avant continuer

9. **Signatures**
   ```
   BAS DE PAGE SD:

   "Je certifie avoir compté les dépôts ci-dessus"
   Signature Auditeur: _______________  Date: _______

   "J'ai vérifié et approuvé les variances"
   Signature Superviseur: ____________  Date: _______
   ```

   - Auditeur signe TOUJOURS
   - Superviseur signe SI:
     - Variance totale > 10.00$
     OU
     - Variance individuelle > 5.00$
     OU
     - Situation inhabituelle

10. **Impression et dépôt**
    ```
    IMPRESSION:
    - Fichier → Imprimer
    - 2 copies:
      Copy 1: Enveloppe blanche (comptabilité)
      Copy 2: Garder avec caisses

    DÉPÔT PHYSIQUE DES CAISSES:
    - Remettre toutes les enveloppes dans le coffre
    - OU: Déposer sur bureau superviseur
    - OU: Dans sac de dépôt banque (selon procédure hôtel)

    ANNOTER SUR COPIE 1:
    "SD - [DATE] - [Nombre] dépôts - Total: [Montant]"
    ```

**Vérification:**
- [ ] Tous les dépôts du coffre comptés
- [ ] Montants POSitouch récupérés (DSR page 5)
- [ ] Fichier SD complété (toutes colonnes)
- [ ] Variances calculées et expliquées
- [ ] Variances > 5$ approuvées par superviseur
- [ ] Totaux concordent avec RECAP
- [ ] Signatures auditeur + superviseur
- [ ] 2 copies imprimées
- [ ] Cash remis en sécurité

**Documents produits:**
- Fichier Excel SD (2 copies imprimées)
- Rapport d'incident (si variance critique)

**Système utilisé:** Excel (SD), POSitouch (DSR)

**Durée:** 30 minutes

**Erreurs courantes:**
- Oublier de compter la monnaie (quarters, dimes) → variance
- Confondre CASH et TIPS sur DSR → mauvais montant
- Ne pas recompter quand variance détectée → erreur comptage
- Signer sans obtenir signature superviseur → audit non conforme
- Remettre cash sans enveloppe → perte/vol possible

**Note importante:** Ce fichier SD sera utilisé dans ÉTAPE 8 (RECAP) et ÉTAPE 9 (copie vers RJ).

---

## [SUITE À VENIR]

Les étapes 8-19 seront détaillées avec le même niveau d'exhaustivité dans les prochaines sections.

---

## 📊 Réconciliations critiques

### Balance #1: RECAP (Comptant)

**Formule:**
```
Daily Revenue (Cash) = POSitouch (Cash) + DueBack + Variances SD
```

**Documents requis:**
- Daily Revenue page 5-6
- POSitouch DSR page 5
- Onglet DueBack (RJ)
- Fichier SD
- Onglet RECAP (RJ)

**Tolérance:** 0.00$ (doit balancer parfaitement)

---

### Balance #2: TRANSELECT (Cartes de crédit)

**Formule:**
```
LightSpeed Payment Breakdown = POSitouch Établissement + Moneris Batchs + FreedomPay
```

**Documents requis:**
- Payment Breakdown (LightSpeed)
- POSitouch Établissement
- 4 rapports Moneris
- FreedomPay report
- Onglet TRANSELECT (RJ)

**Tolérance:** ±0.01$ par type de carte

---

### Balance #3: GEAC/UX (Réconciliation finale)

**Formule:**
```
Transelect Totals = GEAC Settlement + Adjustments
```

**Documents requis:**
- Onglet TRANSELECT complété
- Settlement Details
- Credit Card Not in BLT File
- Onglet GEAC/UX (RJ)

**Tolérance:** 0.00$

---

### Balance #4: QUASIMODO (Réconciliation globale)

**Formule:**
```
RJ Total Payments = Quasimodo Total (en négatif)
```

**Documents requis:**
- RJ onglet Jour (ligne totaux)
- Fichier Quasimodo complété
- Onglet TRANSELECT
- RECAP

**Tolérance:** ±0.01$ (ajuster AMEX si nécessaire)

---

## 🔍 Dépannage et erreurs courantes

### Problème: RECAP ne balance pas

**Symptômes:**
- Variance ≠ 0.00$ dans onglet RECAP
- Différence entre Daily Revenue et total cash

**Causes possibles:**
1. Erreur de comptage SD
2. DueBack mal calculé
3. Interac/chèques non extraits
4. Ajustements non inclus
5. Folio 40.52 ≠ 0

**Diagnostic:**
```
ÉTAPE 1: Vérifier SD
- Recompter les dépôts physiques
- Comparer total SD avec ligne RECAP
- Vérifier signatures superviseur

ÉTAPE 2: Vérifier DueBack
- Recalculer chaque ligne
- Vérifier Interac/chèques extraits
- Comparer total avec Daily Revenue

ÉTAPE 3: Vérifier Daily Revenue
- Page 5: total cash
- Page 6: breakdown par département
- Comparer avec POSitouch

ÉTAPE 4: Chercher ajustements
- LightSpeed: ajustements de la journée
- Corrections manuelles
- Voids/refunds
```

**Solution:**
- Identifier la source de variance
- Corriger le montant
- Documenter l'ajustement
- Obtenir signature superviseur
- Re-balancer

**Si variance persiste > 30 min:**
- Appeler superviseur
- Appeler contrôleur (si > 50$)
- Compléter rapport variance
- Documenter toutes tentatives

---

### Problème: Terminaux Moneris ne ferment pas

**Symptômes:**
- Erreur sur écran terminal
- "Batch already closed"
- "Communication error"

**Solutions:**

**Erreur: "Batch already closed"**
```
CAUSE: Batch déjà fermé plus tôt dans la journée
ACTION:
1. Ne rien faire (c'est normal)
2. Chercher rapport de fermeture (shift précédent)
3. Utiliser ce rapport pour Transelect
4. Noter heure de fermeture
```

**Erreur: "Communication error"**
```
CAUSE: Problème réseau/connexion
ACTION:
1. Vérifier câble réseau branché
2. Vérifier écran affiche "READY"
3. Attendre 30 secondes
4. Réessayer fermeture
5. Si échec: débrancher 30 sec, rebrancher
6. Si échec: appeler support 1-866-319-7450
```

**Erreur: "Declined"**
```
CAUSE: Transaction en attente
ACTION:
1. Terminer la transaction
2. Demander au shift précédent
3. Annuler transaction si nécessaire
4. Réessayer fermeture
```

---

### Problème: VNC ne se connecte pas à POSitouch

**Symptômes:**
- "Connection refused"
- "Authentication failed"
- Écran noir

**Solutions:**

**Vérifier connexion réseau:**
```
1. Ouvrir invite commande (cmd)
2. Taper: ping [IP POSitouch]
3. Si timeout → problème réseau
4. Appeler IT/support
```

**Vérifier mot de passe:**
```
1. Confirmer mot de passe avec superviseur
2. Réessayer (attention CAPS LOCK)
3. Si échec 3×: attendre 5 min (lockout)
```

**Serveur POSitouch arrêté:**
```
1. Aller physiquement au serveur
2. Vérifier écrans allumés
3. Vérifier lumières réseau
4. Si éteint: appeler IT IMMÉDIATEMENT
5. Ne PAS redémarrer sans autorisation
```

**Alternative temporaire:**
```
Si VNC inaccessible < 1h avant PART:
- Utiliser rapports imprimés shift précédent
- Noter "VNC indisponible" sur RJ
- Imprimer rapports POST-PART quand accessible
- Documenter incident
```

---

### Problème: Fichier Excel RJ corrompu

**Symptômes:**
- "File is corrupt"
- Formules brisées
- #REF! errors
- Onglets manquants

**Solution immédiate:**
```
1. NE PAS PANIQUER
2. NE PAS FERMER Excel
3. Fichier → Enregistrer sous → nouveau nom
4. Fermer Excel
5. Chercher backup: [Lecteur]\\Backup\\RJ\\
6. Ouvrir backup le plus récent
7. Comparer avec notes papier
8. Ressaisir données manquantes
```

**Prévention:**
```
TOUJOURS:
1. Enregistrer toutes les 15 minutes (Ctrl+S)
2. Garder notes papier parallèles
3. Ne jamais "Enregistrer" sur fichier original
4. Toujours "Enregistrer sous" nouveau nom
5. Vérifier backup quotidiens
```

**Si backup inexistant/corrompu:**
```
1. Appeler contrôleur IMMÉDIATEMENT
2. Reconstruire RJ depuis:
   - Daily Revenue (LightSpeed)
   - POSitouch reports
   - Moneris batchs
   - FreedomPay
   - Notes papier
3. Documenter: "RJ reconstruit - fichier corrompu"
4. Demander IT investigation
```

---

## 📖 Glossaire

### Termes hôteliers

**ADR (Average Daily Rate)**
- Tarif moyen par chambre
- Formule: Revenus chambres ÷ Nombre chambres occupées
- Indicateur performance clé

**CK/CN/CO/CP (Checked-in / Cancelled / Checked-out / Comp)**
- Statistiques mouvements chambres quotidiens
- Rapportées dans onglet Jour du RJ

**DueBack**
- Montant dû par un employé de réception
- Solde caisse à remettre/recevoir
- Négatif = employé doit de l'argent
- Positif = hôtel doit à l'employé

**Folio**
- Compte client dans LightSpeed
- Enregistre toutes les charges
- Imprimé lors check-out

**OOO (Out of Order)**
- Chambre hors service
- Raisons: rénovation, réparation, maintenance
- Comptée mais non vendable

**OTB (On The Books)**
- Réservations futures confirmées
- Revenus prévisionnels
- Utilisé pour DBRS et prévisions

**PART (Partition)**
- Opération LightSpeed à 03h00
- Sépare jour comptable précédent/actuel
- CRITIQUE: ne pas travailler pendant PART

**Stayover**
- Client qui reste plusieurs nuits
- Pas check-in ni check-out ce jour

### Termes F&B

**DSR (Daily Sales Report)**
- Rapport quotidien ventes POSitouch
- 9 pages, inclut toutes transactions F&B
- Source primaire réconciliation restaurants

**Server Cashout**
- Procédure fin de shift serveur
- Remettre cash, signer rapport
- Déclarer tips

**Void**
- Transaction annulée
- Doit être approuvée par superviseur
- Suivie dans rapports POSitouch

### Termes paiements

**Batch**
- Lot de transactions cartes de crédit
- Fermé quotidiennement (End of Day)
- Numéro séquentiel

**BLT (Billing Ledger Transaction)**
- Transaction enregistrée dans LightSpeed
- "Not in BLT File" = transaction CC non matchée

**Establishment / Établissement**
- Rapport POSitouch des paiements par type
- Utilisé pour Transelect

**FreedomPay**
- Processeur CC backend Marriott
- Payment Breakdown requis pour réconciliation

**Interac**
- Paiement débit direct
- Traité différemment des cartes de crédit

**Settlement**
- Règlement final transactions CC
- Montant net après frais

### Termes Excel

**RECAP**
- Réconciliation comptant (cash)
- Onglet critique du RJ
- Doit balancer à 0.00$

**TRANSELECT**
- Réconciliation cartes de crédit et Interac
- Onglet du RJ
- Compare LightSpeed, POSitouch, Moneris, FreedomPay

**GEAC/UX**
- Onglet réconciliation finale CC
- Vérification settlement details
- Doit balancer à 0.00$

**Quasimodo**
- Fichier réconciliation globale quotidienne
- Compare RJ total avec breakdown par mode
- Variance acceptable: ±0.01$

### Acronymes systèmes

**HP (Hotel Promotion)**
- Département interne
- Consommation F&B pour promotion hôtel
- Suivi dans Excel HP-ADMIN

**Admin (Administration)**
- Département interne
- Consommation F&B pour staff/réunions
- Suivi dans Excel HP-ADMIN

**PMS (Property Management System)**
- Système gestion hôtelière
- Sheraton utilise: LightSpeed Galaxy

**POS (Point of Sale)**
- Système caisses restaurants/bars
- Sheraton utilise: POSitouch

**DBRS (Daily Business Review Summary)**
- Rapport performance quotidien Marriott
- Requis chaque jour
- Inclut: rooms, revenue, ADR, OTB

**SD (Sommaire Dépôts)**
- Fichier Excel réconciliation cash employés
- Compare déclaré, compté, POSitouch
- Signé par auditeur et superviseur

**RJ (Revenue Journal)**
- Fichier Excel principal audit Back
- Consolide toutes réconciliations
- Source unique vérité financière journée

---

## 🔗 Notes d'intégration webapp

### Fonctionnalités requises

#### 1. Système de tâches (checklist)

**Structure tâches Back:**
```
CATÉGORIES:
1. Setup & Triage (étapes 1-2)
2. Caisses & Terminaux (étapes 3-4)
3. Rapports PRÉ-PART (étapes 5-8)
4. ⚠️ PART 03h00 (pause système)
5. Réconciliations POST-PART (étapes 9-14)
6. Finalisations (étapes 15-19)

POUR CHAQUE TÂCHE:
- Titre
- Description
- Durée estimée
- Système(s) utilisé(s)
- Documents requis (input)
- Documents produits (output)
- Check-list vérification
- Dépendances (tâche X doit être complétée avant)
- Instructions étape par étape
- Screenshots/vidéos
- Erreurs courantes
- Dépannage
```

#### 2. Formulaires de saisie

**Formulaires requis:**

```
HP/ADMIN:
- Date picker
- Radio: Hotel Promotion / Administration
- Champs monétaires: Nourriture, Boisson, Bière, Vin, Minéraux, Autre, Pourboire
- Text: Raison (suggestion: dropdown options communes)
- Text: Autorisé par (autocomplete noms approuvés)
- Bouton: Ajouter ligne
- Validation: tous champs obligatoires sauf "Autre"

SOMMAIRE DÉPÔTS:
- Pour chaque employé:
  - Nom (autocomplete depuis liste serveurs)
  - Montant POSitouch (auto-rempli depuis DSR uploadé)
  - Montant déclaré (input)
  - Montant compté (input)
  - Variance (auto-calculée)
  - Status (auto: OK / À réviser / Critique)
  - Notes (textarea)
- Alert si variance > 5$
- Signature électronique auditeur/superviseur

TRANSELECT:
- Section POSitouch:
  - Upload DSR → auto-extract montants
  - OU: saisie manuelle par type carte
- Section Moneris:
  - Par terminal (4): Visa, MC, Amex, Débit
  - Upload photo rapports OU saisie manuelle
- Section FreedomPay:
  - Upload CSV/Excel OU saisie manuelle
- Calcul variance automatique
- Highlight si variance > 0.01$

GEAC/UX:
- Auto-populate depuis Transelect
- Upload Settlement Details
- Calcul concordance
- Red/Green indicator balance

QUASIMODO:
- Auto-populate date
- Copier montants depuis:
  - Transelect (F&B, Réception, Tablettes)
  - RECAP (Cash CAD/USD)
- AMEX: calcul automatique ×0.9735
- Variance auto-calculée
- Warning si variance > 0.01$
- Bouton ajustement (si ≤0.01$)

ONGLET JOUR (RJ):
- Statistiques:
  - Départs (CK out)
  - Arrivées (CK in)
  - Stayovers
  - Rooms OOO
  - Comp rooms
- Revenus F&B: auto-populate depuis POSitouch
- Dépôts on hand: saisie
- Forfaits: auto-calculé
- Variance caisse: doit = 0
- Bouton "Transfert" (final action)
```

#### 3. Upload et parsing documents

**Documents à supporter:**

```
LIGHTSPEED (LightSpeed Galaxy):
- Cashier Details (PDF) → extract montants par dept
- Payment Breakdown (PDF/Excel) → extract CC par type
- Daily Revenue (PDF) → extract totaux pages 5-6
- Folio (PDF) → archive

POSITOUCH (via VNC):
- Daily Sales Report (PDF - 9 pages) → extract:
  - Page 1: totaux
  - Page 5: cash by server
  - Page 6: payment breakdown
- Paiement par Établissement (PDF) → extract par type CC
- Server Cashout Totals (PDF) → extract cash per server
- Memo Listings (PDF) → parse et categorize

MONERIS:
- Batch reports (photo/PDF) → OCR extract:
  - Batch #
  - Visa total
  - MC total
  - Amex total
  - Débit total

FREEDOMPAY:
- Payment Breakdown (CSV/Excel) → import direct
- Settlement (PDF) → extract net amounts

SONIFI:
- Email (EML/PDF) → extract revenue amount

EXCEL:
- Import RJ d'hier → template nouveau RJ
- Import SD template
- Import HP-ADMIN → filter date vide
```

#### 4. Validations et alertes

**Validations critiques:**

```
AVANT PART (03h00):
- [ ] TOUTES tâches PRÉ-PART complétées
- [ ] Terminaux Moneris fermés (4/4)
- [ ] Rapports POSitouch imprimés
- [ ] HP/Admin saisi
- [ ] SD complété et signé
- [ ] RECAP préliminaire balancé
→ Si non: ALERTE ROUGE bloquer PART

POST-PART:
- [ ] Transelect balancé (±0.01$ max)
- [ ] GEAC/UX balancé (0.00$)
- [ ] Quasimodo balancé (±0.01$ max)
- [ ] Onglet Jour variance caisse = 0
→ Si non: ALERTE ORANGE documenter variance

SOUMISSION FINALE:
- [ ] Enveloppe blanche check-list complète
- [ ] DBRS complété
- [ ] Courriels envoyés
- [ ] Signatures obtenues
→ Si non: ALERTE JAUNE manque documents
```

#### 5. Rapports et exports

**Exports requis:**

```
PDF ENVELOPPE BLANCHE:
- Génération automatique pack complet:
  - Index (table des matières)
  - Daily Sales Report (9p)
  - Paiement par Département
  - Cashier Details (tous)
  - POSitouch reports (tous)
  - Pile CC (assemblée)
  - RECAP + SD
  - RJ (onglets pertinents)
  - HP/Admin
  - DBRS
  - Quasimodo
- Bookmark par section
- Numérotation pages
- Watermark "COMPTABILITÉ - [DATE]"

EXCEL EXPORTS:
- RJ complet (tous onglets)
- SD (avec signatures)
- HP-ADMIN (journalier)
- DBRS (formule + master updated)
- Quasimodo

EMAIL AUTO:
- À: Contrôleur, GM, Superviseurs
- CC: Auditeur
- Objet: "Audit Back [DATE] - Complété"
- Corps:
  - Résumé balances
  - Variances notables
  - Actions requises
  - Pièces jointes (RJ, DBRS summary)
```

#### 6. Tableau de bord (Dashboard)

**Vue d'ensemble audit:**

```
INDICATEURS TEMPS RÉEL:
┌──────────────────────────────────────┐
│ Progression: 65% (étape 12/19)       │
│ Temps écoulé: 4h 23min               │
│ Temps estimé restant: 1h 45min       │
│ PART dans: 47 minutes                │
└──────────────────────────────────────┘

STATUTS BALANCES:
RECAP:         ✅ Balancé (0.00$)
TRANSELECT:    ⚠️ Variance -0.02$ (OK)
GEAC/UX:       ⏳ En cours
QUASIMODO:     ⏸️ Pas démarré
ONGLET JOUR:   ⏸️ Pas démarré

DOCUMENTS:
Imprimés:      18/32 (56%)
Uploadés:      12/15 (80%)
Signés:        3/5 (60%)

ALERTES:
🔴 URGENT: Terminal Bar Moneris non fermé
🟠 ATTENTION: Variance SD employé #3: +12.50$
🟡 INFO: Quasimodo pas démarré (normal, POST-PART)
```

#### 7. Aide contextuelle

**Pour chaque tâche:**

```
PANNEAU LATÉRAL:
├─ Instructions (étape par étape)
├─ Vidéo tutoriel (embedded)
├─ Screenshots (gallery)
├─ Vérifications (checklist interactive)
├─ Erreurs courantes (accordéon)
├─ Dépannage (decision tree)
└─ Contact urgence (si bloqué)

CHATBOT ASSISTANT:
- Questions fréquentes
- Recherche dans documentation
- Suggestions contextuelles
- Escalade vers superviseur si nécessaire
```

#### 8. Permissions et audit trail

**Rôles:**

```
AUDITEUR BACK:
- Accès lecture/écriture toutes tâches
- Upload documents
- Saisie données
- Signature électronique
- Export rapports

SUPERVISEUR:
- Accès lecture toutes tâches
- Approbation variances
- Signature électronique
- Override blocages
- Accès dashboard temps réel

CONTRÔLEUR:
- Accès lecture seule toutes tâches
- Export tous rapports
- Accès historique audits
- Analytics et tendances

GM (General Manager):
- Accès lecture dashboard
- Rapports sommaires
- Alertes critiques seulement

AUDIT TRAIL:
- Horodatage chaque action
- User qui a fait l'action
- Avant/après (pour modifications)
- IP address
- Export audit log
- Rétention: 7 ans
```

#### 9. Intégrations API

**APIs à développer/utiliser:**

```
LIGHTSPEED:
- GET /cashier-details/{dept}/{date}
- GET /payment-breakdown/{date}
- GET /daily-revenue/{date}
- GET /folio/{folio-number}
→ Return: JSON parsed data

POSITOUCH (VNC Automation):
- Script: connect VNC
- Script: navigate to reports
- Script: generate + download PDFs
- Parse PDFs → extract data
→ Return: JSON structured data

MONERIS (si API disponible):
- GET /batch-close/{terminal}/{date}
→ Return: JSON batch details

FREEDOMPAY:
- GET /payment-breakdown/{property}/{date}
→ Return: CSV/JSON

EMAIL (SONIFI):
- IMAP: connect to email
- Filter: from=sonifi, subject contains date
- Extract: attachment PDF
- Parse PDF → extract revenue
→ Return: JSON

EXCEL (Local):
- Read: RJ template
- Write: populate onglets
- Calculate: formulas
- Export: PDF/XLSX
→ Return: File paths
```

#### 10. Mobile responsive

**Considérations:**

```
DEVICES:
- Desktop: interface complète (priorité)
- Tablet: interface adaptée (consultation rapports)
- Mobile: vue sommaire + alertes (pas saisie)

OFFLINE MODE:
- Service worker: cache tâches + instructions
- IndexedDB: sauvegarde locale saisies
- Sync: quand connexion rétablie
- Alert: "Mode hors ligne - données non sauvegardées"

PRINT:
- CSS print: format optimisé impression
- Page breaks: entre sections logiques
- Headers/footers: date, page #, auditeur
- Landscape: tableaux larges
```

---

## 📅 Calendrier maintenance

### Quotidien
- [ ] Audit Back complet (6-7h)
- [ ] Sauvegarde RJ dans dossier quotidien
- [ ] Vérification backup automatiques

### Hebdomadaire
- [ ] Révision variances cumulées
- [ ] Mise à jour listes employés (SD)
- [ ] Vérification espace disque serveur

### Mensuel
- [ ] Archivage RJ mois précédent
- [ ] Révision procédures (changements?)
- [ ] Formation nouveaux auditeurs
- [ ] Mise à jour templates Excel

### Annuel
- [ ] Audit complet procédures
- [ ] Révision complète documentation
- [ ] Formation recyclage tous auditeurs
- [ ] Mise à jour DBRS formules (si changements Marriott)

---

## 📞 Contacts urgence

### Support technique

**LightSpeed Galaxy**
- Support: 1-800-xxx-xxxx
- Email: support@lightspeed.com
- Disponibilité: 24/7

**POSitouch**
- Support: 1-888-xxx-xxxx
- Email: support@positouch.com
- Disponibilité: 24/7

**Moneris**
- Support: 1-866-319-7450
- Email: support@moneris.com
- Disponibilité: 24/7

**FreedomPay / Marriott**
- Support: 1-800-xxx-xxxx (ligne Marriott)
- Disponibilité: 24/7

### Personnel hôtel

**Contrôleur**
- Nom: [À compléter]
- Cell: xxx-xxx-xxxx
- Email: controleur@sheratonlaval.com
- Appeler si: variance > 100$, système down, urgence financière

**General Manager**
- Nom: [À compléter]
- Cell: xxx-xxx-xxxx
- Email: gm@sheratonlaval.com
- Appeler si: incident majeur, urgence sécurité

**Superviseur de nuit**
- Cell: xxx-xxx-xxxx
- Appeler si: variance > 20$, approbations, questions opérationnelles

**IT / Support technique**
- Cell: xxx-xxx-xxxx (on-call)
- Email: it@sheratonlaval.com
- Appeler si: serveur down, réseau down, systèmes critiques

---

## 📄 Annexes

### Annexe A: Templates Excel

**Localisation:** `documentation/back/templates/`

- RJ_template.xls
- SD_template.xls
- HP-ADMIN_template.xlsx
- DBRS_formule_template.xlsm
- Quasimodo_template.xlsx

### Annexe B: Scripts et outils

**Localisation:** `documentation/back/scripts/`

- vnc_auto_connect.py (automatisation VNC)
- pdf_parser_cashier.py (parse Cashier Details)
- moneris_ocr.py (OCR rapports Moneris)
- email_sonifi_extract.py (extraction email Sonifi)

### Annexe C: Vidéos formation

**Localisation:** `documentation/back/videos/`

- 01_setup_poste.mp4
- 02_triage_papiers.mp4
- 03_caisses_dueback.mp4
- 04_moneris_fermeture.mp4
- 05_positouch_vnc.mp4
- [... 19 vidéos au total]

### Annexe D: Checklist imprimable

**Localisation:** `documentation/back/checklist_imprimable.pdf`

- Version 1 page pour référence rapide
- Cases à cocher
- Espaces pour notes
- Plastifier et utiliser marker effaçable

---

**Document créé:** 2024-12-20
**Dernière mise à jour:** 2024-12-20
**Version:** 2.0 (Exhaustive)
**Auteur:** Documentation Sheraton Laval
**Révisé par:** [À compléter]

---

*Ce document est la propriété du Sheraton Laval. Toute reproduction ou distribution sans autorisation est interdite. Pour questions ou corrections, contacter le département de comptabilité.*
