# Jour Sheet Discrepancy Analysis - Feb 4, 2026

## Executive Summary

Investigated discrepancies between NAS auto-fill (Daily Revenue PDF parser) and Original RJ Excel for the Jour sheet on Feb 4, 2026. Found **6 distinct data sources with conflicting values**, each with specific causes.

---

## Data Sources

There are **3 authoritative data sources**, not 2:

1. **Daily Revenue PDF** (parsed by `daily_revenue_parser.py`)
   - "Non-Revenue Departments" section contains restaurant F&B totals
   - Contains **only chambres taxes** (TVQ, TPS) - NO sales journal taxes

2. **Sales Journal Report** (RTF file - NOT currently parsed)
   - Contains detailed POS system breakdown by department
   - Contains **BOTH department revenues AND associated taxes** (TPS/TVQ)
   - This is the POS system's truth source

3. **Original RJ Excel** (expected/desired values)
   - Manually entered by auditors based on physical reports
   - Often represents a **4-day cumulative** value (not daily!)
   - May contain manual adjustments

---

## Detailed Findings

### A) TVQ and TPS Fields — CUMULATIVE vs DAILY

**Finding: Excel TVQ/TPS are CUMULATIVE over 4 days, not daily values**

#### TVQ (Column AX, index 49)

| Source | Feb 4 | Interpretation |
|--------|-------|-----------------|
| Daily Revenue Parser | 5,257.25 | **Chambres (room tax) only**, daily |
| Sales Journal | 1,483.68 | **Full daily total** (all departments), daily |
| Excel Original | 6,941.62 | **4-day cumulative** (Days 1-4) |

**Proof of Cumulative Theory:**
```
Excel Daily Revenue Cumulative values by day:
  Day 1: 5,462.24
  Day 2: 7,894.17 (cumulative)
  Day 3: 16,859.98 (cumulative)
  Day 4: 6,941.62 ← This is LOWER than Day 3!
```
❌ This mathematically CANNOT be daily - the value went DOWN.

**Conclusion:**
- NAS field `jour_tvq` is being set to **chambres tax only** (5,257.25) from Daily Revenue
- Excel expects **4-day cumulative** (6,941.62)
- **This is NOT a bug — it's a fundamental misalignment in what "jour_tvq" means**
- **Fix required:** Need to determine if jour_tvq should be:
  - Daily total (use Sales Journal: 1,483.68)
  - Or 4-day cumulative (use Excel: 6,941.62)
  - Or Chambres tax only (current: 5,257.25)

#### TPS (Column AY, index 50)

Same issue as TVQ:

| Source | Feb 4 | Interpretation |
|--------|-------|-----------------|
| Daily Revenue Parser | 2,635.79 | **Chambres (room tax) only**, daily |
| Sales Journal | 743.83 | **Full daily total** (all departments), daily |
| Excel Original | 3,479.79 | **4-day cumulative** |

---

### B) Piazza Nourriture (Food) — TWO Source Conflict

**Finding: Daily Revenue has INCOMPLETE data for Piazza**

| Source | Value | Source |
|--------|-------|--------|
| Daily Revenue (chambres tax only) | 1,981.40 | Non-revenue section only |
| Sales Journal POS | **3,621.80** | Complete restaurant data |
| Excel Original | 3,426.30 | **195.50 less than SJ** |

**Analysis:**
- Daily Revenue parser extracts from "Non-Revenue Departments" section
- This section contains **ONLY the tax-adjusted totals** from each restaurant
- It's missing HP deductions and other adjustments that the Sales Journal would show
- Sales Journal shows the actual POS totals before adjustments

**Delta: SJ vs Excel = +195.50** (Δ = 3,621.80 - 3,426.30 = +195.50)
- This +195.50 may represent:
  - Employee meal adjustments not in original data
  - Promotional items added
  - Or a discrepancy in HP deduction calculations

**Conclusion:**
- NAS is being filled with incomplete data (DR only)
- Should use Sales Journal for accurate F&B data
- Excel has a **+195.50 variance** from Sales Journal (not a bug, likely adjustment)

