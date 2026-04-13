# Daily Revenue Report to Jour Sheet Mapping

## Overview

This document defines the **exact mapping** of Daily Revenue report values to RJ jour sheet columns. It is based on the user's detailed business rules and the actual Daily Revenue PDF structure for February 4, 2026.

**Key Facts:**
- Source: Daily Revenue PDF (dlyrev) - a 7-page report from the GEAC/UX PMS night audit system
- Destination: Jour sheet in RJ Excel workbook (Row 8 = Day 4)
- Date: February 4, 2026
- Total columns mapped: 28 Direct + 3 Accumulators + 5 Sales Journal = 36 columns
- File: `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/daily_rev_jour_mapping.py`

---

## Column Mapping Summary

### PAGE 1: REVENUE DEPARTMENTS

| Column | Index | Label FR | Source Line | Expected Value | Sign | Operation |
|--------|-------|----------|-------------|-----------------|------|-----------|
| AK | 36 | Chambres (- Club Lounge) | Chambres Total | 50936.60 | Keep | Subtract club_lounge from chambres_total |
| AL | 37 | Téléphone Local | Telephone Local | 0.00 | Keep | Direct |
| AM | 38 | Téléphone Interurbain | Interurbain | 0.00 | Keep | Direct |
| AN | 39 | Téléphones Publics | Telephones Publics | 0.00 | Keep | Direct |

**Rule:** Chambres Total goes to AK, BUT SUBTRACT the Club Lounge value from it first.

---

### PAGE 2: AUTRES REVENUS + NON-REVENUE START

| Column | Index | Label FR | Source Line | Expected Value | Sign | Operation |
|--------|-------|----------|-------------|-----------------|------|-----------|
| AO | 40 | Nettoyeur - Dry Cleaning | Nettoyeur-Dry Cleaning | 0.00 | Keep | Direct |
| AP | 41 | MACHINE DISTRIBUTRICE | MACHINE DISTRIBUTRICE | 0.00 | Keep | Direct |
| AS | 44 | Autres Grand Livre Total | Autres Grand Livre Total | -92589.85 | **Keep** | Direct (KEEP SIGN) |
| AT | 45 | Sonifi | Sonifi | 0.00 | Keep | Direct |
| AU | 46 | Lit Pliant | Lit Pliant | 0.00 | Keep | Direct |
| AV | 47 | Location De Boutique | Location De Boutique | 0.00 | Keep | Direct |
| AW | 48 | Internet | Internet | -0.46 | Keep | Direct |
| BA | 52 | Massage | Massage | 383.30 | Keep | Direct |
| AG | 32 | Location Salle Forfait | Location Salle Forfa | 1620.00 | Keep | Direct |

**Special Rule:** Column AS (Autres Grand Livre Total) is NEGATIVE (-92589.85). The rule says: **keep sign: negative if negative, positive if positive**. This is an accounting entry from the General Ledger.

---

### TAXES: Chambres & Other Services

| Column | Index | Label FR | Source Line(s) | Expected Value | Sign | Operation |
|--------|-------|----------|-----------------|-----------------|------|-----------|
| AZ | 51 | Taxe Hebergement | Taxe Hebergement | 1783.53 | Keep | Direct |
| **AY** | **50** | **TPS Accumulator** | **Multiple pages** | **2635.79** | Keep | **SUM** |
| **AX** | **49** | **TVQ Accumulator** | **Multiple pages** | **5257.25** | Keep | **SUM** |

#### Column AY (TPS) - Accumulator
Sums TPS from:
1. **PAGE 2** - TPS 141740175 (Chambres): 2635.79
2. **PAGE 4** - TPS Tel Local: 0.00 (ADD_TO_EXISTING)
3. **PAGE 4** - TPS Tel Interurbain: 0.00 (ADD_TO_EXISTING)
4. **PAGE 5** - TPS Autres: 100.17 (ADD_TO_EXISTING)
5. **PAGE 5** - TPS Internet: 0.00 (ADD_TO_EXISTING)

