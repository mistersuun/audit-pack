# Budget Import & Variance Analysis Feature

## Overview
Complete budget management system for the Sheraton Laval Night Audit webapp, featuring:
- Manual budget entry (form-based)
- CSV/Excel import functionality  
- Monthly variance analysis (Budget vs Actual)
- Year-to-date (YTD) variance tracking
- Interactive charts and analytics

## Files Created

### 1. `/routes/budget.py`
Flask blueprint with 6 API endpoints:

**Page Routes:**
- `GET /budget/` - Main budget management page

**API Endpoints:**
- `GET /api/budget/<year>/<month>` - Retrieve budget for a month
- `POST /api/budget/save` - Save/update budget data (manual entry)
- `POST /api/budget/import` - Import budget from CSV/Excel
- `GET /api/budget/variance/<year>/<month>` - Variance analysis (budget vs actual)
- `GET /api/budget/ytd/<year>` - Year-to-date variance summary
- `DELETE /api/budget/<year>/<month>` - Delete a month's budget

**Access Control:**
- Restricted to roles: `admin`, `gm`, `gsm`, `accounting`
- Uses `@budget_required` decorator for auth/authorization

### 2. `/utils/budget_analyzer.py`
Utility class for budget analysis and import parsing:

**Class: `BudgetAnalyzer(year, month)`**

Methods:
- `get_budget_dict()` - Returns monthly budget as dictionary
- `get_actual_data()` - Sums daily metrics for the month
- `get_variance_report()` - Full variance analysis with items and metadata
- `get_ytd_summary()` - Year-to-date aggregation with monthly breakdown
- `parse_budget_csv(file_content)` - Parse CSV imports
- `parse_budget_excel(file_content)` - Parse Excel imports (requires openpyxl)

**Variance Calculation:**
- Actual data pulled from `DailyJourMetrics` table
- Categories: Revenue (rooms, outlets, total), Occupancy (rooms sold, ADR), F&B breakdown
- Variance = Actual - Budget
- Variance % = (Variance / Budget) * 100
- Favorable flag: True if variance >= 0 for revenue items

**CSV/Excel Import Format:**
```
Field Name        | Jan | Feb | Mar | ... | Dec
rooms_target      | 500 | 510 | 520 | ... | 600
adr_target        | 221 | 225 | 230 | ... | 250
room_revenue      | ... | ... | ... | ... | ...
[all MonthlyBudget columns]
```

### 3. `/templates/budget.html`
Full-featured responsive HTML page with 3 tabs:

**Tab 1: Saisie Budget (Manual Entry)**
- Month/Year selector with "Load" button
- Interactive form with sections:
  - Revenus (6 fields + total)
  - Main-d'œuvre (13 departments)
  - Frais Fixes (8 cost types)
  - Ratios de Coûts (5 ratio fields)
- Save & Reset buttons
- CSV/Excel drag-drop import zone

**Tab 2: Analyse des Écarts (Variance Analysis)**
- Month selector + Load button
- Summary cards: Revenue, Rooms Sold, ADR (with budget, actual, variance, status)
- Detailed variance table with columns:
  - Catégorie | Budget | Réel | Écart ($) | Écart (%) | Status (badge)
- Bar chart: Budget vs Actual comparison
- Color-coded status badges (green=favorable, red=unfavorable)
- Alert handling for no budget / no actuals scenarios

**Tab 3: Cumul Annuel (Year-to-Date)**
- Year selector + Load button
- YTD summary cards (Budget, Actual, Variance totals)
- Monthly trend table (Jan-Dec with variance)
- YTD totals row (highlighted)
- Line chart: Budget vs Actual trend over the year

**Styling:**
- Matches existing direction_portal.html style
- Uses CSS variables for theming (dark mode support)
- Card-based layout
- Responsive grid (mobile-friendly)
- Feather icons throughout
- Smooth animations & transitions

### 4. Updated `main.py`
- Added import: `from routes.budget import budget_bp`
- Registered blueprint: `app.register_blueprint(budget_bp)`

### 5. Updated `templates/base.html`
- Added Budget menu item in Direction sidebar section
- Icon: `trending-up`
- Label: "Budget & Écarts"
- Route: `{{ url_for('budget.budget_page') }}`
- Active highlighting when on /budget path

## Data Model Integration

### MonthlyBudget Model (existing)
Used directly with all 40+ columns:
- Revenue targets: `rooms_target`, `adr_target`, `room_revenue`, outlets (piazza, cupola, banquet, spesa, giotto, location_salle)
- Labor: 13 department fields
- Fixed costs: 8 types
- Ratios: 5 cost/benefits fields

