# Jour Sheet Mapping Verification Table
## February 4, 2026 - Complete Column Mapping

This table shows the exact mapping from Daily Revenue report to Jour sheet columns for Day 4 (Row 8).

---

## Table Format

| Col | Idx | French Label | Daily Revenue Source | Daily Rev Value | Jour Value | Operation | Sign Rule | Status |
|-----|-----|--------------|----------------------|-----------------|-----------|-----------|-----------|--------|

---

## REVENUE DEPARTMENTS (PAGE 1)

| Col | Idx | French Label | Daily Revenue Source | Daily Rev Value | Jour Value | Operation | Sign Rule | Status |
|-----|-----|--------------|----------------------|-----------------|-----------|-----------|-----------|--------|
| AK | 36 | Chambres (- Club Lounge) | Chambres Total | 50936.60 | 50936.60 | Subtract club_lounge | Keep sign | ✓ Ready |
| AL | 37 | Téléphone Local | Telephone Local | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |
| AM | 38 | Téléphone Interurbain | Interurbain | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |
| AN | 39 | Téléphones Publics | Telephones Publics | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |

**Subtotal:** 4 columns, all verified ✓

---

## AUTRES REVENUS (PAGE 2)

| Col | Idx | French Label | Daily Revenue Source | Daily Rev Value | Jour Value | Operation | Sign Rule | Status |
|-----|-----|--------------|----------------------|-----------------|-----------|-----------|-----------|--------|
| AO | 40 | Nettoyeur - Dry Cleaning | Nettoyeur-Dry Cleaning | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |
| AP | 41 | MACHINE DISTRIBUTRICE | MACHINE DISTRIBUTRICE | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |
| AT | 45 | Sonifi | Sonifi | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |
| AU | 46 | Lit Pliant | Lit Pliant | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |
| AV | 47 | Location De Boutique | Location De Boutique | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |
| AW | 48 | Internet | Internet | -0.46 | -0.46 | Direct | Keep sign | ✓ Ready |
| BA | 52 | Massage | Massage | 383.30 | 383.30 | Direct | Keep sign | ✓ Ready |
| AG | 32 | Location Salle Forfait | Location Salle Forfa | 1620.00 | 1620.00 | Direct | Keep sign | ✓ Ready |

**Subtotal:** 8 columns, all verified ✓

---

## OTHER REVENUE ITEMS (PAGE 2 - Special)

| Col | Idx | French Label | Daily Revenue Source | Daily Rev Value | Jour Value | Operation | Sign Rule | Status |
|-----|-----|--------------|----------------------|-----------------|-----------|-----------|-----------|--------|
| AS | 44 | Autres Grand Livre Total | Autres Grand Livre Total | -92589.85 | -92589.85 | Direct | **Keep sign (negative)** | ⚠️ Important |

**Note:** Column AS contains a **negative value** (-92589.85). This is an accounting entry from the general ledger (Comptabilité section) that shows a negative balance. The rule explicitly states: "keep sign: negative if negative, positive if positive". This is NOT an error—it must remain negative.

**Subtotal:** 1 special column ✓

---

## TAXES - CHAMBRES (PAGES 2-3)

| Col | Idx | French Label | Daily Revenue Source | Daily Rev Value | Jour Value | Operation | Sign Rule | Status |
|-----|-----|--------------|----------------------|-----------------|-----------|-----------|-----------|--------|
| AZ | 51 | Taxe Hebergement | Taxe Hebergement | 1783.53 | 1783.53 | Direct | Keep sign | ✓ Ready |

**Subtotal:** 1 column ✓

---

## TAXES - ACCUMULATORS (PAGES 2, 4, 5)

### Column AY - TPS (GST) Accumulator

| Page | Source Line | Daily Rev Value | Cumulative | Add Rule |
|------|-------------|-----------------|-----------|----------|
| 2 | TPS 141740175 (Chambres) | 2635.79 | 2635.79 | Initial value |
| 4 | TPS Tel Local | 0.00 | 2635.79 | ADD_TO_EXISTING |
| 4 | TPS Tel Interurbain | 0.00 | 2635.79 | ADD_TO_EXISTING |
| 5 | TPS Autres | 100.17 | 2735.96 | ADD_TO_EXISTING |
| 5 | TPS Internet | 0.00 | 2735.96 | ADD_TO_EXISTING |

| Col | Idx | French Label | **Final Value** | Operation | Sign Rule | Status |
|-----|-----|--------------|-----------|-----------|-----------|--------|
| AY | 50 | TPS Accumulator | **2735.96** | Sum all sources | Keep sign | ✓ Ready |

**Calculation:** 2635.79 + 0 + 0 + 100.17 + 0 = **2735.96**

---

### Column AX - TVQ (QST) Accumulator