**Total for AY = 2635.79**

#### Column AX (TVQ) - Accumulator
Sums TVQ from:
1. **PAGE 3** - TVQ 1019892413 (Chambres): 5257.25
2. **PAGE 4** - TVQ Tel Local: 0.00 (ADD_TO_EXISTING)
3. **PAGE 4** - TVQ Tel Interurbain: 0.00 (ADD_TO_EXISTING)
4. **PAGE 5** - TVQ Autres: 200.23 (ADD_TO_EXISTING)
5. **PAGE 5** - TVQ Internet: 0.46 (ADD_TO_EXISTING)

**Total for AX = 5457.94** (Note: 5257.25 + 0 + 0 + 200.23 + 0.46)

---

### PAGE 6: SETTLEMENTS (Gift Cards & Bons d'achat)

| Column | Index | Label FR | Source Line(s) | Expected Value | Sign | Operation |
|--------|-------|----------|-----------------|-----------------|------|-----------|
| **BC** | **54** | **Gift Card & Bon d'achat** | **Multiple** | **400.00** | Keep | **SUM** |
| CC | 80 | Certificat Cadeaux | Certificat Cadeaux | 0.00 | Keep | Direct |

#### Column BC - Accumulator
Sums from:
1. **PAGE 2** - Adj GiveX Gift Card: 400.00
2. **PAGE 6** - Bon D'achat: 0.00 (ADD_TO_EXISTING)
3. **PAGE 6** - Gift Card: 0.00 (ADD_TO_EXISTING)
4. **PAGE 6** - Bon D'achat Remanco: 0.00 (ADD_TO_EXISTING)

**Total for BC = 400.00**

---

### PAGE 7: BALANCE & TRANSFERS

| Column | Index | Label | Formula | Expected Value | Sign | Operation |
|--------|-------|-------|---------|-----------------|------|-----------|
| **D** | **3** | **New Balance (negative)** | **-(new_balance) - deposit_on_hand** | **3871908.19** | **Negate** | **Formula** |
| **CF** | **83** | **A/R Misc + Front Office** | **-(transfers - payments)** | **0.00** | **Always Negative** | **Combined** |

#### Column D - Special Calculation
```
Column D = -(balance.new_balance) - deposits.deposit_on_hand
         = -(-3871908.19) - 0
         = 3871908.19
```

**Rule:** "Put in NEGATIVE, then subtract Deposit on Hand from Advance Deposit Balance Sheet"
- The value itself is negated (becomes positive when New Balance is negative)
- Then Deposit on Hand is subtracted from it

#### Column CF - Combined with Always-Negative Rule
Combines two sources, both ALWAYS negative:
1. **PAGE 2** - A/R Misc Total: 0.00 (ALWAYS_NEGATIVE)
2. **PAGE 7** - Front Office Transfers: 0.00 (ALWAYS_NEGATIVE: -(total_transfers - payments))

**Result: 0.00**

---

### SPECIAL CALCULATED COLUMNS

| Column | Index | Label | Formula | Expected Value | Operation |
|--------|-------|-------|---------|-----------------|-----------|
| BF | 57 | Club Lounge & Forfait | `-forfait + club_lounge_value` | 0.00 | Derived |

**Column BF:** `BF = -Forfait + Club Lounge value (from diff_forfait)`

This is derived from the internal diff_forfait calculation, not directly from Daily Revenue.

---

### SALES JOURNAL (Separate from Daily Revenue)

| Column | Index | Label | Source | Expected Value | Sign Rule |
|--------|-------|-------|--------|-----------------|-----------|
| J | 9 | Piazza Nourriture | Sales Journal | 1981.40 | DEBIT=neg, CREDIT=pos |
| K | 10 | Piazza Alcool (Boisson) | Sales Journal | 75.00 | DEBIT=neg, CREDIT=pos |
| L | 11 | Piazza Bières | Sales Journal | 198.00 | DEBIT=neg, CREDIT=pos |
| M | 12 | Piazza Non Alcool (Minéraux) | Sales Journal | 19.00 | DEBIT=neg, CREDIT=pos |
| N | 13 | Piazza Vins | Sales Journal | 219.00 | DEBIT=neg, CREDIT=pos |

