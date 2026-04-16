# Management Report Sheets

## Overview

Six sheets compose the management reporting layer of the RJ workbook. Three pages form the daily Director Report (`Rapp_p1` through `Rapp_p3`), comparing actual performance against budget. The `Etat rev` sheet provides a formal revenue statement, while two `Ristourne` sheets track corporate rebates and discounts.

These sheets are output-oriented: they consume data from the daily audit sheets and present it in a format suitable for hotel management review.

---

## 1. Rapp_p1 -- Director Report Page 1: Revenue Summary

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Rapp_p1`                                      |
| Dimensions  | 53 rows x 9 cols                               |
| Purpose     | Daily vs MTD vs budget revenue comparison       |

### Column Reference

| Col | Header           | Description                     |
|-----|------------------|---------------------------------|
| 0   | (row labels)     | Revenue category names          |
| 1   | CE JOUR          | Today's actual value            |
| 2   | CE MOIS          | Month-to-date actual            |
| 3   | BUDGET CE JOUR   | Today's budgeted value          |
| 4   | BUDGET CE MOIS   | Month-to-date budget            |
| 5-8 | (variance cols)  | Variance and percentage columns |

### Key Rows

| Row Label            | CE JOUR     | CE MOIS       | BUDGET CE MOIS |
|----------------------|-------------|---------------|----------------|
| Chambres Louees      | 74          | 4,314         | --             |
| Taux Moyen (ADR)     | 191.82      | --            | --             |
| Total Chambres       | 14,194.83   | 901,999.87    | 825,332        |
| Location de salle    | --          | --            | --             |
| Giotto               | --          | --            | --             |
| Piazza               | 12,940.00   | --            | --             |
| Cupola               | --          | --            | --             |
| Banquets Hotel       | --          | --            | --             |
| Banquets II          | --          | --            | --             |
| Total Restauration   | 13,288.88   | --            | --             |

### Data Flow & Integration

```
jour sheet ──────────> Rapp_p1 (CE JOUR columns)
Monthly accumulators ─> Rapp_p1 (CE MOIS columns)
Budget workbook ──────> Rapp_p1 (BUDGET columns)
```

### Analytics Potential

- Daily revenue vs budget variance tracking.
- MTD pace analysis (on track vs behind budget).
- Revenue mix breakdown (rooms vs F&B vs ancillary).

---

## 2. Rapp_p2 -- Director Report Page 2: Hours & Employees

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Rapp_p2`                                      |
| Dimensions  | 33 rows x 8 cols                               |
| Purpose     | Labor hours and employee count summary          |
| Header      | SOMMAIRE HEURES & EMPLOYES                     |

### Column Reference

| Col | Header           | Description                     |
|-----|------------------|---------------------------------|
| 0   | (row labels)     | Department / metric names       |
| 1   | CE JOUR          | Today's actual                  |
| 2   | CE MOIS          | Month-to-date actual            |
| 3   | BUDGET CE JOUR   | Today's budgeted value          |
| 4   | BUDGET CE MOIS   | Month-to-date budget            |
| 5-7 | (variance cols)  | Variance and percentage columns |

### Data Flow & Integration

```
salaires sheet ──> Rapp_p2 (labor hours by department)
Feuil1 sheet ────> Rapp_p2 (granular role-level hours)
Budget workbook ─> Rapp_p2 (budgeted hours/headcount)
```

### Analytics Potential

- Labor efficiency by department (hours per room sold, hours per cover).
- Headcount vs budget compliance.
- Overtime detection via daily hour spikes.

---