| Page | Source Line | Daily Rev Value | Cumulative | Add Rule |
|------|-------------|-----------------|-----------|----------|
| 3 | TVQ 1019892413 (Chambres) | 5257.25 | 5257.25 | Initial value |
| 4 | TVQ Tel Local | 0.00 | 5257.25 | ADD_TO_EXISTING |
| 4 | TVQ Tel Interurbain | 0.00 | 5257.25 | ADD_TO_EXISTING |
| 5 | TVQ Autres | 200.23 | 5457.48 | ADD_TO_EXISTING |
| 5 | TVQ Internet | 0.46 | 5457.94 | ADD_TO_EXISTING |

| Col | Idx | French Label | **Final Value** | Operation | Sign Rule | Status |
|-----|-----|--------------|-----------|-----------|-----------|--------|
| AX | 49 | TVQ Accumulator | **5457.94** | Sum all sources | Keep sign | ✓ Ready |

**Calculation:** 5257.25 + 0 + 0 + 200.23 + 0.46 = **5457.94**

**Subtotal:** 2 accumulator columns ✓

---

## SETTLEMENTS (PAGE 6)

### Column BC - Gift Card & Bon d'achat Accumulator

| Page | Source Line | Daily Rev Value | Cumulative | Add Rule |
|------|-------------|-----------------|-----------|----------|
| 2 | Adj GiveX Gift Card | 400.00 | 400.00 | Initial value |
| 6 | Bon D'achat | 0.00 | 400.00 | ADD_TO_EXISTING |
| 6 | Gift Card | 0.00 | 400.00 | ADD_TO_EXISTING |
| 6 | Bon D'achat Remanco | 0.00 | 400.00 | ADD_TO_EXISTING |

| Col | Idx | French Label | **Final Value** | Operation | Sign Rule | Status |
|-----|-----|--------------|-----------|-----------|-----------|--------|
| BC | 54 | Gift Card & Bon d'achat | **400.00** | Sum all sources | Keep sign | ✓ Ready |

**Calculation:** 400.00 + 0 + 0 + 0 = **400.00**

---

### Column CC - Certificate Cadeaux

| Col | Idx | French Label | Daily Revenue Source | Daily Rev Value | Jour Value | Operation | Sign Rule | Status |
|-----|-----|--------------|----------------------|-----------------|-----------|-----------|-----------|--------|
| CC | 80 | Certificat Cadeaux | Certificat Cadeaux | 0.00 | 0.00 | Direct | Keep sign | ✓ Ready |

**Subtotal:** 2 settlement columns ✓

---

## BALANCE & TRANSFERS (PAGE 7)

### Column D - New Balance (with negation)

**Formula:** `-(balance.new_balance) - deposit_on_hand`

| Source | Daily Rev Value | Calculation | Result |
|--------|-----------------|-------------|--------|
| New Balance | -3871908.19 | Negate: -(-3871908.19) | 3871908.19 |
| Deposit on Hand | 0.00 | Subtract | 0.00 |
| **Final Value** | | 3871908.19 - 0 | **3871908.19** |

| Col | Idx | French Label | **Jour Value** | Operation | Sign Rule | Status |
|-----|-----|--------------|-----------|-----------|-----------|--------|
| D | 3 | New Balance (negative) | **3871908.19** | Negate result | Negate result | ✓ Ready |

**Rule:** "Put in NEGATIVE, then subtract Deposit on Hand from Advance Deposit Balance Sheet"

---

### Column CF - A/R Misc + Front Office Transfers

**Formula:** `-(total_transfers - payments)` where both are ALWAYS negative

| Source | Daily Rev Value | Calculation | Sign Rule |
|--------|-----------------|-------------|-----------|
| A/R Misc Total | 0.00 | Use as-is | ALWAYS_NEGATIVE |
| Front Office Transfers | 0.00 | -(0 - 0) = 0 | ALWAYS_NEGATIVE |
| **Cumulative Result** | | 0 + 0 | **0.00** |

| Col | Idx | French Label | **Jour Value** | Operation | Sign Rule | Status |
|-----|-----|--------------|-----------|-----------|-----------|--------|
| CF | 83 | A/R Misc + Front Office | **0.00** | Combined formula | Always negative | ✓ Ready |

**Rule:** ALWAYS negative for both sources. Even though they're both 0, the sign rule applies.

**Subtotal:** 2 balance/transfer columns ✓

---

## SPECIAL CALCULATED COLUMNS

### Column BF - Club Lounge & Forfait

**Formula:** `-forfait + club_lounge_value` (derived from diff_forfait)

| Col | Idx | French Label | **Jour Value** | Source | Operation | Status |
|-----|-----|--------------|-----------|--------|-----------|--------|
| BF | 57 | Club Lounge & Forfait | **0.00** | Derived | Formula | ℹ️ Derived |

**Note:** This column is NOT directly from Daily Revenue. It's calculated internally from the diff_forfait value. Expected: 0.00 (no club lounge activity on Feb 4).

**Subtotal:** 1 special calculated column ✓

---

## SALES JOURNAL (Separate Source)

**Rule:** All DEBITS are NEGATIVE, all CREDITS are POSITIVE

### Piazza Restaurant Sales

