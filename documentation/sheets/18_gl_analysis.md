# GL Analysis & Utility Sheets

## Overview

Six sheets handle general ledger analysis, auditor management, and detailed labor tracking. Three GL-focused sheets (`Analyse 101100 autre`, `Analyse 100401`, `autre GL`) provide transaction-level detail for clearing accounts, bank transfers, and non-standard GL postings. The `Auditeur` sheet is a simple reference list used by session management. Two working sheets (`Feuil1`, `Feuil7`) provide granular labor data and scratch space.

---

## 1. Analyse 101100 autre -- GL Account 101100 (Clearing Account)

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Analyse 101100 autre`                         |
| Dimensions  | 60 rows x 92 cols                              |
| GL Account  | 101100 COMPTE TRANSITOIRE                      |
| Purpose     | Clearing/transitory account transaction analysis|

### Column Reference

| Col   | Header      | Description                              |
|-------|-------------|------------------------------------------|
| 0     | DESCRIPTION | Transaction description                  |
| 1     | N           | Negatif / Debit amount                   |
| 2     | P           | Positif / Credit amount                  |
| 3     | SOLDE       | Running balance                          |
| 4     | CORRECTION  | Correction flag or amount                |
| 5-91  | (daily)     | Daily detail columns across the month    |

### Sample Data

Clearing account entries with debit/credit pairs. The 92 columns provide daily granularity, allowing auditors to trace when specific transactions hit the transitory account and when they were cleared.

### Data Flow & Integration

```
PMS daily postings ──> Analyse 101100 autre (debit/credit detail)
                            │
                            ├── SOLDE tracks outstanding balance
                            └── CORRECTION flags items needing adjustment
```

### Analytics Potential

- Aging analysis of clearing account items.
- Identification of stale/uncleared transactions.
- Daily clearing activity volume.

---

## 2. Analyse 100401 -- GL Account 100401 (Bank Transfers)

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Analyse 100401`                               |
| Dimensions  | 81 rows x 8 cols                               |
| GL Account  | 100401 Transfer Bancaire                       |
| Purpose     | Bank transfer reconciliation                    |

### Column Reference

| Col | Header      | Description                              |
|-----|-------------|------------------------------------------|
| 0   | DESCRIPTION | Transfer description                     |
| 1   | N           | Negatif / Debit amount                   |
| 2   | P           | Positif / Credit amount                  |
| 3   | SOLDE       | Running balance                          |
| 4   | CORRECTION  | Correction flag or amount                |
| 5-7 | (detail)   | Additional detail columns                |

### Data Flow & Integration

```
Bank statements ──> Analyse 100401 ──> Reconciliation vs PMS records
```

### Analytics Potential

- Bank transfer reconciliation and exception flagging.
- Cash flow tracking through transfer timing analysis.

---

## 3. autre GL -- Other GL Accounts Detail

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `autre GL`                                     |
| Dimensions  | 180 rows x 61 cols                             |
| Purpose     | Comprehensive non-standard GL transaction log   |
| Header      | Hotel Sheraton Laval - Autres Grand Livre       |

### Column Reference

Row 3 contains category headers, row 4 contains GL codes:

| Col Block | Header            | GL Code | Description                    |
|-----------|-------------------|---------|--------------------------------|
| --        | Abonnement        | 935052  | Subscriptions                  |
| --        | Transf Bank SCOTIA| 100401  | Scotia bank transfers          |
| --        | CHQ NSF           | 101600  | NSF cheques                    |
| --        | Transf Bank BNC   | 101100  | BNC bank transfers             |
| --        | Transfert Autre   | 442751  | Other transfers (2 columns)    |
| --        | Transf Bank       | 101655  | General bank transfers         |
| --        | A-V               | 101703  | Accounts various               |
| --        | lib syndicat      | 101990  | Union dues                     |
| --        | Due Back          | 946000  | Due backs                      |
| --        | Mauvaises Creances| 424100  | Bad debts                      |
| --        | diff paiement     | --      | Payment differences            |
| --        | Uniformes         | --      | Uniform charges                |

The 61 columns cover many GL account categories, with daily transaction entries in the rows below.

