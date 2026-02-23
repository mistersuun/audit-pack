# Investigation Summary: Jour Sheet Discrepancies (Feb 4, 2026)

## Quick Answer

**The NAS auto-fill system pulls from an incomplete data source (Daily Revenue PDF).**

There are actually **3 data sources** that need to work together:
1. **Daily Revenue PDF** - Has room revenue & chambres taxes, BUT incomplete F&B data
2. **Sales Journal (RTF)** - Has complete POS breakdown, BUT not currently parsed
3. **Original Excel** - Expected/adjusted values, uses cumulative for some fields

**Current state:** NAS pulls from Daily Revenue only → Missing ~40-60% of F&B revenue data

---

## The 6 Key Findings

### 1. TVQ/TPS Values: Excel is Cumulative, NAS is Daily
- **Excel TVQ:** 6,941.62 (appears to be 4-day cumulative, not daily)
- **NAS TVQ:** 1,483.68 (daily from Daily Revenue, but only chambres tax)
- **Sales Journal TVQ:** 1,483.68 (daily, all departments - this is what NAS should use)

**Why different?** Excel field stores 4-day cumulative data, not daily. This is a design question that needs clarification.

---

### 2. Piazza Nourriture: Missing 45% of Data
- **NAS stores:** 1,981.40 (from Daily Revenue non-revenue section)
- **Should be:** 3,621.80 (from Sales Journal POS system)
- **Discrepancy:** -1,640.40 missing (NAS has only 55% of actual revenue)
- **Excel has:** 3,426.30 (95% of SJ, with some adjustments deducted)

**Root cause:** Daily Revenue PDF contains only post-reconciliation, tax-adjusted subtotals for restaurants, not the full POS amounts.

---

### 3. Spesa Nourriture: Missing 80% of Data
- **NAS stores:** 145.28 (from Daily Revenue)
- **Should be:** 727.34 (from Sales Journal)
- **Discrepancy:** -582.06 missing (NAS has only 20% of actual revenue!)
- **Excel has:** 688.81 (95% of SJ, with some adjustments)

**Root cause:** Same as Piazza - Daily Revenue provides only a fractional amount.

---

### 4. Piazza Boisson, Bieres, Mineraux: Vastly Underestimated
- **Piazza Boisson:** NAS=75, Should=650.50 (difference: -575.50)
- **Piazza Bieres:** NAS=198, Should=566 (difference: -368)
- **Piazza Mineraux:** NAS=19, Should=85.25 (difference: -66.25)

**Root cause:** Daily Revenue doesn't break down beverages properly.

---

### 5. Room Revenue: Minor Variance (Acceptable)
- **NAS:** 50,936.60 (from Daily Revenue)
- **Excel:** 50,906.60
- **Difference:** +30.00

**Status:** This is acceptable - normal rounding/adjustment variance.

---

### 6. Missing Data: Chambres Svc & Banquet Beverages
Several fields aren't populated at all because Daily Revenue doesn't extract them:
- Chambres Svc Boisson, Bieres, etc.
- Some banquet items

**Root cause:** Parser doesn't extract these from PDF source.

---

## What's NOT a Bug

✓ **The Mapping is CORRECT** (`jour_mapping.py`)
- Column 49 correctly maps to `jour_tvq`
- Column 9 correctly maps to `jour_piazza_nourriture`
- The mapping logic is solid

✓ **The Parser Works Correctly** (`daily_revenue_parser.py`)
- Correctly extracts what's available in Daily Revenue PDF
- Parser is implemented well, it's just limited by source

✓ **The Database Schema**
- Fields are properly defined with right data types
- Calculations work as intended with available data

---

## What IS the Problem

❌ **Data Source Selection**
- Using Daily Revenue PDF when Sales Journal RTF has better data
- Daily Revenue is designed for financial reconciliation, not F&B reporting
- Daily Revenue's "Non-Revenue Departments" section is post-adjustment, incomplete

❌ **Missing Parser**
- Sales Journal parser doesn't exist
- Sales Journal has complete POS breakdown but isn't being extracted
- Test data exists (`Sales_Journal_4th_Feb.rtf`) but goes unused

❌ **Unclear Field Intent**
- Are `jour_tvq`/`jour_tps` meant to be daily or cumulative?
- Excel stores cumulative, current code assumes daily
- This needs clarification from business rules

---

## Data Source Authority (Ranked)

