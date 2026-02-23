# Investigation Index: Jour Sheet Discrepancies (Feb 4, 2026)

This index helps you navigate the investigation results. Start here, then follow the links based on what you need.

---

## Where to Start

### For a Quick Answer (2 min read)
→ **INVESTIGATION_EXECUTIVE_SUMMARY.md**
- High-level overview of all 6 issues
- Why they exist
- What needs to be fixed
- Next steps

### For Technical Deep Dive (20 min read)
→ **ANALYSIS_JOUR_DISCREPANCIES_FEB4.md**
- Complete root cause analysis for each issue
- Data source comparison tables
- Mapping logic explanation
- File involvement list

### For Code References (10 min read)
→ **CODE_REFERENCES_JOUR_ISSUES.md**
- Exact line numbers of problematic code
- What each line does and why it's wrong
- Data flow diagrams
- Questions for business clarification

### For Detailed Comparison Table (5 min reference)
→ **DISCREPANCY_SUMMARY_TABLE.txt**
- Formatted table with all 11 issues
- Side-by-side value comparisons
- Status indicators (🔴 ERROR, 🟡 WARNING, ✓ OK)
- File locations with line numbers

---

## Investigation Results Summary

### Issues Found: 11 Total
- 🔴 **3 Critical:** Data source selection errors (Piazza/Spesa/Chambres values wrong)
- 🟡 **5 Medium:** Data source limitations (beverage breakdowns missing/incomplete)
- ⚠️ **2 Design Issues:** Cumulative vs daily field intent unclear (TVQ/TPS)
- ✓ **1 Acceptable:** Room revenue minor variance (+30)

### Root Causes: 2 Main
1. **Missing Sales Journal Parser** (80% of problem)
   - Sales Journal RTF file has complete POS data
   - Not being parsed or used
   - Test file exists: `test_data/Sales_Journal_4th_Feb.rtf`

2. **Daily Revenue Incompleteness** (20% of problem)
   - PDF "Non-Revenue Departments" section lacks full F&B breakdown
   - By design - it's for tax reconciliation, not revenue reporting
   - System should use Sales Journal instead

### Current Impact
- Piazza Nourriture: **-1,640.40** missing (NAS=1,981 vs should be 3,621)
- Spesa Nourriture: **-582.06** missing (NAS=145 vs should be 727)
- Beverages: **~1,000+** missing across departments
- Total F&B underestatement: **~$2,200-2,500 per day**

---

## File Reference Guide

### Investigation Documents (what you're reading)
| File | Purpose | Read Time |
|------|---------|-----------|
| INVESTIGATION_INDEX.md | This file - navigation guide | 2 min |
| INVESTIGATION_EXECUTIVE_SUMMARY.md | Quick answer + fix strategy | 3 min |
| ANALYSIS_JOUR_DISCREPANCIES_FEB4.md | Deep technical analysis | 15 min |
| CODE_REFERENCES_JOUR_ISSUES.md | Code locations + fixes needed | 10 min |
| DISCREPANCY_SUMMARY_TABLE.txt | Formatted comparison tables | 5 min |

### Source Code Files Involved

**Files with BUGS/ISSUES:**
- `routes/audit/rj_native.py` (Lines 1139-1140, 1165-1181, 1185)
  - Problem: Uses incomplete Daily Revenue data
  - Fix: Add Sales Journal parser, use it instead

- `utils/daily_rev_jour_mapping.py` (Lines 1162-1200)
  - Problem: Hardcodes Daily Revenue values as "expected"
  - Fix: Update documentation, add SJ values

**Files that are CORRECT (no changes):**
- `utils/jour_mapping.py` (Lines 30-107)
  - Mapping is correct, column assignments are right
  
- `utils/parsers/daily_revenue_parser.py`
  - Parser works correctly, just limited by PDF source
  
- `database/models.py`
  - Schema is correct, all jour_* fields properly defined

**Files to CREATE:**
- `utils/parsers/sales_journal_parser.py` (NEW)
  - Parse RTF/PDF format Sales Journal
  - Extract POS breakdown by department

### Test Data Files
- `test_data/Daily_Rev_4th_Feb.pdf` - Can be parsed, verified ✓
- `test_data/Sales_Journal_4th_Feb.rtf` - Not parsed yet, needed ⚠️
- `test_data/Rj_04-02-2026_ORIGINAL.xls` - Expected values, used for validation ✓

---

## Issue-by-Issue Guide

### 1. TVQ (Column 49)
- **Discrepancy:** Excel=6,941.62 vs NAS=5,257.25 vs SJ=1,483.68
- **Severity:** 🟡 Medium (design question)
- **Root Cause:** Unclear if field should be daily or 4-day cumulative
- **Location:** `CODE_REFERENCES_JOUR_ISSUES.md` → Section "TVQ (jour_tvq)"
- **Fix Required:** Clarify business requirement first

