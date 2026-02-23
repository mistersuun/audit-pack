# Procédure Complète Back - Analyse Détaillée

**Source:** `2025-02 - Procédure Complete Back (Audition).docx`
**Dernière mise à jour:** 19 décembre 2024
**Analysé le:** 2026-01-18

---

## Vue d'Ensemble du Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUX DE TRAVAIL AUDITION BACK                        │
└─────────────────────────────────────────────────────────────────────────────┘

AVANT MINUIT (Part 1)
═════════════════════
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   Triage    │ ──► │   DueBack   │ ──► │     SD      │
    │  Papiers    │     │  (Tab RJ)   │     │   (Excel)   │
    └─────────────┘     └─────────────┘     └─────────────┘
           │                   │                   │
           ▼                   ▼                   ▼
    Séparer F&B /       Previous (-)         Montant Positouch
    Réception           Current (+)          Montant Vérifié
                                             Variance

APRÈS MINUIT (Part 2)
═════════════════════
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   RECAP     │ ◄── │     SD      │ ──► │   DEPOT     │
    │  (Tab RJ)   │     │  Variance   │     │  (Tab RJ)   │
    └─────────────┘     └─────────────┘     └─────────────┘
           │                                       ▲
           │         COPIE MANUELLE               │
           │         "Montant Vérifié"            │
           └───────────────────────────────────────┘

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ TRANSELECT  │ ──► │   GEAC/UX   │ ──► │    JOUR     │
    │  (Tab RJ)   │     │  (Tab RJ)   │     │  (Tab RJ)   │
    └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Phase 1: Mise en Place (Lignes 15-23)

### Actions Initiales
1. **Échange d'information** avec le superviseur
2. **Vérification des courriels**
3. **Vérification du panneau d'incendie**
4. **Nettoyer le bureau** et organiser l'espace de travail

### Préparation du Fichier RJ
```
1. Ouvrir le fichier RJ de HIER
2. Faire "Enregistrer sous" avec la date d'AUJOURD'HUI
3. Onglet "Contrôle": mettre à jour date + nom auditeur
4. EFFACER les onglets: RECAP, TRANSELECT, GEAC/UX
```

> **Important:** Le RJ est copié d'hier, pas créé de zéro!

---

## Phase 2: Triage des Papiers (Lignes 24-47)

### Séparation des Documents

```
PANIER DES CAISSES
        │
        ├──► Enveloppe GRISE/BRUNE ──► Réception
        │
        └──► Enveloppe BLEUE ──► F&B
                    │
                    ├── Débit
                    ├── Visa
                    ├── MasterCard
                    ├── AmericanExpress
                    ├── Forfait
                    ├── Admin & Hotel Prom
                    ├── Rapport journalier serveurs
                    └── Bordereaux de dépôt
```

### Documents à Imprimer
- **Details Tickets** (1-99 et all Sub departments)
- **Cashier detail** de chaque département avec code réceptionniste
- **Settlements**: paiements interacs (98-13) et chèques (98-14) séparément

---

## Phase 3: DueBack - CRITIQUE (Lignes 49-54)

### Concept du DueBack

Le DueBack représente l'argent que chaque réceptionniste doit ou a en trop.

```
┌─────────────────────────────────────────────────────────────┐
│                    ONGLET DUEBACK DU RJ                     │
├─────────────────────────────────────────────────────────────┤
│  Jour │ Col B  │ Araujo │ Latulippe │ Caron │ ... │ Col Z  │
│       │ (R/J)  │   C    │     D     │   E   │     │ TOTAL  │
├───────┼────────┼────────┼───────────┼───────┼─────┼────────┤
│ Ligne │Previous│ -50.00 │   -25.00  │ -10.00│     │        │
│   1   │(négatif)                                           │
├───────┼────────┼────────┼───────────┼───────┼─────┼────────┤
│ Ligne │Current │ +75.00 │   +30.00  │ +15.00│     │        │
│   2   │(positif)                                           │
└───────┴────────┴────────┴───────────┴───────┴─────┴────────┘
```

### Règles d'Entrée
| Ligne | Valeur | Source |
|-------|--------|--------|
| **Ligne 1** | DueBack PRÉCÉDENT | Rapport caisse réceptionniste (EN NÉGATIF) |
| **Ligne 2** | DueBack AUJOURD'HUI | Total de chaque employé (EN POSITIF) |

### Formule Colonne Z
```
Colonne Z = SUM(C[ligne1]:Y[ligne2]) + B[ligne1]
         = Total tous réceptionnistes + Référence R/J
```

---

## Phase 4: SD - Sommaire Journalier (Lignes 137-151)

### Localisation
```
Bureau → Dossier "SD" → Fichier du mois → Onglet de la date
```

