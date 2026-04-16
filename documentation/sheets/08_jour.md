# Jour (Master Daily Output)

**Excel Sheet:** `jour` | **UI Tab:** None (computed) | **Dimensions:** 31 R x 117 C
**Template:** No dedicated tab -- jour is computed from other tabs
**Mapper:** utils/rj_mapper.py -> `DAILY_REV_TO_JOUR` (via daily_rev_jour_mapping.py)
**API:** POST /api/rj/fill-jour

## 1. Purpose

The jour sheet is the master daily output of the night audit workbook. It consolidates data from multiple sources -- daily revenue, sales journal, A/R summary, HP deductions, and manual entries -- into a single row per day of the month. With 117 columns and 31 day-rows, it is the most complex sheet in the RJ workbook.

Unlike other sheets that receive direct user input through the web UI, jour is a computed sheet. Its values are derived from parsers, macros, and cross-sheet operations. There is no dedicated UI tab for jour.

## 2. Sheet Layout

| Row | Content |
|-----|---------|
| 0 | Blank |
| 1 | Column headers |
| 2-32 | Days 1-31 (one row per day) |

**Row offset formula:** Day N is at row `JOUR_DAY_ROW_OFFSET + N - 1 = N + 1` (0-indexed). So Day 1 = row 2, Day 15 = row 16, Day 31 = row 32.

The 117 columns span multiple functional groups across the audit domain (revenue categories, taxes, card settlements, tips, recap output, etc.).

## 3. Field Classification

| Column(s) | Range | Content | Source | Type |
|-----------|-------|---------|--------|------|
| D | col 3 | New Balance | Formula: -(balance.new_balance) - deposit_on_hand | FORMULA / COMBINED |
| E-I | cols 4-8 | Cafe Link categories | SalesJournalParser (direct) | PARSED |
| J-N | cols 9-13 | Piazza categories | SalesJournalParser - HP deductions - adjustments | COMPUTED |
| O-S | cols 14-18 | Banquet/Link/Tabagie categories | SalesJournalParser | PARSED |
| T-X | cols 19-23 | Service Chambres categories | SalesJournalParser | PARSED |
| AK | col 36 | Chambres | DR total - club_lounge | COMPUTED |
| AL-AO | cols 37-40 | Telephones, Autres Revenus | DailyRevenueParser | PARSED |
| AX | col 49 | TVQ accumulator | Accumulated from 10 sources | ACCUMULATE |
| AY | col 50 | TPS accumulator | Accumulated from 10 sources | ACCUMULATE |
| BC | col 54 | Gift Card / Bons d'achat | Accumulator | ACCUMULATE |
| BF | col 57 | -Forfait + Club Lounge | Formula / combined | FORMULA |
| BI-BN | cols 60-65 | Card totals from transelect | calcul_carte macro | MACRO |
| BQ-BR | cols 68-69 | Tips from HP | HPExcelParser (direct write) | PARSED |
| BU-CA | cols 72-78 | Recap output | envoie_dans_jour macro | MACRO |
| CF | col 83 | A/R Misc + FO Transfers | ARSummaryParser (always_negative) | PARSED |

## 4. Cell Mappings (from rj_mapper.py)

The jour sheet does not use a traditional `{field_name: cell_ref}` mapping. Instead, `DAILY_REV_TO_JOUR` (defined in `daily_rev_jour_mapping.py`) maps source fields to column indices with operation types:

### Operation Types

| Operation | Description | Example |
|-----------|-------------|---------|
| `direct` | value = base_field | Cafe Link cols from SJ |
| `subtract` | value = base_field - subtract_field | Piazza cols (SJ - HP deductions) |
| `accumulate` | value = sum(accumulator_fields) | TVQ (col 49), TPS (col 50) |
| `formula` | Custom computation | Column D, BF, CF |
| `combined` | Multi-source merge | Columns using multiple parsers |

### Sign Handling Flags

| Flag | Behavior |
|------|----------|
| `keep_sign` | Preserve the original sign of the parsed value |
| `negate_result` | Multiply the final value by -1 |
| `always_negative` | Force the output to be negative (e.g., CF / col 83) |

### Filler Function