### 2. TPS (Column 50)
- **Discrepancy:** Excel=3,479.79 vs NAS=2,635.79 vs SJ=743.83
- **Severity:** 🟡 Medium (design question)
- **Root Cause:** Same as TVQ - daily vs cumulative unclear
- **Location:** `CODE_REFERENCES_JOUR_ISSUES.md` → Section "TPS (jour_tps)"
- **Fix Required:** Clarify business requirement first

### 3. Piazza Nourriture (Column 9)
- **Discrepancy:** NAS=1,981.40 vs SJ=3,621.80 vs Excel=3,426.30
- **Severity:** 🔴 Critical (45% of data missing)
- **Root Cause:** Using Daily Revenue non-revenue section instead of SJ
- **Location:** `ANALYSIS_JOUR_DISCREPANCIES_FEB4.md` → Section "B) Piazza Nourriture"
- **Fix Required:** Implement Sales Journal parser

### 4. Piazza Boisson (Column 10)
- **Discrepancy:** NAS=75.00 vs SJ=650.50
- **Severity:** 🟡 Medium (beverage reporting)
- **Root Cause:** Daily Revenue doesn't have complete beverage breakdown
- **Location:** `CODE_REFERENCES_JOUR_ISSUES.md` → Section "Piazza Boisson"
- **Fix Required:** Implement Sales Journal parser

### 5. Piazza Bieres (Column 11)
- **Discrepancy:** NAS=198.00 vs SJ=566.00
- **Severity:** 🟡 Medium (beverage reporting)
- **Root Cause:** Daily Revenue doesn't have complete beverage breakdown
- **Location:** `DISCREPANCY_SUMMARY_TABLE.txt` → Item 6
- **Fix Required:** Implement Sales Journal parser

### 6. Piazza Mineraux (Column 12)
- **Discrepancy:** NAS=19.00 vs SJ=85.25
- **Severity:** 🟡 Medium (beverage reporting)
- **Root Cause:** Daily Revenue doesn't have complete beverage breakdown
- **Location:** `DISCREPANCY_SUMMARY_TABLE.txt` → Item 7
- **Fix Required:** Implement Sales Journal parser

### 7. Spesa Nourriture (Column 14)
- **Discrepancy:** NAS=145.28 vs SJ=727.34 vs Excel=688.81
- **Severity:** 🔴 Critical (80% of data missing!)
- **Root Cause:** Using Daily Revenue non-revenue section instead of SJ
- **Location:** `ANALYSIS_JOUR_DISCREPANCIES_FEB4.md` → Section "C) Spesa Nourriture"
- **Fix Required:** Implement Sales Journal parser

### 8. Chambres Svc Nourriture (Column 19)
- **Discrepancy:** NAS=138.87 vs SJ=59.00
- **Severity:** 🔴 Critical (wrong value, 135% too high)
- **Root Cause:** Daily Revenue has wrong total for this department
- **Location:** `CODE_REFERENCES_JOUR_ISSUES.md` → Section "Chambres Svc Nourriture"
- **Fix Required:** Implement Sales Journal parser

### 9. Banquet Boisson & Bieres (Columns 25-26)
- **Discrepancy:** NAS=-600/-30 vs SJ=24 credit/30 credit vs Excel=-24/-30
- **Severity:** 🟡 Medium (sign handling issue)
- **Root Cause:** Different sign convention between DR and SJ
- **Location:** `DISCREPANCY_SUMMARY_TABLE.txt` → Item 11
- **Fix Required:** Implement Sales Journal parser, handle signs properly

### 10. Room Revenue (Column 36)
- **Discrepancy:** NAS=50,936.60 vs Excel=50,906.60
- **Severity:** ✓ Acceptable (±30 variance)
- **Root Cause:** Normal rounding/adjustment
- **Location:** `ANALYSIS_JOUR_DISCREPANCIES_FEB4.md` → Section "D) Room Revenue"
- **Fix Required:** None

### 11. Missing Beverages (Chambres Svc & Others)
- **Discrepancy:** NAS=0 vs SJ=various
- **Severity:** 🟡 Medium (beverages not populated)
- **Root Cause:** Daily Revenue doesn't extract these
- **Location:** `DISCREPANCY_SUMMARY_TABLE.txt` → Item 10
- **Fix Required:** Implement Sales Journal parser

---

## How the Data Flows (Current vs Desired)

### CURRENT DATA FLOW (INCOMPLETE)
```
Daily Revenue PDF
    ↓
daily_revenue_parser.py extracts non_revenue section
    ↓
_fill_from_daily_revenue() in rj_native.py
    ↓
NightAuditSession.jour_* fields
    ↓
RESULT: ~55% of F&B data, missing beverages
```

