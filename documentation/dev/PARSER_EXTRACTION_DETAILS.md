# Sales Journal Parser - Extraction Details

## File Location
`/sessions/laughing-sharp-johnson/mnt/audit-pack/utils/parsers/sales_journal_parser.py`

## Parsing Flow

```
Sales Journal File (RTF or TXT)
  ↓
_decode_file() - Convert bytes to text
  ↓
_clean_rtf() - Remove RTF markup
  ↓
_parse_metadata() - Extract report date/time
_parse_departments() - Extract revenue by department
_parse_taxes() - Extract TPS/TVQ
_parse_payments() - Extract payment methods (COMPTANT, VISA, etc.)
_parse_adjustments() - Extract adjustments (FORFAIT, HOTEL PROMOTION, etc.)
  ↓
_build_rj_mapping() - Create RJ cell mapping
  ↓
extracted_data dict with all results
```

---

## 1. COMPTANT (CASH) EXTRACTION

### Code Location
- Line 333: Pattern definition
- Lines 342-345: Pattern matching
- Line 584: RJ mapping

### Pattern Regex
```python
'comptant': r'COMPTANT\s+(\d+\.\d+)'
```

### Test Data Match
```
Input:  "COMPTANT                                737.99"
Output: $737.99
```

### RJ Mapping
```python
'recap': {
    'comptant_lightspeed': payments.get('comptant', 0.0),  # 737.99
}
```

### Sales Journal File Location
- **Page:** 1
- **Section:** Payment Methods
- **Line 53 of test file:** `COMPTANT                                737.99`

---

## 2. FORFAIT EXTRACTION

### Code Location
- Line 378: Pattern definition
- Lines 383-386: Pattern matching in adjustments
- Lines 360-372: Adjustment parsing (page 2)

### Pattern Regex
```python
'forfait': r'FORFAIT\s+(\d+\.\d+)'
```

### Test Data Match
```
Input:  "FORFAIT                     58.65   "
Output: $58.65
```

### Data Storage
```python
# Stored in extracted_data
extracted_data = {
    'adjustments': {
        'forfait': 58.65  # ← NOT currently in RJ mapping
    }
}
```

### Sales Journal File Location
- **Page:** 2 (Adjustments section)
- **Section:** Adjustments/Corrections
- **Line 71 of test file:** `FORFAIT                     58.65   `

### Missing RJ Mapping
```python
# CURRENT: Not mapped
# Expected mapping would be:
'jour': {
    'difference_forfait': adjustments.get('forfait', 0.0),  # 58.65 (to Jour!BF)
}
```

---

## 3. ALL PAYMENT METHODS

### Code Location
Lines 332-345 (payment items dict and matching loop)

### Extraction Pattern
```python
payment_items = {
    'comptant': r'COMPTANT\s+(\d+\.\d+)',
    'visa': r'VISA\s+(\d+\.\d+)',
    'mastercard': r'MASTERCARD\s+(\d+\.\d+)',
    'amex': r'AMEX\s+(\d+\.\d+)',
    'interac': r'INTERAC\s+(\d+\.\d+)',
    'chambre': r'CHAMBRE\s+(\d+\.\d+)',
    'correction': r'CORRECTION\s+(\d+\.\d+)',
}
```

### Test Data Results
```
COMPTANT:    $737.99     ✓ Extracted, ✓ Mapped to recap
VISA:        $2,344.84   ✓ Extracted, ✓ Mapped to transelect
MASTERCARD:  $807.83     ✓ Extracted, ✓ Mapped to transelect
AMEX:        $496.53     ✓ Extracted, ✓ Mapped to transelect
INTERAC:     $880.15     ✓ Extracted, ✓ Mapped to transelect
CHAMBRE:     $13,265.41  ✓ Extracted, ✗ NOT mapped
CORRECTION:  $11,176.96  ✓ Extracted, ✗ NOT mapped
```

---

## 4. ALL ADJUSTMENTS

### Code Location
Lines 375-386 (adjustment items dict and matching loop)

