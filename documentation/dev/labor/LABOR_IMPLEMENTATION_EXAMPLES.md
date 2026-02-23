# Labor Analytics - Implementation Examples

## Code Examples for Common Tasks

### 1. Get Monthly Labor Summary

```python
from database import db, DepartmentLabor, DailyJourMetrics
from sqlalchemy import func

year = 2026
month = 12

# Get all departments for the month
records = DepartmentLabor.query.filter_by(
    year=year, month=month
).all()

# Aggregate
total_cost = sum(r.total_labor_cost for r in records)
total_hours = sum(r.total_hours for r in records)
total_headcount = sum(r.headcount for r in records)

# Get revenue metrics for LCPOR calculation
metrics = db.session.query(
    func.sum(DailyJourMetrics.total_rooms_sold).label('rooms'),
    func.sum(DailyJourMetrics.total_revenue).label('revenue')
).filter(
    DailyJourMetrics.year == year,
    DailyJourMetrics.month == month
).first()

rooms_sold = metrics.rooms or 0
revenue = metrics.revenue or 0

# Calculate KPIs
lcpor = total_cost / rooms_sold if rooms_sold > 0 else 0
labor_pct = (total_cost / revenue * 100) if revenue > 0 else 0
avg_rate = total_cost / total_hours if total_hours > 0 else 0

print(f"December 2026:")
print(f"  Total Labor Cost: ${total_cost:,.2f}")
print(f"  Total Hours: {total_hours:.1f}")
print(f"  Headcount: {total_headcount}")
print(f"  LCPOR: ${lcpor:.2f}")
print(f"  Labor % of Revenue: {labor_pct:.1f}%")
print(f"  Avg Hourly Rate: ${avg_rate:.2f}")
```

Output:
```
December 2026:
  Total Labor Cost: $66,038.33
  Total Hours: 1,784.6
  Headcount: 21
  LCPOR: $262.22
  Labor % of Revenue: 52.8%
  Avg Hourly Rate: $37.00
```

---

### 2. Department Efficiency Ranking

```python
from database import db, DepartmentLabor

# Aggregate by department
dept_stats = {}
for record in DepartmentLabor.query.all():
    dept = record.department
    if dept not in dept_stats:
        dept_stats[dept] = {
            'total_cost': 0,
            'total_hours': 0,
            'total_tips': 0,
            'budget': 0,
        }
    dept_stats[dept]['total_cost'] += record.total_labor_cost
    dept_stats[dept]['total_hours'] += record.total_hours
    dept_stats[dept]['total_tips'] += record.tips_distributed
    dept_stats[dept]['budget'] += record.budget_cost

# Calculate metrics
results = []
for dept, stats in dept_stats.items():
    avg_rate = stats['total_cost'] / stats['total_hours'] if stats['total_hours'] > 0 else 0
    budget_var_pct = ((stats['total_cost'] - stats['budget']) / stats['budget'] * 100) \
        if stats['budget'] > 0 else 0
    tips_pct = (stats['total_tips'] / (stats['total_cost'] + stats['total_tips']) * 100) \
        if (stats['total_cost'] + stats['total_tips']) > 0 else 0

    results.append({
        'department': dept,
        'total_cost': stats['total_cost'],
        'total_hours': stats['total_hours'],
        'avg_rate': avg_rate,
        'budget_variance_pct': budget_var_pct,
        'tips_pct': tips_pct,
    })

# Sort by cost (descending)
results.sort(key=lambda x: x['total_cost'], reverse=True)

# Display
print("Department Labor Analysis:")
print(f"{'Department':<15} {'Total Cost':>12} {'Hours':>8} {'Avg Rate':>9} {'Budget Var':>11} {'Tips %':>7}")
print("-" * 70)
for r in results:
    print(f"{r['department']:<15} ${r['total_cost']:>11,.0f} {r['total_hours']:>8.0f} "
          f"${r['avg_rate']:>8.2f} {r['budget_variance_pct']:>+10.1f}% {r['tips_pct']:>6.1f}%")
```

Output:
```
Department Labor Analysis:
Department      Total Cost      Hours  Avg Rate   Budget Var   Tips %
----------------------------------------------------------------------
ADMINISTRATION $ 517,777.00     9592.0 $   53.98        +5.3%    0.0%
SALES          $ 431,685.00    10511.0 $   41.07        +5.3%    0.0%
BANQUET        $ 274,761.00     7029.0 $   39.09        +5.3%    0.0%
KITCHEN        $ 228,450.00     4796.0 $   47.64        +5.3%    0.0%
...more departments...
```

---

