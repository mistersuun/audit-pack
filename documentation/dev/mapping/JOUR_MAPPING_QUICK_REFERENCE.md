# Jour Sheet Mapping - Quick Reference Guide

## What This Document Is

A quick lookup guide for the mapping between Daily Revenue report values and Jour sheet columns. For detailed information, see:
- `DAILY_REVENUE_TO_JOUR_MAPPING.md` (complete rules and explanations)
- `JOUR_MAPPING_VERIFICATION_TABLE.md` (detailed verification with calculations)
- `utils/daily_rev_jour_mapping.py` (Python implementation)

---

## Column Index by Letter

```
A=0   B=1   C=2   D=3   E=4   F=5   G=6   H=7   I=8   J=9
K=10  L=11  M=12  N=13  O=14  P=15  Q=16  R=17  S=18  T=19
U=20  V=21  W=22  X=23  Y=24  Z=25
AA=26 AB=27 AC=28 AD=29 AE=30 AF=31 AG=32 AH=33 AI=34 AJ=35
AK=36 AL=37 AM=38 AN=39 AO=40 AP=41 AQ=42 AR=43 AS=44 AT=45
AU=46 AV=47 AW=48 AX=49 AY=50 AZ=51 BA=52 BB=53 BC=54 ...
```

---

## All Jour Columns Mapped

### Direct Columns (Simple Copy)
```
AK=36  Chambres (minus Club Lounge)      → 50936.60
AL=37  Téléphone Local                   → 0.00
AM=38  Téléphone Interurbain             → 0.00
AN=39  Téléphones Publics                → 0.00
AO=40  Nettoyeur - Dry Cleaning          → 0.00
AP=41  MACHINE DISTRIBUTRICE             → 0.00
AT=45  Sonifi                            → 0.00
AU=46  Lit Pliant                        → 0.00
AV=47  Location De Boutique              → 0.00
AW=48  Internet                          → -0.46
BA=52  Massage                           → 383.30
AG=32  Location Salle Forfait            → 1620.00
AS=44  Autres Grand Livre Total          → -92589.85 [KEEP NEGATIVE]
AZ=51  Taxe Hebergement                  → 1783.53
CC=80  Certificat Cadeaux                → 0.00
```

### Accumulator Columns (Sum Multiple Sources)
```
AY=50  TPS (GST) Total
       = 2635.79 (TPS Chambres)
       + 0.00 (TPS Tel Local)
       + 0.00 (TPS Tel Interurbain)
       + 100.17 (TPS Autres)
       + 0.00 (TPS Internet)
       = 2735.96

AX=49  TVQ (QST) Total
       = 5257.25 (TVQ Chambres)
       + 0.00 (TVQ Tel Local)
       + 0.00 (TVQ Tel Interurbain)
       + 200.23 (TVQ Autres)
       + 0.46 (TVQ Internet)
       = 5457.94

BC=54  Gift Cards & Bons
       = 400.00 (GiveX)
       + 0.00 (Bon D'achat)
       + 0.00 (Gift Card)
       + 0.00 (Bon D'achat Remanco)
       = 400.00
```

### Formula Columns (Apply Calculation)
```
D=3    New Balance = -(−3871908.19) − 0 = 3871908.19
       [NEGATE the New Balance value, then subtract Deposit on Hand]

CF=83  A/R Misc + Front Office = 0.00
       [ALWAYS NEGATIVE rule applies, but both sources are 0]
```

### Special Columns (Not from Daily Revenue)
```
BF=57  Club Lounge & Forfait (DERIVED)
       = −Forfait + Club Lounge value
       = 0.00
       [Calculated internally, not from Daily Revenue PDF]
```

### Sales Journal Columns (Separate Source)
```
J=9    Piazza Nourriture         → 1981.40 (minus HP deductions)
K=10   Piazza Alcool (Boisson)   → 75.00
L=11   Piazza Bières             → 198.00
M=12   Piazza Non Alcool         → 19.00
N=13   Piazza Vins               → 219.00
```