### Structure du SD

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     SOMMAIRE JOURNALIER DES DÉPÔTS                         │
├──────────┬─────────────┬─────────────────┬─────────────────┬───────────────┤
│ Employé  │ Département │ Montant         │ Montant         │ Variance      │
│          │             │ (Positouch)     │ VÉRIFIÉ         │               │
├──────────┼─────────────┼─────────────────┼─────────────────┼───────────────┤
│ Serveur1 │ Restaurant  │ 150.00          │ 150.00          │ 0.00          │
│ Serveur2 │ Bar         │ 200.00          │ 195.00          │ -5.00         │
│ Serveur3 │ Banquet     │ 300.00          │ 300.00          │ 0.00          │
├──────────┴─────────────┼─────────────────┼─────────────────┼───────────────┤
│ TOTAL                  │ 650.00          │ 645.00          │ -5.00         │
└────────────────────────┴─────────────────┴─────────────────┴───────────────┘
```

### Colonnes Importantes

| Colonne | Description | Source |
|---------|-------------|--------|
| **Montant (Positouch)** | Montant que l'employé DEVRAIT avoir déposé | Système Positouch |
| **Montant VÉRIFIÉ** | Montant RÉELLEMENT déposé dans le coffre | Feuille de dépôt physique |
| **Variance** | Différence = Montant - Vérifié | Calcul automatique |

> **ATTENTION:** Ne pas imprimer le SD avant d'avoir balancé le RECAP!
> Le SD peut être modifié pour balancer.

---

## Phase 5: RECAP - Balance Comptant (Lignes 172-199)

### Documents Nécessaires
- Pages 5 et 6 du **Daily Revenue** (LightSpeed)
- Total **Variance du SD**
- Total **DueBack**

### Flux de Données vers RECAP

```
                    ┌─────────────────┐
                    │     RECAP       │
                    │   (Onglet RJ)   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Daily Revenue │ │   SD Variance   │ │    DueBack      │
│   (LightSpeed)  │ │    (Total)      │ │   (Total Z)     │
│   Pages 5-6     │ │                 │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Objectif
Le RECAP doit **balancer à $0.00**

---

## Phase 6: DEPOT - La Connexion Clé (Lignes 201-211)

### Instruction Exacte de la Procédure

> **Ligne 208:** "Copier les montants de la colonne « Montant Vérifié » du SD dans l'onglet « Dépôt » du RJ"

### Workflow Actuel (MANUEL)

```
┌─────────────────┐                    ┌─────────────────┐
│       SD        │                    │     DEPOT       │
│    (Excel)      │                    │   (Onglet RJ)   │
├─────────────────┤     COPIE          ├─────────────────┤
│ Montant Vérifié │ ═══MANUELLE═══►    │ Client 6        │
│    645.00       │                    │ Client 8        │
│                 │                    │ Total: 645.00   │
└─────────────────┘                    └─────────────────┘
```

### Structure du Depot

```
┌─────────────────────────────────────────────────────────────┐
│                    ONGLET DEPOT (RJ)                        │
├─────────────────────────────────────────────────────────────┤
│ CLIENT 6 (Compte #1844-22)                                  │
│   Date: ____________    Montant: ____________               │
│   Date: ____________    Montant: ____________               │
│                         Sous-total: ____________            │
├─────────────────────────────────────────────────────────────┤
│ CLIENT 8 (Compte #4743-66)                                  │
│   Date: ____________    Montant: ____________               │
│   Date: ____________    Montant: ____________               │
│                         Sous-total: ____________            │
├─────────────────────────────────────────────────────────────┤
│ TOTAL GÉNÉRAL: ____________                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 7: SetD - Variances (Lignes 210-211)

### Instruction
> "Transcrire les informations au sujet des variances (et des remboursements s'il y en a) dans l'onglet SetD du RJ"

### Contenu SetD
- Variances par employé
- Remboursements
- Suivi des montants en suspens

---

## Phase 8: TRANSELECT - Cartes de Crédit (Lignes 214-226)

### Sources de Données

| Section | Source | Données |
|---------|--------|---------|
| **Section 1: Restaurant** | Terminaux Moneris + Batch Positouch | Montants par terminal |
| **Colonne POSITOUCH** | Rapport "Établissement" | Interac + Panne Interac |
| **Section 2: Réception** | FreedomPay / FuseBox | Montants par type carte |

### Objectif
- Variance doit être **$0.00** (vert)
- Si variance: vérifier saisie des données

---

## Phase 9: GEAC/UX - Balance Finale CC (Lignes 473-514)

### Sources de Données

| Section | Source |
|---------|--------|
| **Daily Cash Out** | Rapport "Daily Cash Out" |
| **Daily Revenue** | Page 6 du Daily Revenue |

### Validation
```
Daily Cash Out = Daily Revenue
        ↓
  Variance = 0
