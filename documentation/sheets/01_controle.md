# Controle (Controle)

**Excel Sheet:** `Controle` | **UI Tab:** Nouveau Jour | **Dimensions:** ~28 rows x 2 cols (A-B)
**Template:** `templates/audit/rj/tabs/nouveau_jour.html`
**Mapper:** `utils/rj_mapper.py` -> `CONTROLE_MAPPING`
**API:** `POST /api/rj/controle` and `POST /api/rj/autofill-controle`

## 1. Purpose

The Controle sheet is the master control panel for the daily audit. It stores the current audit date, hotel metadata, weather conditions, and year-to-date performance statistics. All other sheets in the RJ workbook reference the date and named ranges defined here, making it the first sheet that must be filled when starting a new day.

## 2. Sheet Layout

```
     A                          B
  +--------------------------+----------------------------+
1 |                          |                            |
2 | Prepare par              | [name]                     |  B2
3 | Jour                     | [DD]                       |  B3
4 | Mois                     | [MM]                       |  B4
5 | Annee                    | [YYYY]                     |  B5
6 | Temperature              | [value]                    |  B6
7 | Condition                | [weather text]             |  B7
8 |                          |                            |
9 | Chambres a refaire       | [count]                    |  B9
10| Vente dollar annuel YTD  | [amount]                   |  B10
11| Vente dollar annuel prev | [amount]                   |  B11
12| Ch. disponible YTD       | [count]                    |  B12
13| Ch. disponible prev      | [count]                    |  B13
14| Ch. Occupees YTD         | [count]                    |  B14
15| Ch. Occupees prev        | [count]                    |  B15
16| Revenu Chambre YTD       | [amount]                   |  B16
17| Revenu Chambre prev      | [amount]                   |  B17
18| Balance de fermeture     | [amount]                   |  B18
19|                          |                            |
20| Hotel                    | HOTEL SHERATON LAVAL       |  B20
21| Total Rooms              | 252                        |  B21
22-26|                       |                            |
27| Days in month            | [28-31]                    |  B27
28| Audit date               | [Excel serial date]        |  B28
  +--------------------------+----------------------------+
```

### Sections

- **Rows 2-7:** Date identification and weather
- **Row 9:** Housekeeping info
- **Rows 10-18:** Year-to-date and prior-year performance comparisons
- **Rows 20-21:** Hotel constants
- **Rows 27-28:** Derived date values

## 3. Field Classification

| Cell | Field Name | Type | Source | Notes |
|------|-----------|------|--------|-------|
| B2 | prepare_par | USER_INPUT | Manual | Name of the person preparing the audit |
| B3 | jour | USER_INPUT | Manual | Day of month (DD), integer 1-31 |
| B4 | mois | USER_INPUT | Manual | Month (MM), integer 1-12 |
| B5 | annee | USER_INPUT | Manual | Year (YYYY), e.g. 2026 |
| B6 | temperature | USER_INPUT | Manual / Autofill | Temperature value |
| B7 | condition | USER_INPUT | Manual / Autofill | Weather condition text (e.g. "Ensoleille") |
| B9 | chambres_refaire | USER_INPUT | Manual | Number of rooms to redo |
| B10 | dollar_sales_ytd | USER_INPUT | Manual | Dollar sales year-to-date |
| B11 | dollar_sales_prev | USER_INPUT | Manual | Dollar sales previous year |
| B12 | rooms_available_ytd | USER_INPUT | Manual | Rooms available year-to-date |
| B13 | rooms_available_prev | USER_INPUT | Manual | Rooms available previous year |
| B14 | rooms_occupied_ytd | USER_INPUT | Manual | Rooms occupied year-to-date |
| B15 | rooms_occupied_prev | USER_INPUT | Manual | Rooms occupied previous year |
| B16 | room_revenue_ytd | USER_INPUT | Manual | Room revenue year-to-date |
| B17 | room_revenue_prev | USER_INPUT | Manual | Room revenue previous year |
| B18 | closing_balance | USER_INPUT | Manual | Closing balance amount |
| B20 | hotel_name | USER_INPUT | Manual | Hotel name constant ("HOTEL SHERATON LAVAL") |
| B21 | total_rooms | USER_INPUT | Manual | Total room count (252) |
| B27 | days_in_month | USER_INPUT | Manual | Number of days in the audit month (28-31) |
| B28 | audit_date | AUTO_CALCULATED | B3/B4/B5 | Excel serial date computed from jour/mois/annee |

