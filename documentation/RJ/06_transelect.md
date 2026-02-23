# transelect Sheet Documentation

**Sheet Name:** `transelect`
**Dimensions:** 40 rows x 32 columns
**Purpose:** Credit card transaction reconciliation between POS systems and GEAC

---

## Overview

The `transelect` sheet reconciles:
- Credit card transactions from restaurant/bar POS (Positouch)
- Credit card transactions from room charges (FreedomPay/GEAC)
- Calculates variances between systems
- Applies discount rates for each card type
- Determines net amounts after fees

---

## Structure

### Header Section (Rows 1-8)

| Row | Content |
|-----|---------|
| 4 | HÔTEL SHERATON LAVAL |
| 5 | DATE: 46014.00 |
| 6 | Préparé par: Khalil Mouatarif | Restaurant/Banquet/S headers |
| 7 | TYPE | BAR A | BAR B | BAR C | SPESA D | ROOM E | EXTRA codes... | TOTAL 1 | TOTAL 2 | POSITOUCH | VARIANCE |
| 8 | | A | B | C | D | E | (batch codes) | | | | | ESCOMPTE | $ | NET |

### Restaurant/Bar Section (Rows 9-14)

**POS Transactions by Card Type:**

| Row | Type | BAR A | BAR B | BAR C | Banquet... | TOTAL 1 | TOTAL 2 | POSITOUCH | VARIANCE | NET |
|-----|------|-------|-------|-------|------------|---------|---------|-----------|----------|-----|
| 9 | DÉBIT | 381.10 | 590.86 | 75.39 | 420.25... | 1,047.35 | 660.10 | 895.63 | 811.82 | 1,707.45 |
| 10 | VISA | 673.64 | 882.71 | 198.07 | 222.26... | 1,754.42 | 699.72 | 13,228.69 | -10,774.55 | 2,411.19 |
| 11 | MASTER | 220.12 | 915.16 | | 242.62... | 1,135.28 | 390.23 | 1,290.43 | 235.08 | 1,504.15 |
| 12 | DISCOVER | | | | | | | | | |
| 13 | AMEX | 71.49 | | 102.54 | 46.39... | 174.03 | 46.39 | 102.54 | 117.88 | 214.58 |
| 14 | **TOTAL** | 1,346.35 | 2,388.73 | 376.00 | 931.52... | **4,111.08** | **1,796.44** | **15,517.29** | **-9,609.77** | **5,837.37** |

### GEAC/Room Section (Rows 18-25)

**Room Charges via FreedomPay/GEAC:**

| Row | Type | Bank Report | Réception | TOTAL | Daily Revenue | ESCOMPTE | $ | NET |
|-----|------|-------------|-----------|-------|---------------|----------|---|-----|
| 20 | DÉBIT | | | | | | | |
| 21 | VISA | 7,625.85 | | 7,625.85 | 7,625.85 | 0.02 | 133.45 | 7,492.40 |
| 22 | MASTER | 10,595.05 | | 10,595.05 | 10,595.05 | 0.01 | 148.33 | 10,446.72 |
| 23 | DISCOVER | | | | | 0.03 | | |
| 24 | AMEX | 5,714.14 | | 5,714.14 | 5,714.14 | 0.03 | 151.42 | 5,562.72 |
| 25 | **TOTAL** | **23,935.04** | | **23,935.04** | **23,935.04** | | **433.21** | **23,501.83** |

### Summary Section (Rows 27-40)

**Grand Totals by Card Type:**

| Row | Section | AMEX | DISCOVER | MASTER | VISA | DEBIT | AMEX GLOBAL |
|-----|---------|------|----------|--------|------|-------|-------------|
| 28-29 | TOTAUX | 5,714.14 | | 12,120.56 | 10,079.99 | 1,707.45 | 220.42 |
| 30-32 | TOTAUX TRANSELECT | | | 1,525.51 | 2,454.14 | 1,707.45 | 220.42 |
| 33-35 | TOTAUX GEAC | 5,562.72 | | 10,595.05 | 7,625.85 | | |

---

## Key Calculations

### Discount Rates (ESCOMPTE)

