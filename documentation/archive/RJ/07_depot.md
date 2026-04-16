# depot Sheet Documentation

**Sheet Name:** `depot`
**Dimensions:** 54 rows x 16 columns
**Purpose:** Daily bank deposit tracking for Canadian accounts

---

## Overview

The `depot` sheet tracks:
- Daily cash deposits to the bank
- Multiple deposit accounts (Client 6 - Compte #1, Client 8 - Compte #47)
- Individual deposit amounts with dates
- Running totals and grand total

---

## Structure

### Header Section (Rows 1-9)

| Row | Content |
|-----|---------|
| 1 | GROUPE HÔTELIER GRAND CHÂTEAU |
| 2 | HOTEL SHERATON LAVAL |
| 4 | DATE: [Excel date] |
| 6 | COMPTE CANADIEN | COMPTE CANADIEN |
| 7 | CLIENT 6 COMPTE # 1 | CLIENT 8 COMPTE # 47 |
| 9 | DATE | MONTANT | SIGNATURE | DATE | MONTANT | SIGNATURE |

### Deposit Columns Layout

**Account 1 (Columns A-G):**
| Column | Content |
|--------|---------|
| A | Date |
| B | Montant (Amount) |
| C | Subtotal/Signature |
| E | (spacer) |
| F | (spacer) |
| G | Signature |

**Account 2 (Columns I-K):**
| Column | Content |
|--------|---------|
| I | Date |
| J | Montant (Amount) |
| K | Subtotal/Signature |

### Deposit Data (Rows 10-45)

**Example entries:**

| Date | Account 1 (Col B) | Account 2 (Col J) |
|------|-------------------|-------------------|
| 19 DECEMBRE | 48.15, 313.15, 4.70, 48.15 = **414.15** | 73.90, 180.40, 119.95, 7.45, 861.00 = **1,242.70** |
| 20 DECEMBRE | 66.35, 119.55, 308.75, 67.15, 79.26, 77.50 = **652.21** | - |
| 21 DECEMBRE | 424.35, 131.20, 550.00, 51.50, 1261.25, 328.60, 44.25, 53.00, 62.00 = **2,906.15** | - |
| 22 DECEMBRE | 68.30, 73.30, 41.05 = **182.65** | - |
| 23 DECEMBRE | 106.70, 18.70, 67.60, 72.80, 128.10, 65.50 = **459.40** | - |

### Totals Section (Rows 46-48)

| Row | Column | Value | Description |
|-----|--------|-------|-------------|
| 46 | C | 4,614.56 | Account 1 Total |
| 46 | J | 18,994.55 | Account 2 Total |
| 48 | J | **23,609.11** | **GRAND TOTAL** |

---

## Day 23 Deposit Details

| Entry | Amount |
|-------|--------|
| 1 | 106.70 |
| 2 | 18.70 |
| 3 | 67.60 |
| 4 | 72.80 |
| 5 | 128.10 |
| 6 | 65.50 |
| **Subtotal** | **459.40** |

This matches Recap Row 20 "Total dépôt net" = 459.40

---

## Connections

### To Recap Sheet

| depot | Recap | Description |
|-------|-------|-------------|
| Day subtotal (459.40) | Row 20 | Total dépôt net |
| Day subtotal | Row 22 | Dépôt Canadien |

### To rj Sheet

| depot | rj Row | Description |
|-------|--------|-------------|
| Day subtotal | 25 | Canadien (DEPOT section) |
| Monthly total | 27 | TOTAL DEPOT |

---

## VBA Macros

### `imp_depot()` - Module4
```vba
Sub imp_depot()
    ' Print depot sheet
    Sheets("depot").PrintOut
End Sub
```

### `Eff_depot()` - Module4
```vba
Sub Eff_depot()
    ' Clear depot at named range eff_depot
    Range("eff_depot").ClearContents
End Sub
```

### `aller_depot()` - Module4
```vba
Sub aller_depot()
    ' Navigate to depot sheet
    Application.Goto Reference:=Range("home_depot")
End Sub
```

---

## Named Ranges

| Named Range | Purpose |
|-------------|---------|
| `home_depot` | Navigation to depot |
| `eff_depot` | Clear range for depot |

---

## Validation

**Daily Check:**
- depot day subtotal should = Recap "Total dépôt net"
- depot day subtotal should = Recap "Dépôt Canadien"

**Monthly Check:**
- Sum of all daily subtotals = TOTAL (Row 46)
- Account 1 + Account 2 = GRAND TOTAL

---

## Implementation Notes

### For WebApp:

1. **Input Fields:**
   - Individual deposit amounts
   - Date for each deposit group
   - Account selection (1 or 2)

2. **Auto-Calculated:**
   - Daily subtotals
   - Account totals
   - Grand total

3. **Validation:**
   - Daily subtotal must match Recap "Total dépôt net"
   - Discrepancy indicates reconciliation error

4. **Buttons/Actions:**
   - Print depot
   - Clear depot (Eff_depot)
   - Add new deposit entry

### Entry Format:
- Multiple amounts per day grouped together
- Subtotal at end of each day's group
- Two separate account columns

### Bank Accounts:
- **Client 6 - Compte #1**: Main operating account
- **Client 8 - Compte #47**: Secondary account (larger deposits)