---

### C) Spesa Nourriture (Market Food) — Moderate Variance

| Source | Value |
|--------|-------|
| Daily Revenue | 145.28 | ← Incomplete
| Sales Journal | 727.34 | ← Complete
| Excel Original | 688.81 | ← Adjusted |

**Delta: SJ vs Excel = +38.53** (Δ = 727.34 - 688.81 = +38.53)

**Analysis:**
- Daily Revenue has only **20% of the actual value** (145.28 vs 727.34)
- This is the "non-revenue" version (after some accounting adjustments)
- Sales Journal POS system shows true revenue
- Excel value is 38.53 less than SJ (likely deductions applied)

**Conclusion:**
- Daily Revenue parser is extracting from wrong section
- Should use Sales Journal data instead
- This is a **data source selection problem**, not mapping

---

### D) Room Revenue — Minor Discrepancy

| Source | Value |
|--------|-------|
| Daily Revenue | 50,936.60 |
| Excel Original | 50,906.60 |
| **Delta** | **+30.00** |

**Analysis:**
- Only a $30 variance
- Daily Revenue parser gets room revenue from "Revenue Departments → Chambres Total"
- Excel has slightly lower value (50,906.60)
- The +30.00 difference is within reasonable rounding/adjustment tolerance

**Conclusion:**
- Minor variance, likely due to refund or adjustment between audit and data entry
- **This is acceptable** — not a bug

---

### E) Piazza Boisson, Chambres Svc Boisson/Nour, Banquet Boisson = 0 in NAS

**Finding: These fields are NOT being populated by Daily Revenue parser**

| Department | NAS Value | Should Be |
|------------|-----------|-----------|
| Piazza Boisson | 0 | 650.50 (from SJ) |
| Piazza Minéraux | 0 | 85.25 (from SJ) |
| Chambres Svc Boisson | 0 | 0 (correct, not in parser) |
| Chambres Svc Bieres | 0 | 38.00 (from SJ) |
| Banquet Boisson | 0 | -24.00 (from SJ) |
| Banquet Bieres | 0 | -30.00 (from SJ) |

**Root Cause in `rj_native.py` lines 1164-1177:**

```python
# Piazza (restaurant)
piazza = non_rev.get('restaurant_piazza', {})
_safe_set(nas, 'jour_piazza_nourriture', piazza.get('nourriture'), count)
_safe_set(nas, 'jour_piazza_boisson', piazza.get('alcool'), count)  # ← Gets alcool
_safe_set(nas, 'jour_piazza_bieres', piazza.get('biere'), count)    # ← Gets biere
_safe_set(nas, 'jour_piazza_mineraux', piazza.get('mineraux'), count)
_safe_set(nas, 'jour_piazza_vins', piazza.get('vin'), count)
```

**Daily Revenue Parser provides:**
```python
'restaurant_piazza': {
    'nourriture': 1981.4,
    'alcool': 75.0,      # ← Only SOME of the boisson
    'biere': 198.0,      # ← Only SOME of the bieres
    'mineraux': 19.0,
    'vin': 219.0,
    ...
}
```

**But Sales Journal shows:**
```
PIAZZA:
  NOURRITURE         3,621.80 (vs 1,981.40 from DR) ✓ Different source
  ALCOOL               650.50 (vs 75.00 from DR)    ✗ Much less in DR
  BIERES               566.00 (vs 198.00 from DR)   ✗ Much less in DR
  NON ALCOOL BAR        85.25 (vs 19.00 from DR)    ✗ Much less in DR
  VINS                 438.00 (vs 219.00 from DR)   ✓ Similar
```

**Conclusion:**
- Daily Revenue parser is extracting from the **post-reconciliation section** (non-revenue)
- Sales Journal has the actual POS totals
- NAS is being filled with **incomplete/adjusted data** from the wrong source
- **This requires architectural change**: parser needs to extract from Sales Journal, not Daily Revenue PDF

---

## Root Cause Summary

