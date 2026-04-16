# Salaires - Labor/Payroll by Department ([salaires])

**Excel Sheet:** `salaires` | **Dimensions:** 132 rows x 92 cols
**Parsed by:** `rj_sheet_parser.py` -> `parse_salaires_sheet()`
**Database model:** `DepartmentLabor`, `DailyLaborMetrics`

## 1. Purpose

The salaires sheet tracks labor and payroll data broken down by department and employee role. It captures regular hours, overtime, escalier (step/shift differential) hours, corresponding pay rates, and total costs. The 92-column width accommodates either a daily breakdown across the month (31 days x ~3 metrics) or multiple department group columns. This sheet is central to labor cost analysis and departmental staffing oversight.

## 2. Sheet Layout

- **Row 4 (header):** Department and metric column labels.
- **Rows 5-132:** Data rows organized by department, then by role within each department.
- **Departments appear as section headers** followed by their constituent roles:
  - **RECEPTION:** Reception, Reservation, Auditeur, Portier, Commis, Club Lounge
  - **CHAMBRE:** Chambre, Preposee, Equipiere
  - Additional departments: PIAZZA, BANQUET, CUISINE, and others
- **Columns span 92 wide**, grouping labor metrics per department or per day.

## 3. Column Reference

| Col Group       | Header       | Type   | Description                                          |
|-----------------|--------------|--------|------------------------------------------------------|
| A               | Departement  | String | Department or role name                              |
| B-E             | (identifiers)| Mixed  | Sub-department codes or employee grouping fields     |
| F               | HRES SUP     | Float  | Overtime hours (heures supplementaires)              |
| G               | H ESC        | Float  | Escalier (shift differential) hours                  |
| H               | H ESC S      | Float  | Escalier supplementary hours                         |
| I               | TAUX         | Float  | Regular hourly rate                                  |
| J               | TAUX SUP     | Float  | Overtime hourly rate                                 |
| K               | TAUX ESC     | Float  | Escalier hourly rate                                 |
| L               | ESC SUP      | Float  | Escalier supplementary rate                          |
| M               | TOTAL HRES   | Float  | Total hours worked (all categories combined)         |
| N               | $ TOTAL      | Float  | Total dollar cost for the row                        |
| O-CN (approx)   | Daily columns| Float  | Repeated daily or departmental metric groups         |

## 4. Sample Data

```
Row 4 (header):
Departement | | | | | HRES SUP | H ESC | H ESC S | TAUX | TAUX SUP | TAUX ESC | ESC SUP | TOTAL HRES | $ TOTAL

Department sections:
RECEPTION
  Reception      | ... | 12.5 | 3.0 | 1.5 | 18.50 | 27.75 | 20.35 | 30.53 | 245.0 | 5,122.50
  Reservation    | ... |  4.0 | 0.0 | 0.0 | 17.25 | 25.88 | 0.00  |  0.00 | 160.0 | 2,760.00
  Auditeur       | ... |  8.0 | 2.0 | 0.0 | 19.00 | 28.50 | 20.90 |  0.00 | 178.0 | 3,534.00
  ...
CHAMBRE
  Chambre        | ... | ...
  Preposee       | ... | ...
  Equipiere      | ... | ...
```

## 5. Data Flow

```
Excel RJ workbook (salaires sheet)
  -> rj_sheet_parser.py :: parse_salaires_sheet()
    -> DepartmentLabor model (per-department monthly aggregates)
    -> DailyLaborMetrics model (per-day breakdowns if daily columns present)
      -> Labor cost analysis dashboards
      -> Budget vs actual labor variance
```

- The parser identifies department section headers and iterates through role rows beneath each.
- Hourly rates and hour counts are multiplied to verify against the `$ TOTAL` column.
- Daily columns (if structured as 31-day breakdown) feed `DailyLaborMetrics` for day-level staffing analysis.

## 6. Integration Status

| System      | Status                                                              |
|-------------|---------------------------------------------------------------------|
| Web app     | Parsed into `DepartmentLabor` and `DailyLaborMetrics` models        |
| CRM         | Not integrated; no direct guest-facing data                         |
| Analytics   | Department-level labor cost tracking available for dashboards        |

## 7. Analytics Potential

- **Overtime monitoring:** Flag departments with disproportionate HRES SUP relative to regular hours.
- **Rate benchmarking:** Compare TAUX across roles and departments to identify pay scale inconsistencies.
- **Staffing efficiency:** Correlate TOTAL HRES per department against revenue (from Recap/EJ) to compute labor cost ratios.
- **Daily staffing patterns:** If daily columns are present, identify peak staffing days and optimize scheduling.
- **Department cost ranking:** Rank departments by `$ TOTAL` to prioritize cost control efforts.
- **Escalier analysis:** Track shift differential usage to evaluate scheduling of off-peak or split shifts.
