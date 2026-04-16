# Nettoyeur / Sommaire Nettoyeur (Staff Gratuities Detail + Summary)

**Excel Sheet:** `nettoyeur`, `sommaire_nettoyeur` | **UI Tab:** None | **Dimensions:** Variable
**Template:** No dedicated tab in the web UI
**Mapper:** No dedicated mapper entries
**API:** No dedicated API endpoints

## 1. Purpose

These are two related minor sheets that track staff gratuities:

1. **Nettoyeur (Staff Gratuities Detail):** Daily per-employee breakdown of tips received across various sources.
2. **Sommaire Nettoyeur (Gratuities Summary):** Monthly summary of gratuities aggregated by employee and department.

These sheets are peripheral to the core night audit workflow. They serve as a record-keeping mechanism for gratuity distribution rather than a reconciliation tool.

## 2. Sheet Layout

### Nettoyeur (Detail)

| Section | Content |
|---------|---------|
| Header | Employee names and department identifiers |
| Body | Daily tip amounts per employee from various POS and payment sources |
| Footer | Period totals per employee |

### Sommaire Nettoyeur (Summary)

| Section | Content |
|---------|---------|
| Header | Month/period identifier |
| Body | Monthly accumulated gratuities by employee |
| Footer | Department-level gratuity summaries and grand totals |

## 3. Field Classification

| Field Category | Type | Source |
|----------------|------|--------|
| Employee names | STATIC / USER_INPUT | Entered directly in Excel |
| Department codes | STATIC / USER_INPUT | Entered directly in Excel |
| Daily tip amounts | USER_INPUT | POS reports / manual entry |
| Monthly totals | FORMULA | Excel SUM formulas |
| Department summaries | FORMULA | Excel aggregation formulas |

## 4. Cell Mappings (from rj_mapper.py)

There are no dedicated cell mappings for these sheets in `rj_mapper.py`. The nettoyeur and sommaire nettoyeur sheets are not managed through the web application's fill system.

## 5. Macros & Operations

No macros, no reset ranges, no autofill operations.

The only programmatic connection to these sheets is indirect: the HPExcelParser extracts tip data that populates columns BQ (col 68) and BR (col 69) in the jour sheet. This tip data relates to the same gratuity figures tracked in the nettoyeur sheets, but the data flows are independent -- HP tips go to jour, while nettoyeur is maintained separately.

## 6. Data Flow

```
POS Reports (manual)
    |
    v
Nettoyeur sheet (direct Excel entry)
    |
    v (monthly aggregation via Excel formulas)
Sommaire Nettoyeur sheet

Separate but related:
HPExcelParser --> jour BQ/BR (tips)
                  (same underlying data, independent flow)
```

## 7. UI Implementation

There is no dedicated tab in the web UI for either sheet. All data entry and review happens directly in the Excel workbook. The web application does not read from or write to these sheets.

## 8. Known Issues & Gotchas

- **Not managed by the web app:** These sheets exist only in the Excel workbook. Any automation or validation must be done in Excel directly.
- **Indirect relationship to jour:** The HP-parsed tip values in jour BQ/BR and the nettoyeur detail may represent the same underlying data. Discrepancies between them must be reconciled manually.
- **Variable dimensions:** The sheet size depends on the number of employees, which can change month to month. There is no fixed layout assumed by any code.
- **Manual maintenance burden:** Since these sheets are outside the automated pipeline, they are prone to data entry errors and delayed updates.