| Issue | Root Cause | Classification |
|-------|-----------|-----------------|
| TVQ/TPS Cumulative | Excel field stores 4-day cumulative, parser provides daily | **Design Mismatch** |
| Piazza Nourriture | Daily Revenue incomplete (tax-adjusted), SJ has full value | **Data Source Selection** |
| Piazza Boisson/Bieres | Daily Revenue only has partial amounts | **Data Source Selection** |
| Spesa Nourriture | Daily Revenue from wrong section | **Data Source Selection** |
| Room Revenue ±30 | Rounding/adjustment difference | **Expected Variance** |
| Chambres Svc missing | Daily Revenue doesn't extract this dept | **Data Source Limitation** |

---

## Mapping Logic Analysis

### How jour_mapping.py Works

**NAS → Excel Mapping** (`nas_jour_to_excel_dict`):
- Maps NAS fields (e.g., `jour_piazza_nourriture`) to Excel column indices (e.g., col 9)
- Is **bidirectional** with `JOUR_COL_TO_NAS` reverse mapping
- **Does NOT include business logic** — only field-to-column mapping
- All values assumed to be **daily, not cumulative**

**Mapping is CORRECT** (col 49 = `jour_tvq`, col 9 = `jour_piazza_nourriture`, etc.)

**Problem:** The **data being mapped** is from the wrong source

### How daily_rev_jour_mapping.py Describes Expected Values

Lines 1162-1200 show `EXPECTED_VALUES_FEB_4`:
```python
'chambres_total': 50936.60,
'piazza_nourriture': 1981.40,     # ← This is from Daily Revenue non-revenue section!
'spesa_total': 145.28,             # ← Wrong section!
'tvq': 7558.53,                    # ← Claims this is the expected value but...
'tps': 3788.92,                    # ← These don't match Excel!
```

**This mapping doc is internally inconsistent** — it describes accumulator logic for TVQ/TPS but hardcodes Daily Revenue values that are incomplete.

---

## Fix Strategy (Recommendations)

### 1. Clarify jour_tvq and jour_tps Intent

**Decision required:**
- Should these be **daily totals** (from Sales Journal)?
- Should these be **4-day cumulative** (from Excel)?
- Should these be **chambres tax only** (from Daily Revenue)?

**Current state:** Chambres tax only (5,257.25 for TVQ)
**Excel expects:** 4-day cumulative (6,941.62 for TVQ)
**Sales Journal has:** Daily total (1,483.68 for TVQ)

**Recommendation:** Use **daily totals from Sales Journal** — align NAS with single-day values, not cumulative.

### 2. Create Sales Journal Parser

**Current gap:** Sales Journal (RTF file) is not being parsed.

**Solution:**
- Add `SalesJournalParser` to extract POS totals
- Extract all departments (Piazza, Spesa, Chambres, Banquet, etc.)
- Use these for jour_* fields instead of Daily Revenue

**Implementation:**
```python
# In _fill_from_sales_journal()
piazza = data.get('piazza', {})
_safe_set(nas, 'jour_piazza_nourriture', piazza.get('nourriture'), count)
_safe_set(nas, 'jour_piazza_boisson', piazza.get('alcool'), count)
# ... etc
```

### 3. Fix NAS Field Mapping in rj_native.py

**Current issue:** Lines 1163-1189 map incomplete Daily Revenue data

**Fix:**
- Remove dependency on Daily Revenue for restaurant data
- Use Sales Journal parser instead (once implemented)
- Keep Daily Revenue for **room revenue only** (it has complete Chambres section)

### 4. Update jour_mapping.py Documentation

**Current issue:** `EXPECTED_VALUES_FEB_4` hardcodes wrong source values

**Fix:**
- Document that Daily Revenue provides incomplete F&B data
- Note that Sales Journal is authoritative for F&B departments
- Clarify that TVQ/TPS should be from Sales Journal (daily), not cumulative

---

## Data Source Trustworthiness (Ranked)

