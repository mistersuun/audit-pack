# Diff.Caisse Column Decomposition - Complete Guide

## Overview

This directory contains comprehensive documentation on how the **Diff.Caisse** (cash discrepancy) column in the Excel RJ workbook is structured and how it should be decomposed into individual adjustment entries.

## Files in This Documentation

1. **diff_caisse_analysis.md** — High-level analysis of the Diff.Caisse column structure
   - Overview of Jour sheet (source) and Diff.Caisse# sheet (decomposition)
   - Current data from Feb 2026 RJ workbook
   - Monthly summary with all 25 days' variances
   - Implementation notes for RJ Natif

2. **diff_caisse_diagram.txt** — Visual ASCII diagrams
   - Data flow from Jour sheet to Diff.Caisse# sheet
   - 36-slot adjustment decomposition structure
   - Monthly variance summary table
   - Example adjustment entry pattern
   - Implementation roadmap (phases 1-5)

3. **diff_caisse_technical_spec.md** — Complete technical specification
   - Excel sheet structure and column definitions
   - Data model design for NightAuditSession
   - Frontend UI architecture and HTML templates
   - JavaScript functions for load/save/calculate
   - API endpoints with code examples
   - Validation rules and error handling
   - Storage strategy (JSON vs scalar columns)
   - Excel export function
   - Testing scenarios and edge cases

## Quick Summary

### What is Diff.Caisse?

The **Diff.Caisse** column (Column C in the Jour sheet) represents the daily cash discrepancy—the difference between:
- **Actual cash position** (from bank deposits, POS records, etc.)
- **Expected cash position** (from revenue calculations, opening balance, etc.)

### How is it Tracked?

The **Diff.Caisse#** sheet (Index 4) decomposes this discrepancy into:

| Component | Purpose |
|-----------|---------|
| **Column A** | Day number (1-25) |
| **Column B** | Total Diff.Caisse from Jour sheet |
| **Columns C-AL (36 slots)** | Individual adjustment entries (currently empty) |
| **Column AM** | Remaining unallocated balance |

### Current Status (Feb 2026)

- **Total days**: 25
- **Days with discrepancies**: 23 (92%)
- **Days with allocations entered**: 0 (0%)
- **Largest variance**: Day 25: +$866,165.21 (requires investigation)
- **Total month variance**: ±$854,837.54 (unresolved)

### Example: Day 24

```
Jour Sheet:
  Column C (Diff.Caisse) = $385.56

Diff.Caisse# Sheet:
  Column B (Total) = $385.56
  Columns C-AL (Adjustments) = [empty]
  Column AM (Remaining) = $385.56 (unallocated)
```

## For Developers Implementing RJ Natif

### Key Implementation Steps

1. **Add to database model** (`database/models.py`):
   ```python
   diff_caisse_adjustments = db.Column(db.Text)  # JSON array
   ```

2. **Create new tab** (rj_native.html):
   - "Diff.Caisse" as Tab 10 (between Jour and Quasimodo)
   - Form to add adjustment entries
   - Table to display entries with edit/delete options

3. **Add API endpoint** (routes/audit/rj_native.py):
   ```python
   POST /api/rj/native/save/diff_caisse
   ```

4. **Implement recalc function**:
   ```javascript
   recalcDiffCaisse() {
     // Sum all allocated amounts
     // Calculate remaining = total - allocated
     // Update UI with validation status
   }
   ```

5. **Add validation**:
   - Warn if remaining ≠ 0
   - Allow submission with acknowledgment
   - Store warning in validation_notes

### Data Model Design

**Recommended: JSON Array Structure**

```json
{
  "adjustments": [
    {
      "slot": 1,
      "reason": "Rounding error in Transelect",
      "amount": 150.00,
      "timestamp": "2026-02-27T14:32:15Z"
    },
    {
      "slot": 2,
      "reason": "Customer refund reversal",
      "amount": 235.56,
      "timestamp": "2026-02-27T14:35:22Z"
    }
  ],
  "remaining": 0.00,
  "last_updated": "2026-02-27T14:35:22Z"
}
```

This approach allows:
- Descriptive reasons for each adjustment
- Timestamp tracking for audit trail
- Flexibility for future enhancements
- Easy export to Excel or JSON

## For Auditors Using RJ Natif

### Workflow

1. **Open Diff.Caisse tab** after completing Jour tab
2. **Review total discrepancy** (automatically populated from Jour)
3. **Identify adjustment causes**:
   - Rounding errors
   - Transaction reversals
   - Unprocessed refunds
   - Banking timing issues
4. **Allocate each cause** to a slot (1-36) with:
   - Description/reason
   - Amount (positive or negative)
5. **Monitor remaining balance**:
   - Target: Remaining = $0.00 (fully decomposed)
   - Warning: Remaining ≠ 0 (unresolved discrepancy)
6. **Save and submit** when complete

### Business Rules

- **Balanced days**: Remaining = $0.00 ± $0.01 tolerance
- **Unresolved**: Remaining > $0.01 triggers warning, not error
- **Submission**: Can proceed even with unresolved balance
- **Validation**: Required for audit compliance

## Data Integration

### Connection to Other RJ Tabs

- **Jour** (source): Diff.Caisse value calculated from F&B, rooms, deposits, cards
- **Transelect**: May contain reversals contributing to discrepancies
- **Quasimodo**: Global reconciliation should align with Diff.Caisse
- **SD/Depot**: Rounding or timing issues may explain variances

### Excel Workbook References

- **File**: `/sessions/laughing-sharp-johnson/mnt/uploads/Rj 24-02-2026.xls`
- **Sheet Names**:
  - Index 4: Diff.Caisse# (decomposition data)
  - Index 9: jour (source of Diff.Caisse values)
  - Index 28: geac_ux (reference for adjustment categories)

## Known Issues & Anomalies

### Day 25: +$866,165.21 Variance
This is exceptionally large and requires investigation:
- Check opening balance (bal.ouv column)
- Verify Jour calculations
- Review transaction processing
- May indicate data entry error or system issue

### Days with Negative Variances
13 out of 23 discrepancy days are **negative** (cash shortage):
- Common: POS rounding errors, timing issues
- Review: Daily reconciliation procedures

## Testing

See `diff_caisse_technical_spec.md` Section 10 for:
- Test Case 1: Full allocation (remaining = $0)
- Test Case 2: Partial allocation (unresolved)
- Test Case 3: Over-allocation (validation error)
- Test Case 4: Negative variance handling

## Resources

- **Main Documentation**: `documentation/RJ/00_INDEX.md`
- **Jour Calculations**: `documentation/RJ/12_procedure_back_complete.md` (Phase X)
- **Excel Analysis**: `documentation/RJ/diff_caisse_diagram.txt`
- **Implementation Guide**: `documentation/RJ/diff_caisse_technical_spec.md`

---

**Last Updated**: 2026-02-27  
**Analyst**: Claude Code Analysis  
**Status**: Ready for implementation
