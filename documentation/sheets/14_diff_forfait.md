# Diff Forfait - Forfeiture/Package Difference Tracking ([diff_forfait])

**Excel Sheet:** `diff_forfait` | **Dimensions:** 44 rows x 92 cols
**Parsed by:** Not directly parsed by web app (Excel formula-driven)
**Database model:** Linked indirectly via Recap `jour` Column BF (Col 57)

## 1. Purpose

The diff_forfait sheet reconciles hotel room packages (forfaits) with their associated F&B (Food & Beverage) charges. When a guest books a package that includes meals or lounge access, the package value must be split between rooms revenue and F&B revenue. This sheet tracks the daily difference between what packages should be worth and what was actually charged to F&B outlets. The 92-column width reflects the large number of distinct package types offered by the Hotel Sheraton Laval.

## 2. Sheet Layout

- **Row 0-1:** Hotel header ("Hotel Sheraton Laval" / "Verification difference...").
- **Row 2 (header):** Day column followed by package type identifiers across 92 columns.
- **Rows 3-33:** Days 1-31, one row per day, with variance amounts per package type.
- **Rows 34-44:** Summary rows (monthly totals, package-level aggregates, reconciliation notes).
- The sheet title references "Verification difference", confirming its role as a reconciliation control.

## 3. Column Reference

| Col | Header                        | Type    | Description                                        |
|-----|-------------------------------|---------|----------------------------------------------------|
| A   | Jour                          | Integer | Day of the month (1-31)                            |
| B   | 12                            | Float   | Package variant code 12 variance                   |
| C   | Allocation ClubLevel          | Float   | Club Level room allocation adjustment              |
| D   | Facture restaurant forfait    | Float   | Restaurant invoice for package meals               |
| E   | FORFAIT 75$                   | Float   | $75 package variance                               |
| F   | coupon restaurant club        | Float   | Club restaurant coupon redemption variance         |
| G   | Forfait 63$                   | Float   | $63 package variance                               |
| H   | Forfait BRUNCH                | Float   | Brunch package variance                            |
| I   | Forfait 87$                   | Float   | $87 package variance                               |
| J   | FORFAIT 90$                   | Float   | $90 package variance                               |
| K   | FORFAIT 98$ Wurth             | Float   | $98 Wurth corporate package variance               |
| L   | ADPQ ADE29A                   | Float   | ADPQ tourism program variant ADE29A               |
| M   | ADPQ DPE29A                   | Float   | ADPQ tourism program variant DPE29A               |
| N   | COUPON RESTO ADPQ             | Float   | ADPQ restaurant coupon variance                    |
| O   | SYI22A                        | Float   | Package code SYI22A variance                      |
| P-CN| (additional package types)    | Float   | Remaining package variants (up to 92 total cols)  |

## 4. Sample Data

```
Jour | Alloc ClubLevel | Fact. rest. forfait | FORFAIT 75$ | coupon rest. club | Forfait 63$ | ...
-----|-----------------|---------------------|-------------|-------------------|-------------|----
  1  |     125.00      |       -75.00        |    75.00    |      -25.00       |     0.00    |
  2  |     250.00      |      -150.00        |   150.00    |      -50.00       |    63.00    |
  3  |       0.00      |         0.00        |     0.00    |        0.00       |     0.00    |
  ...
```

- Day 2 shows Club Level allocations of $250, offset by $150 in restaurant forfait invoices.
- Package amounts should net to zero when correctly reconciled across all columns for a given day.

## 5. Data Flow

```
PMS package bookings + POS F&B charges
  -> Excel formulas in diff_forfait sheet
    -> Daily package variance per type (cols B-CN)
      -> Row totals feed Recap jour Column BF (Col 57)
        -> Recap formula: -Forfait + Club Lounge
          -> Surplus/deficit impact on daily revenue
```

- This sheet is **formula-driven within Excel** and not directly parsed by the web application.
- The Recap sheet's `jour` tab references diff_forfait totals at Column BF (column index 57) using the formula `-Forfait + Club Lounge`.
- The net forfait variance adjusts daily revenue figures to properly allocate package revenue between rooms and F&B departments.

## 6. Integration Status

| System      | Status                                                              |
|-------------|---------------------------------------------------------------------|
| Web app     | Not directly parsed; values flow through Recap Column BF            |
| CRM         | Not integrated; package booking data resides in PMS                 |
| Analytics   | Available only as aggregated value via Recap currently              |

## 7. Analytics Potential

- **Package profitability:** Analyze which forfait types generate the largest variances to evaluate package pricing.
- **Club Level utilization:** Track Allocation ClubLevel trends to assess lounge access costs against revenue.
- **ADPQ program tracking:** Monitor tourism program variants (ADE29A, DPE29A) for compliance and reimbursement accuracy.
- **Package mix analysis:** Identify which forfait types are most frequently booked and their revenue impact.
- **Daily reconciliation alerts:** Flag days where net variance across all package types exceeds a threshold.
- **Direct parsing opportunity:** A dedicated parser for this sheet would unlock package-level analytics, enabling per-forfait profitability tracking and trend analysis in the web app.
- **Corporate package monitoring:** Track corporate-specific packages (e.g., Wurth $98) to verify negotiated rate compliance.
