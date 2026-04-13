# SetD Sheet Documentation

**Sheet Name:** `SetD`
**Dimensions:** 44 rows x 158 columns
**Purpose:** Settlement/Deposit tracking by employee for direct billing and suspense

---

## Overview

The `SetD` sheet tracks:
- Daily settlements by employee (mostly banquet/sales staff)
- Direct billing suspense accounts
- GL account coding
- Monthly reconciliation of outstanding amounts

**"SetD"** = Settlement/Deposit tracking.

---

## Structure

### Header Section (Rows 1-4)

**Row 1: Date and Department Headers**
| Column | Content |
|--------|---------|
| A | Date (46014.00) |
| I | COMPTAB |
| J | COMPTAB. |
| K | BANQUET |
| AB | MD BANQUET |

**Row 2: Employee Last Names**
| Column | Employee |
|--------|----------|
| A | Jour |
| B | RJ |
| C | Martine |
| E | Petite |
| F | Conc. |
| G | Corr. |
| H | JEAN |
| I | Tristan |
| J | Mandy |
| K | Frederic |
| L | Florence |
| M | Marie |
| N | Patrick |
| O | KARL |
| P | Stéphane |
| Q | natalie |
| R | DAVID |
| S | YOUSSIF |
| T | MYRLENE |
| U | EMMANUELLE |
| V | DANIELLE |
| W | VALERIE |
| X | Youri |
| Y | Alexandre |
| Z | Julie |
| AA | PATRICK |
| AB | Nelson |
| AC | NAOMIE |
| AD | SOPHIE |

**Row 3: Employee First Names/Titles**
| Column | Name |
|--------|------|
| B | neg=débiteur |
| C | Breton |
| E | Caisse |
| F | Banc. |
| G | Mois suivant |
| H | PHILIPPE |
| I | Tremblay |
| J | Le |
| K | Dupont |
| ... | ... |

**Row 4: GL Account Codes**
| Column | Code |
|--------|------|
| C | 2-946000 |
| D | 2-101100 |
| E | 2-946000 |
| F | 2-101701 |
| G | 2-101704 |
| H | 2-101704 |
| I | 2-101704 |
| J | 2-101704 |
| K | 2-101701 |
| M | 2-101704 |
| N | 2-101704 |
| O | 2-101704 |
| P | 2-101704 |
| Q | 2-101704 |
| R | 2-101704 |
| S | 2-101704 |
| Y | 2-101704 |
| Z | 2-101704 |
| AA | 2-101704 |
| AB | 2-101704 |

---

## Daily Data (Rows 5-35)

| Row | Day | RJ (B) | Sample Employee Values |
|-----|-----|--------|------------------------|
| 5 | 1.00 | 32.40 | AD:-24.00 |
| 6 | 2.00 | -33.91 | |
| 7 | 3.00 | 141.41 | |
| 8 | 4.00 | 1,735.79 | O:161.26, U:4.35, AD:13.50 |
| 9 | 5.00 | 6,170.84 | |
| 10 | 6.00 | 6,819.07 | K:6.22, O:977.74, R:452.55 |
| 11 | 7.00 | 1,842.32 | |
| 12 | 8.00 | 640.01 | |
| 13 | 9.00 | 403.21 | AD:-100.83 |
| 14 | 10.00 | 373.26 | |
| 15 | 11.00 | 1,880.18 | U:123.65, AD:-57.90 |
| 16 | 12.00 | 4,755.25 | O:80.61, U:2,242.26, Y:20.95, Z:34.15 |
| 17 | 13.00 | 3,157.89 | K:-860.38, O:-96.53, P:300.08, U:372.17, Y:861.00, Z:108.06 |
| 18 | 14.00 | 1,076.71 | |
| 19 | 15.00 | 1,683.30 | I:2,135.00 |
| 20 | 16.00 | 1,223.57 | AD:-62.96 |
| 21 | 17.00 | 685.70 | |
| 22 | 18.00 | 536.46 | |
| 23 | 19.00 | 1,175.60 | O:80.71, P:85.50, U:26.86, Z:53.86 |
| 27 | 23.00 | | O:-329.68 |

---

## Summary Section (Rows 36-44)

| Row | Label | RJ (B) | Employee Totals |
|-----|-------|--------|-----------------|
| 36 | total | 34,299.06 | I:2,135.00, K:-854.16, O:874.11, P:385.58, R:452.55, U:2,769.29, Y:881.95, Z:196.07, AD:-232.19 |
| 37 | Reel | 0.15 | |
| 38 | 2-946000 | | |
| 39 | Petite caisse | | |
| 40 | 2-101704 | | |
| 41 | Suspend | 28,830.75 | |
| 43 | | 1,534.01 | |
| 44 | | -27,296.74 | |

---

## Day 23 Analysis

| Column | Employee | Amount |
|--------|----------|--------|
| O | KARL LECLERC | -329.68 |

**Note:** Day 23 shows negative value for KARL (-329.68), indicating a credit or adjustment.

---

## GL Account Codes

| Code | Description |
|------|-------------|
| 2-946000 | Petite caisse (Petty cash) |
| 2-101100 | Main operating account |
| 2-101701 | Suspense account type 1 |
| 2-101704 | Suspense account type 4 |

---

## Key Calculations

### Total RJ Column (B)
```
Sum of days 1-31 = 34,299.06
```

### Suspense Reconciliation (Row 41)
```
Suspend: 28,830.75
Additional: 1,534.01
Net: -27,296.74
```

### Employee Monthly Totals
| Employee | Total |
|----------|-------|
| I (Tristan) | 2,135.00 |
| K (Frederic) | -854.16 |
| O (KARL) | 874.11 |
| P (Stéphane) | 385.58 |
| R (DAVID) | 452.55 |
| U (EMMANUELLE) | 2,769.29 |
| Y (Alexandre) | 881.95 |
| Z (Julie) | 196.07 |
| AD (SOPHIE) | -232.19 |

---

## Connections

### To jour Sheet

| SetD | jour | Description |
|------|------|-------------|
| Column B total | Balance calculations | Settlement totals |

### To rj Sheet

| SetD | rj Row | Description |
|------|--------|-------------|
| Settlement totals | Various credits | Direct billing |

### To Accounting

| SetD | Destination | Description |
|------|-------------|-------------|
| GL code distribution | Journal entries | Account distribution |
| Suspense totals | Reconciliation | Outstanding items |

---

## Implementation Notes

### For WebApp:

1. **Input Fields:**
   - Daily amounts by employee
   - Settlement adjustments
   - Credit/debit entries

2. **Auto-Calculated:**
   - Daily totals
   - Employee monthly totals
   - GL code subtotals

3. **Features:**
   - Filter by employee
   - Filter by GL code
   - Suspense account tracking

### Suspense Account Management:
- Track outstanding direct billing
- Monitor employee settlements
- Reconcile at month-end

### Sign Convention:
- **Positive**: Amount owed TO the hotel
- **Negative**: Amount owed BY the hotel (credit)

### Employee Tracking:
- Mostly banquet sales staff
- Track deposits received
- Monitor outstanding balances