### DailyJourMetrics Model (existing)
Queried for actual data:
- Revenue fields: `room_revenue`, `piazza_total`, `banquet_total`, `spesa_total`, `total_revenue`
- Occupancy: `total_rooms_sold`, `occupancy_rate`
- Metrics computed for variance: ADR, revenue totals, F&B by category

### Variance Calculation Flow
1. Load MonthlyBudget for year/month
2. Load all DailyJourMetrics for year/month
3. Sum daily actuals by category
4. Calculate variance: actual - budget
5. Calculate variance %: (variance / budget) * 100
6. Flag favorable: variance >= 0 for revenue
7. Return structured JSON with all items

## Usage

### For Users (Direction Staff)
1. Go to Budget & Écarts (new sidebar menu item)
2. **Manual Entry:**
   - Select month/year → Load (if exists)
   - Fill form fields
   - Click "Enregistrer le Budget"
3. **Import:**
   - Prepare CSV/Excel with field names + monthly columns
   - Drag-drop or click import zone
4. **View Variance:**
   - Go to "Analyse des Écarts" tab
   - Select month/year → Load
   - Review summary cards, table, and chart
5. **Year-to-Date:**
   - Go to "Cumul Annuel" tab
   - Select year → Load
   - Review monthly trend and YTD totals

### For Developers
```python
from utils.budget_analyzer import BudgetAnalyzer

# Variance report
analyzer = BudgetAnalyzer(2026, 2)
report = analyzer.get_variance_report()

# YTD summary
summary = analyzer.get_ytd_summary()

# Import CSV
result = BudgetAnalyzer.parse_budget_csv(file_content)
```

## Features & Capabilities

✅ **Manual Budget Entry**
- 40+ fields organized in 4 sections
- Form validation with numeric input constraints
- Load existing budget for editing
- Save with timestamp

✅ **CSV/Excel Import**
- Flexible field name mapping
- Support for 12 months in single file
- Automatic month detection
- Error handling & reporting

✅ **Variance Analysis**
- Budget vs Actual comparison
- Favorable/Unfavorable flagging (revenue-positive)
- Percentage variance calculation
- Category-level breakdown

✅ **Visualizations**
- Bar chart: Budget vs Actual (horizontal)
- Line chart: Monthly trend (YTD)
- Using Chart.js v4.4.1

✅ **Responsive Design**
- Works on desktop (1400px+)
- Mobile-friendly layouts
- Sidebar collapse on small screens
- Scrollable tables

✅ **French Localization**
- All labels & messages in French
- Month names in French
- Currency formatted as $X,XXX.XX (CAD)

✅ **Security**
- CSRF token protection on POST requests
- Role-based access control
- Database transaction rollback on errors

## Technical Stack

- **Backend:** Flask, SQLAlchemy (ORM), SQLite
- **Frontend:** Vanilla JS, Chart.js, Feather Icons
- **Styling:** CSS Variables (theme-aware), Grid/Flexbox
- **Data Format:** JSON (API responses)
- **File Support:** CSV, Excel (.xlsx, .xls via openpyxl)

## Assumptions & Limitations

1. **Actuals Source:** DailyJourMetrics must be populated via RJ uploads
2. **Excel Support:** Requires `openpyxl` package (graceful fallback to CSV)
3. **Timezone:** All dates in UTC (as per existing app)
4. **Financial Year:** Calendar year (Jan-Dec) only
5. **Rounding:** All amounts rounded to 2 decimal places

## Future Enhancements

- Export variance reports to PDF
- Budget vs Actual trend analysis (rolling months)
- Department-level labor variance tracking
- Automated budget templates (copy from prior year)
- Multi-year budget planning
- Budget adjustment requests & approvals
- Integration with P&L forecasting

## Testing Checklist

- [ ] Test budget form submission
- [ ] Test budget load/edit cycle
- [ ] Test CSV import with sample file
- [ ] Test variance report generation
- [ ] Test YTD summary calculation
- [ ] Verify responsive layout on mobile
- [ ] Test CSRF protection
- [ ] Test access control (non-direction users blocked)
- [ ] Test charts rendering
- [ ] Test error handling (no budget, no actuals)

## Troubleshooting

**Import fails:** Check CSV format (first row = headers, first column = field names)
**No variance data:** Ensure DailyJourMetrics are populated for the month
**Charts not rendering:** Check browser console for JS errors
**Access denied:** Verify user role is one of: admin, gm, gsm, accounting

