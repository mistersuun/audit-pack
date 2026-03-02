# X20, ESCOMPTE, AND DIFF.CAISSE: COMPLETE RELATIONSHIP ANALYSIS

## Executive Summary

**X20** (the NET card total in column C27 of the TRANSELECT sheet) is calculated as:
```
X20 = Bank Total - Merchant Fees
    = C21 - C26
    = C21 × (1 - C25%)
```

**ESCOMPTE** (merchant fees):
```
Escompte $ (C26) = Bank Total (C21) × Escompte % (C25)
```

**VARIANCE** (C24) is a separate reconciliation check:
```
Variance = Bank (C21) - POS (C23)
```

**DIFF.CAISSE** is completely independent and relates to cash, not cards.

---

## Sheet Structure: TRANSELECT (Sheet 25)

| Column | Label | Description |
|--------|-------|-------------|
| C1-C5 | Dept Totals | BAR A, BAR B, BAR C, SPESA D, ROOM E |
| C6-C20 | Terminal Totals | Individual POS terminal totals |
| C21 | **TOTAL 1** | **Bank Total** (sum of terminals, what bank reported) |
| C22 | — | Blank |
| C23 | **POSITOUCH** | **POS Total** (what POS system reported) |
| C24 | **VARIANCE** | **Bank - POS** (reconciliation check) |
| C25 | **ESCOMPTE %** | Merchant fee percentage by card type |
| C26 | **$ escompte** | **Merchant fee in dollars** (= C21 × C25%) |
| C27 | **NET** | **X20 = C21 - C26** (depositable amount) |

---

## Formula Verification: FEB 24 & FEB 23

### FEB 24 - TOTAL ROW (Row 13)

| Metric | Value | Formula |
|--------|-------|---------|
| Bank (C21) | $7,659.81 | — |
| POS (C23) | $7,156.51 | — |
| Variance (C24) | **$503.30** | = C21 - C23 = 7659.81 - 7156.51 |
| Escompte % (C25) | — | Varies by card |
| Escompte $ (C26) | **$117.92** | = SUM(Bank × Card%) |
| X20 / NET (C27) | **$7,541.89** | = C21 - C26 = 7659.81 - 117.92 |

### FEB 24 - INDIVIDUAL CARDS

| Card | Bank(C21) | Esc%(C25) | Esc$(C26) | X20(C27) | Check |
|------|-----------|-----------|-----------|----------|-------|
| DEBIT | $697.14 | 0.00% | $0.00 | $697.14 | ✓ |
| VISA | $3,762.42 | 1.75% | $65.84 | $3,696.58 | ✓ |
| MASTER | $2,618.03 | 1.40% | $36.65 | $2,581.38 | ✓ |
| DISCOVER | $0.00 | 2.80% | $0.00 | $0.00 | ✓ |
| AMEX | $582.22 | 2.65% | $15.43 | $566.79 | ✓ |
| **TOTAL** | **$7,659.81** | — | **$117.92** | **$7,541.89** | ✓ |

### FEB 23 - TOTAL ROW (Row 13)

| Metric | Value | Formula |
|--------|-------|---------|
| Bank (C21) | $4,547.51 | — |
| POS (C23) | $6,172.50 | — |
| Variance (C24) | **-$1,624.99** | = C21 - C23 = 4547.51 - 6172.50 |
| Escompte % (C25) | — | Varies by card |
| Escompte $ (C26) | **$63.44** | = SUM(Bank × Card%) |
| X20 / NET (C27) | **$4,484.07** | = C21 - C26 = 4547.51 - 63.44 |

### FEB 23 - INDIVIDUAL CARDS

| Card | Bank(C21) | Esc%(C25) | Esc$(C26) | X20(C27) | Check |
|------|-----------|-----------|-----------|----------|-------|
| DEBIT | $851.45 | 0.00% | $0.00 | $851.45 | ✓ |
| VISA | $2,271.97 | 1.75% | $39.76 | $2,232.21 | ✓ |
| MASTER | $1,124.93 | 1.40% | $15.75 | $1,109.18 | ✓ |
| DISCOVER | $0.00 | 2.80% | $0.00 | $0.00 | ✓ |
| AMEX | $299.16 | 2.65% | $7.93 | $291.23 | ✓ |
| **TOTAL** | **$4,547.51** | — | **$63.44** | **$4,484.07** | ✓ |

---

## The Variance (C24) Does NOT Affect X20

**Critical finding:** The Variance (Bank - POS difference) is a diagnostic metric only.

- It does NOT reduce X20
- It does NOT flow into Quasimodo or cash reconciliation
- It is simply a way to track where the discrepancy lies

**Why the variance exists:**
- FEB 24: Bank reported $503.30 MORE than POS (possibly pending deposits or timing)
- FEB 23: Bank reported $1,624.99 LESS than POS (could be refunds, voids, or POS system issues)

**What matters for reconciliation:** Only X20 ($7,541.89 on Feb 24, $4,484.07 on Feb 23) is used in Quasimodo to verify against cash + other sources.

---

## The DIFF.CAISSE Mystery (FEB 23)

From the JOUR sheet, row 24, column C:
```
Diff.Caisse = -$1,692.93
```

**Tested relationships:**
- ✗ Diff.Caisse ≠ Variance (-$1,624.99)
- ✗ Diff.Caisse ≠ Escompte ($63.44)
- ✗ Diff.Caisse ≠ Variance + Escompte (-$1,688.43)
- ✗ Diff.Caisse ≠ X20 ($4,484.07)

**Conclusion:** Diff.Caisse is **completely independent** from the card payment data.

It is calculated from:
1. **Actual cash in safe** (physical count)
2. **Expected cash** (previous day balance + today's F&B cash sales)
3. **Variance** = Actual - Expected

The large negative value (-$1,692.93) suggests either:
- An error in cash counting
- A large cash withdrawal or deposit not recorded
- A recording discrepancy between the cash register and the audit

**This is separate from and independent of the TRANSELECT card variance.**

---

## Key Business Rules

1. **Merchant fees only apply to card brands with non-zero rates:**
   - DEBIT: 0% (no fee)
   - VISA: 1.75%
   - MASTER: 1.40%
   - AMEX: 2.65%
   - DISCOVER: 2.80% (but rarely used)

2. **X20 is the official card total for reconciliation:**
   - Used in Quasimodo to check: Cards + Cash = Total Revenue
   - The variance is informational only
   - Merchant fees reduce the deposited amount but are known costs

3. **Diff.Caisse and X20 are independent reconciliations:**
   - Diff.Caisse: Cash variance in the safe
   - X20: Card net receipts after fees
   - Both should be close to zero (or explained) but calculated separately

---

## Implementation Notes for RJ Natif

When building the Transelect tab in the web app:

1. **Bank Total (C21):** Sum of all terminal subtotals
2. **POS Total (C23):** Read from Lightspeed export
3. **Variance (C24):** Automatically calculate = C21 - C23 (for diagnostics)
4. **Escompte % (C25):** Card-type-specific fixed rates (DEBIT=0%, VISA=0.0175, MASTER=0.014, AMEX=0.0265, DISCOVER=0.028)
5. **Escompte $ (C26):** Automatically calculate = C21 × C25% (per card, sum for total)
6. **X20 / NET (C27):** Automatically calculate = C21 - C26 (this is what goes into Quasimodo)

The Variance should be **displayed** (for troubleshooting) but **not used** in downstream calculations.

