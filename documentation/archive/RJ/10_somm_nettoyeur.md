# somm_nettoyeur Sheet Documentation

**Sheet Name:** `somm_nettoyeur`
**Dimensions:** 103 rows x 8 columns
**Purpose:** Summary of daily gratuity payments and invoice tracking

---

## Overview

The `somm_nettoyeur` sheet provides:
- Daily summary of gratuity payments
- Invoice tracking for external cleaning services
- Monthly totals by category
- Payment distribution records

**"Sommaire Nettoyeur"** = Summary of staff gratuities/cleaning payments.

---

## Structure

### Header Section (Rows 1-4)

| Row | Content |
|-----|---------|
| 1 | Title/Header |
| 2-4 | Column headers |

### Daily Summary (Rows 5-35)

| Row | Day | Column B (Brut) | Column C | Column D | Column E (Net) | Column F (Special) |
|-----|-----|-----------------|----------|----------|----------------|-------------------|
| 5 | 1 : | 624.95 | | | 624.95 | 85.55 (ok) |
| 6 | 2 : | 76.25 | | | 76.25 | |
| 7 | 3 : | 474.85 | 296.45 | 296.45 | 178.40 | |
| 8 | 4 : | 59.20 | | | 59.20 | |
| 9 | 5 : | 429.45 | 294.10 | 294.10 | 135.35 | |
| 12 | 8 : | 335.75 | 45.55 | 45.55 | 290.20 | |
| 13 | 9 : | 239.85 | | | 239.85 | 7.80 |
| 14 | 10 : | 136.25 | 54.10 | 54.10 | 82.15 | |
| 15 | 11 : | 244.85 | 112.45 | 112.45 | 132.40 | 51.00 |
| 16 | 12 : | 237.05 | | | 237.05 | 95.60 |
| 19 | 15 : | 368.30 | 68.60 | 68.60 | 299.70 | |
| 20 | 16 : | 176.30 | | | 176.30 | |
| 21 | 17 : | 577.40 | 165.20 | 165.20 | 412.20 | |
| 22 | 18 : | 65.15 | | | 65.15 | |
| 23 | 19 : | 208.20 | 166.75 | 166.75 | 41.45 | |
| 26 | 22 : | 755.30 | 210.85 | 210.85 | 544.45 | 25.50 |
| 27 | 23 : | 34.05 | | | 34.05 | |

### Special Items (Row 36-37)

| Row | Item | Column B | Column C | Column D |
|-----|------|----------|----------|----------|
| 36 | SPECIAL 1 : | 1,414.05 | 1,414.05 | 1,414.05 |
| 37 | SPECIAL 2 : | | | |

### Monthly Totals (Row 38)

| Column | Value |
|--------|-------|
| B | 6,457.20 |
| C | 2,828.10 |
| D | 2,828.10 |
| E | 3,629.10 |
| F | 265.45 |

---

## Distribution Section (Rows 42-103)

### Cost Distribution Headers (Rows 42-44)

| Column | Header |
|--------|--------|
| A | Département |
| B | CODE |
| C | BRUT |
| D | ESCOMPTE (0.35) |
| E | NET |
| F | TPS (0.05) |
| G | TVQ (0.10) |
| H | TOTAL A PAYER |

### Distribution by Department (Rows 45-60)

| Row | Department | Code | Brut | Net |
|-----|------------|------|------|-----|
| 45 | CLIENTS | 02-502000 | 1,414.05 | 919.13 |
| 47 | A payer | 02-201060 | 239.95 | 239.95 |
| 48 | Chambre | 02-406150 | 485.70 | 485.70 |
| 49 | Literie chambre | 02-406150 | | |
| 50 | Nourriture | 02-426150 | 2,313.80 | 2,313.80 |

### Invoice/Payment Section (Rows 97-103)

| Row | Content |
|-----|---------|
| 97 | EXPEDIER LE CHEQUE | LAISSER À LA RÉCEPTION |
| 100 | DEMANDE | GALINA BUNICOVSCHII | DATE: 46016.00 |
| 101 | APPROUVE | | DATE |
| 102 | VERIFIE | | DATE |
| 103 | | | # LOT |

---

## Key Calculations

### Daily Net Calculation
```
NET = BRUT - Deductions
```

### Monthly Summary
```
Total BRUT: 6,457.20
Total Deductions: 2,828.10
Total NET: 3,629.10
Special Items: 265.45
```

### GL Code Distribution

| Code | Department | Purpose |
|------|------------|---------|
| 02-502000 | CLIENTS | Client-related tips |
| 02-422000 | (accounting) | |
| 02-201060 | A payer | Payables |
| 02-406150 | Chambre | Room department |
| 02-426150 | Nourriture | Food department |

---

## Connections

### From Nettoyeur Sheet

| Nettoyeur | somm_nettoyeur | Description |
|-----------|----------------|-------------|
| Row 340 daily totals | Daily summary | BRUT column |
| Category totals | Department distribution | GL coding |

### To Accounting

| somm_nettoyeur | Destination | Description |
|----------------|-------------|-------------|
| GL code totals | Journal entries | Accounting distribution |
| Payment records | Payroll/AP | Check processing |

---

## VBA Macros

### `somm_valet()` - Module27
```vba
Sub somm_valet()
    ' Navigate to sommaire valet section
    Application.Goto Reference:=Range("home_somm_valet")
End Sub
```

---

## Implementation Notes

### For WebApp:

1. **Auto-Generated:**
   - Daily summary pulled from Nettoyeur totals
   - Department distribution calculated

2. **Manual Entry:**
   - Special items (SPECIAL 1, SPECIAL 2)
   - Approval signatures
   - Invoice references

3. **Output:**
   - Print for payment processing
   - Export to accounting system

### GL Code Reference:
- **02-xxxxxx** format indicates hotel's chart of accounts
- Distribution ensures proper expense allocation

### Payment Process:
1. Night audit generates daily totals
2. Month-end summary created
3. Check request prepared
4. Approval obtained
5. Payment issued