## 3. Rapp_p3 -- Director Report Page 3: Revenue vs Labor

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Rapp_p3`                                      |
| Dimensions  | 57 rows x 25 cols                              |
| Purpose     | Revenue vs labor cost by department             |

### Column Reference

The 25 columns are grouped in repeating blocks:

| Block             | Columns                                       |
|-------------------|-----------------------------------------------|
| JOURNALIER        | Revenus, Hres Travaillees, Nbr Employes, Salaires, % |
| MENSUEL A CE JOUR | Revenus, Hres Travaillees, Nbr Employes, Salaires, % |
| BUDGET A CE JOUR  | Revenus, Hres Travaillees, Nbr Employes, Salaires, % |

### Sample Data

| Department | Daily Rev    | MTD Rev       | Budget MTD Rev |
|------------|-------------|---------------|----------------|
| CHAMBRES   | 14,194.83   | 901,999.87    | 825,332        |

Each department row includes: revenue, hours worked, employee count, total wages, and labor cost as a percentage of revenue.

### Data Flow & Integration

```
Rapp_p1 (revenue) ──┐
Rapp_p2 (labor)   ──┼──> Rapp_p3 (combined revenue vs labor analysis)
salaires sheet ──────┘
```

### Analytics Potential

- Labor cost percentage by department (key hotel KPI).
- Departmental profitability ranking.
- Budget adherence for both revenue and labor simultaneously.

---

## 4. Etat rev -- Revenue Statement

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Etat rev`                                     |
| Dimensions  | 53 rows x 8 cols                               |
| Purpose     | Formal revenue statement with statistics        |
| Header      | ETAT DES REVENUS ET STATISTIQUES               |

### Column Reference

| Col | Header           | Description                     |
|-----|------------------|---------------------------------|
| 0   | (row labels)     | Revenue line items              |
| 1   | CE JOUR          | Today's actual                  |
| 2   | (day number)     | Current day of month (e.g., 22) |
| 3   | CE MOIS          | Month-to-date actual            |
| 4   | BUDGET CE JOUR   | Today's budgeted value          |
| 5   | BUDGET CE MOIS   | Month-to-date budget            |
| 6-7 | (variance cols)  | Variance calculations           |

### Data Flow & Integration

```
jour sheet ──> Etat rev (mirrors Rapp_p1 in formal statement format)
```

Similar to Rapp_p1 but formatted as an official revenue and statistics statement rather than a management dashboard page.

### Analytics Potential

- Formal monthly revenue reporting.
- Statistical summaries (occupancy %, ADR, RevPAR).

---

## 5. 201802 Ristourne -- Rebate/Discount Analysis (Daily)

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `201802 Ristourne`                             |
| Dimensions  | 36 rows x 41 cols                              |
| Purpose     | Daily rebate tracking by corporate account      |
| Period      | Monthly (named by YYYYMM)                      |

### Column Reference

| Col   | Header          | Description                       |
|-------|-----------------|-----------------------------------|
| 0     | JOUR            | Day number (1-31)                 |
| 1-40  | Corporate accts | One column per corporate account  |

### Known Corporate Accounts

CN8026-CNAM, Club de Hockey (2 accounts), Cumberland, FCSSQ, Ice Breakers, JHD, Kaldec, Les Spartans, Maple Soft (2 accounts), Max Puissance, Maxi Power, NB Elite, and others.

### Sample Data

Each cell contains room nights or rebate dollar amounts for a given corporate account on a given day.

### Data Flow & Integration

```
PMS corporate rate data ──> 201802 Ristourne (daily by account)
                                 │
                                 └──> Ristourne Analyse (monthly summary)
```

### Analytics Potential

- Corporate account utilization patterns (which days, which accounts).
- Rebate cost analysis by account.
- Identification of high-volume corporate clients.

---

## 6. Ristourne Analyse -- Rebate Summary

### Sheet Details

| Property    | Value                                          |
|-------------|------------------------------------------------|
| Excel Sheet | `Ristourne Analyse`                            |
| Dimensions  | 34 rows x 7 cols                               |
| Purpose     | Monthly rebate/discount summary                 |
| Header      | 201802 RISTOURNE                               |

### Column Reference

Summarizes total rebates and discounts given during the month, aggregated from the daily `201802 Ristourne` sheet.

### Data Flow & Integration

```
201802 Ristourne (daily detail) ──> Ristourne Analyse (monthly totals)
```

### Analytics Potential

- Total monthly rebate exposure.
- Rebate trends month-over-month (when combined across periods).
- Top corporate accounts by discount volume.
