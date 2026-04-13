# Code References: Jour Sheet Discrepancies

## Quick Navigation

### Problematic Code Locations in rj_native.py

| Issue | Line | Current Code | Problem |
|-------|------|--------------|---------|
| TVQ (jour_tvq) | 1140 | `jour_tvq = taxes.get('tvq')` | Gets chambres tax only from Daily Revenue; should be daily total from Sales Journal (1,483.68, not 5,257.25) |
| TPS (jour_tps) | 1139 | `jour_tps = taxes.get('tps')` | Gets chambres tax only from Daily Revenue; should be daily total from Sales Journal (743.83, not 2,635.79) |
| Piazza Nourriture | 1165 | `piazza.get('nourriture')` | Gets 1,981.40 from Daily Revenue non-revenue section; should be 3,621.80 from Sales Journal |
| Piazza Boisson | 1166 | `piazza.get('alcool')` | Gets 75.00 from DR; should be 650.50 from Sales Journal |
| Piazza Bieres | 1167 | `piazza.get('biere')` | Gets 198.00 from DR; should be 566.00 from Sales Journal |
| Piazza Mineraux | 1168 | `piazza.get('mineraux')` | Gets 19.00 from DR; should be 85.25 from Sales Journal |
| Spesa Nourriture | 1185 | `spesa.get('la_spesa')` | Gets 145.28 from DR; should be 727.34 from Sales Journal |
| Chambres Svc Nour | 1181 | `svc.get('nourriture')` | Gets 138.87 from DR; should be 59.00 from Sales Journal |

---

## The Problem Explained by Source

### A) Daily Revenue Parser (daily_revenue_parser.py)

**File:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/parsers/daily_revenue_parser.py`

**Lines 192-217:** Where restaurant data is extracted

```python
# Line 192-205: Restaurant Piazza section
'restaurant_piazza': {
    'nourriture': 1981.40,      # ← From "Non-Revenue Departments" section
    'alcool': 75.00,            # ← Incomplete beverage breakdown
    'biere': 198.00,            # ← Missing 368.00
    'mineraux': 19.00,          # ← Missing 66.25
    'vin': 219.00,
    ...
}

# Line 237-242: La Spesa section
'la_spesa': {
    'la_spesa': 145.28,         # ← From "Non-Revenue Departments"
    'tps': 6.32,
    'tvq': 12.60,
    'total': 164.20
}

# Line 211-217: Services aux Chambres
'services_chambres': {
    'nourriture': 138.87,       # ← Wrong! Should be 59.00
    'pourboire': 3.44,
    'tps': 1.15,
    'tvq': 2.29,
    'total': 145.75
}
```

**Root Cause:**
- Lines 122-183 hardcode values extracted from the PDF's "Non-Revenue Departments" section
- This section contains **tax-adjusted subtotals**, not full POS amounts
- Real Daily Revenue parser reads from PDF, but the PDF itself is incomplete

**Proof:** Compare Daily Revenue non-revenue section vs Sales Journal:
- Piazza Nourriture: 1,981.40 (DR) vs 3,621.80 (SJ) = 45% missing
- Spesa: 145.28 (DR) vs 727.34 (SJ) = 80% missing
- Chambres Svc: 138.87 (DR) vs 59.00 (SJ) = WRONG DIRECTION (135% too much!)

---

### B) Where Daily Revenue Data Gets Into NAS (rj_native.py)

**File:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/routes/audit/rj_native.py`

**Function:** `_fill_from_daily_revenue(data, nas, day)` - Lines 1085-1217

#### Key code blocks:

**Lines 1136-1140: Taxes extraction**
```python
# Taxes
taxes = non_rev.get('chambres_tax', {})
_safe_set(nas, 'jour_taxe_hebergement', taxes.get('taxe_hebergement'), count)
_safe_set(nas, 'jour_tps', taxes.get('tps'), count)        # ← Line 1139: WRONG
_safe_set(nas, 'jour_tvq', taxes.get('tvq'), count)        # ← Line 1140: WRONG
```

**What it does:** Gets `non_rev['chambres_tax']` which contains ONLY room taxes
- `tvq` = 5,257.25 (chambres only)
- `tps` = 2,635.79 (chambres only)