### Data Flow & Integration

```
Daily audit entries ──> autre GL (categorized by GL code)
                             │
                             ├── Feeds GL account analyses (101100, 100401)
                             └── Supports month-end closing adjustments
```

### Analytics Potential

- Full non-standard transaction visibility across all GL accounts.
- NSF cheque tracking and bad debt monitoring.
- Union dues and subscription cost tracking.
- Due back reconciliation.

---

## 4. Auditeur -- Auditor List

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Auditeur`                                     |
| Dimensions  | 5 rows x 2 cols                                |
| Purpose     | Auditor name reference list                     |

### Column Reference

| Col | Content                |
|-----|------------------------|
| 0   | Auditor name           |
| 1   | (empty or metadata)    |

### Current Auditors

1. Khalil Mouatarif
2. Taha Abdelmoumen
3. Souleymane Camara
4. Dann-Sherley Derisca

### Data Flow & Integration

```
Auditeur sheet ──> controle sheet (prepare_par dropdown)
                ──> Session management (user identification)
```

This list populates the "Prepare par" field on the controle sheet and is used by the web application for session/user management.

### Analytics Potential

- Limited. Reference data only.
- Could be extended to track auditor workload distribution.

---

## 5. Feuil1 -- Working Sheet (Labor Hours Detail)

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Feuil1`                                       |
| Dimensions  | 40 rows x 98 cols                              |
| Purpose     | Granular daily labor hours by role              |

### Column Reference

| Col | Header       | Description                          |
|-----|-------------|--------------------------------------|
| 0   | HEURES      | Row label (JOUR in data rows)        |
| 1   | REC_ADM     | Reception -- Administration          |
| 2   | REC_PROM    | Reception -- Promotion               |
| 3   | REC_AUDIT   | Reception -- Audit                   |
| 4   | REC_SERV    | Reception -- Service                 |
| 5   | REC_PORTIER | Reception -- Doorman                 |
| 6   | REC_CLUB    | Reception -- Club                    |
| 7   | GOUVERNANTE | Housekeeping supervisor              |
| 8   | FDC         | Front desk clerk                     |
| 9   | equipiere   | Team member                          |
| 10  | PIAZZA_ADM  | Piazza -- Administration             |
| 11  | PIAZZA SERV | Piazza -- Service                    |
| 12  | PIAZZA_CD   | Piazza -- Chef de cuisine            |
| 13  | GIOTTO_ADM  | Giotto -- Administration             |
| 14  | GIOTTO Serv | Giotto -- Service                    |
| ... | ...         | Continues for 98 total columns       |

### Sample Data (Row 1)

| REC_ADM | REC_PROM | REC_AUDIT | REC_SERV | REC_PORTIER | REC_CLUB | GOUVERNANTE | FDC | equipiere | PIAZZA_ADM | PIAZZA SERV | PIAZZA_CD |
|---------|----------|-----------|----------|-------------|----------|-------------|-----|-----------|------------|-------------|-----------|
| 32      | 0        | 25        | 32.25    | 0           | 0        | 32          | 76  | 32        | 0          | 33.19       | 16.50     |

### Data Flow & Integration

```
Timekeeping system ──> Feuil1 (98 role-level columns)
                            │
                            ├──> salaires sheet (aggregated by department)
                            └──> Rapp_p2 / Rapp_p3 (management reports)
```

This sheet provides more granular labor tracking than the `salaires` sheet, breaking hours down to individual role level rather than department level.

### Analytics Potential

- Role-level staffing analysis.
- Identification of understaffed or overstaffed positions.
- Labor distribution across front-of-house vs back-of-house.
- Correlation of specific role hours with revenue performance.

---

## 6. Feuil7 -- Scratch/Working Data

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Feuil7`                                       |
| Dimensions  | 28 rows x 20 cols                              |
| Purpose     | Temporary calculation area                      |

### Column Reference

Sparse data with occasional monetary values (e.g., 397.50, 320). No consistent column structure.

### Data Flow & Integration

Standalone working sheet. Used for ad-hoc calculations during the audit process. No formal upstream or downstream dependencies.

### Analytics Potential

- None. Temporary workspace only.
