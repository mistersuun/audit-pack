# DueBack (DueBack)

**Excel Sheet:** `DueBack` | **UI Tab:** DueBack | **Dimensions:** 65 rows x 26 cols (A-Z)
**Template:** `templates/audit/rj/tabs/dueback.html`
**Mapper:** `utils/rj_mapper.py` -> `DUEBACK_RECEPTIONIST_COLUMNS`
**API:** `POST /api/rj/fill/dueback`, `POST /api/rj/dueback/bulk`, `POST /api/rj/dueback/save`

## 1. Purpose

The DueBack sheet tracks cash due-back balances and daily operations for each receptionist across the entire month. Each day occupies two rows: a balance row showing running totals and an operations row recording the day's transactions. Column Z aggregates the total across all receptionists plus the R/J carry-forward. The sheet feeds due-back values into the Recap sheet (B16/B17) and syncs to the SetD sheet via macro.

## 2. Sheet Layout

```
     A        B (R/J)    C (Araujo)  D (Latulippe) ... Y (ANNIE-LIS)  Z (Total)
  +--------+----------+------------+--------------+---+--------------+----------+
1 | Header |          |            |              |   |              |          |
2 | Header |          |            |              |   |              |          |
3 | Header |          |            |              |   |              |          |
  +--------+----------+------------+--------------+---+--------------+----------+
4 | Day 1  | [R/J]    | [balance]  | [balance]    |   | [balance]    | =SUM+B   |  balance row
5 | (ops)  |          | [ops]      | [ops]        |   | [ops]        | =SUM+B   |  operations row
  +--------+----------+------------+--------------+---+--------------+----------+
6 | Day 2  | [R/J]    | [balance]  | [balance]    |   | [balance]    | =SUM+B   |  balance row
7 | (ops)  |          | [ops]      | [ops]        |   | [ops]        | =SUM+B   |  operations row
  +--------+----------+------------+--------------+---+--------------+----------+
  ...
  +--------+----------+------------+--------------+---+--------------+----------+
64| Day 31 | [R/J]    | [balance]  | [balance]    |   | [balance]    | =SUM+B   |  balance row
65| (ops)  |          | [ops]      | [ops]        |   | [ops]        | =SUM+B   |  operations row
  +--------+----------+------------+--------------+---+--------------+----------+
```

### Row Addressing Formula

For any day X (1-31):
- **Balance row** = `2 + (X * 2)` (0-indexed), i.e. Excel row = `3 + (X * 2) - 1` = `2 + X*2`
- **Operations row** = balance_row + 1

| Day | Balance Row | Operations Row |
|-----|-------------|----------------|
| 1   | 4           | 5              |
| 2   | 6           | 7              |
| 3   | 8           | 9              |
| ... | ...         | ...            |
| 15  | 32          | 33             |
| 28  | 58          | 59             |
| 31  | 64          | 65             |

### Column Structure

- **Column A:** Row labels / day indicators
- **Column B (R/J):** Read-only reference to the Jour sheet's previous total due-back balance (carry-forward from prior day)
- **Columns C-Y:** 23 individual receptionists
- **Column Z (Total):** Formula = SUM(C:Y) + B for each row

## 3. Field Classification

| Cell Range | Field Name | Type | Source | Notes |
|------------|-----------|------|--------|-------|
| B (all rows) | R/J carry-forward | FORMULA / AUTO_FILL | Jour sheet | Previous day's total due-back; read-only |
| C4:Y4 | Day 1 balances | USER_INPUT | Manual | Balance per receptionist |
| C5:Y5 | Day 1 operations | USER_INPUT | Manual | Daily operations per receptionist |
| C6:Y65 | Days 2-31 | USER_INPUT | Manual | Same pattern for all remaining days |
| Z (all rows) | Total | FORMULA | =SUM(C:Y)+B | Row total across all receptionists plus R/J |

## 4. Cell Mappings (from rj_mapper.py)

```python
DUEBACK_RECEPTIONIST_COLUMNS = {
    'Araujo': 'C',
    'Latulippe': 'D',
    'Caron': 'E',
    'Nader': 'F',
    'Mompremier': 'G',
    'oppong': 'H',
    'SEDDIK': 'I',
    'Kimberly': 'J',
    'AYA': 'K',
    'Leo': 'L',
    'THANKARAJAH': 'M',
    'CINDY': 'N',
    'Manolo': 'O',
    'MOUATARIF': 'P',
    'KRAY': 'Q',
    'NITHYA': 'R',
    'DAMAL': 'S',
    'MAUDE': 'T',
    'OLGA': 'U',
    'Sylvie': 'V',
    'Emery': 'W',
    'Ben mansour': 'X',
    'ANNIE-LIS': 'Y',
    'Total': 'Z',           # Formula column -- SUM(C:Y) + B
}
```