---

## Column Summary Table

| Col | Idx | Value | Source | Type |
|-----|-----|-------|--------|------|
| D | 3 | 3,871,908.19 | New Balance (negated) | Formula |
| J | 9 | 1,981.40 | Piazza Nourriture | SJ |
| K | 10 | 75.00 | Piazza Alcool | SJ |
| L | 11 | 198.00 | Piazza Bières | SJ |
| M | 12 | 19.00 | Piazza Minéraux | SJ |
| N | 13 | 219.00 | Piazza Vins | SJ |
| AG | 32 | 1,620.00 | Location Salle Forfait | Direct |
| AK | 36 | 50,936.60 | Chambres - Club Lounge | Direct |
| AL | 37 | 0.00 | Téléphone Local | Direct |
| AM | 38 | 0.00 | Téléphone Interurbain | Direct |
| AN | 39 | 0.00 | Téléphones Publics | Direct |
| AO | 40 | 0.00 | Nettoyeur | Direct |
| AP | 41 | 0.00 | Machine Distributrice | Direct |
| AS | 44 | -92,589.85 | Autres Grand Livre | Direct* |
| AT | 45 | 0.00 | Sonifi | Direct |
| AU | 46 | 0.00 | Lit Pliant | Direct |
| AV | 47 | 0.00 | Location Boutique | Direct |
| AW | 48 | -0.46 | Internet | Direct |
| AX | 49 | 5,457.94 | TVQ Accumulator | Accum |
| AY | 50 | 2,735.96 | TPS Accumulator | Accum |
| AZ | 51 | 1,783.53 | Taxe Hebergement | Direct |
| BA | 52 | 383.30 | Massage | Direct |
| BC | 54 | 400.00 | Gift Card Accum | Accum |
| CC | 80 | 0.00 | Certificat Cadeaux | Direct |
| CF | 83 | 0.00 | A/R + FO Transfer | Formula |
| BF | 57 | 0.00 | Club Lounge & Forfait | Derived |

**Legend:** SJ=Sales Journal, Direct=Copy directly, Accum=Sum multiple sources, Formula=Calculate using formula, Derived=Internal calculation, *=Keep negative sign

---

## Key Rules to Remember

### Rule 1: AK = Chambres MINUS Club Lounge
```
AK = chambres_total - club_lounge_total
   = 50936.60 - 0.00
   = 50936.60
```

### Rule 2: AS Must Be NEGATIVE
```
AS = -92589.85  ← This is an accounting entry, KEEP THE NEGATIVE SIGN
```

### Rule 3: Accumulators SUM All Sources
```
AY (TPS) = 2635.79 + 0 + 0 + 100.17 + 0 = 2735.96
AX (TVQ) = 5257.25 + 0 + 0 + 200.23 + 0.46 = 5457.94
BC (Gift) = 400.00 + 0 + 0 + 0 = 400.00
```

### Rule 4: D is Negated New Balance
```
D = -(new_balance) - deposit_on_hand
  = -(−3,871,908.19) - 0
  = 3,871,908.19
```

### Rule 5: CF is ALWAYS NEGATIVE
```
CF = -(Front Office Transfers - Payments)
   = -(0 - 0)
   = 0.00 [Even when 0, the rule is: ALWAYS NEGATIVE]
```

### Rule 6: Sales Journal Signs
```
J, K, L, M, N: All DEBITS are NEGATIVE, all CREDITS are POSITIVE
               Sign handling is critical
```

---

## Most Common Mistakes to Avoid

❌ **Wrong:** Forget to subtract club_lounge from AK
✓ **Right:** `AK = 50936.60 - 0 = 50936.60`

❌ **Wrong:** Change AS from negative to positive
✓ **Right:** `AS = -92589.85` (keep it negative)

❌ **Wrong:** Put exact Daily Revenue value in AY without adding TPS Autres (100.17)
✓ **Right:** `AY = 2635.79 + 100.17 = 2735.96`