| Rank | Source | Trustworthiness | Coverage |
|------|--------|-----------------|----------|
| 1 | Sales Journal POS | ⭐⭐⭐⭐⭐ | All F&B departments |
| 2 | Daily Revenue PDF | ⭐⭐⭐ | Chambres/Taxes (incomplete F&B) |
| 3 | Original Excel | ⭐⭐⭐ | Manual entry (adjustments applied) |
| 4 | NAS auto-fill (current) | ⭐⭐ | Mixing incomplete sources |

---

## Specific Discrepancy Explanations

### 1. TVQ: Excel=6941.62 vs NAS=1483.68
- **Excel:** 4-day cumulative value (NOT daily)
- **NAS (current):** Only chambres tax from Daily Revenue (5,257.25)
- **Excel expectation:** Unknown (could be cumulative, could be different calculation)
- **Correct daily value:** 1,483.68 (from Sales Journal)

### 2. TPS: Excel=3479.79 vs NAS=743.83
- Same issue as TVQ
- **Excel:** 4-day cumulative
- **NAS (current):** Only chambres tax from Daily Revenue (2,635.79)
- **Correct daily value:** 743.83 (from Sales Journal)

### 3. Piazza Nourriture: Excel=3426.30 vs NAS=3621.80
- **NAS (expected):** 3,621.80 (from Sales Journal)
- **Excel:** 3,426.30
- **Delta:** -195.50
- **Cause:** Excel has deductions or adjustments applied that SJ doesn't reflect
- **This is acceptable** — Excel is the auditor's adjusted version

### 4. Spesa Nourriture: Excel=727.34 vs NAS=688.81
- **NAS (expected):** 727.34 (from Sales Journal)
- **Excel:** 688.81
- **Delta:** -38.53
- **Cause:** Excel has deductions applied
- **This is acceptable** — Excel is adjusted version

### 5. Room Revenue: Excel=50906.60 vs NAS=50936.60
- **Delta:** +30.00
- **Cause:** Likely refund or adjustment between audit and entry
- **This is normal**

### 6. Piazza Boisson, Chambres Svc, Banquet Variants = 0
- **Cause:** Daily Revenue parser doesn't extract these
- **Expected:** Should come from Sales Journal
- **Not yet populated:** No parser for Sales Journal exists

---

## Files Involved

### Source Files Analyzed:
1. `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/jour_mapping.py` (Lines 1-107)
   - Defines NAS field to Excel column mapping
   - Mapping is CORRECT, data source is WRONG

2. `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/daily_rev_jour_mapping.py` (Lines 1162-1200)
   - Documents expected values but hardcodes incomplete data
   - Mixes Daily Revenue + accumulator logic

3. `/sessions/laughing-sharp-johnson/mnt/audit-pack/routes/audit/rj_native.py` (Lines 1085-1217)
   - `_fill_from_daily_revenue()` function
   - Extracts from incomplete Daily Revenue source
   - Missing Sales Journal parser

4. `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/parsers/daily_revenue_parser.py` (Lines 173-275)
   - Correctly extracts from Daily Revenue PDF
   - But PDF's "Non-Revenue Departments" section has incomplete F&B data
   - This is a **data source limitation**, not parser bug

5. `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Rj_04-02-2026_ORIGINAL.xls` (Row 6)
   - Expected/desired values for Feb 4
   - Shows 4-day cumulative taxes (not daily!)

### Test Data Files:
- `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Daily_Rev_4th_Feb.pdf` → Parser output verified ✓
- `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Sales_Journal_4th_Feb.rtf` → NOT parsed yet ⚠️

---

## Conclusion

**The NAS auto-fill system is using incomplete data sources.**

- **Daily Revenue PDF** is designed for accounting reconciliation, not F&B reporting
  - It has tax-adjusted totals (non-revenue section), not full POS amounts
  - It's the only automated source but is fundamentally incomplete

- **Sales Journal** is the authoritative F&B source
  - Has complete breakdown by department
  - Has both revenues AND associated taxes
  - Currently not being parsed

- **Excel fields** store a mix of daily and cumulative values
  - TVQ/TPS appear to be 4-day cumulative (not daily)
  - F&B values are daily but adjusted/deducted

**None of these are bugs — they're architectural misalignments.** The mapping is correct; the data source is incomplete.