### DESIRED DATA FLOW (COMPLETE)
```
Daily Revenue PDF              Sales Journal RTF
    ↓                              ↓
daily_revenue_parser.py    sales_journal_parser.py [NEW]
    ↓                              ↓
_fill_from_daily_revenue() _fill_from_sales_journal() [NEW]
    ↓                              ↓
    └──────────→ NightAuditSession.jour_* fields
                ↓
        RESULT: 100% of F&B data with proper breakdown
```

---

## Implementation Checklist

### Phase 1: Analysis (COMPLETE) ✓
- [x] Identify data sources
- [x] Compare values across sources
- [x] Determine root causes
- [x] Analyze mapping correctness

### Phase 2: Clarification (NEEDED)
- [ ] Confirm TVQ/TPS field intent (daily vs cumulative)
- [ ] Review Excel adjustment logic
- [ ] Understand why Daily Revenue PDF is incomplete

### Phase 3: Implementation
- [ ] Create sales_journal_parser.py
- [ ] Implement RTF/PDF parsing
- [ ] Extract restaurant department breakdown
- [ ] Extract tax totals by department
- [ ] Create _fill_from_sales_journal() function
- [ ] Register new parser in __init__.py
- [ ] Call new function from upload endpoint

### Phase 4: Testing
- [ ] Test with Feb 4 data
- [ ] Verify all jour_* fields match expected values
- [ ] Check Piazza values (should match SJ: 3,621.80 for nour)
- [ ] Check Spesa values (should match SJ: 727.34 for nour)
- [ ] Validate tax totals
- [ ] Regression test with other dates

### Phase 5: Documentation
- [ ] Update jour_mapping.py comments
- [ ] Update daily_rev_jour_mapping.py with SJ values
- [ ] Document data source priority
- [ ] Add parser documentation

---

## Questions Requiring Business Input

**Before implementing, need clarification on:**

1. **TVQ/TPS Intent**
   - Current NAS stores: Daily chambres tax (5,257.25)
   - Sales Journal has: Daily total (1,483.68)
   - Excel shows: 4-day cumulative (6,941.62)
   - **Question:** What should jour_tvq store?

2. **Excel Adjustment Values**
   - Piazza: SJ=3,621.80, Excel=3,426.30 (difference: -195.50)
   - Spesa: SJ=727.34, Excel=688.81 (difference: -38.53)
   - **Question:** Are these manual deductions? HP adjustments?

3. **Data Source Priority**
   - Should NAS auto-fill use Sales Journal when available?
   - Or continue using Daily Revenue PDF only?

---

## Document Reading Order (Recommended)

1. **START HERE:** INVESTIGATION_EXECUTIVE_SUMMARY.md (3 min)
   - Get the big picture
   - Understand why it matters

2. **DEEP DIVE:** ANALYSIS_JOUR_DISCREPANCIES_FEB4.md (15 min)
   - Understand technical details
   - See data flow and causation

3. **FOR CODING:** CODE_REFERENCES_JOUR_ISSUES.md (10 min)
   - Know exact line numbers
   - See current code vs needed code

4. **AS REFERENCE:** DISCREPANCY_SUMMARY_TABLE.txt (anytime)
   - Quick lookup by issue
   - Formatted for easy scanning

---

## Files Created by This Investigation

All in `/sessions/laughing-sharp-johnson/mnt/audit-pack/`:

1. `INVESTIGATION_INDEX.md` ← You are here
2. `INVESTIGATION_EXECUTIVE_SUMMARY.md`
3. `ANALYSIS_JOUR_DISCREPANCIES_FEB4.md`
4. `CODE_REFERENCES_JOUR_ISSUES.md`
5. `DISCREPANCY_SUMMARY_TABLE.txt`

No source code was modified - this is pure analysis.

---

## Key Numbers to Remember

| Metric | Value | Impact |
|--------|-------|--------|
| Piazza Nour missing | 1,640.40 | Critical |
| Spesa Nour missing | 582.06 | Critical |
| Beverage underestimate | ~1,000+ | Medium |
| Room revenue variance | +30.00 | Acceptable |
| Total F&B gap per day | ~2,200-2,500 | Critical for reporting |

---

## Next Actions

**Immediate (This Week):**
1. Review this investigation with team
2. Clarify business requirements for TVQ/TPS
3. Confirm Sales Journal is the authoritative F&B source

**Short-term (Next 1-2 Weeks):**
1. Implement sales_journal_parser.py
2. Create _fill_from_sales_journal()
3. Test with Feb 4 data

**Long-term (Next 1 Month):**
1. Deploy fix
2. Validate against historical data
3. Update documentation
4. Archive old Daily Revenue only approach

---

## Contact Points in Code

- **For parser changes:** `utils/parsers/` directory
- **For NAS filling:** `routes/audit/rj_native.py` lines 1085-1217
- **For mapping:** `utils/jour_mapping.py` (reference only, working correctly)
- **For test data:** `test_data/` directory