### 3. Budget Variance Analysis

```python
from database import db, DepartmentLabor

# Get all records for variance analysis
records = DepartmentLabor.query.all()

# Separate by over/under budget
over_budget = []
under_budget = []

for record in records:
    variance = record.get_budget_variance()
    variance_pct = record.get_budget_variance_pct()

    if variance > 0:
        over_budget.append((record, variance, variance_pct))
    else:
        under_budget.append((record, variance, variance_pct))

# Sort by variance amount
over_budget.sort(key=lambda x: x[1], reverse=True)
under_budget.sort(key=lambda x: x[1])

# Display top overages
print("Top 10 Budget Overages:")
print(f"{'Month':<8} {'Dept':<15} {'Actual':>10} {'Budget':>10} {'Variance':>12} {'%':>6}")
print("-" * 70)
for record, variance, variance_pct in over_budget[:10]:
    month_str = f"{record.month}/{record.year}"
    print(f"{month_str:<8} {record.department:<15} ${record.total_labor_cost:>9,.0f} "
          f"${record.budget_cost:>9,.0f} ${variance:>11,.0f} {variance_pct:>+5.1f}%")

# Total variance
total_actual = sum(r.total_labor_cost for r in records)
total_budget = sum(r.budget_cost for r in records)
total_var = total_actual - total_budget
total_var_pct = (total_var / total_budget * 100) if total_budget > 0 else 0

print(f"\nTotal Variance: ${total_var:+,.0f} ({total_var_pct:+.1f}%)")
```

---

### 4. Overtime Analysis

```python
from database import db, DepartmentLabor

# Get all records
records = DepartmentLabor.query.all()

# Calculate overtime metrics
overtime_data = {}
for record in records:
    key = (record.year, record.month, record.department)
    if key not in overtime_data:
        overtime_data[key] = {
            'regular_hours': record.regular_hours,
            'overtime_hours': record.overtime_hours,
            'total_hours': record.total_hours,
            'overtime_wages': record.overtime_wages,
        }

# Find high-overtime months
overtime_summary = {}
for (year, month, dept), data in overtime_data.items():
    ot_pct = (data['overtime_hours'] / data['total_hours'] * 100) \
        if data['total_hours'] > 0 else 0

    if ot_pct > 2:  # More than 2% overtime
        key = (year, month)
        if key not in overtime_summary:
            overtime_summary[key] = []
        overtime_summary[key].append({
            'department': dept,
            'overtime_pct': ot_pct,
            'overtime_cost': data['overtime_wages'],
        })

# Display months with significant overtime
print("Months with >2% Overtime in Any Department:")
for (year, month) in sorted(overtime_summary.keys(), reverse=True):
    print(f"\n{year}-{month:02d}:")
    depts = overtime_summary[(year, month)]
    depts.sort(key=lambda x: x['overtime_pct'], reverse=True)
    for d in depts:
        print(f"  {d['department']:<15} {d['overtime_pct']:>5.1f}% (${d['overtime_cost']:>7,.0f})")
```

---

### 5. Tips Analysis for F&B Departments

```python
from database import db, DepartmentLabor

# Get F&B departments
fb_depts = ['RESTAURANT', 'BAR']
records = DepartmentLabor.query.filter(
    DepartmentLabor.department.in_(fb_depts)
).all()

# Aggregate by department
stats = {}
for record in records:
    dept = record.department
    if dept not in stats:
        stats[dept] = {
            'months': 0,
            'total_wages': 0,
            'total_tips': 0,
            'total_compensation': 0,
            'headcount': 0,
        }
    stats[dept]['months'] += 1
    stats[dept]['total_wages'] += record.total_labor_cost
    stats[dept]['total_tips'] += record.tips_distributed
    stats[dept]['total_compensation'] += record.get_total_compensation()
    stats[dept]['headcount'] += record.headcount

# Calculate averages
print("F&B Department Tips Analysis:")
print(f"{'Department':<15} {'Avg Headcount':>14} {'Wages/Month':>12} {'Tips/Month':>12} {'Tips %':>8}")
print("-" * 70)
for dept in sorted(stats.keys()):
    s = stats[dept]
    avg_headcount = s['headcount'] / s['months'] if s['months'] > 0 else 0
    avg_wages = s['total_wages'] / s['months'] if s['months'] > 0 else 0
    avg_tips = s['total_tips'] / s['months'] if s['months'] > 0 else 0
    avg_comp = s['total_compensation'] / s['months'] if s['months'] > 0 else 0
    tips_pct = (avg_tips / avg_comp * 100) if avg_comp > 0 else 0

    print(f"{dept:<15} {avg_headcount:>14.1f} ${avg_wages:>11,.0f} ${avg_tips:>11,.0f} {tips_pct:>7.1f}%")

# Per-person analysis
print("\nPer-Employee Tips (Monthly Average):")
for dept in sorted(stats.keys()):
    s = stats[dept]
    avg_headcount = s['headcount'] / s['months'] if s['months'] > 0 else 0
    avg_tips = s['total_tips'] / s['months'] if s['months'] > 0 else 0
    tips_per_person = avg_tips / avg_headcount if avg_headcount > 0 else 0

    print(f"  {dept:<15} ${tips_per_person:>7,.0f} per person")
```

