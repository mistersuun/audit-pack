# Transelect - Credit Card Terminal Reconciliation (`Transelect`)

**Excel Sheet:** `Transelect` | **UI Tab:** Transelect | **Dimensions:** 40 x 22
**Template:** templates/audit/rj/tabs/transelect.html
**Mapper:** utils/rj_mapper.py -> `TRANSELECT_MAPPING`, `TRANSELECT_TO_JOUR_CARD_MAP`
**API:** POST /api/rj/fill/transelect, POST /api/rj/autofill-cashout

## 1. Purpose

Transelect reconciles credit/debit card transactions across all point-of-sale terminals (restaurant, bar, reception, bank). It aggregates card-type totals from multiple terminals and feeds summary figures into the Jour sheet via the `calcul_carte()` macro. This sheet is the single source of truth for daily card transaction reconciliation.

## 2. Sheet Layout

The sheet is divided into two major input sections and a formula-based summary:

| Row(s)  | Content                                                |
|---------|--------------------------------------------------------|
| 1-6     | Headers (date, prepared by)                            |
| 7-14    | **SECTION 1:** Restaurant/Bar Terminals (POSITOUCH)    |
| 15-17   | Spacing / section divider                              |
| 18-25   | **SECTION 2:** Reception / Bank                        |
| 26      | Spacing                                                |
| 27-40   | **Summary totals** (all FORMULA - do not overwrite)    |

### Section 1: Restaurant/Bar Terminals (Rows 7-14)

| Terminal     | Column | Card Types Available                |
|--------------|--------|-------------------------------------|
| BAR 701      | B      | Debit, Visa, Master, Amex           |
| BAR 702      | C      | Debit, Visa, Master, Amex           |
| BAR 703      | D      | Debit, Visa, Master, Amex           |
| SPESA 704    | E      | Debit, Visa, Master, Amex           |
| ROOM 705     | F      | Visa only                           |
| EXTRA        | G+     | Additional terminals as needed      |
| BANQUET      | -      | Banquet terminal entries             |

### Section 2: Reception/Bank (Rows 18-25)

| Terminal            | Column | Card Types Available                |
|---------------------|--------|-------------------------------------|
| FuseBoxe (FreedomPay)| B     | Visa, Master, Amex                  |
| Reception K053      | D      | Debit, Visa, Master, Amex           |
| Terminal 8.0        | C      | Debit only                          |
| Quasimodo           | E      | Debit, Visa, Master, Amex           |

### Summary Section (Rows 27-40)

Row 38 contains the compact summary block with card-type totals that feed into the Jour sheet via `calcul_carte()`.

## 3. Field Classification

| Field                | Cell/Range      | Type    | Notes                              |
|----------------------|-----------------|---------|------------------------------------|
| Date                 | B5              | INPUT   | Daily date                         |
| Prepared by          | B6              | INPUT   | Preparer name                      |
| Section 1 data       | B9:U13          | INPUT   | Restaurant/Bar terminal amounts    |
| Section 1 extra      | X9:X13          | INPUT   | Additional terminal column         |
| Section 2 data (left)| B20:H24         | INPUT   | Reception/Bank amounts             |
| Section 2 data (right)| J20:P24        | INPUT   | Additional reception amounts       |
| Summary totals       | Rows 27-40      | FORMULA | Aggregated totals - do not overwrite|
| Row 38 card totals   | Row 38, cols 0-5| FORMULA | Feeds Jour via calcul_carte()      |

## 4. Cell Mappings (from rj_mapper.py)

### Section 1: POSITOUCH (Restaurant/Bar)

```python
# BAR 701 (Column B)
'bar_701_debit': 'B9',  'bar_701_visa': 'B10',
'bar_701_master': 'B11', 'bar_701_amex': 'B13'

# BAR 702 (Column C)
'bar_702_debit': 'C9',  'bar_702_visa': 'C10',
'bar_702_master': 'C11', 'bar_702_amex': 'C13'

# BAR 703 (Column D)
'bar_703_debit': 'D9',  'bar_703_visa': 'D10',
'bar_703_master': 'D11', 'bar_703_amex': 'D13'

# SPESA 704 (Column E)
'spesa_704_debit': 'E9',  'spesa_704_visa': 'E10',
'spesa_704_master': 'E11', 'spesa_704_amex': 'E13'

# ROOM 705 (Column F)
'room_705_visa': 'F10'
```

### Section 2: Reception / Bank