### Extraction Pattern
```python
adjustment_items = {
    'administration': r'ADMINISTRATION\s+(\d+\.\d+)',
    'hotel_promotion': r'HOTEL PROMOTION\s+(\d+\.\d+)',
    'forfait': r'FORFAIT\s+(\d+\.\d+)',
    'empl_30': r'EMPL 30%\s+(\d+\.\d+)',
    'pourboire_charge': r'POURBOIRE CHARGE\s+(\d+\.\d+)',
}
```

### Test Data Results
```
ADMINISTRATION:    $263.69     ✓ Extracted, ✗ NOT mapped
HOTEL PROMOTION:   $266.59     ✓ Extracted, ✓ Mapped to hp
FORFAIT:           $58.65      ✓ Extracted, ✗ NOT mapped
EMPL 30%:          $44.57      ✓ Extracted, ✗ NOT mapped
POURBOIRE CHARGE:  $913.64     ✓ Extracted, ✗ NOT mapped
```

---

## 5. DEPARTMENTS

### Code Location
Lines 215-296

### Extraction Pattern
```python
dept_names = ['CAFE LINK', 'PIAZZA', 'BAR CUPOLA', 'CHAMBRES', 'BANQUET',
              'SPESA', 'CLUB LOUNG']
```

### Sub-Items (Standardized)
```python
SUBITEM_STANDARDIZATION = {
    'nourriture': 'nourriture',
    'alcool': 'boisson',
    'bieres': 'bieres',
    'mineraux': 'mineraux',
    'vins': 'vins',
    'tabagie': 'tabagie',
}
```

### Test Data Results
```
PIAZZA:
  NOURRITURE:       $3,621.80
  ALCOOL:           $650.50
  BIERES:           $566.00
  NON ALCOOL BAR:   $85.25
  VINS:             $438.00
  POURBOIRE A PAYER: $230.29
  LOCATION SALLE:   $1,675.00

CHAMBRES:
  NOURRITURE:       $59.00
  BIERES:           $38.00
  FR/ETAGE:         $12.00

BANQUET:
  NOURRITURE:       $5,670.00
  ALCOOL:           $24.00
  BIERES:           $30.00
  POURBOIRE A PAYER: $1,010.88
  EQ. DIVERS:       $565.00
  LOCATION SALLE:   $600.00

SPESA:
  NOURRITURE:       $727.34
  TABAGIE:          $653.13
```

---

## 6. TAXES

### Code Location
Lines 298-318

### Extraction Pattern
```python
tps_match = re.search(r'TPS\s+(\d+\.\d+)', text)
tvq_match = re.search(r'TVQ\s+(\d+\.\d+)', text)
```

### Test Data Results
```
TPS:  $743.83   ✓ Extracted
TVQ:  $1,483.68 ✓ Extracted
```

---

## 7. RJ MAPPING BUILDING

### Code Location
Lines 570-606

### Current Mapping Structure
```python
mapping = {
    'recap': {
        'comptant_lightspeed': 737.99,
    },
    'transelect': {
        'visa': 2344.84,
        'mastercard': 807.83,
        'amex': 496.53,
        'interac': 880.15,
    },
    'hp': {
        'hotel_promotion': 266.59,
    },
    'jour': {
        'piazza_total': departments['piazza']['total'],
        'banquet_total': departments['banquet']['total'],
        'chambres_total': departments['chambres']['total'],
        'spesa_total': departments['spesa']['total'],
        'tabagie': departments['spesa']['tabagie'],
        'tps': 743.83,
        'tvq': 1483.68,
    }
}
```

### Missing from Mapping
```python
# These are extracted but NOT in the mapping:
adjustments['administration']    # 263.69
adjustments['forfait']           # 58.65  ← IMPORTANT FOR JOUR!BF
adjustments['empl_30']           # 44.57
adjustments['pourboire_charge']  # 913.64
payments['chambre']              # 13265.41
payments['correction']           # 11176.96
```

---

## 8. DATA FLOW FOR INTERNET & SONIFI

### Sales Journal → Jour Sheet

**No direct extraction** in parser for Internet or Sonifi from Sales Journal.

**Instead:**
1. Sales Journal provides totals for departments (PIAZZA, BANQUET, etc.)
2. These feed into Jour sheet totals
3. Internet and Sonifi are either:
   - Manual entries on Jour sheet
   - Pulled from LightSpeed CD reports separately
   - Calculated as adjustments to department totals

