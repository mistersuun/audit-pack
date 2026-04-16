# RECAP (Recap) Sheet Documentation

**Sheet Name:** `Recap`
**Dimensions:** 26 rows x 14 columns
**Purpose:** Daily cash reconciliation summary - calculates deposit amounts

---

## Overview

The `Recap` sheet is the **daily cash reconciliation** that:
- Summarizes cash and payments received
- Calculates refunds and adjustments
- Determines the net deposit amount
- Tracks DueBack (money owed to/from reception)
- Shows Surplus/Deficit for validation

This is one of the most important sheets for the night auditor.

---

## Complete Structure

### Header Section (Rows 1-5)

| Row | Column A | Column D | Column E |
|-----|----------|----------|----------|
| 1 | | Date: | 46014 (Excel date) |
| 4 | RECAP | | |
| 5 | Description | Lecture | Corr. +(-) | Net |

### Cash Receipts (Rows 6-10)

| Row | Description | Col B (Lecture) | Col D (Net) |
|-----|-------------|-----------------|-------------|
| 6 | Comptant LightSpeed | 521.20 | 521.20 |
| 7 | Comptant Positouch | 696.05 | 696.05 |
| 8 | Chèque payment register AR | | |
| 9 | Chèque Daily Revenu | | |
| 10 | **Total** | **1,217.25** | **1,217.25** |

### Refunds Section (Rows 11-14)

| Row | Description | Col B (Lecture) | Col D (Net) |
|-----|-------------|-----------------|-------------|
| 11 | Moins Remboursement Gratuité | -2,543.42 | -2,543.42 |
| 12 | Moins Remboursement Client | -1,067.61 | -1,067.61 |
| 13 | Moins Remboursement Loterie | | |
| 14 | **Total** | **-2,393.78** | **-2,393.78** |

### DueBack & Adjustments (Rows 15-20)

| Row | Description | Col B | Col D | Col E | Col F |
|-----|-------------|-------|-------|-------|-------|
| 15 | Moins échange U.S. | | | 0.00 | EC |
| **16** | **Due Back Réception** | **653.10** | **653.10** | **-653.10** | **WR** |
| **17** | **Due Back N/B** | **667.61** | **667.61** | **-667.61** | **WN** |
| 18 | Total à déposer | -1,073.07 | -1,073.07 | | |
| 19 | Surplus/déficit (+ou-) | 1,532.47 | 1,532.47 | -1,532.47 | WS |
| 20 | Total dépôt net | 459.40 | 459.40 | | |

### Deposit Summary (Rows 21-24)

| Row | Description | Col B | Col D | Col E |
|-----|-------------|-------|-------|-------|
| 21 | Depot US | | | 0.00 |
| 22 | Dépôt Canadien | 459.40 | 459.40 | 2,853.18 |
| 23 | Total dépôt net | 459.40 | 459.40 | |
| 24 | Argent Reçu : | 4,070.43 | | |

### Signature (Row 26)

| Row | Description | Col B |
|-----|-------------|-------|
| 26 | Préparé par : | Khalil Mouatarif |

---

## Row 19 Special Calculation Columns (H-N)

Row 19 "Surplus/déficit" contains a breakdown of the calculation:

| Column | Value | Source | Description |
|--------|-------|--------|-------------|
| H | 4,070.43 | jour!BU | Argent Reçu |
| I | -1,067.61 | jour!BV | Remb. Client |
| J | -2,543.42 | jour!BW | Remb. Gratuité |
| K | 0.00 | | (empty) |
| **L** | **-653.10** | **jour!BY** | **Due Back Réception** |
| M | 0.00 | | (empty) |
| N | -1,532.47 | jour!CA | Surplus/Def |

---

## Column Codes (Column F)

| Code | Meaning | Row |
|------|---------|-----|
| EC | Exchange (U.S.) | 15 |
| WR | DueBack Reception | 16 |
| WN | DueBack N/B | 17 |
| WS | Surplus/Deficit | 19 |

