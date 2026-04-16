# DUEBACK# (DUBACK#) Sheet Documentation

**Sheet Name:** `DUBACK#`
**Dimensions:** 67 rows x 26 columns (A-Z)
**Purpose:** Track DueBack (money owed) between receptionists and night journal

---

## Overview

The `DUBACK#` sheet tracks:
- Daily DueBack amounts from the R/J (jour sheet)
- Individual receptionist DueBack balances
- Two rows per day (previous balance + current adjustment)
- Monthly totals for validation

**"DueBack"** = Money that receptionists owe back or are owed from previous shifts.

---

## Structure

### Header Section (Rows 2-3)

**Row 2: Column Headers**
| Column | Header | Description |
|--------|--------|-------------|
| A | DATE | Day number |
| B | R/J | Reference from jour sheet |
| C | Araujo | Receptionist name |
| D | Latulippe | Receptionist name |
| E | Caron | Receptionist name |
| ... | ... | ... |
| Z | Total | Sum of all columns |

**Row 3: Receptionist First Names**
| Column | Name |
|--------|------|
| B | (date) 46014.00 |
| C | Debby |
| D | Josée |
| E | Isabelle |
| ... | ... |

### Data Rows (Rows 5-66)

Each **day uses TWO rows**:
- **Odd row** (first): Previous balance (typically negative)
- **Even row** (second): Current day adjustment (typically positive)

**Pattern:**
| Row | Day | Column A | Column B | Column C-Y | Column Z |
|-----|-----|----------|----------|------------|----------|
| 5 | 1 | 1.00 | -675.18 | (previous) | |
| 6 | 1 | 1.00 | | (current) | (total) |
| 7 | 2 | 2.00 | -1227.76 | (previous) | |
| 8 | 2 | 2.00 | | (current) | (total) |
| ... | ... | ... | ... | ... | ... |

### Monthly Total (Row 67)

| Column | Value | Description |
|--------|-------|-------------|
| B | -22,745.81 | Monthly R/J total |
| C | 348.35 | Receptionist total |
| E | 3,954.10 | Receptionist total |
| M | 2,217.02 | Receptionist total |
| N | 2,517.94 | Receptionist total |
| O | 1,902.94 | Receptionist total |
| P | 1,353.20 | Receptionist total |
| Q | 3,390.49 | Receptionist total |
| V | 3,871.92 | Receptionist total |
| W | 2,607.97 | Receptionist total |
| **Z** | **22,163.93** | **Monthly Column Z total** |

---

## Day 23 Example (Rows 49-50)

| Row | Column A | Column B | Column M | Column W | Column Z |
|-----|----------|----------|----------|----------|----------|
| 49 | 23.00 | **-653.10** | | | |
| 50 | 23.00 | | 323.42 | 329.68 | (calculated) |

**Day 23 Analysis:**
- Column B (R/J): -653.10 (from jour!BY25)
- Receptionist M: 323.42
- Receptionist W: 329.68
- Column Z: Sum of both rows + Column B

---

## Key Columns

### Column A - Day Number
- Repeated twice per day (for previous/current rows)
- Values 1.00 through 31.00

### Column B - R/J Reference
- **Formula:** `=+jour!BY[row]`
- Contains the DueBack value from the jour sheet
- Only populated in the **first row** of each day (previous balance)
- Always **negative** (money owed back)

### Columns C-Y - Receptionists
- Individual receptionist DueBack amounts
- **First row** (odd): Previous balance they're returning (negative)
- **Second row** (even): New amount they're taking (positive)

### Column Z - Total
- **Formula:** `=SUM(C[row]:Y[row+1])+B[row]`
- Correct formula: `=SUM(C45:Y46)+B45` (for day example)
- Sums BOTH rows (previous + current) plus Column B

---

## Column Z Formula (CRITICAL)

The Column Z formula is:
```excel
=SUM(C[first_row]:Y[second_row])+B[first_row]
```