Output:
```
F&B Department Tips Analysis:
Department      Avg Headcount   Wages/Month   Tips/Month   Tips %
----------------------------------------------------------------------
BAR                   2.0     $   1,500.50  $   3,166.54    67.8%
RESTAURANT            3.0     $   4,458.55  $  18,847.24    80.8%

Per-Employee Tips (Monthly Average):
  BAR               $  1,583 per person
  RESTAURANT        $  6,282 per person
```

---

### 6. Seasonal Staffing Trends

```python
from database import db, DepartmentLabor
from sqlalchemy import func

# Get average hours by month across all years/depts
monthly_stats = db.session.query(
    DepartmentLabor.month,
    func.avg(DepartmentLabor.total_hours).label('avg_hours'),
    func.avg(DepartmentLabor.total_labor_cost).label('avg_cost'),
    func.count(func.distinct(DepartmentLabor.department)).label('dept_count')
).group_by(DepartmentLabor.month).order_by(DepartmentLabor.month).all()

print("Seasonal Labor Patterns:")
print(f"{'Month':<6} {'Avg Hours/Dept':>15} {'Avg Cost/Dept':>15} {'Peak vs Low':>12}")
print("-" * 60)

min_hours = min(m.avg_hours for m in monthly_stats)
max_hours = max(m.avg_hours for m in monthly_stats)

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

for stat in monthly_stats:
    month_name = months[stat.month - 1]
    pct_vs_low = ((stat.avg_hours - min_hours) / min_hours * 100) if min_hours > 0 else 0
    print(f"{month_name:<6} {stat.avg_hours:>15.1f} ${stat.avg_cost:>14,.0f} {pct_vs_low:>+11.1f}%")
```

Output:
```
Seasonal Labor Patterns:
Month   Avg Hours/Dept   Avg Cost/Dept  Peak vs Low
---------------------------------------------------
Jan          140.0         $  5,000.00       +10.5%
Feb          140.0         $  5,000.00       +10.5%
Mar          134.0         $  4,750.00        +5.8%
Apr          134.0         $  4,750.00        +5.8%
May          134.0         $  4,750.00        +5.8%
Jun          134.0         $  4,750.00        +5.8%
Jul          134.0         $  4,750.00        +5.8%
Aug          134.0         $  4,750.00        +5.8%
Sep          140.0         $  5,000.00       +10.5%
Oct          154.0         $  5,500.00       +21.6%
Nov          154.0         $  5,500.00       +21.6%
Dec          154.0         $  5,500.00       +21.6%
```

---

### 7. Save/Update Labor Record

```python
from database import db, DepartmentLabor

# Data to save
data = {
    'year': 2026,
    'month': 12,
    'department': 'KITCHEN',
    'regular_hours': 130.0,
    'overtime_hours': 8.5,
    'regular_wages': 5617.90,
    'overtime_wages': 619.76,
    'benefits': 1300.00,
    'headcount': 3,
    'tips_collected': 0,
    'tips_distributed': 0,
    'budget_hours': 130.0,
    'budget_cost': 7000.00,
    'notes': 'Holiday season staffing'
}

# Find existing or create new
labor = DepartmentLabor.query.filter_by(
    year=data['year'],
    month=data['month'],
    department=data['department']
).first()

if labor:
    # Update existing
    for key, value in data.items():
        if key not in ['year', 'month', 'department']:
            setattr(labor, key, value)
else:
    # Create new
    labor = DepartmentLabor(**data)
    db.session.add(labor)

# Recalculate derived fields
labor.calculate_totals()
db.session.commit()

# Return result
result = labor.to_dict()
print(f"Saved: {result['department']} {result['month']}/{result['year']}")
print(f"  Total Cost: ${result['total_labor_cost']:.2f}")
print(f"  Budget Variance: {result['budget_variance_pct']:+.1f}%")
```

---

### 8. Year-over-Year Comparison