❌ **Wrong:** Put exact Daily Revenue value in AX without adding TVQ Autres (200.23) and TVQ Internet (0.46)
✓ **Right:** `AX = 5257.25 + 200.23 + 0.46 = 5457.94`

❌ **Wrong:** Forget to negate new balance in column D
✓ **Right:** `D = -(-3871908.19) = 3871908.19`

❌ **Wrong:** Leave CF empty or make it positive
✓ **Right:** `CF = 0.00` (but the rule says ALWAYS NEGATIVE)

---

## Column Order in Jour Sheet (Left to Right)

Row 8 (Day 4) should have these values in order:
```
A    B    C    D            E    ... J      K     L     M    N    ...
?    ?    ?    3,871,908    ?    ... 1,981  75    198   19   219  ...

         AG       AK        AL   AM   AN  AO  AP  AS    AT  AU  AV  AW  AX      AY      AZ    BA  BC  CC  CF
...      1,620    50,936    0    0    0   0   0   -92,590 0   0   0   -0.46 5,457.94 2,735.96 1,784 383 400 0
```

---

## Daily Revenue PDF Pages Covered

✓ **PAGE 1:** Revenue Departments (Chambres, Telephones)
✓ **PAGE 2:** Autres Revenus + Non-Revenue start (Taxes, GiveX, Comptabilité)
✓ **PAGE 3:** Non-Revenue continued (TVQ Internet)
✓ **PAGE 4:** Non-Revenue taxes (TPS/TVQ Tel)
✓ **PAGE 5:** More taxes (TPS/TVQ Autres, TPS/TVQ Internet)
✓ **PAGE 6:** Settlements (Gift Cards, Bons)
✓ **PAGE 7:** Balance section (New Balance, Transfers)
✓ **SALES JOURNAL:** Separate source (Piazza sales)

---

## Quick Validation

Run these checks before finalizing jour sheet:

1. **AK** = 50,936.60 ✓
2. **AS** = -92,589.85 (negative!) ✓
3. **AY** = 2,735.96 (includes TPS Autres 100.17) ✓
4. **AX** = 5,457.94 (includes TVQ Autres 200.23 + TVQ Internet 0.46) ✓
5. **BC** = 400.00 ✓
6. **D** = 3,871,908.19 (negated) ✓
7. **CF** = 0.00 (with always-negative rule) ✓

If all these check out, your mapping is correct!

---

## File References

- **Module:** `utils/daily_rev_jour_mapping.py`
- **Full Documentation:** `DAILY_REVENUE_TO_JOUR_MAPPING.md`
- **Verification Table:** `JOUR_MAPPING_VERIFICATION_TABLE.md`
- **Daily Revenue PDF:** `Daily_Rev_4th_Feb.pdf`
- **Daily Revenue Parser:** `utils/parsers/daily_revenue_parser.py`

---

## Implementation Example (Python)

```python
from utils.daily_rev_jour_mapping import (
    DAILY_REV_TO_JOUR,
    ACCUMULATOR_COLUMNS,
    col_letter_to_index
)
from utils.parsers.daily_revenue_parser import DailyRevenueParser

# Parse Daily Revenue
with open('Daily_Rev_4th_Feb.pdf', 'rb') as f:
    parser = DailyRevenueParser(f.read())
    data = parser.get_result()['data']

# Get a single column mapping
ak_mapping = DAILY_REV_TO_JOUR['AK']
print(f"Column: {ak_mapping['label_fr']}")
print(f"Index: {ak_mapping['column_index']}")
print(f"Expected: {ak_mapping['expected_value']}")

# Get accumulator configuration
ay_config = ACCUMULATOR_COLUMNS['AY']
print(f"Sources: {len(ay_config['sources'])}")

# Convert column letter to index
index = col_letter_to_index('AK')  # Returns 36
```

---

**Last Updated:** 2026-02-09
**Status:** ✓ Complete - All columns mapped and verified