**What it should do:** Get full daily tax total from Sales Journal
- `tvq` = 1,483.68 (all departments)
- `tps` = 743.83 (all departments)

**Lines 1163-1169: Piazza extraction**
```python
# Piazza (restaurant)
piazza = non_rev.get('restaurant_piazza', {})
_safe_set(nas, 'jour_piazza_nourriture', piazza.get('nourriture'), count)  # ← 1981.40
_safe_set(nas, 'jour_piazza_boisson', piazza.get('alcool'), count)         # ← 75.00
_safe_set(nas, 'jour_piazza_bieres', piazza.get('biere'), count)           # ← 198.00
_safe_set(nas, 'jour_piazza_mineraux', piazza.get('mineraux'), count)      # ← 19.00
_safe_set(nas, 'jour_piazza_vins', piazza.get('vin'), count)
```

**What it does:** Gets incomplete restaurant_piazza from Daily Revenue

**What it should do:** Get from Sales Journal POS breakdown
- piazza_nourriture: 3,621.80 (vs current 1,981.40)
- piazza_boisson: 650.50 (vs current 75.00)
- piazza_bieres: 566.00 (vs current 198.00)
- piazza_mineraux: 85.25 (vs current 19.00)

**Lines 1183-1185: Spesa extraction**
```python
# La Spesa (Marché)
spesa = non_rev.get('la_spesa', {})
_safe_set(nas, 'jour_spesa_nourriture', spesa.get('la_spesa'), count)  # ← 145.28
```

**What it does:** Gets la_spesa from Daily Revenue (145.28)

**What it should do:** Get from Sales Journal (727.34)

**Lines 1179-1181: Chambres Svc extraction**
```python
# Services aux chambres
svc = non_rev.get('services_chambres', {})
_safe_set(nas, 'jour_chambres_svc_nourriture', svc.get('nourriture'), count)  # ← 138.87
```

**What it does:** Gets from Daily Revenue (138.87)

**What it should do:** Get from Sales Journal (59.00)

---

## Where Data Flows From

### Current Flow (INCOMPLETE):

```
Sales Journal (RTF file)
    ↓
[NOT PARSED]
    ↓
   ✗ Lost

Daily Revenue (PDF file)
    ↓
daily_revenue_parser.py (lines 192-217)
    ↓
Extracts non_revenue section:
  - restaurant_piazza (incomplete)
  - la_spesa (very incomplete)
  - services_chambres (wrong values)
    ↓
_fill_from_daily_revenue() in rj_native.py (lines 1085-1217)
    ↓
NightAuditSession.jour_* fields
    ↓
JOUR sheet in RJ Excel (via jour_mapping.py)
```

### Desired Flow (COMPLETE):

```
Daily Revenue (PDF file)
    ↓
daily_revenue_parser.py
    ↓
Extracts:
  - chambres/room_revenue ✓
  - taxes (chambres only, OK)
    ↓
_fill_from_daily_revenue() ✓

Sales Journal (RTF file)
    ↓
[NEW] sales_journal_parser.py
    ↓
Extracts:
  - piazza complete breakdown
  - spesa complete breakdown
  - chambres svc complete breakdown
  - banquet complete breakdown
  - taxes by department
  - adjustments
    ↓
[NEW] _fill_from_sales_journal()
    ↓
NightAuditSession.jour_* fields ✓
    ↓
JOUR sheet in RJ Excel (via jour_mapping.py) ✓
```

---

## Mapping File Analysis

**File:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/jour_mapping.py`

**Status:** ✓ CORRECT - No changes needed

**What it does (lines 30-107):**
- Maps NAS field names to Excel column indices
- Example: `'jour_piazza_nourriture': 9` (column J)

**JOUR_NAS_TO_COL dictionary:**
```python
'jour_piazza_nourriture': 9,    # Col J - ✓ Correct mapping
'jour_piazza_boisson': 10,      # Col K - ✓ Correct mapping
'jour_piazza_bieres': 11,       # Col L - ✓ Correct mapping
'jour_piazza_mineraux': 12,     # Col M - ✓ Correct mapping
'jour_piazza_vins': 13,         # Col N - ✓ Correct mapping
'jour_tvq': 49,                 # Col AX - ✓ Correct mapping
'jour_tps': 50,                 # Col AY - ✓ Correct mapping
# ... all others are correct too
```

**Helper functions (lines 148-276):**
- `nas_jour_to_excel_dict()` - Converts NAS to Excel format ✓
- `excel_jour_to_nas_dict()` - Converts Excel to NAS format ✓
- `get_jour_column_info()` - Looks up column info ✓

**Conclusion:** This file is working correctly. The problem is upstream (source data).

---

## Daily Revenue Jour Mapping Documentation

**File:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/daily_rev_jour_mapping.py`