```python
# FuseBoxe - FreedomPay (Column B)
'fusebox_visa': 'B21', 'fusebox_master': 'B22', 'fusebox_amex': 'B24'

# Reception K053 (Column D)
'reception_debit': 'D20', 'reception_visa_term': 'D21',
'reception_master_term': 'D22', 'reception_amex_term': 'D24'

# Terminal 8.0 (Column C)
'reception_debit_term8': 'C20'

# Quasimodo (Column E)
'quasimodo_debit': 'E20', 'quasimodo_visa': 'E21',
'quasimodo_master': 'E22', 'quasimodo_amex': 'E24'
```

### Reset Ranges

```python
'transelect': [
    {'row_start': 8, 'row_end': 13, 'col_start': 1, 'col_end': 21},  # B9:U13
    {'row_start': 8, 'row_end': 13, 'col': 23},                       # X9:X13
    {'row_start': 19, 'row_end': 24, 'col_start': 1, 'col_end': 8},   # B20:H24
    {'row_start': 19, 'row_end': 24, 'col_start': 9, 'col_end': 16},  # J20:P24
]
```

## 5. Macros & Operations

| Operation          | Function / Endpoint              | Description                                      |
|--------------------|----------------------------------|--------------------------------------------------|
| Fill terminal data | POST /api/rj/fill/transelect     | Write amounts to mapped terminal cells           |
| Autofill cashout   | POST /api/rj/autofill-cashout    | Auto-populate from cashout source data           |
| Card totals sync   | `calcul_carte()`                 | Read row 38 totals and write to Jour cols BI-BN  |

### calcul_carte() Macro

Reads row 38 (0-indexed row 37), columns 0-5, and writes the values to the Jour sheet columns 60-65 (BI-BN):

```python
TRANSELECT_TO_JOUR_CARD_MAP = {
    0: 60,  # Amex Elavon   -> Jour col BI
    1: 61,  # Discover      -> Jour col BJ
    2: 62,  # Master        -> Jour col BK
    3: 63,  # Visa          -> Jour col BL
    4: 64,  # Debit         -> Jour col BM
    5: 65,  # Amex Global   -> Jour col BN
}
```

**Card types tracked:** DEBIT, VISA, MASTER, DISCOVER, AMEX (Elavon + Global separate).

## 6. Data Flow

```
POS Terminals ──manual/autofill──> Transelect (Sections 1 & 2)
                                        │
                                   (Excel formulas)
                                        ▼
                                   Row 38 card totals
                                        │
                                  calcul_carte()
                                        ▼
                              Jour cols BI-BN (card breakdown)
```

- **Upstream:** Terminal transaction data entered manually or via autofill-cashout endpoint.
- **Internal:** Sections 1 and 2 input cells are summed by Excel formulas into the summary section (rows 27-40). Row 38 holds the compact per-card-type totals.
- **Downstream:** `calcul_carte()` reads row 38 and writes to Jour columns BI through BN, providing the daily card-type breakdown.

## 7. UI Implementation

**Template:** `templates/audit/rj/tabs/transelect.html`

The UI provides:
- Two-section layout mirroring the Restaurant/Bar and Reception/Bank divisions
- Per-terminal card-type input fields matching the cell mapping
- Autofill button triggering `/api/rj/autofill-cashout` for automated population from cashout reports
- Summary view (read-only) for the formula-driven totals section

## 8. Known Issues & Gotchas

- **Rows 27-40 are FORMULA:** Never write data to the summary section. All totals are calculated by Excel formulas.
- **Row 12 gap:** Note that Amex entries are at row 13, not row 12. Row 12 may contain DISCOVER or be reserved. Check the mapping carefully before adding new card types.
- **Two Amex types:** Amex Elavon (col 0 in row 38) and Amex Global (col 5) are tracked separately. Do not combine them.
- **Reset range gaps:** The reset ranges do not cover the summary section (rows 27-40) since those are formulas. However, column X (col 23) has a separate single-column reset for Section 1 -- ensure this extra column is not missed during data entry.
- **0-indexed vs 1-indexed:** The `calcul_carte()` macro uses 0-indexed rows and columns internally (row 37 = Excel row 38, col 60 = Excel col BI). The `TRANSELECT_MAPPING` uses Excel-style cell references (e.g., 'B9'). Be careful when mixing these conventions.
- **ROOM 705 limitation:** Only Visa is mapped for ROOM 705 (`F10`). Other card types for this terminal are either not accepted or handled elsewhere.
