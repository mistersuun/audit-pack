# Diff.Caisse# - Cash Register Variance ([Diff.Caisse#])

**Excel Sheet:** `Diff.Caisse#` | **Dimensions:** 38 rows x 39 cols
**Parsed by:** Not directly parsed by web app (Excel formula-driven)
**Database model:** Linked indirectly via Recap `jour` Column C (Diff.Caisse)

## 1. Purpose

The Diff.Caisse# sheet tracks daily cash register variances -- the difference between the system-reported totals and the physically counted cash for each register/terminal. It provides a day-by-day, register-by-register view of cash over/short positions. This is an essential audit control sheet: persistent variances on specific registers or specific days trigger investigation. The daily totals from this sheet feed into the Recap sheet's jour Column C.

## 2. Sheet Layout

- **Row 0 (header):** `Jour` followed by register identifiers (`geac ux` repeated across columns for each terminal).
- **Rows 2-32:** Days 1 through 31 of the month, one row per day.
- **Rows 33-38:** Summary rows (monthly totals, averages, or notes).
- **Column B:** Aggregate daily cash difference across all registers.
- **Columns C-AM (approx):** Individual register/terminal variance columns, with `geac ux` headers identifying each POS terminal.
- **39 columns** accommodate the day label, the daily aggregate, and variances for each individual register.

## 3. Column Reference

| Col | Header         | Type    | Description                                          |
|-----|----------------|---------|------------------------------------------------------|
| A   | Jour           | Integer | Day of the month (1-31)                              |
| B   | (daily total)  | Float   | Net cash variance for the day across all registers   |
| C   | geac ux        | Float   | Cash variance for register/terminal 1                |
| D   | geac ux        | Float   | Cash variance for register/terminal 2                |
| ... | geac ux        | Float   | Additional register/terminal variances               |
| AM  | geac ux        | Float   | Cash variance for last tracked register              |

## 4. Sample Data

```
Jour | Daily Total | Reg 1  | Reg 2  | Reg 3  | ...
-----|-------------|--------|--------|--------|----
  1  |      0.00   |  0.00  |  0.00  |  0.00  |
  2  |   -527.71   | -312.40| -215.31|   0.00 |
  3  |    683.85   |  400.00|  150.00| 133.85 |
  ...
```

- Day 2 shows a total cash short of -527.71 spread across two registers.
- Day 3 shows a cash over of 683.85 distributed across three registers.

## 5. Data Flow

```
POS terminals (GEAC UX)
  -> Excel formulas in Diff.Caisse# sheet
    -> Daily aggregate (Column B)
      -> Recap sheet jour Column C (Diff.Caisse value)
        -> Recap surplus/deficit tracking
```

- This sheet is **formula-driven within Excel** and not directly parsed by the web application.
- The daily totals in Column B are referenced by the Recap sheet's `jour` tab to populate the Diff.Caisse column.
- The Recap parser picks up the aggregated value indirectly.

## 6. Integration Status

| System      | Status                                                              |
|-------------|---------------------------------------------------------------------|
| Web app     | Not directly parsed; values flow through Recap indirectly           |
| CRM         | Not integrated                                                      |
| Analytics   | Available only via Recap's Diff.Caisse column currently             |

## 7. Analytics Potential

- **Register-level variance tracking:** Identify specific terminals with chronic over/short patterns.
- **Daily anomaly detection:** Flag days where the aggregate variance exceeds a configurable threshold.
- **Staff correlation:** Cross-reference variance patterns with shift schedules to identify training needs or procedural issues.
- **Trend analysis:** Plot daily variances over the month to detect escalating or resolving patterns.
- **Audit trail:** Maintain historical variance data per register for year-over-year comparison.
- **Direct parsing opportunity:** Implementing a dedicated parser for this sheet would enable register-level analytics in the web app rather than relying solely on the Recap aggregate.