`fill_jour_day(day, jour_values)` writes a dict of `{col_index: value}` for a single day. The `day` parameter determines the target row via the offset formula.

### JourMapper.compute_all()

This is the central computation method. It processes every entry in `DAILY_REV_TO_JOUR`, applies the operation type and sign handling, and produces the final `{col_index: value}` dict for the day.

## 5. Macros & Operations

### envoie_dans_jour (Recap -> jour BU:CA)

Transfers computed values from the Recap sheet into jour columns 72-78 (BU through CA). This macro runs after the Recap sheet is filled and handles the cross-sheet propagation.

### calcul_carte (transelect -> jour BI:BN)

Transfers card-type totals from the transelect sheet into jour columns 60-65 (BI through BN). This macro runs after transelect data is available.

### HP Deduction Logic

The HPExcelParser produces deduction values that are subtracted from Sales Journal amounts for specific columns (primarily the Piazza group, cols 9-13).

**New format:** `jour_deductions` dict with `{col_index_str: amount}` -- amounts are subtracted from the corresponding SJ column values.

**Legacy format:** Flat keys (`piazza_nourr`, `tabagie_nourr`, etc.) mapped to known columns.

**Exception -- BQ (68) / BR (69):** These are direct writes (tip amounts), not deductions. HP parser writes tip values directly to these columns without subtracting from anything.

### Reset

There is no reset range for the jour sheet itself. The related `daily` sheet has reset range `B2:B41, B44, B47`.

## 6. Data Flow

```
DailyRevenueParser (PDF)
    |
    +--> revenue, taxes, settlements, balance
    |
SalesJournalParser (Text/RTF)
    |
    +--> restaurant department sales (Cafe Link, Piazza, Banquet, etc.)
    |
ARSummaryParser (Excel)
    |
    +--> A/R activity --> CF (col 83)
    |
HPExcelParser (Excel)
    |
    +--> deductions (subtract from SJ cols)
    +--> tips (direct write to BQ/BR)
    |
Manual values
    |
    +--> club_lounge, deposit_on_hand
    |
    v
JourMapper.compute_all()
    |
    +--> applies DAILY_REV_TO_JOUR mappings
    +--> handles operation types + sign flags
    |
    v
fill_jour_day(day, jour_values)
    |
    v
jour sheet row N+1

Macros (post-fill):
    Recap ----envoie_dans_jour----> jour BU:CA (cols 72-78)
    transelect --calcul_carte-----> jour BI:BN (cols 60-65)
```

## 7. UI Implementation

There is no dedicated UI tab for the jour sheet. It is filled programmatically via:

- **POST /api/rj/fill-jour** -- the dedicated API endpoint (not accessible through the generic `/api/rj/fill/{sheet}` pattern)
- Cross-sheet macros triggered after other tabs are filled
- The user interacts with source sheets (Daily Revenue, Sales Journal, etc.) and jour is populated as a downstream effect

## 8. Known Issues & Gotchas

- **117 columns:** The sheer width makes debugging difficult. Column indices are the primary reference (not letter codes) in the mapper logic.
- **No direct UI:** Users cannot manually edit jour through the web app. If a value is wrong, the source sheet or parser output must be corrected and jour re-filled.
- **HP deduction dual behavior:** Columns BQ/BR (68/69) are direct writes while all other HP values are subtractions. Mixing these up will produce incorrect jour output.
- **Legacy vs new HP format:** Both formats must be supported. The new `jour_deductions` dict format is preferred but older data may use flat keys.
- **Sign handling is critical:** Incorrect sign flags will silently produce wrong values. The `always_negative` flag on CF (col 83) and `negate_result` on certain fields are easy to overlook.
- **Column D (New Balance):** This is a formula column: `-(balance.new_balance) - deposit_on_hand`. The `deposit_on_hand` value is manual input and must be provided separately.
- **Row offset:** Day numbering starts at 1 but rows are 0-indexed with an offset. Off-by-one errors here will write data to the wrong day.
- **Macro ordering matters:** `envoie_dans_jour` and `calcul_carte` must run after their source sheets are filled. Running them prematurely will write stale or empty values.
- **No reset for jour:** Unlike other sheets, jour has no reset range. Refilling a day overwrites the existing row, but orphaned data in unfilled columns will persist.
