# Budget - Annual/Monthly Targets ([Budget])

**Excel Sheet:** `Budget` | **Dimensions:** 134 rows x 17 cols
**Parsed by:** `rj_sheet_parser.py` -> `parse_budget_sheet()`
**Database model:** `MonthlyBudget` -> `BudgetAnalyzer`

## 1. Purpose

The Budget sheet holds annual and month-to-date budget targets for all revenue and expense categories. Each row maps a budget category to its annual target, a named range key for programmatic lookup, and MTD budget figures. This sheet is the reference point for all variance analysis -- comparing actual performance (from Recap, EJ, and other sheets) against planned targets. It feeds directly into the Rapp_p1 report for budget vs actual comparison.

## 2. Sheet Layout

- **Rows 1-134:** One budget category per row.
- **Column structure:** Category name, annual budget amount, intermediate columns, named range key, MTD budget, and additional breakdown columns.
- **17 columns** provide enough width for annual total, monthly allocations, and named range identifiers.
- Categories cover all hotel revenue streams: rooms, food & beverage by outlet, banquet, equipment, telecom, laundry, and miscellaneous.

## 3. Column Reference

| Col | Header              | Type    | Description                                           |
|-----|---------------------|---------|-------------------------------------------------------|
| A   | Category            | String  | Budget line item name (French)                        |
| B   | Annual Budget       | Float   | Full-year budget target                               |
| C-L | (monthly/interim)   | Mixed   | Monthly allocations or intermediate calculation fields|
| M   | Named Range Key     | String  | Programmatic key for lookups (e.g., `BU_VE_CHAMBRE`) |
| N   | MTD Budget          | Float   | Month-to-date budget figure                           |
| O-Q | (additional)        | Mixed   | Supplementary breakdown or variance fields            |

## 4. Sample Data

| Category                        | Annual Budget | Named Range Key     |
|---------------------------------|---------------|---------------------|
| Chambres                        | 1,112,404     | BU_VE_CHAMBRE       |
| Nour. Piazza/Bar                | 370,000       | BU_VE_NOUREST       |
| Nour. Banquet                   | 750,000       | BU_VE_NOUBQT        |
| Nour. Marche                    | 32,500        | BU_VE_NOUJAR        |
| Nour. Pause Marche              | 16,000        | BU_VE_NOUBAR        |
| Nour. Serv.Ch.                  | 8,264         | BU_VE_NOUSERCH      |
| Boisson Piazza/Bar              | 137,875       | BU_VE_BOIREST       |
| Boisson Banquet                 | 245,000       | BU_VE_BOIBQT        |
| Location de Salles              | 150,000       | BU_VE_LOCSALLE      |
| Equipement & Divers banquet     | 120,000       | BU_VE_EQUIPEMENT    |
| Tel Inter                       | 72            | (telecom key)       |
| Tel Local                       | 29            | (telecom key)       |
| Buanderie                       | 495           | (laundry key)       |

## 5. Data Flow

```
Excel RJ workbook (Budget sheet)
  -> rj_sheet_parser.py :: parse_budget_sheet()
    -> MonthlyBudget model (database)
      -> BudgetAnalyzer (variance computation engine)
        -> Rapp_p1 report (budget vs actual)
        -> Dashboard variance widgets
```

- The parser extracts each category row, mapping the named range key to the annual and MTD budget values.
- `BudgetAnalyzer` compares `MonthlyBudget` records against actual figures from Recap/EJ to produce variance reports.
- Named range keys (e.g., `BU_VE_CHAMBRE`) serve as stable identifiers that survive category name changes across periods.

## 6. Integration Status

| System      | Status                                                              |
|-------------|---------------------------------------------------------------------|
| Web app     | Parsed into `MonthlyBudget`; feeds `BudgetAnalyzer` for variances   |
| CRM         | Not directly integrated                                             |
| Analytics   | Core input for budget vs actual dashboards and Rapp_p1 report       |

## 7. Analytics Potential

- **Variance analysis:** Compare MTD actual (from Recap/EJ) against MTD budget to flag over/under-performing categories.
- **Annual pacing:** Track cumulative actuals against annual budget to project year-end performance.
- **Revenue mix analysis:** Compare budget allocation percentages across categories to actual revenue mix.
- **Seasonal adjustment:** Analyze monthly budget distribution patterns to identify expected seasonality.
- **Departmental accountability:** Link budget categories to department heads for performance reviews.
- **Forecasting:** Use YTD variance trends to build revised forecasts for remaining months.