```

> **Si variance persistante:** Envoyer courriel à Roula et Mandy.
> Aucune correction possible par l'auditeur.

---

## Phase 10: JOUR - Consolidation Finale (Lignes 523-560)

### Colonnes à Compléter

| Source | Colonnes RJ |
|--------|-------------|
| Departures/Arrivals/Stayovers | CO (clients), CP (hors service) |
| Complimentary Rooms Report | CK (occupées), CN (complémentaires) |
| A/R Summary Report | CF (Transfer to A/R) |
| Advance Deposit Balance | D (Deposit on Hand - négatif) |
| Sales Journal for Entire House | E à AJ, AU, AX, AY, BF, BQ, BR |
| Daily Revenue | AK-AL-AM-AN-AO-AS-AT-AU-AV-AW-AX-AY-AZ-BA-BB-BC-BD-BF-CB-CC |

### Validation Finale
```
Colonne C (Diff. Caisse) = $0.00
```

Si pas à zéro: variance dans GEAC/UX ou différence cartes de crédit.

---

## Résumé: Relations Entre Onglets

### Flux de Données Complet

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        FLUX COMPLET DES DONNÉES                          │
└──────────────────────────────────────────────────────────────────────────┘

ENTRÉE MANUELLE           CALCULS                    SORTIE FINALE
═══════════════           ═══════                    ═════════════

┌─────────────┐
│  Rapports   │
│  Caisse     │
│Réceptionnist│──────┐
└─────────────┘      │
                     ▼
              ┌─────────────┐
              │   DUEBACK   │──────────────────────┐
              │ Previous(-) │                      │
              │ Current(+)  │                      │
              └─────────────┘                      │
                                                   │
┌─────────────┐                                    │
│  Feuilles   │                                    │
│   Dépôt     │──────┐                             │
│  (Coffre)   │      │                             │
└─────────────┘      │                             │
                     ▼                             ▼
              ┌─────────────┐              ┌─────────────┐
              │     SD      │              │    RECAP    │
              │ Positouch   │──Variance───►│             │
              │ Vérifié     │              │  Balance=0  │
              └──────┬──────┘              └─────────────┘
                     │                             │
                     │ COPIE MANUELLE              │
                     ▼                             │
              ┌─────────────┐                      │
              │   DEPOT     │                      │
              │ Client 6    │                      │
              │ Client 8    │──────────────────────┘
              └─────────────┘

              ┌─────────────┐              ┌─────────────┐
              │ TRANSELECT  │──────────────│    JOUR     │
              │ Moneris     │              │             │
              │ FreedomPay  │              │  Diff=0     │
              └─────────────┘              └─────────────┘
                     │
                     ▼
              ┌─────────────┐
              │   GEAC/UX   │
              │ Cash Out    │
              │ Revenue     │
              └─────────────┘
```

---

## Points Clés pour l'Application Web

### 1. Workflow SD → Depot (PRIORITÉ HAUTE)

**Problème actuel:**
- Copie MANUELLE des "Montant Vérifié" du SD vers Depot
- Source d'erreurs et de duplication

**Solution proposée:**
- Bouton "Auto-remplir depuis SD" dans l'onglet Depot
- Ou fusion des deux onglets

### 2. DueBack → Recap

**Flux actuel:**
- DueBack Total Z → Recap "Due Back Réception"
- Fonctionne via API `/api/rj/dueback/column-b`

### 3. Validations Automatiques

| Onglet | Validation |
|--------|------------|
| SD | Variance = Montant - Vérifié |
| RECAP | Balance = $0.00 |
| TRANSELECT | Variance = $0.00 |
| GEAC/UX | Cash Out = Revenue |
| JOUR | Diff. Caisse = $0.00 |

### 4. Ordre des Opérations

```
1. DueBack (avant SD)
2. SD (avant RECAP)
3. RECAP (doit balancer avant imprimer SD)
4. DEPOT (après RECAP, copie depuis SD)
5. SetD (après RECAP)
6. TRANSELECT
7. GEAC/UX
8. JOUR (dernier)
```

---

## Annexe: Documents Finaux

### Enveloppe Blanche (Comptabilité)
- Voir lignes 601-640 pour liste complète

### Dossier Bleu Daté
- Contient tous les rapports de la journée
- Ordre spécifique de classement

### DBRS (Daily Business Review Summary)
- Fichier séparé pour statistiques hôtelières
- Complété en dernier

---

## Références

| Document | Localisation |
|----------|--------------|
| Procédure originale | `documentation/back/2025-02 - Procédure Complete Back (Audition).docx` |
| Texte extrait | `documentation/back/procedure_extracted.txt` |
| Documentation DueBack | `documentation/RJ/05_DUEBACK.md` |
| Documentation Depot | `documentation/RJ/07_depot.md` |
| Documentation Recap | `documentation/RJ/04_RECAP.md` |