**Note:** Receptionist names have inconsistent casing (e.g. `oppong` lowercase, `SEDDIK` uppercase, `Ben mansour` mixed). The mapper keys must match exactly as defined.

## 5. Macros & Operations

### Reset Operation

No explicit reset ranges are documented for the DueBack sheet. Day rows are addressed individually based on the current audit date.

### Sync Operations

- **`sync_duback_to_setd()`**: Reads the operations row for the current day and writes values to the SetD sheet via `DUBACK_TO_SETD_MAPPING`. This keeps the SetD (Settlement Detail) sheet synchronized with due-back activity.

### Validation Rules

- Column B values are read-only references; writing to them will break the carry-forward chain.
- Column Z is a formula column; writing to it will overwrite the SUM formula.
- Day rows beyond `days_in_month` (from Controle B27) should not be populated.
- Operations row values represent daily changes; balance row values represent cumulative running totals.

## 6. Data Flow

### Inputs

- User enters due-back amounts per receptionist per day via the DueBack UI
- Column B is auto-filled from the Jour sheet's previous total due-back balance
- Bulk entry is supported via the `/api/rj/dueback/bulk` endpoint

### Outputs

- Due-back totals feed into Recap B16 (due_back_reception) and B17 (due_back_nb)
- Operations row data is synced to SetD via `sync_duback_to_setd()`
- Column Z totals provide the daily aggregate

```
  +-------------+
  |  Jour sheet |----> Column B (R/J carry-forward)
  +-------------+
        |
        v
  +------------------------------------------------------+
  |                    DueBack Sheet                      |
  |  B (R/J)  |  C-Y (23 receptionists)  |  Z (Total)   |
  |  read-only |  USER_INPUT per day      |  FORMULA      |
  +------------------------------------------------------+
        |                    |
        |                    v
        |            sync_duback_to_setd()
        |                    |
        v                    v
  +-------------+    +-------------+
  | Recap sheet |    |  SetD sheet |
  | B16, B17    |    | (mapped)    |
  +-------------+    +-------------+
```

## 7. UI Implementation

- **Template:** `templates/audit/rj/tabs/dueback.html`
- **API Endpoints:**
  - `POST /api/rj/fill/dueback` -- Write a single cell (one receptionist, one day)
  - `POST /api/rj/dueback/bulk` -- Write multiple entries at once
  - `POST /api/rj/dueback/save` -- Save all entries for a given day
  - `GET /api/rj/dueback/names` -- Retrieve the list of receptionist names (keys from `DUEBACK_RECEPTIONIST_COLUMNS`)
  - `GET /api/rj/dueback/total` -- Retrieve the column Z total for a given day
  - `GET /api/rj/dueback/column-b` -- Retrieve the R/J carry-forward values from column B
- **Form layout:**
  - Grid/table view with receptionists as columns and the current day's balance/operations as rows
  - Column B displayed as read-only (greyed out or disabled)
  - Column Z displayed as computed total (read-only)
  - Save button triggers `POST /api/rj/dueback/save` for the active day
- **Special behaviors:**
  - The receptionist list is dynamic -- fetched from `/api/rj/dueback/names`
  - Bulk save reduces round-trips compared to individual cell writes
  - The UI should distinguish between the balance row and the operations row for clarity

## 8. Known Issues & Gotchas

- **Receptionist name casing is inconsistent** (`oppong` vs `SEDDIK` vs `Ben mansour`). All lookups must use the exact key strings from `DUEBACK_RECEPTIONIST_COLUMNS`. Case normalization will break the mapping.
- **Row addressing is offset-based**, not direct Excel row references. The formula `2 + (day * 2)` uses 0-indexed rows. Off-by-one errors are common when converting between the internal addressing and Excel's 1-based row numbers.
- **Column B is read-only.** Writing to column B will break the carry-forward chain from the Jour sheet. The UI must prevent edits to this column.
- **Column Z contains formulas.** Overwriting Z cells with literal values will destroy the SUM formulas. Only columns C through Y should receive user input.
- **Days beyond `days_in_month` exist in the sheet** (rows always go to day 31). Writing data to day 29-31 in a month with fewer days will not cause an error but the data will be orphaned and potentially confusing.
- **The sync macro name has a typo** (`sync_duback_to_setd` -- missing an "e" in "dueback"). This is intentional in the codebase and must be referenced exactly as spelled.
- **23 receptionists is a fixed layout.** Adding or removing receptionists requires updating `DUEBACK_RECEPTIONIST_COLUMNS`, the Excel sheet structure, and the column Z formula range.