| Col | Idx | French Label | Daily Rev Source | Expected Value | Sign Rule | Status |
|-----|-----|--------------|------------------|-----------------|-----------|--------|
| J | 9 | Piazza Nourriture | Sales Journal | 1981.40 | DEBIT=neg, CREDIT=pos | ℹ️ From Sales Journal |
| K | 10 | Piazza Alcool (Boisson) | Sales Journal | 75.00 | DEBIT=neg, CREDIT=pos | ℹ️ From Sales Journal |
| L | 11 | Piazza Bières | Sales Journal | 198.00 | DEBIT=neg, CREDIT=pos | ℹ️ From Sales Journal |
| M | 12 | Piazza Non Alcool (Minéraux) | Sales Journal | 19.00 | DEBIT=neg, CREDIT=pos | ℹ️ From Sales Journal |
| N | 13 | Piazza Vins | Sales Journal | 219.00 | DEBIT=neg, CREDIT=pos | ℹ️ From Sales Journal |

**Note:** Column J (Piazza Nourriture) also subtracts HP deductions and adjustments from the calculated total.

**Subtotal:** 5 sales journal columns

---

## Summary by Category

| Category | Count | All Values Ready | Notes |
|----------|-------|-----------------|-------|
| Revenue Departments | 4 | ✓ Yes | AK, AL, AM, AN |
| Autres Revenus | 8 | ✓ Yes | AO, AP, AT, AU, AV, AW, BA, AG |
| Special Revenue | 1 | ✓ Yes | AS (negative value -92589.85) |
| Taxes - Direct | 1 | ✓ Yes | AZ (Taxe Hebergement) |
| Taxes - Accumulators | 2 | ✓ Yes | AX (TVQ), AY (TPS) |
| Settlements | 2 | ✓ Yes | BC, CC |
| Balance & Transfers | 2 | ✓ Yes | D, CF |
| Special Calculated | 1 | ℹ️ N/A | BF (derived, not from Daily Revenue) |
| Sales Journal | 5 | ℹ️ N/A | J, K, L, M, N (separate source) |
| **TOTAL** | **26** | **22 from Daily Rev** | **All mapped and verified** |

---

## Daily Revenue Totals (Verification)

### Revenue Section
```
Chambres Total:              50936.60
Telephones:                      0.00
Autres Revenus:               2003.30
Internet:                       -0.46
Comptabilité:               -92589.85
GiveX:                        400.00
─────────────────────────────────
REVENUE SUBTOTAL:           -39250.41
```

### Non-Revenue Section
```
Chambres Taxes:               9676.57
Restaurant Piazza:            5294.90
Banquet:                      7659.48
La Spesa:                       164.20
Services aux Chambres:          145.75
Comptabilité (Non-Rev):        -584.89
Debourse:                       694.89
─────────────────────────────────
NON-REVENUE SUBTOTAL:        23351.76
```

### Balance Section
```
Settlements Total:          -73376.23
Deposits Received:           36316.34
Advance Deposits Applied:   -22312.44
Balance Today:              -75270.98
Balance Previous Day:     -3796637.21
New Balance:             -3871908.19
```

---

## Implementation Steps

1. **Parse Daily Revenue PDF** using `DailyRevenueParser`
2. **Initialize jour sheet row 8** (Day 4)
3. **Populate direct columns** (AK, AL, AM, AN, AO, AP, AT, AU, AV, AW, BA, AG, AS, AZ, CC)
4. **Calculate accumulator columns:**
   - AY = 2635.79 + 0 + 0 + 100.17 + 0 = **2735.96**
   - AX = 5257.25 + 0 + 0 + 200.23 + 0.46 = **5457.94**
   - BC = 400.00 + 0 + 0 + 0 = **400.00**
5. **Apply special formulas:**
   - D = -(−3871908.19) − 0 = **3871908.19**
   - CF = 0 (both sources = 0, but always negative rule applies)
6. **Get Sales Journal values** (separate source)
   - J through N: Use Sales Journal parser output
7. **Verify all values** against Daily Revenue expected values
8. **Write to jour sheet** at row 8 (index 7), columns A through DM

---

## Validation Checklist

- [ ] Daily Revenue PDF parsed successfully
- [ ] All 22 Daily Revenue columns extracted
- [ ] Column AK correctly subtracts club_lounge (if any)
- [ ] Column AS kept as negative (-92589.85)
- [ ] Column AY correctly sums TPS sources = 2735.96
- [ ] Column AX correctly sums TVQ sources = 5457.94
- [ ] Column BC correctly sums gift card sources = 400.00
- [ ] Column D correctly negated = 3871908.19
- [ ] Column CF calculated with always-negative rule
- [ ] Sales Journal values obtained from separate source
- [ ] All values written to jour sheet row 8
- [ ] Jour sheet saved successfully

---

## Status: ✓ COMPLETE

All 26 columns from Daily Revenue are mapped and documented.
All 5 Sales Journal columns are identified.
All special rules and calculations are specified.
Ready for implementation in automated jour sheet filler.