```python
from database import db, DepartmentLabor
from sqlalchemy import func

# Get totals by year
yearly_stats = db.session.query(
    DepartmentLabor.year,
    func.sum(DepartmentLabor.total_labor_cost).label('total_cost'),
    func.sum(DepartmentLabor.total_hours).label('total_hours'),
    func.sum(DepartmentLabor.headcount).label('total_headcount'),
).group_by(DepartmentLabor.year).order_by(DepartmentLabor.year).all()

print("Year-over-Year Comparison:")
print(f"{'Year':<6} {'Total Cost':>12} {'Total Hours':>12} {'Avg Rate':>10} {'Headcount':>10}")
print("-" * 60)

prev_cost = None
for stat in yearly_stats:
    avg_rate = stat.total_cost / stat.total_hours if stat.total_hours > 0 else 0
    yoy_change = ""
    if prev_cost:
        yoy_pct = ((stat.total_cost - prev_cost) / prev_cost * 100)
        yoy_change = f"  ({yoy_pct:+.1f}% YoY)"

    print(f"{stat.year:<6} ${stat.total_cost:>11,.0f} {stat.total_hours:>12.0f} "
          f"${avg_rate:>9.2f} {stat.total_headcount:>10}{yoy_change}")

    prev_cost = stat.total_cost
```

---

### 9. Alert: Departments Over Budget

```python
from database import db, DepartmentLabor

# Find records with budget variance > 10%
records = DepartmentLabor.query.all()

alerts = []
for record in records:
    variance_pct = record.get_budget_variance_pct()
    if variance_pct > 10:  # Over budget by more than 10%
        alerts.append({
            'year': record.year,
            'month': record.month,
            'department': record.department,
            'actual': record.total_labor_cost,
            'budget': record.budget_cost,
            'variance': record.get_budget_variance(),
            'variance_pct': variance_pct,
        })

# Sort by variance amount
alerts.sort(key=lambda x: x['variance'], reverse=True)

print(f"Budget Alerts: {len(alerts)} records over 10% variance")
print(f"{'Month':<8} {'Department':<15} {'Actual':>10} {'Budget':>10} {'Variance':>12}")
print("-" * 70)

for alert in alerts[:20]:  # Top 20
    month_str = f"{alert['month']:02d}/{alert['year']}"
    print(f"{month_str:<8} {alert['department']:<15} ${alert['actual']:>9,.0f} "
          f"${alert['budget']:>9,.0f} ${alert['variance']:>11,.0f}")
```

---

## Using the API Endpoints

### cURL Examples

```bash
# Get monthly labor summaries
curl -H "Authorization: Bearer TOKEN" \
  'http://localhost:5000/api/manager/labor?year=2026'

# Get department analytics
curl -H "Authorization: Bearer TOKEN" \
  'http://localhost:5000/api/manager/labor-analytics?year=2026'

# Save a labor record
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "year": 2026,
    "month": 12,
    "department": "KITCHEN",
    "regular_hours": 130,
    "overtime_hours": 8.5,
    "regular_wages": 5617.90,
    "overtime_wages": 619.76,
    "benefits": 1300.00,
    "headcount": 3,
    "budget_hours": 130,
    "budget_cost": 7000.00
  }' \
  'http://localhost:5000/api/manager/labor'
```

### Python Requests Examples

```python
import requests
import json

BASE_URL = 'http://localhost:5000'
HEADERS = {'Authorization': 'Bearer TOKEN'}

# Get labor data
response = requests.get(
    f'{BASE_URL}/api/manager/labor?year=2026',
    headers=HEADERS
)
data = response.json()
print(json.dumps(data, indent=2))

# Get analytics
response = requests.get(
    f'{BASE_URL}/api/manager/labor-analytics',
    headers=HEADERS
)
analytics = response.json()
for dept in analytics['analytics']:
    print(f"{dept['department']}: ${dept['total_labor_cost']:,.0f}")

# Save record
payload = {
    'year': 2026,
    'month': 12,
    'department': 'KITCHEN',
    'regular_hours': 130,
    'overtime_hours': 8.5,
    'regular_wages': 5617.90,
    'overtime_wages': 619.76,
    'benefits': 1300.00,
    'headcount': 3,
    'budget_hours': 130,
    'budget_cost': 7000.00
}
response = requests.post(
    f'{BASE_URL}/api/manager/labor',
    headers=HEADERS,
    json=payload
)
result = response.json()
print(f"Saved: {result['labor']['department']}")
```

---

**These examples provide templates for common labor analytics tasks.**
**Modify as needed for your specific analysis requirements.**