**Jour sheet columns:**
- `AT` = Sonifi Film (from Sonifi tab or manual entry)
- `AW` = Internet (from Internet tab or manual entry)

**Reconciliation:**
- Internet tab pulls `Jour!AW` to compare against LightSpeed CD
- Sonifi tab pulls `Jour!AT` to compare against LightSpeed CD

---

## 9. RECOMMENDATIONS FOR FORFAIT MAPPING

### Current Situation
- Forfait is extracted from Sales Journal ($58.65)
- But NOT mapped to any RJ sheet

### Options

**Option A: Auto-map to Jour!BF**
```python
# Add to _build_rj_mapping() method:
'jour': {
    # ... existing mappings ...
    'difference_forfait': adjustments.get('forfait', 0.0),  # Maps to Jour!BF
}
```

**Option B: Keep manual in diff_forfait sheet**
- Current approach allows granular daily tracking by forfait type
- Sales Journal forfait validates overall amount
- diff_forfait sheet breaks down by meal plan type (75$, 63$, 87$, etc.)

**Option C: Both**
- Auto-map total forfait to Jour!BF for validation
- Keep diff_forfait sheet for detailed breakdown

---

## 10. TEST DATA SUMMARY

### Sales Journal File
- **Path:** `test_data/Sales_Journal_4th_Feb.rtf`
- **Report Date:** 02/04/2026
- **Report Time:** 2:38:35.78
- **Total Balanced:** $31,137.86 (debits = credits)
- **Pages:** 2

### RJ Excel Workbook
- **Path:** `test_data/Rj_03-02-2026_pour_test.xls`
- **Audit Date:** 03-02-2026
- **Sheets:** 38 total
- **Internet Sheet:** Row 7-41 (days 1-31 or selected days)
- **Sonifi Sheet:** Row 6-40 (days 1-31 or selected days)
- **Jour Sheet:** 233 rows, 117 columns (main reconciliation)

---

## 11. PARSER CLASS HIERARCHY

```python
class SalesJournalParser(BaseParser):
    """Parser for Sales Journal reports from POS system."""
    
    # FIELD_MAPPINGS: Map extracted fields to RJ cell references (lines 18-39)
    # __init__: Initialize parser (lines 41-46)
    # load_from_file(): Class method to load and parse file (lines 48-68)
    # parse(): Main parsing method (lines 70-126)
    # validate(): Validation checks (lines 128-150)
    # _decode_file(): Decode bytes to text (lines 152-165)
    # _clean_rtf(): Remove RTF markup (lines 167-197)
    # _parse_metadata(): Extract date/time (lines 199-213)
    # _parse_departments(): Extract revenue (lines 215-296)
    # _parse_taxes(): Extract TPS/TVQ (lines 298-318)
    # _parse_payments(): Extract payment methods (lines 320-347)
    # _parse_adjustments(): Extract adjustments (lines 349-388)
    # _extract_total(): Extract balanced total (lines 390-406)
    # _split_pages(): Split by page headers (lines 408-420)
    # _is_line_item(): Check if line is data (lines 422-446)
    # _parse_line_item(): Parse line to name + amounts (lines 448-512)
    # _normalize_name(): Normalize for dict keys (lines 544-553)
    # _standardize_subitem(): Standardize food types (lines 555-568)
    # _build_rj_mapping(): Build RJ cell mapping (lines 570-606)
```

---

## 12. USAGE EXAMPLE

```python
from utils.parsers.sales_journal_parser import SalesJournalParser

# Load and parse
result = SalesJournalParser.load_from_file('test_data/Sales_Journal_4th_Feb.rtf')

# Access extracted data
print(result['extracted_data']['adjustments']['forfait'])  # 58.65
print(result['extracted_data']['payments']['comptant'])    # 737.99
print(result['extracted_data']['rj_mapping']['recap']['comptant_lightspeed'])  # 737.99

# Check validation
print(result['is_valid'])      # True/False
print(result['confidence'])    # 0.95 (95% confidence)
```

---

**Document Generated:** February 21, 2026
**Parser Version:** As of latest audit-pack commit
**Test Data:** Sales Journal for 02/04/2026, RJ for 03-02-2026