## 4. Cell Mappings (from rj_mapper.py)

```python
CONTROLE_MAPPING = {
    'jour': 'B3',              # Day (DD)
    'mois': 'B4',              # Month (MM)
    'annee': 'B5',             # Year (YYYY)
    'temperature': 'B6',       # Temperature
    'condition': 'B7',         # Weather condition
    'chambres_refaire': 'B9',  # Rooms to redo
    'prepare_par': 'B2',       # Prepared by
    'dollar_sales_ytd': 'B10',       # Vente dollar annuel (YTD)
    'dollar_sales_prev': 'B11',      # Vente dollar annuel (previous year)
    'rooms_available_ytd': 'B12',    # Ch. disponible (YTD)
    'rooms_available_prev': 'B13',   # Ch. disponible (previous year)
    'rooms_occupied_ytd': 'B14',     # Ch. Occupees (YTD)
    'rooms_occupied_prev': 'B15',    # Ch. Occupees (previous year)
    'room_revenue_ytd': 'B16',       # Revenu Chambre (YTD)
    'room_revenue_prev': 'B17',      # Revenu Chambre (previous year)
    'closing_balance': 'B18',        # Balance de fermeture
    'hotel_name': 'B20',             # HOTEL SHERATON LAVAL
    'total_rooms': 'B21',            # 252
    'days_in_month': 'B27',          # e.g. 28, 31
    'audit_date': 'B28',             # Excel serial date
}
```

## 5. Macros & Operations

### Reset Operation

No reset ranges are defined for the Controle sheet. Fields persist across days and are overwritten by the filler method when a new day is initialized.

### Sync Operations

- **No macros act on this sheet directly.** Controle is a source sheet -- other sheets reference its named ranges.
- The filler method `RJFiller.update_controle(vjour, mois, annee, idate)` writes date fields and then calls `fill_sheet('controle', data)` to populate all mapped cells.

### Validation Rules

- `jour` must be between 1 and `days_in_month` (B27)
- `mois` must be between 1 and 12
- `annee` must be a 4-digit year
- `audit_date` (B28) is an Excel serial date derived from the three date components; it must not be manually edited

## 6. Data Flow

### Inputs

- User enters date (jour/mois/annee) and hotel statistics via the "Nouveau Jour" UI tab
- Autofill endpoint (`POST /api/rj/autofill-controle`) can populate weather and YTD fields automatically

### Outputs

- Named ranges for date values consumed by all other RJ sheets
- `audit_date` (B28) used as reference date across the workbook
- `days_in_month` (B27) determines valid row ranges in sheets like DueBack and Jour

```
  [UI: Nouveau Jour]
        |
        v
  POST /api/rj/controle
        |
        v
  RJFiller.update_controle()
        |
        v
  +-------------+
  |  Controle    |-----> Named ranges (date, hotel info)
  |  B2-B28     |-----> Referenced by: Recap, DueBack, Jour, SetD, etc.
  +-------------+
```

## 7. UI Implementation

- **Template:** `templates/audit/rj/tabs/nouveau_jour.html`
- **Form fields:** Date picker or manual entry for jour/mois/annee, text inputs for all other fields
- **Special behaviors:**
  - The autofill button triggers `POST /api/rj/autofill-controle` to populate weather data (temperature, condition) and YTD statistics from external sources
  - Changing the date triggers recalculation of `audit_date` (B28) and `days_in_month` (B27)
  - Hotel name (B20) and total rooms (B21) are typically pre-filled constants

## 8. Known Issues & Gotchas

- **B28 is an Excel serial date**, not a human-readable date string. Writing a text date here will break formulas in other sheets that depend on it.
- **No reset means stale data risk.** If a field from the previous day is not overwritten (e.g. `chambres_refaire`), it carries forward silently.
- **B20 and B21 are constants** (hotel name and total rooms) but are mapped as editable fields. Changing them could affect calculations throughout the workbook.
- The YTD vs previous-year fields (B10-B17) are paired comparisons. Entering data in only one of each pair will produce misleading variance calculations in downstream sheets.