| Card Type | Rate | Applied To |
|-----------|------|------------|
| VISA | 0.02 (2%) | Both sections |
| MASTER | 0.01 (1%) | Both sections |
| AMEX | 0.03 (3%) | Both sections |
| DISCOVER | 0.03 (3%) | Both sections |
| DÉBIT | 0.00 | No fee |

### Net Calculation
```
NET = Gross Amount - (Gross Amount × Discount Rate)
```

### Variance Calculation
```
VARIANCE = TOTAL 1 + TOTAL 2 - POSITOUCH
```

---

## Column Definitions

### Restaurant/Bar Columns (B-U)

| Column | Code | Description |
|--------|------|-------------|
| B | A | BAR terminal A |
| C | B | BAR terminal B |
| D | C | BAR terminal C |
| E | D | SPESA terminal |
| F | E | ROOM charges |
| G-U | Batch codes | Banquet batch transactions |

### Summary Columns (V-AB)

| Column | Header | Description |
|--------|--------|-------------|
| V | TOTAL 1 | Sum of bar terminals |
| W | TOTAL 2 | Sum of banquet batches |
| X | POSITOUCH | POS system total |
| Y | VARIANCE | Difference (should be ~0) |
| Z | ESCOMPTE | Discount rate |
| AA | $ | Discount amount |
| AB | NET | Net after fees |

---

## Connections

### To jour Sheet
Via `calcul_carte()` macro:
```vba
' Copies credit card totals to jour!CC_[day]
```

| transelect | jour | Description |
|------------|------|-------------|
| Row 29 totals | CC_[day] range | Daily credit card totals |

### To rj Sheet

| transelect | rj Row | Description |
|------------|--------|-------------|
| Grand Total | 64 | Transfert C.C |
| AMEX total | 32 | Amex Elavon |
| MASTER total | 34 | Master Card |
| VISA total | 35 | Visa |
| AMEX Global | 36 | Amex Global |
| DÉBIT total | 38 | Carte Debit |

---

## VBA Macros

### `aller_trans()` - Module4
```vba
Sub aller_trans()
    ' Navigate to transelect (home_trans)
    Application.Goto Reference:=Range("home_trans")
End Sub
```

### `imp_trans()` - Module5
```vba
Sub imp_trans()
    ' Print transelect sheet
    Sheets("transelect").PrintOut
End Sub
```

### `eff_trans()` - Module30
```vba
Sub eff_trans()
    ' Clear transelect data
    ' Clears entry ranges for new day
End Sub
```

### `calcul_carte()` - Module4
```vba
Sub calcul_carte()
    ' Copy credit card totals to jour sheet
    vjour = Range("vjour").Value
    ' Copy transelect totals to jour!CC_[vjour]
End Sub
```

---

## Named Ranges

| Named Range | Purpose |
|-------------|---------|
| `home_trans` | Navigation to transelect |
| `eff_trans` | Clear range for transelect |

---

## Row 14 Variance (CRITICAL)

**Column Y Row 14: -9,609.77**

This variance represents the difference between:
- What the POS system reports (POSITOUCH)
- What the credit card batches show (TOTAL 1 + TOTAL 2)

**This value flows to:**
- jour!C[day] as Diff.Caisse
- rj Row 49 as "Difference de caisse"

---

## Implementation Notes

### For WebApp:

1. **Input Fields:**
   - Individual terminal totals (Columns B-U)
   - POSITOUCH report value (Column X)
   - Batch codes from Banquet

2. **Auto-Calculated:**
   - TOTAL 1 (sum of bar terminals)
   - TOTAL 2 (sum of banquet batches)
   - VARIANCE (difference)
   - Discount amounts
   - NET amounts

3. **Validation:**
   - VARIANCE should be close to 0
   - Large variances indicate reconciliation issues
   - Grand totals should match rj credit card section

4. **Buttons/Actions:**
   - Print transelect
   - Clear transelect (eff_trans)
   - Send to jour (calcul_carte)

### Critical Values to Track:
- Row 14 TOTAL (4,111.08 + 1,796.44 = 5,907.52)
- Row 25 TOTAL (23,935.04)
- Grand Total = Row 14 + Row 25

### Variance Investigation:
If variance is large:
1. Check batch codes match receipts
2. Verify POSITOUCH report accuracy
3. Look for missing or duplicate transactions