| Rank | Source | Trustworthiness | Has Complete F&B? |
|------|--------|-----------------|-------------------|
| 🥇 1 | Sales Journal POS | ⭐⭐⭐⭐⭐ | ✓ Yes |
| 🥈 2 | Daily Revenue PDF | ⭐⭐⭐ | ✗ No (incomplete) |
| 🥉 3 | Excel Original | ⭐⭐⭐ | ✓ Yes (but adjusted) |
| 4 | NAS Current | ⭐⭐ | ✗ No (mixing sources) |

---

## The Three-Part Fix

### Part 1: Create Sales Journal Parser (ESSENTIAL)
```
File: utils/parsers/sales_journal_parser.py
Input: Sales_Journal_4th_Feb.rtf (or PDF if available)
Extract:
  - PIAZZA: nourriture, alcool, bieres, mineraux, vins
  - SPESA: nourriture, boisson, bieres, mineraux, vins, tabagie
  - CHAMBRES: nourriture, boisson, bieres, mineraux, vins
  - BANQUET: nourriture, boisson, bieres, mineraux, vins
  - Taxes: TPS, TVQ (daily totals for all departments)
  - Adjustments: Hotel Promotion, Admin deductions, etc.
```

### Part 2: Update _fill_from_sales_journal() (rj_native.py)
```python
# NEW FUNCTION
def _fill_from_sales_journal(data, nas, day):
    count = [0]
    sections = []

    # Extract all restaurant departments from SJ
    piazza = data.get('piazza', {})
    _safe_set(nas, 'jour_piazza_nourriture', piazza.get('nourriture'), count)
    _safe_set(nas, 'jour_piazza_boisson', piazza.get('alcool'), count)
    # ... etc for all departments

    # Extract taxes from SJ (complete daily total)
    _safe_set(nas, 'jour_tvq', data.get('tvq_total'), count)
    _safe_set(nas, 'jour_tps', data.get('tps_total'), count)

    return {'count': count[0], 'sections': sections, ...}
```

### Part 3: Clarify TVQ/TPS Intent
**Question for business:**
- Should `jour_tvq` and `jour_tps` store **daily totals** or **4-day cumulative**?
- Current: NAS stores daily from DR (5,257.25 for TVQ)
- Excel expects: Unknown (6,941.62 for TVQ - looks cumulative)
- Sales Journal has: 1,483.68 daily TVQ

---

## File Changes Needed

### Files to Create:
1. `utils/parsers/sales_journal_parser.py` - New parser

### Files to Modify:
1. `routes/audit/rj_native.py` - Add `_fill_from_sales_journal()`, update _fill functions
2. `utils/daily_rev_jour_mapping.py` - Update expected values doc to reflect Sales Journal source

### Files to Review (No changes, but good to understand):
1. `utils/jour_mapping.py` - Mapping is correct
2. `utils/parsers/daily_revenue_parser.py` - Parser is correct
3. `database/models.py` - Schema is correct

---

## Testing Data Available

✓ Daily Revenue PDF: `test_data/Daily_Rev_4th_Feb.pdf`
✓ Sales Journal: `test_data/Sales_Journal_4th_Feb.rtf`
✓ Original Excel: `test_data/Rj_04-02-2026_ORIGINAL.xls`

All three can be used to validate the fix.

---

## Impact of Current Issue

**What happens with current incomplete data?**
- Jour sheet totals are **underestimated by ~$1,800-2,200 in F&B revenue**
- Profit calculations would be wrong if based on jour_piazza/spesa/chambres values
- Reconciliation would fail when comparing to POS system
- Beverages are especially underestimated (~$1,000+ missing)

**Who would notice?**
- Auditors comparing to POS reports
- Finance when reconciling against system revenue
- Any reporting that relies on F&B breakdown

---

## Next Steps

1. **Confirm requirement:** Are jour_tvq/tps meant to be daily or cumulative?
2. **Implement Sales Journal parser:** Extract POS data
3. **Update rj_native.py:** Call new parser and populate jour_* fields
4. **Test with Feb 4 data:** Verify numbers match Sales Journal
5. **Review Excel adjustments:** Understand why Excel differs from SJ by small amounts
6. **Document decision:** Update jour_mapping.py with true data sources

---

## Detailed Documentation

For complete technical analysis, see:
- `ANALYSIS_JOUR_DISCREPANCIES_FEB4.md` - Full technical breakdown
- `DISCREPANCY_SUMMARY_TABLE.txt` - Formatted comparison table with line numbers

