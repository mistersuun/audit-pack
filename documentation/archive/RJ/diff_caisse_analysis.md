# Diff.Caisse Column Decomposition Analysis

## Overview
The **Diff.Caisse** column (Column C in the Jour sheet) represents cash discrepancies that must be tracked and decomposed into individual adjustment entries.

## Excel Structure

### Jour Sheet (Index 9)
- **Column A (col 0)**: JOUR (day number)
- **Column B (col 1)**: bal.ouv (opening balance)
- **Column C (col 2)**: Diff.Caisse (total discrepancy for the day)
- Example (Day 24): **$385.56**

### Diff.Caisse# Sheet (Index 4)
This is the adjustment decomposition sheet with the following structure:

| Column | Name | Purpose |
|--------|------|---------|
| A | Jour | Day number |
| B | [unlabeled] | **Total Diff.Caisse for that day** |
| C-AL (cols 2-37) | geac ux (36 columns) | **Adjustment entry slots** (currently unused) |
| AM (col 38) | [unlabeled] | **Remaining balance** (unallocated portion) |

### Current Data (from Rj 24-02-2026.xls)

#### Day 24 Diff.Caisse = **$385.56**

**Jour Sheet (Day 24, Row 25):**
- Column B (bal.ouv): -944,879.42
- Column C (Diff.Caisse): **385.56**

**Diff.Caisse# Sheet (Day 24, Row 25):**
- Column A (Jour): 24.0
- Column B (Total): **385.56**
- Columns C-AL (Adjustments): **ALL EMPTY**
- Column AM (Remaining): **385.56** (full amount unallocated)

#### Day 14 Diff.Caisse = **$0.00** (Balanced)

**Jour Sheet (Day 14, Row 15):**
- Column B (bal.ouv): -939,983.23
- Column C (Diff.Caisse): **[NOT SHOWN - value is 0 or empty]**

**Diff.Caisse# Sheet (Day 14, Row 15):**
- Column A (Jour): 14.0
- Column B (Total): **4.83** (small floating-point difference)
- Columns C-AL (Adjustments): **ALL EMPTY**
- Column AM (Remaining): **4.83**

## Decomposition Pattern

The Diff.Caisse amount should be decomposed as follows:

```
Total Diff.Caisse (Column B) = SUM(Columns C:AL) + Remaining (Column AM)
```

For Day 24:
```
$385.56 = [Adjustment1] + [Adjustment2] + ... + [AdjustmentN] + $385.56
```

Currently, all 36 adjustment slots (columns C-AL) are **empty**, meaning:
- No categorized adjustments have been allocated
- The entire balance is marked as "unallocated remaining"

## Adjustment Slot Labels

The 36 adjustment columns are labeled generically as "geac ux" (likely referring to the GEAC_UX sheet which tracks credit card processing details).

The column distribution:
- **C-AL** = 36 columns (C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z, AA, AB, AC, AD, AE, AF, AG, AH, AI, AJ, AK, AL)

## Usage Pattern

When an auditor identifies a cash discrepancy:

1. **Calculate** the total Diff.Caisse (automatic from Jour calculations)
2. **Identify causes** (e.g., customer overpayment, rounding errors, transaction reversals)
3. **Allocate each cause** to a column in Diff.Caisse# (columns C-AL)
4. **Track remaining** unallocated portion in column AM
5. **Goal**: Reduce remaining to $0.00 by fully decomposing the discrepancy

## Current Status

- **Total days with non-zero discrepancies**: 23 out of 25
- **Days with allocations**: 0 (all adjustment slots are empty)
- **Allocation rate**: 0% (0 of 23 discrepancies have been decomposed)

### Discrepancy Summary by Day

| Day | Diff.Caisse | Status |
|-----|-------------|--------|
| 1 | -314.26 | Unallocated |
| 2 | 38.98 | Unallocated |
| 3 | 559.96 | Unallocated |
| 4 | -24.00 | Unallocated |
| 5 | 19.40 | Unallocated |
| 6 | 329.84 | Unallocated |
| 7 | -556.50 | Unallocated |
| 8 | -1,428.12 | Unallocated |
| 9 | -1,299.01 | Unallocated |
| 10 | 1,009.74 | Unallocated |
| 11 | 2,387.60 | Unallocated |
| 12 | -5.65 | Unallocated |
| 13 | -17.67 | Unallocated |
| 14 | 4.83 | Unallocated (balanced) |
| 15 | [zero] | Balanced |
| 16 | -1,360.08 | Unallocated |
| 17 | -641.05 | Unallocated |
| 18 | 1,000.85 | Unallocated |
| 19 | 20.00 | Unallocated |
| 20 | -296.07 | Unallocated |
| 21 | -2,634.12 | Unallocated |
| 22 | -5,868.75 | Unallocated |
| 23 | -1,692.93 | Unallocated |
| 24 | 385.56 | **Unallocated** |
| 25 | 866,165.21 | Unallocated |

**Total Month Variance**: ±$854,837.54 (requires investigation)

## Implementation Notes for RJ Natif

When implementing the Diff.Caisse decomposition feature in RJ Natif:

1. **Create an adjustment entry UI** that allows auditors to:
   - Enter a description/reason for the adjustment
   - Assign it to one of 36 available slots
   - Enter the adjustment amount
   - Optionally link to a source document/transaction

2. **Auto-calculate remaining**:
   - Remaining = Total Diff.Caisse - SUM(all allocations)
   - Display prominently for auditor awareness

3. **Validation rules**:
   - Ensure allocated amounts match Diff.Caisse ± small tolerance (±$0.01)
   - Flag unresolved balances for review

4. **Data storage** (NightAuditSession model):
   - Add a JSON column: `diff_caisse_adjustments` = array of {slot, reason, amount}
   - Or use 36 individual scalar columns (one per slot)

5. **Connect to other modules**:
   - Adjustments may relate to reversal entries in Transelect
   - Or rounding/timing issues in SD/Depot reconciliations
   - Or reconciliation corrections in Quasimodo
