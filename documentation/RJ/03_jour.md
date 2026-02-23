# jour Sheet Documentation

**Sheet Name:** `jour`
**Dimensions:** 233 rows x 117 columns
**Purpose:** Master daily data journal - stores all transaction data by day

---

## Overview

The `jour` sheet is the **MASTER DATA SOURCE** for the entire RJ workbook. It contains:
- Daily balances and transactions for each day of the month (columns)
- Revenue by department and category (rows)
- Monthly totals and summaries
- Source data for DUEBACK#, Recap, rj, and other sheets

---

## Structure

### Column Layout

| Columns | Purpose |
|---------|---------|
| A | Day number (1-31) |
| B | Balance d'ouverture (Opening balance) |
| C | Diff.Caisse (Cash difference) |
| D | (calculated) |
| E-I | PAUSE SPESA (Nou, Boi, Bie, Min, Vin) |
| J-N | PIAZZA/CUPOLA (Nou, Boi, Bie, Min, Vin) |
| O-S | MARCHÉ LA SPESA (Nou, Boi, Bie, Min, Vin) |
| T-X | SERVICE AUX CHAMBRES (Nou, Boi, Bie, Min, Vin) |
| Y-AC | BANQUET (Nou, Boi, Biere, Min, Vin) |
| AD | Pourboires |
| ... | (continues with more categories) |
| BU (72) | Argent recu (Cash received) |
| BV (73) | Remb. Serverveurs (Server refunds) |
| BW (74) | Remb. Gratuite (Gratuity refunds) |
| BY (76) | Due back reception |
| CA (78) | Surplus/Def |

### Row Layout

| Rows | Content |
|------|---------|
| 1 | Department headers |
| 2 | Column sub-headers |
| 3-33 | Daily data (Days 1-31) |
| 34 | Monthly totals |
| 35+ | Additional calculations |

---

## Key Columns (Important for Connections)

### Column B - Balance d'ouverture
- Opening balance for each day
- Day 1 starts with previous month's closing
- Each subsequent day = previous day's closing

### Column C - Diff.Caisse
- Cash register difference
- Values can be positive or negative
- Flows to Diff.Caisse# sheet

### Department Revenue Columns

| Department | Columns | Sub-categories |
|------------|---------|----------------|
| PAUSE SPESA | E-I | Nou, Boi, Bie, Min, Vin |
| PIAZZA/CUPOLA | J-N | Nou, Boi, Bie, Min, Vin |
| MARCHÉ LA SPESA | O-S | Nou, Boi, Bie, Min, Vin |
| SERVICE AUX CHAMBRES | T-X | Nou, Boi, Bie, Min, Vin |
| BANQUET | Y-AC | Nou, Boi, Biere, Min, Vin |

### Financial Summary Columns (70-80)

| Column | Index | Header | Day 23 Value | Purpose |
|--------|-------|--------|--------------|---------|
| BU | 72 | Argent recu | 4,070.43 | Cash received |
| BV | 73 | Remb. Serverveurs | -1,067.61 | Server refunds |
| BW | 74 | Remb. Gratuite | -2,543.42 | Gratuity refunds |
| BY | 76 | Due back reception | **-653.10** | DueBack (to DUEBACK#) |
| CA | 78 | Surplus/Def | -1,532.47 | Surplus/Deficit |

---

## Data for Day 23 (Row 25)

| Column | Value | Description |
|--------|-------|-------------|
| A | 23 | Day number |
| B | -3,554,670.64 | Opening balance |
| C | -9,609.77 | Cash difference |
| J | 8,999.76 | Piazza food |
| K | 2,194.75 | Piazza beverage |
| O | 348.87 | Marché food |
| T | 217.00 | Room service food |
| BU | 4,070.43 | Cash received |
| BV | -1,067.61 | Server refunds |
| BW | -2,543.42 | Gratuity refunds |
| BY | -653.10 | Due back reception |
| CA | -1,532.47 | Surplus/Deficit |

---

## Monthly Totals (Row 34)

| Column | Total | Description |
|--------|-------|-------------|
| C | -6,875.45 | Total cash differences |
| E | 11,134.00 | Total SPESA food |
| J | 356,956.88 | Total Piazza food |
| K | 74,109.81 | Total Piazza beverage |
| Y | 652,245.74 | Total Banquet food |
| AD | 186,842.82 | Total tips |

---

## Named Ranges in jour Sheet

| Named Range | Pattern | Purpose |
|-------------|---------|---------|
| `ar_[day]` | ar_1, ar_2, ... ar_31 | Argent Recu for each day |
| `CC_[day]` | CC_1, CC_2, ... CC_31 | Credit Card totals for each day |
| `j_[day]` | j_1, j_2, ... j_31 | Navigation to day column |

---

## Connections FROM jour Sheet

### To DUEBACK# Sheet
```
DUEBACK#!B[row] = jour!BY[day+2]
```
- Column B in DUEBACK# references jour!BY for the corresponding day
- Day offset: jour row = day + 2 (headers take rows 1-2)

### To Recap Sheet
| jour Column | Recap Row | Recap Field |
|-------------|-----------|-------------|
| BU (Argent recu) | 24 | Argent Reçu |
| BV (Remb. Serverveurs) | 12 | Moins Remb. Client |
| BW (Remb. Gratuite) | 11 | Moins Remb. Gratuité |
| BY (Due back reception) | 16 | Due Back Réception (ABS) |
| CA (Surplus/Def) | 19 | Surplus/déficit |

### To rj Sheet
| jour Column | rj Row | rj Field |
|-------------|--------|----------|
| BU | 51 | Argent recu |
| BV | 52 | Remboursement Client |
| BW | 53 | Remboursement Gratuité |
| BY | 55 | Depot Du reception |
| CA | 54 | S & D de caisse |

---

## VBA Macros Related to jour

### `aller_jour()` - Module4
```vba
Sub aller_jour()
    ' Navigate to jour sheet at current day column
    Application.Goto Reference:=Range("j_" & Range("vjour").Value)
End Sub
```

### `calcul_carte()` - Module4
```vba
Sub calcul_carte()
    ' Copy credit card totals to jour sheet at CC_[day]
    vjour = Range("vjour").Value
    ' Copies transelect totals to jour!CC_[day]
End Sub
```

### `envoie_dans_jour()` - Module15
```vba
Sub envoie_dans_jour()
    ' Copy Recap H19:N19 to jour at ar_[day]
    vjour = Range("vjour").Value
    Sheets("Recap").Range("H19:N19").Copy
    Sheets("jour").Range("ar_" & vjour).PasteSpecial xlPasteValues
End Sub
```

---

## Formula Patterns

### Balance Calculation
```excel
B[day+1] = Previous day's closing balance
C[day] = Cash register difference (from POS systems)
```

### Monthly Total (Row 34)
```excel
=SUM([column]3:[column]33)
```

---

## Implementation Notes

### For WebApp:

1. **Read Source** - jour is the primary data source
2. **Day Selection** - Use `vjour` from controle to determine current day
3. **Column BY** - Key for DueBack values, flows to DUEBACK# and Recap
4. **Auto-Population** - Many Recap values come directly from jour

### Important Columns for DueBack:
- **BY (76)**: "Due back reception" - Source for DUEBACK# Column B
- This value is negative in jour (e.g., -653.10)
- Displayed as positive in Recap (653.10)

### Data Entry Points:
- Most data comes from POS systems (Lightspeed, GEAC)
- Some manual adjustments in columns C (Diff.Caisse)
- DueBack values may be calculated or entered

### Row Offset:
- Day 1 = Row 3
- Day 23 = Row 25
- Formula: `Row = Day + 2`
