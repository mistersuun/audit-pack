# Macro Implementations

Source: `utils/rj_filler.py` (Python), `routes/audit/rj_macros.py` (API endpoints)

The original RJ workbook contained VBA macros for common operations. These have been
reimplemented in Python within the `RJFiller` class. Each macro reads from the xlrd
read-only workbook (`self.rb`) and writes to the xlwt writable copy (`self.wb`).

---

## reset_tabs

**VBA origin**: `efface_recap()`, `eff_trans()`, `efface_rapport_geac()`, `Eff_depot()`

**Python method**: `RJFiller.reset_tabs()`

**Purpose**: Clear specific data ranges in Recap, transelect, geac_ux, and depot sheets
when starting a new audit day.

**Inputs**: None (uses `RESET_RANGES` from `rj_mapper.py`)

**Outputs**: Returns count of cells cleared.

**Behavior**: Iterates over `RESET_RANGES` dict. For each sheet, iterates over range
definitions and writes `None` to each cell in the range.

**Trigger endpoint**: `POST /api/rj/reset`

**Response**:
```json
{
    "success": true,
    "message": "Onglets reinitialisees avec succes (N cellules effacees)",
    "cleared_count": 245
}
```

---

## reset_single_tab

**VBA origin**: Individual clear macros (e.g. `efface_recap()` alone)

**Python method**: `RJFiller.reset_single_tab(sheet_name)`

**Purpose**: Clear data ranges for a single sheet only.

**Inputs**: `sheet_name` -- one of `'Recap'`, `'transelect'`, `'geac_ux'`, `'depot'`, `'daily'`

**Outputs**: Returns count of cells cleared.

**Trigger endpoint**: `POST /api/rj/reset/<sheet_name>`

**Response**:
```json
{
    "success": true,
    "message": "Recap efface (N cellules)",
    "sheet": "Recap",
    "cleared_count": 42
}
```

---

## envoie_dans_jour

**VBA origin**: `envoie_dans_jour()` macro

**Python method**: `RJFiller.envoie_dans_jour(day=None)`

**Purpose**: Copy the Recap summary row (H19:N19, 7 values) into the jour sheet
at the row for the specified day, columns BU through CA (indices 72-78).

**Inputs**: `day` (int, 1-31). If None, reads from controle B3 (vjour).

**Outputs**: Dict with `day`, `recap_values` (list of 7 values), `target_row`, `columns`.

**Source cells**: Recap row 18 (0-indexed), columns 7-13 (H through N)

**Target cells**: Jour row = `JOUR_DAY_ROW_OFFSET + day - 1`, columns `JOUR_RECAP_COLS` (72-78)

**Trigger endpoint**: `POST /api/rj/macro/envoie-jour`

**Request body** (optional):
```json
{ "day": 23 }
```

**Response**:
```json
{
    "success": true,
    "message": "Recap envoye dans jour pour le jour 23",
    "data": {
        "day": 23,
        "recap_values": [100.0, 200.0, ...],
        "target_row": 24,
        "columns": "BU:CA"
    }
}
```

---

## calcul_carte

**VBA origin**: `calcul_carte()` macro

**Python method**: `RJFiller.calcul_carte(day=None)`

**Purpose**: Copy credit card totals from the transelect compact summary row (row 37, 0-indexed)
into the jour sheet for the specified day.

**Inputs**: `day` (int, 1-31). If None, reads from controle B3.

**Source**: Transelect row 37, columns 0-5 (amex_elavon, discover, master, visa, debit, amex_global)

**Target**: Jour row for day, columns BI(60), BJ(61), BK(62), BL(63), BM(64), BN(65)

**Mapping** (from `TRANSELECT_TO_JOUR_CARD_MAP`):

| Transelect Col | Jour Col | Card Type |
|---|---|---|
| 0 | 60 (BI) | Amex Elavon |
| 1 | 61 (BJ) | Discover |
| 2 | 62 (BK) | MasterCard |
| 3 | 63 (BL) | Visa |
| 4 | 64 (BM) | Debit |
| 5 | 65 (BN) | Amex Global |

**Trigger endpoint**: `POST /api/rj/macro/calcul-carte`

**Request body** (optional):
```json
{ "day": 23 }
```

**Response**:
```json
{
    "success": true,
    "message": "Cartes calculees pour le jour 23",
    "data": {
        "day": 23,
        "card_totals": { "amex_elavon": 5000.0, "visa": 12000.0, ... },
        "target_row": 24,
        "columns": "BI/BJ/BK/BL/BM/BN"
    }
}
```

---

## sync_duback_to_setd

**VBA origin**: Manual copy-paste from DUBACK# to SetD

**Python method**: `RJFiller.sync_duback_to_setd(current_day)`

**Purpose**: Read DueBack amounts for the current day from DUBACK# sheet and write
the matching values into the SetD sheet.

**Inputs**: `current_day` (int, 1-31)

**Outputs**: Number of updates made.

**Behavior**:
1. Read DUBACK# header row (row 1) to map receptionist names to columns
2. Read the operations row for the target day using `get_dueback_row_for_day()`
3. For each name with a numeric value, look up the corresponding SetD column
   using `DUBACK_TO_SETD_MAPPING` (name translation) and header matching
4. Write the value to SetD at the target day's row

**Trigger endpoint**: `POST /api/rj/sync`

**Request body** (optional):
```json
{ "day": 23 }
```

If `day` is omitted, reads from controle B3.

---

## fill_jour_day

**VBA origin**: No direct VBA equivalent -- this is a new Python-only operation that
replaces manual data entry across 100+ jour columns.

**Python method**: `RJFiller.fill_jour_day(day, jour_values)`

**Purpose**: Write computed values from `JourMapper.compute_all()` to the jour sheet
for a specific day.

**Inputs**:
- `day` (int, 1-31)
- `jour_values` (dict `{column_index: value}`)

**Outputs**: Dict with `day`, `filled_count`, `target_row`, `columns_filled`.

**Target row**: `get_jour_row_for_day(day)` = `JOUR_DAY_ROW_OFFSET + day - 1`

**Trigger endpoint**: `POST /api/rj/fill-jour`

**Request body**:
```json
{
    "day": 23,
    "parsed_data": {
        "daily_revenue": { ... },
        "sales_journal": { ... },
        "hp_excel": { ... }
    },
    "manual_values": {
        "club_lounge": 0,
        "deposit_on_hand": 5000
    },
    "adjustments": []
}
```

---

## Other RJFiller Methods

### update_controle(vjour, mois, annee, idate)

Updates the controle sheet with day/date values. Computes Excel date serial number
if idate is not provided. Triggered by `POST /api/rj/controle`.

### fill_dueback_day(day, receptionist, amount, line_type)

Fills a single DueBack entry for a specific day and receptionist.
`line_type='previous'` writes to the balance row; `'nouveau'` writes to the operations row.

### fill_dueback_by_col(day, col_letter, amount, line_type)

Same as above but uses column letter directly (for dynamic receptionists).

### fill_setd_day(day, amount, account_col)

Fills a SetD entry for a specific day and column.

### update_deposit(date_str, amount)

Writes a verified deposit amount to the depot tab, matching by date or appending to first empty row.