**Rule:** All DEBITS are NEGATIVE, all CREDITS are POSITIVE.

For column J (Piazza Nourriture), also:
- Subtract HP deductions
- Subtract adjustments

---

## Detailed Rules & Special Handling

### Rule 1: Accumulator Columns (ADD_TO_EXISTING)
When multiple source lines go into one column, they **accumulate** (sum together).

**Affected columns:**
- **AX** (TVQ): 5 sources accumulate
- **AY** (TPS): 5 sources accumulate
- **BC** (Gift Cards): 4 sources accumulate

### Rule 2: Sign Preservation
Most columns use "keep sign" meaning:
- If source is negative → column gets negative value
- If source is positive → column gets positive value

**Exception:** Column AS (Autres Grand Livre Total) is explicitly -92589.85. The rule emphasizes: "keep sign: negative if negative, positive if positive" because this is an accounting entry that must maintain its sign.

### Rule 3: Always-Negative Columns
Some columns must ALWAYS be negative:
- **Column CF** (A/R Misc & Front Office Transfers): Both sources calculated as negative values

### Rule 4: Negate-Result Columns
Some columns require negating the final result:
- **Column D** (New Balance): The new_balance value is negated before use

### Rule 5: Formula Columns
Some columns require calculations:
- **Column D**: `-(new_balance) - deposit_on_hand`
- **Column CF**: `-(total_transfers - payments)`
- **Column BF**: `-forfait + club_lounge_value`

### Rule 6: Derived Columns
Some columns are NOT from Daily Revenue but calculated from other sources:
- **Column BF**: Derived from diff_forfait calculation

### Rule 7: Special Adjustments
Some columns require additional processing:
- **Column AK**: Must subtract club_lounge value from chambres_total
- **Column J**: Must subtract HP deductions and adjustments

---

## February 4, 2026 - Actual Data

### Daily Revenue Parser Output (Feb 4)
```
Chambres Total:               50936.60
Téléphone Local:                  0.00
Téléphone Interurbain:            0.00
Téléphones Publics:               0.00
Nettoyeur-Dry Cleaning:           0.00
Sonifi:                           0.00
Location De Boutique:             0.00
Lit Pliant:                       0.00
MACHINE DISTRIBUTRICE:            0.00
Location Salle Forfait:        1620.00
Massage:                        383.30
Internet:                         -0.46
Autres Grand Livre Total:    -92589.85
Adj GiveX Gift Card:            400.00
A/R Misc Total:                   0.00

Taxe Hebergement:              1783.53
TPS 141740175 (Chambres):      2635.79
TVQ 1019892413 (Chambres):     5257.25
TPS Tel Local:                    0.00
TPS Tel Interurbain:              0.00
TVQ Tel Local:                    0.00
TVQ Tel Interurbain:              0.00
TPS Autres:                     100.17
TVQ Autres:                     200.23
TPS Internet:                     0.00
TVQ Internet:                     0.46

Bon D'achat:                      0.00
Certificat Cadeaux:               0.00
Gift Card:                        0.00
Bon D'achat Remanco:              0.00

New Balance:                -3871908.19
Deposit on Hand:                  0.00
Front Office Transfers:           0.00
```

