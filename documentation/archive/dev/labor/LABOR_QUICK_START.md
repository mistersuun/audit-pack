# Labor Analytics Quick Start

## Setup (One-time)

```bash
cd /sessions/laughing-sharp-johnson/mnt/audit-pack

# Run the import script to seed data
python import_labor.py
```

Expected output:
```
✓ Labor import complete: 324 records created
  Departments: 9
  Period: Jan 2024 - Dec 2026
```

## API Endpoints

### Get All Labor Data
```bash
curl http://localhost:5000/api/manager/labor?year=2026
```

Returns monthly labor summaries with all departments, hours, costs, and budget variance.

### Get Department Analytics
```bash
curl http://localhost:5000/api/manager/labor-analytics?year=2026
```

Returns ranked efficiency metrics by department including:
- Revenue per labor hour
- Budget variance %
- Tips as % of compensation
- Overtime analysis

### Save/Update Labor Record
```bash
curl -X POST http://localhost:5000/api/manager/labor \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "month": 12,
    "department": "KITCHEN",
    "regular_hours": 128.5,
    "overtime_hours": 4.3,
    "regular_wages": 5549.89,
    "overtime_wages": 288.77,
    "benefits": 1226.94,
    "headcount": 3,
    "tips_collected": 0,
    "tips_distributed": 0,
    "budget_hours": 126.2,
    "budget_cost": 6712.32
  }'
```

## Key Metrics

### LCPOR (Labor Cost Per Occupied Room)
```
= Total Labor Cost ÷ Rooms Sold
Benchmark: $35-50
```

### Labor % of Revenue
```
= Total Labor Cost ÷ Total Revenue × 100
Benchmark: 28-32%
```

### Revenue per Labor Hour
```
= Total Revenue ÷ Total Labor Hours
By Department:
- Kitchen: ~$26/hr
- Bar: ~$17/hr
- Restaurant: ~$13/hr
- Sales: ~$12/hr
- Admin: ~$13/hr
```

### Budget Variance %
```
= (Actual - Budget) ÷ Budget × 100
Positive = Over budget
Benchmark: ±5%
```

## Data Structure

Each record includes:
- **Identifiers**: year, month, department
- **Hours**: regular_hours, overtime_hours, total_hours
- **Wages**: regular_wages, overtime_wages (1.5×), benefits (~15-20%)
- **Staffing**: headcount, avg_hourly_rate
- **Tips**: tips_collected, tips_distributed (F&B only)
- **Budget**: budget_hours, budget_cost
- **Variance**: budget_variance, budget_variance_pct

## Sample Data

Dec 2026 totals:
- Total Labor Cost: $66,038
- Total Hours: 1,785
- Headcount: 21
- LCPOR: $262
- Labor % Revenue: 52.8%

## Departments

1. **RECEPTION** ($28/hr) - Front desk, 32 hrs/week
2. **KITCHEN** ($43.23/hr) - Kitchen staff, 29.2 hrs/week
3. **RESTAURANT** ($20/hr) - Servers, 35 hrs/week, tips-eligible
4. **BAR** ($19/hr) - Bartenders, 25 hrs/week, tips-eligible
5. **BANQUET** ($33.93/hr) - Events, 42.8 hrs/week
6. **ROOMS** ($22/hr) - Housekeeping, 32 hrs/week
7. **ADMINISTRATION** ($46.86/hr) - Management, 58.4 hrs/week
8. **SALES** ($35.65/hr) - Sales, 64 hrs/week
9. **MAINTENANCE** ($30/hr) - Engineering, 40 hrs/week

## Seasonal Patterns

- **Oct-Dec (Peak)**: 15% more hours, 5-6% overtime
- **Sept, Jan-Feb (Shoulder)**: 5% more hours, 2-3% overtime
- **Mar-Aug (Normal)**: Standard hours, 1-2% overtime

## Files

- `database/models.py` - DepartmentLabor model
- `routes/manager.py` - API endpoints
- `import_labor.py` - Data import script
- `LABOR_ANALYTICS_GUIDE.md` - Full documentation

## Tips Calculation

Tips are distributed based on:
- F&B revenue (~10%)
- Headcount in tip-eligible departments
- Hours worked

Result: RESTAURANT & BAR staff get 85-90% of compensation from tips.

## Testing

```bash
# Check database
python -c "from database import DepartmentLabor; print(DepartmentLabor.query.count())"

# Start server
python main.py

# Test endpoints
curl http://localhost:5000/api/manager/labor
curl http://localhost:5000/api/manager/labor-analytics
```

---

For detailed documentation, see `LABOR_ANALYTICS_GUIDE.md`
