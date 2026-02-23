# Quick Reference: Internet, Sonifi, and Forfait in RJ

## Where Data Lives

| System | Sheet | Column | Content |
|--------|-------|--------|---------|
| **Jour** (source of truth) | jour | AT | Sonifi Film revenue |
| **Jour** (source of truth) | jour | AW | Internet revenue |
| **Jour** (source of truth) | jour | BF | Difference forfait (variance) |
| **Reconciliation** | Internet | J | Pulls Jour!AW (Internet) |
| **Reconciliation** | Internet | K | Variance (Jour vs LS report) |
| **Reconciliation** | Sonifi | X | Pulls Jour!AT (Sonifi) |
| **Reconciliation** | Sonifi | Y | Variance (Jour vs LS report) |
| **Forfait breakdown** | diff_forfait | A-L | Daily meal plan entries by type |
| **Labor hours** | Feuil1 | B-L | Daily staff hours (not related) |

---

## Sales Journal Parser - What It Extracts

### Payment Methods ✓ Extracted & Mapped
- **COMPTANT** ($737.99) → `recap['comptant_lightspeed']`
- **VISA** ($2,344.84) → `transelect['visa']`
- **MASTERCARD** ($807.83) → `transelect['mastercard']`
- **AMEX** ($496.53) → `transelect['amex']`
- **INTERAC** ($880.15) → `transelect['interac']`

### Payment Methods ✓ Extracted, ✗ NOT Mapped
- **CHAMBRE** ($13,265.41) - Extracted but not in RJ mapping
- **CORRECTION** ($11,176.96) - Extracted but not in RJ mapping

### Adjustments ✓ Extracted, ✗ NOT Mapped
- **FORFAIT** ($58.65) ← **NOT currently mapped to Jour!BF**
- **HOTEL PROMOTION** ($266.59) → Maps to HP sheet
- **ADMINISTRATION** ($263.69) - Extracted but not in RJ mapping
- **EMPL 30%** ($44.57) - Extracted but not in RJ mapping
- **POURBOIRE CHARGE** ($913.64) - Extracted but not in RJ mapping

---

## Expected Formulas (Not Visible in XLRD)

### Internet Sheet - Column J
```
=+jour!AW7  (for day 1)
=+jour!AW8  (for day 2)
=+jour!AW9  (for day 3)
... etc
```

### Sonifi Sheet - Column X
```
=+jour!AT7  (for day 1)
=+jour!AT8  (for day 2)
=+jour!AT9  (for day 3)
... etc
```

---

## Data Example from Test File

### Internet Sheet (Day 1)
```
Column I (Adjusted LS Report): 0.0
Column J (Jour!AW):           -0.27
Column K (Variance):          -0.27
```

### Sonifi Sheet (Day 1)
```
Column W (Adjusted Total):  22.99
Column X (Jour!AT):         22.99
Column Y (Variance):        0.00
```

### Jour Sheet
```
Row 2 (Day 1):
  AT = 22.99 (Sonifi Film)
  AW = -0.27 (Internet)
  BF = -1181.23 (Difference forfait)
```

---

## Key Points

1. **Jour is the source of truth** - Internet and Sonifi tabs pull FROM Jour, not the other way around
2. **Comptant is successfully extracted** from Sales Journal (line 53 in test data)
3. **Forfait is extracted but NOT mapped** - currently in `adjustments['forfait']` but unused in RJ mapping
4. **Negative values expected** - Internet and forfait can be negative (adjustments/deductions)
5. **diff_forfait sheet** - Allows detailed daily tracking of meal plan forfaits by type
6. **Sonifi Film vs Internet** - Both are in "Autres Revenus" section of Jour (columns AT and AW)

---

## Files Referenced

- **RJ Workbook:** `test_data/Rj_03-02-2026_pour_test.xls`
- **Sales Journal:** `test_data/Sales_Journal_4th_Feb.rtf`
- **Parser:** `utils/parsers/sales_journal_parser.py` (lines 18-606)
- **Analysis:** `ANALYSIS_INTERNET_SONIFI_FORFAIT.md` (detailed breakdown)
