# Nettoyeur Sheet Documentation

**Sheet Name:** `Nettoyeur`
**Dimensions:** 343 rows x 36 columns
**Purpose:** Track staff gratuities (pourboires) by employee and department

---

## Overview

The `Nettoyeur` sheet tracks:
- Daily gratuities/tips for each employee
- Organized by department (Reception, Restaurant, Banquet, etc.)
- Daily columns (1-31) for each day of the month
- Employee names in rows

**"Nettoyeur"** = Staff gratuity/tip tracking (literally "cleaner" but used for tip distribution).

---

## Structure

### Header Row (Row 2)

| Column | Content |
|--------|---------|
| A | Employee name |
| B-AF | Days 1-31 |

```
A:ome | B:1.00 | C:2.00 | D:3.00 | E:4.00 | ... | X:23.00 | Y:24.00 | ...
```

### Department Sections

The sheet is organized by department:

| Rows | Department |
|------|------------|
| 3-49 | RECEPTION / CHAMBRE |
| 50+ | RESTAURANT PIAZZA |
| ... | BANQUET |
| ... | BAR |
| ... | SERVICE AUX CHAMBRES |
| 330+ | Summaries |

### Employee Data (Sample from RECEPTION)

| Row | Employee Name | Sample Day Values |
|-----|---------------|-------------------|
| 4 | ARAUJO DEBBY | J:11.10 |
| 5 | CARON, ISABELLE | C:11.10, E:3.70, J:12.10, L:3.70, Q:11.10, S:3.70 |
| 17 | SILVERIO-PEREIRA, MÉLANIE | L:22.20 |
| 18 | VARTEJ RALUCA | R:14.80, W:7.40 |
| 28 | SHERATON (RECEPTION) | T:7.40, X:18.50 |
| 30 | SHERATON (BANQUET) | C:11.10, E:3.70, I:14.80, J:48.10, L:7.40, P:3.70, W:11.10 |
| 31 | SHERATON | D:40.70, J:11.10, M:3.70, P:14.80, R:33.30, W:18.50 |
| 42 | LY GUILLAUME | F:11.10, P:11.10, W:11.10 |
| 45 | CABRERA MANOLO | B:25.90, I:14.80, M:18.50 |
| 46 | MOUATARIF KHALIL | W:40.70 |

### Summary Rows (330-343)

| Row | Category | Sample Values |
|-----|----------|---------------|
| 333 | Chambre | B:25.90, C:22.20, D:40.70, E:7.40... |
| 334 | Nourriture | B:359.75, C:54.05, D:74.80... |
| 336 | Administration | B:153.75, D:62.90, F:28.25... |
| 337 | VALET À PAYER | B:85.55, J:7.80, L:51.00... |
| 340 | **TOTAL À PAYER** | B:624.95, C:76.25, D:178.40... |

---

## Day 23 Example (Column X)

| Employee/Category | Amount |
|-------------------|--------|
| SHERATON (RECEPTION) | 18.50 |
| Chambre total | 15.55 |
| **TOTAL À PAYER** | **34.05** |

---

## Summary Categories (Rows 333-340)

| Row | Category | Description |
|-----|----------|-------------|
| 333 | Chambre | Room service tips |
| 334 | Nourriture | Food service tips |
| 335 | Spesa | SPESA department tips |
| 336 | Administration | Admin allocations |
| 337 | VALET À PAYER | Valet tips to pay |
| 338 | GRATUITÉ | Gratuities given |
| 339 | LITERIE CHAMBRE | Room linen tips |
| 340 | **TOTAL À PAYER** | **Total tips to pay** |

---

## Monthly Totals

From Row 340 (TOTAL À PAYER):

| Day | Amount |
|-----|--------|
| 1 | 624.95 |
| 2 | 76.25 |
| 3 | 178.40 |
| 4 | 59.20 |
| 5 | 135.35 |
| ... | ... |
| 22 | 544.45 |
| 23 | 34.05 |

---

## Connections

### To somm_nettoyeur Sheet

| Nettoyeur | somm_nettoyeur | Description |
|-----------|----------------|-------------|
| Row 340 daily totals | Summary | Daily totals summarized |
| Employee totals | Payment records | For payroll |

### To rj Sheet

| Nettoyeur | rj Row | Description |
|-----------|--------|-------------|
| Monthly total | 36 | Pourboires |

---

## VBA Macros

No specific macros identified for Nettoyeur sheet.

The sheet is primarily for data entry and tracking.

---

## Implementation Notes

### For WebApp:

1. **Input Fields:**
   - Individual employee tip amounts
   - Day selection (column)
   - Department filter

2. **Auto-Calculated:**
   - Daily totals by category (Rows 333-340)
   - Monthly totals per employee
   - Department subtotals

3. **Features:**
   - Search by employee name
   - Filter by department
   - Daily summary view

4. **Validation:**
   - Row 340 totals should balance with tip receipts
   - Monthly total should match rj Row 36

### Data Entry Pattern:
- Select day column
- Enter tip amount for each employee who received tips
- Totals auto-calculate in summary rows

### Employee Categories:
- Individual names (actual employees)
- "SHERATON (RECEPTION)" - General reception pool
- "SHERATON (BANQUET)" - General banquet pool
- "SHERATON" - General hotel pool