**Example for Day 23 (Rows 49-50):**
```excel
=SUM(C49:Y50)+B49
```

**Breakdown:**
- `SUM(C49:Y50)` = Sum of all receptionists for both rows
- `B49` = -653.10 (R/J value from jour sheet)
- Result = Net DueBack for the day

---

## Connections

### From jour Sheet

| DUEBACK# Cell | jour Cell | Description |
|---------------|-----------|-------------|
| B5 (Day 1) | BY3 | Day 1 DueBack |
| B7 (Day 2) | BY4 | Day 2 DueBack |
| B49 (Day 23) | BY25 | Day 23 DueBack |
| ... | ... | ... |

**Formula Pattern:**
```excel
DUEBACK#!B[row] = jour!BY[day+2]
```
Where: `row = (day * 2) + 3` for first row of each day

### To Recap Sheet

| DUEBACK# | Recap | Description |
|----------|-------|-------------|
| B[day_row] | Row 16 | Due Back Réception (ABS value) |

**Note:** Recap shows the **absolute value** (positive) of Column B.

### To controle Sheet

| DUEBACK# | controle | Description |
|----------|----------|-------------|
| B67 | Row 22, Col H | Due Back mois a date |
| Z67 | Row 26, Col H | Due back du jour devrait être |

---

## Monthly Totals Validation

| Sheet | Location | Value | Should Match |
|-------|----------|-------|--------------|
| DUEBACK# | B67 | -22,745.81 | controle H22 |
| DUEBACK# | Z67 | 22,163.93 | controle H26 |

---

## Receptionist Columns (C-Y)

| Column | Header Row 2 | Header Row 3 | GL Code |
|--------|--------------|--------------|---------|
| C | Araujo | Debby | |
| D | Latulippe | Josée | |
| E | Caron | Isabelle | |
| F | Nader | Laeticia | |
| G | Mompremier | Rose-Delande | |
| H | oppong | zaneta | |
| I | SEDDIK | ZAYEN | |
| J | Kimberly | Tavarez | |
| K | AYA | BACHIRI | |
| L | Leo | Scarpa | |
| M | THANKARAJAH | THANEEKAN | |
| N | CINDY | PIERRE | |
| O | Manolo | Cabrera | |
| P | MOUATARIF | KHALIL | |
| Q | KRAY | VALERIE | |
| R | NITHYA | SAY | |
| S | DAMAL | Kelly | |
| T | MAUDE | LEVESQUE | |
| U | OLGA | ARHANTOU | |
| V | Sylvie | Pierre | |
| W | Emery | Uwimana | |
| X | Ben mansour | Ramzi | |
| Y | ANNIE-LIS | KASPERIAN | |

---

## VBA Macros

No specific macros identified for DUEBACK# sheet in the VBA modules.

The sheet is primarily data entry and calculation based.

---

## Implementation Notes

### For WebApp:

1. **Column B (R/J):**
   - **Read-only** - Auto-populated from jour!BY
   - Display as reference value
   - Always negative

2. **Columns C-Y (Receptionists):**
   - **Editable** - Night auditor enters values
   - Two rows per day (previous/current)
   - Can be positive or negative

3. **Column Z (Total):**
   - **Auto-calculated** - Formula: `=SUM(C:Y for both rows)+B`
   - Display the net result
   - Used for validation

4. **Day Selection:**
   - Use `vjour` from controle to determine current day
   - Highlight the two rows for current day

5. **Validation:**
   - B67 should match controle H22
   - Z67 should match controle H26

### Two-Row Pattern:
```
Day N Row 1 (Previous): Column B has R/J value, C-Y have negative (returning)
Day N Row 2 (Current):  Column B empty, C-Y have positive (taking)
Column Z: Sum of both rows + B
```

### Row Calculation:
```python
# For day N:
first_row = (N * 2) + 3  # Previous balance row
second_row = first_row + 1  # Current day row
```