---

## Data Sources

### From jour Sheet

| Recap Row | Recap Field | jour Column | jour Header |
|-----------|-------------|-------------|-------------|
| 11 | Moins Remb. Gratuité | BW (74) | Remb. Gratuite |
| 12 | Moins Remb. Client | BV (73) | Remb. Serverveurs |
| 16 | Due Back Réception | BY (76) | Due back reception |
| 19 | Surplus/déficit | CA (78) | Surplus/Def |
| 24 | Argent Reçu | BU (72) | Argent recu |

### From DUEBACK# Sheet

| Recap Row | Recap Field | DUEBACK# Cell |
|-----------|-------------|---------------|
| 16 | Due Back Réception | B[day_row] (ABS value) |

### Manual Entry

| Recap Row | Recap Field | Source |
|-----------|-------------|--------|
| 6 | Comptant LightSpeed | POS report |
| 7 | Comptant Positouch | POS report |
| **17** | **Due Back N/B** | **PDF (manual)** |

---

## Key Formulas

### Total Cash (Row 10)
```excel
=B6+B7+B8+B9
```

### Total Refunds (Row 14)
```excel
=B11+B12+B13
```

### Total à déposer (Row 18)
```excel
=B10+B14+B15+B16+B17
```
or
```excel
=Total + Refunds + Exchange + DueBack Réception + DueBack N/B
```

### Total dépôt net (Row 20)
```excel
=B18+B19
```
or
```excel
=Total à déposer + Surplus/déficit
```

---

## VBA Macros

### `efface_recap()` - Module11
```vba
Sub efface_recap()
    ' Clear recap at named range eff_recap
    Range("eff_recap").ClearContents
End Sub
```

### `imprime_recap()` - Module11
```vba
Sub imprime_recap()
    ' Print recap sheet
    Sheets("Recap").PrintOut
End Sub
```

### `aller_recap()` - Module9
```vba
Sub aller_recap()
    ' Navigate to recap (home_recap)
    Application.Goto Reference:=Range("home_recap")
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

## Named Ranges

| Named Range | Location | Purpose |
|-------------|----------|---------|
| `eff_recap` | Clear range | For efface_recap macro |
| `home_recap` | Navigation | For aller_recap macro |

---

## DueBack Details

### Row 16: Due Back Réception (Code: WR)

| Aspect | Value | Notes |
|--------|-------|-------|
| Source | jour!BY → DUEBACK#!B | Flows through DUEBACK# |
| jour value | -653.10 | Negative in source |
| Recap B16 | **653.10** | Positive (ABS) |
| Recap E16 | -653.10 | Negative for calculation |

### Row 17: Due Back N/B (Code: WN)

| Aspect | Value | Notes |
|--------|-------|-------|
| Source | **PDF (manual)** | NOT from Excel |
| Recap B17 | **667.61** | Manual entry |
| Recap E17 | -667.61 | Negative for calculation |
| Meaning | Nettoyeur/Banquet DueBack | Separate from Reception |

---

## Implementation Notes

### For WebApp:

1. **Input Fields:**
   - Comptant LightSpeed (Row 6)
   - Comptant Positouch (Row 7)
   - Correction column (C) for adjustments
   - **Due Back N/B (Row 17) - Manual entry**

2. **Auto-Calculated:**
   - All totals (Rows 10, 14, 18, 20)
   - Due Back Réception (Row 16) from DUEBACK#
   - Surplus/déficit (Row 19) from jour

3. **Validation:**
   - Total dépôt net should match bank deposit
   - Row 19 columns H-N should sum correctly
   - Due Back Réception = ABS(DUEBACK# Column B)

4. **Buttons/Actions:**
   - Print Recap
   - Clear Recap (efface_recap)
   - Send to jour (envoie_dans_jour)

### Critical: Row 19 Send to jour
The `envoie_dans_jour` macro copies H19:N19 to the jour sheet. This is how Recap data gets recorded in the master jour sheet.
