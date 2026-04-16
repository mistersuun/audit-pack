# Cell Mappings and Jour Mapping

Sources: `utils/rj_mapper.py`, `utils/daily_rev_jour_mapping.py`

---

## rj_mapper.py -- Cell Mappings

This module defines the static mapping from form field names to Excel cell references
for each RJ sheet. It also holds personnel column mappings and row-computation helpers.

### CELL_MAPPINGS

Top-level dict keyed by sheet name. Each value is a `{field_name: cell_address}` dict.

```python
CELL_MAPPINGS = {
    'controle': CONTROLE_MAPPING,
    'Recap': RECAP_MAPPING,
    'transelect': TRANSELECT_MAPPING,
    'geac_ux': GEAC_UX_MAPPING,
}
```

Used by `RJFiller.fill_sheet(sheet_name, data_dict)` to resolve field names to (row, col) indices.

#### CONTROLE_MAPPING

| Field | Cell | Description |
|-------|------|-------------|
| `jour` | B3 | Day (1-31) |
| `mois` | B4 | Month (1-12) |
| `annee` | B5 | Year |
| `temperature` | B6 | Temperature |
| `condition` | B7 | Weather |
| `prepare_par` | B2 | Prepared by |
| `dollar_sales_ytd` | B10 | YTD dollar sales |
| `rooms_available_ytd` | B12 | YTD rooms available |
| `closing_balance` | B18 | Closing balance |
| `audit_date` | B28 | Excel serial date |

#### RECAP_MAPPING

Fields for cash counts (lecture/corr pairs), cheques, remboursements, due backs,
surplus/deficit, and deposit. Key fields: `comptant_lightspeed_lecture` (B6),
`due_back_reception_lecture` (B16), `argent_recu` (B24), `prepare_par` (B26).

#### TRANSELECT_MAPPING

Maps Positouch restaurant terminals (BAR 701-703, SPESA 704, ROOM 705),
reception terminal fields, and bank report (fusebox) fields.

#### GEAC_UX_MAPPING

Maps Daily Cash Out (Row 6), Daily Revenue (Row 12), Balance Previous Day (Row 32),
Balance Today (Row 37), Facture Direct (Row 41), Advance Deposit (Row 44),
New Balance (Row 53).

### RESET_RANGES

Defines which cell ranges to clear when resetting tabs for a new day.
Keyed by sheet name (`Recap`, `transelect`, `geac_ux`, `depot`, `daily`).
Each range is a dict with `row`/`row_start`/`row_end` and `col`/`col_start`/`col_end` (0-indexed).

Based on original VBA macros: `efface_recap()`, `eff_trans()`, `efface_rapport_geac()`, `Eff_depot()`.

### DUEBACK_RECEPTIONIST_COLUMNS

Maps receptionist names to Excel column letters in the DUBACK# sheet.
24 receptionists from column C (Araujo) to column Y (ANNIE-LIS), plus Total in column Z.

### SETD_PERSONNEL_COLUMNS

Maps 135 personnel names to column letters (C through EI) in the SetD sheet.
Used by `SDParser` for fuzzy name matching.

### DUBACK_TO_SETD_MAPPING

Maps DueBack receptionist names to SetD equivalents for the `sync_duback_to_setd` operation.

### Helper Functions

```python
def get_dueback_row_for_day(day) -> (balance_row, operations_row)
```
Returns 0-based row indices. Day 1 = (4, 5), Day 11 = (24, 25).

```python
def get_setd_row_for_day(day) -> int
```
Returns 0-based row index. Day 1 = 5, Day 2 = 6, etc.

```python
def get_setd_cell(day, column_letter) -> str
```
Returns Excel cell reference, e.g. `get_setd_cell(15, 'I')` -> `'I19'`.

```python
def get_jour_row_for_day(day) -> int
```
Returns 0-indexed row for jour sheet. Uses `JOUR_DAY_ROW_OFFSET = 2`, so Day 1 = row 2.

### Jour Sheet Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `JOUR_RECAP_COLS` | [72..78] | Columns BU-CA in jour |
| `JOUR_RECAP_SOURCE` | Recap row 18, cols 7-13 | H19:N19 source range |
| `TRANSELECT_TOTAUX_ROW` | 37 | Row 38 in transelect (compact summary) |
| `TRANSELECT_TO_JOUR_CARD_MAP` | {0:60, 1:61, 2:62, 3:63, 4:64, 5:65} | Transelect col -> Jour col |
| `JOUR_TOTAL_COLUMNS` | 117 | Total columns in jour sheet |

---

## daily_rev_jour_mapping.py -- DAILY_REV_TO_JOUR

This module defines the comprehensive mapping from Daily Revenue report fields to
jour sheet columns. Each entry is keyed by column letter and contains:

```python
'AK': {
    'column_index': 36,
    'label_en': 'Chambres (minus Club Lounge)',
    'source_page': 'PAGE 1',
    'source_line': 'Chambres Total',
    'operation': 'subtract',           # direct | subtract | accumulate | formula | combined
    'base_field': 'revenue.chambres.total',
    'subtract_field': 'non_revenue.club_lounge.total',
    'sign_handling': 'keep_sign',      # keep_sign | negate_result | always_negative
}
```

### Operations

| Operation | Description | Example |
|-----------|-------------|---------|
| `direct` | Copy value as-is | `AL`: `revenue.telephones.local` |
| `subtract` | base - subtract_field | `AK`: chambres - club_lounge |
| `accumulate` | Sum list of `accumulator_fields` | `AY`: sum of all TPS sources |
| `formula` | Custom calculation | `D`: `-(balance.new_balance) - deposit_on_hand` |
| `combined` | Multiple sources combined | `CF`: AR misc + front office transfers |

### Column Groups

**Revenue departments (PAGE 1-2)**: AK (chambres), AL-AN (telephones), AO-AW (autres revenus/internet/comptabilite/sonifi/lit pliant/boutique)

**Taxes (PAGE 2-5)**: AX (TVQ accumulator), AY (TPS accumulator), AZ (taxe hebergement)

**Settlements (PAGE 6)**: BC (gift card accumulator), CC (certificat cadeaux)

**Balance (PAGE 7)**: D (new balance negative), CF (A/R misc + front office transfers)

**Sales Journal departments**: E-I (Cafe Link), J-N (Piazza), O-S (Spesa), T-X (Service Chambres), Y-AC (Banquet), AJ (Tabagie)

**HP deductions**: Columns matching HP parser output (jour_deductions col indices)

**Card totals (Transelect)**: BI-BN (amex_elavon, discover, master, visa, debit, amex_global)

**Recap summary**: BU-CA (copied from Recap H19:N19)

### Helper Functions

```python
col_letter_to_index(letter)  # 'AK' -> 36
col_index_to_letter(index)   # 36 -> 'AK'
```

### Adding New Mappings

1. Add an entry to `DAILY_REV_TO_JOUR` with the column letter as key
2. Set `column_index`, `operation`, and `base_field` (dot-path into parser extracted_data)
3. For accumulators, list all source fields in `accumulator_fields`
4. Set `sign_handling` to control sign behavior
5. The `JourMapper` will automatically pick it up in `compute_all()`