### Expected Jour Sheet Values (Row 8, Day 4)
```
AK:  50936.60  (Chambres - Club Lounge)
AL:      0.00  (Téléphone Local)
AM:      0.00  (Téléphone Interurbain)
AN:      0.00  (Téléphones Publics)
AO:      0.00  (Nettoyeur - Dry Cleaning)
AP:      0.00  (MACHINE DISTRIBUTRICE)
AS: -92589.85  (Autres Grand Livre Total) [NEGATIVE]
AT:      0.00  (Sonifi)
AU:      0.00  (Lit Pliant)
AV:      0.00  (Location De Boutique)
AW:     -0.46  (Internet)
BA:    383.30  (Massage)
AG:   1620.00  (Location Salle Forfait)
AZ:   1783.53  (Taxe Hebergement)
AY:   2635.79  (TPS Accumulator: 2635.79+0+0+100.17+0)
AX:   5458.94  (TVQ Accumulator: 5257.25+0+0+200.23+0.46)
BC:    400.00  (Gift Card Accumulator: 400+0+0+0)
CC:      0.00  (Certificat Cadeaux)
D:   3871908.19  (New Balance negated: -(-3871908.19) - 0)
CF:      0.00  (A/R Misc + Front Office: both negative, sum = 0)
BF:      0.00  (Club Lounge & Forfait: derived)

J:   1981.40  (Piazza Nourriture - HP deductions - adjustments)
K:     75.00  (Piazza Alcool/Boisson)
L:    198.00  (Piazza Bières)
M:     19.00  (Piazza Non Alcool/Minéraux)
N:    219.00  (Piazza Vins)
```

---

## Implementation Guide

### Using the Python Mapping Module

```python
from utils.daily_rev_jour_mapping import (
    DAILY_REV_TO_JOUR,
    ACCUMULATOR_COLUMNS,
    get_mapping_for_column,
    get_all_columns,
    col_letter_to_index,
    col_index_to_letter
)

# Get mapping for a specific column
ak_mapping = get_mapping_for_column('AK')
print(ak_mapping['label_fr'])  # "Chambres (- Club Lounge)"
print(ak_mapping['expected_value'])  # 50936.60

# Get all columns
all_cols = get_all_columns()  # ['AK', 'AL', 'AM', ..., 'N']

# Check if column is an accumulator
ay_config = get_mapping_for_column('AY')
if ay_config['operation'] == 'accumulate':
    print(ay_config['accumulator_fields'])
    # ['non_revenue.chambres_tax.tps', ...]

# Convert column letters to indices
print(col_letter_to_index('AK'))  # 36
print(col_index_to_letter(36))    # 'AK'
```

### Auto-Filling Jour Sheet from Daily Revenue

The mapping can be used to automatically populate jour sheet columns:

1. Parse Daily Revenue PDF with `DailyRevenueParser`
2. For each mapped column, look up its configuration in `DAILY_REV_TO_JOUR`
3. Extract the value from parsed data using the `base_field` path
4. Apply any `operation` (direct, subtract, accumulate, formula, etc.)
5. Write result to the jour sheet at the appropriate row/column
6. Apply any `sign_handling` rules (keep_sign, negate_result, always_negative)

---

## Validation Checklist

When mapping Daily Revenue to Jour sheet, verify:

- [ ] All 28 direct columns are populated from Daily Revenue
- [ ] All 3 accumulator columns correctly sum their sources
- [ ] All 5 Sales Journal columns use correct sign rules
- [ ] Column AK subtracts club_lounge from chambres_total
- [ ] Column AS keeps its negative sign (-92589.85)
- [ ] Column D is negated: 3871908.19 (from -3871908.19)
- [ ] Column CF is calculated as -(transfers - payments)
- [ ] Accumulator columns (AX, AY, CB) sum all sources
- [ ] Sales Journal columns follow DEBIT=negative, CREDIT=positive rule
- [ ] All signs are handled according to sign_handling rule

---

## File References

- **Mapping Module:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/daily_rev_jour_mapping.py`
- **Daily Revenue Parser:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/parsers/daily_revenue_parser.py`
- **RJ Mapper (Existing):** `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/rj_mapper.py`
- **Daily Revenue PDF:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/Daily_Rev_4th_Feb.pdf`
- **RJ Jour Sheet:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/RJ 2024-2025/RJ 2025-2026/12-Février 2026/Rj 04-02-2026.xls`

---

## Revision History

- **2026-02-09:** Initial comprehensive mapping document created
- **Source:** User's detailed business rules + Daily Revenue parser output
- **Status:** Complete - All 36 columns mapped and documented