**Status:** ⚠️ MISLEADING - Needs updating

**Lines 1162-1200 (EXPECTED_VALUES_FEB_4):**
```python
EXPECTED_VALUES_FEB_4 = {
    'chambres_total': 50936.60,
    'piazza_nourriture': 1981.40,     # ← This is from Daily Revenue
                                       # ✗ WRONG: Should be 3,621.80 (from SJ)
    'spesa_total': 145.28,             # ← This is from Daily Revenue
                                       # ✗ WRONG: Should be 727.34 (from SJ)
    'tvq': 7558.53,                    # ← Claims this but doesn't say from where
    'tps': 3788.92,                    # ← Claims this but doesn't say from where
    # ... more fields
}
```

**Problem:** This file documents "expected values" but hardcodes Daily Revenue values that are known to be incomplete. It's misleading because it doesn't acknowledge that:
1. These are Daily Revenue values, not SJ values
2. Daily Revenue is incomplete for these fields
3. There's a source priority issue

**What needs fixing:**
- Update comments to note Daily Revenue is incomplete source
- Document that Sales Journal should be used instead
- Add SJ expected values for comparison
- Clarify the 4-day cumulative issue for TVQ/TPS

---

## Test Data Available

**File:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Daily_Rev_4th_Feb.pdf`
- Can be parsed with existing parser
- Confirmed values in analysis (room: 50,936.60, Piazza Nour: 1,981.40, etc.)

**File:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Sales_Journal_4th_Feb.rtf`
- Contains complete POS breakdown
- Not currently parsed
- Has values needed to fix the discrepancies

**File:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/test_data/Rj_04-02-2026_ORIGINAL.xls`
- Excel original with expected values
- Row 5 contains Feb 4 data
- Can be used to validate fixes

---

## Database Schema (No Changes Needed)

**File:** `/sessions/laughing-sharp-johnson/mnt/audit-pack/database/models.py`

**NightAuditSession model (~150 columns):**
- All jour_* fields are defined correctly
- Data types are appropriate
- No schema changes required
- Mapping between fields and columns is correct

---

## Summary of Required Changes

### NEW FILES:
1. `utils/parsers/sales_journal_parser.py` - Parse RTF file
2. Possibly update `__init__.py` in parsers to register new parser

### MODIFIED FILES:
1. `routes/audit/rj_native.py` - Add `_fill_from_sales_journal()` function
2. `utils/daily_rev_jour_mapping.py` - Update documentation

### REVIEWED (but NOT modified):
1. `utils/jour_mapping.py` - Correct as-is
2. `utils/parsers/daily_revenue_parser.py` - Correct as-is
3. `database/models.py` - Correct as-is

---

## Questions for Business Clarification

Before implementing the fix, need answers to:

1. **TVQ/TPS Field Intent**
   - Should `jour_tvq` store daily total or 4-day cumulative?
   - Current: Daily value from Daily Revenue chambres tax (5,257.25)
   - Excel has: 6,941.62 (looks like 4-day cumulative)
   - Sales Journal has: 1,483.68 (daily, all departments)

2. **Excel Adjustment Values**
   - Why does Excel have different values than Sales Journal?
   - Example: Piazza Nour SJ=3,621.80, Excel=3,426.30 (-195.50)
   - Are these manual deductions? HP adjustments? System-calculated?

3. **Data Source Priority**
   - Should NAS auto-fill use Sales Journal when available?
   - Or continue with Daily Revenue for consistency?
   - Both sources exist for Feb 4 test data

4. **Missing Departments**
   - Why doesn't Daily Revenue have complete F&B breakdown?
   - Is this expected? Is the PMS (Galaxy Lightspeed) designed that way?
   - Should Sales Journal always be the F&B source?

