# Multi-Property (Multi-Hotel) Support Implementation

## Overview

This document describes the multi-property support added to the Sheraton Laval Night Audit Flask application. The implementation maintains **100% backward compatibility** with existing single-property data while enabling support for multiple hotel properties.

## Architecture

### Key Design Principles

1. **Backward Compatible**: All existing single-property data continues to work. Records with `property_id = NULL` are treated as legacy Sheraton Laval data.
2. **Session-Based**: The active property is stored in the Flask session (`session['property_id']`), allowing each user to work with different properties.
3. **Property-Filtered Queries**: A utility function (`apply_property_filter()`) adds property filters to all queries automatically.
4. **Default Property**: Property ID = 1 is reserved for the default "Sheraton Laval" property.

## Database Schema Changes

### New Table: `properties`

```sql
CREATE TABLE properties (
    id INTEGER PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,        -- e.g., 'SHRLVL', 'MNTRL', 'QBCTY'
    name VARCHAR(200) NOT NULL,              -- e.g., 'Sheraton Laval'
    brand VARCHAR(100) DEFAULT 'Marriott',
    total_rooms INTEGER NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    province VARCHAR(100),
    country VARCHAR(50) DEFAULT 'Canada',
    timezone VARCHAR(50) DEFAULT 'America/Montreal',
    currency VARCHAR(3) DEFAULT 'CAD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    pms_type VARCHAR(50) DEFAULT 'Galaxy Lightspeed',
    pms_property_id VARCHAR(100)
);
```

### Modified Tables

The following tables now have an optional `property_id` column (NULLABLE for backward compat):

- `users` → `default_property_id` (which property the user logs into by default)
- `daily_reports` → `property_id`
- `daily_jour_metrics` → `property_id`
- `monthly_budget` → `property_id`
- `night_audit_sessions` → `property_id`

All columns are **NULLABLE** to maintain backward compatibility with existing data.

## New Files

### 1. `database/models.py` (Modified)
- Added `Property` model class at the beginning
- Added `property_id` columns to 5 existing models
- All changes are backward compatible (nullable columns)

### 2. `utils/property_context.py` (New)
Utility module for property context management:

```python
get_current_property_id()      # Get active property ID from session
get_current_property()          # Get active Property object
set_current_property(id)        # Set active property in session
apply_property_filter(query, model)  # Add property filter to query
get_property_total_rooms()      # Get total_rooms for current property
```

**Usage in routes:**
```python
from utils.property_context import apply_property_filter, get_current_property

# In a route handler:
sessions = apply_property_filter(
    NightAuditSession.query.filter_by(status='draft'),
    NightAuditSession
)
# Returns sessions for current property + legacy data with NULL property_id
```

### 3. `routes/properties.py` (New)
Admin blueprint for property management:

**Endpoints:**
- `GET /properties/` — Property management page (HTML)
- `GET /properties/api/properties` — List all properties (JSON)
- `POST /properties/api/properties` — Create new property
- `PUT /properties/api/properties/<id>` — Update property
- `DELETE /properties/api/properties/<id>` — Deactivate property (soft delete)
- `POST /properties/api/properties/switch/<id>` — Switch active property in session
- `GET /properties/api/properties/portfolio` — Portfolio summary KPIs

### 4. `routes/portfolio.py` (New)
Direction/Admin blueprint for multi-property dashboard:

**Endpoints:**
- `GET /portfolio/` — Portfolio dashboard page (HTML)
- `GET /portfolio/api/portfolio/summary` — Consolidated KPIs across all properties
- `GET /portfolio/api/portfolio/comparison` — Property-to-property comparison data
- `GET /portfolio/api/portfolio/property-list` — Simple list for selection

**Dashboard KPIs:**
- Total rooms across all properties
- Average occupancy (all properties)
- Total revenue (last 30 days)
- Average ADR (last 30 days)
- Number of active properties
- Count of recent audits

**Comparison Charts:**
- Occupancy by property (bar chart)
- ADR by property (bar chart)
- RevPAR by property (bar chart)
- Detailed metrics cards per property

### 5. `templates/properties.html` (New)
Admin page for property management with:
- **Section 1**: List of active properties with status indicators
- **Section 2**: Form to add new properties (all fields)
- **Section 3**: Portfolio view as a table showing key metrics
- JavaScript for CRUD operations on properties

### 6. `templates/portfolio.html` (New)
Direction dashboard with:
- **KPI Summary Row**: Total rooms, avg occupancy, avg ADR, total revenue, property count, recent audits
- **Occupancy Chart**: Bar chart comparing occupancy % by property (30 days)
- **ADR Chart**: Bar chart comparing average daily rate by property (30 days)
- **RevPAR Chart**: Bar chart comparing RevPAR by property (30 days)
- **Comparison Cards**: Detailed metrics for each property
- Chart.js integration for visualization

### 7. `seed_property.py` (New)
Script to seed the default Sheraton Laval property:

```bash
python seed_property.py
```

**Output:**
```
✓ Created default property: Sheraton Laval
  - ID: 1
  - Code: SHRLVL
  - Rooms: 252
  - Location: Laval, Québec
```

## Modified Files

### 1. `main.py`
- Added imports for `properties_bp` and `portfolio_bp`
- Registered both blueprints with `app.register_blueprint()`

### 2. `templates/base.html`
- Updated logo subtitle to show current property name: `{{ session.get('property_name', 'Sheraton Laval') }}`
- Added property indicator card below logo (shows current property with link to properties page)
- Added "Portfolio" link to admin section (`/portfolio/`)
- Added "Propriétés" link to admin section (`/properties/`)
- Added "Portfolio" link to direction section (for GM/GSM/Accounting roles)

## Getting Started

### Setup

1. **Apply database migrations** (models are auto-created on first run):
   ```bash
   python main.py  # Auto-creates all tables including 'properties'
   ```

2. **Seed the default property**:
   ```bash
   python seed_property.py
   ```

3. **Access the properties page** (admin only):
   - Go to `/properties/` to view, create, and manage properties
   - Add new properties via the form

4. **View multi-property dashboard** (direction/admin):
   - Go to `/portfolio/` to see consolidated metrics across all properties

### Creating a New Property

#### Method 1: Via Web UI
1. Login as admin
2. Go to "Propriétés" in the sidebar
3. Fill in the form (Code, Name, Rooms, etc.)
4. Click "Ajouter Propriété"

#### Method 2: Via API
```bash
curl -X POST http://localhost:5000/properties/api/properties \
  -H "Content-Type: application/json" \
  -d '{
    "code": "MNTRL",
    "name": "Sheraton Montreal",
    "brand": "Marriott",
    "total_rooms": 300,
    "city": "Montreal",
    "province": "Québec"
  }'
```

### Switching Properties

Users can switch the active property by:
1. Clicking on the property name in the sidebar header
2. Selecting a new property from the properties page
3. Via API: `POST /properties/api/properties/switch/<property_id>`

After switching, all subsequent operations use the new property's data.

## Backward Compatibility

**Existing Data is Safe:**
- All existing records have `property_id = NULL`
- The `apply_property_filter()` function includes records with NULL property_id
- This means legacy Sheraton Laval data is automatically accessible to users viewing property ID = 1

**Example Query:**
```python
# This query returns:
# 1. All records for property_id = 1 (Sheraton Laval)
# 2. All legacy records with property_id = NULL
sessions = apply_property_filter(
    NightAuditSession.query,
    NightAuditSession
)
```

## Usage in Existing Routes

To add property filtering to existing routes, use the context helper:

```python
from utils.property_context import apply_property_filter, get_current_property

@my_route.route('/audits')
def list_audits():
    # Get audits for current property + legacy data
    audits = apply_property_filter(
        NightAuditSession.query.order_by(NightAuditSession.audit_date.desc()),
        NightAuditSession
    ).all()
    return render_template('audits.html', audits=audits)
```

## Configuration

### Per-Property Settings

Each property has its own settings:

| Field | Purpose | Example |
|-------|---------|---------|
| `code` | Short code for API/reports | `SHRLVL`, `MNTRL` |
| `name` | Display name | `Sheraton Laval` |
| `brand` | Brand/company | `Marriott` |
| `total_rooms` | Number of rooms (used for occupancy calc) | `252` |
| `timezone` | Local timezone | `America/Montreal` |
| `currency` | Default currency | `CAD` |
| `pms_type` | PMS system | `Galaxy Lightspeed` |
| `pms_property_id` | PMS property ID | `LS-12345` |

### Session Storage

When a property is switched, these are stored in Flask session:
- `session['property_id']` — Property ID
- `session['property_name']` — Property name (for display)
- `session['property_code']` — Property code
- `session['total_rooms']` — Total rooms (used for calculations)

## Frontend Integration

### Sidebar Updates

The sidebar now displays:
- Current property name in subtitle
- Property indicator card with link to properties page
- "Portfolio" menu item (admin/direction)
- "Propriétés" menu item (admin only)

### Chart.js Integration

The portfolio dashboard uses Chart.js for visualizations. The dependency is loaded via CDN:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
```

## Security

### Role-Based Access

- **Admin role**: Full access to properties and portfolio management
- **Direction role** (GM, GSM, Accounting): Access to portfolio dashboard
- **Night Auditor role**: Access to audit operations for current property only

### Data Isolation

- Users only see data for the current property (by default)
- Legacy NULL records are included for backward compat but can be filtered out
- Property switching requires explicit user action via UI or API

## Testing

### Quick Test

1. **Create a test property**:
   ```bash
   # Via curl or Postman
   POST /properties/api/properties
   {
     "code": "TEST",
     "name": "Test Property",
     "brand": "Marriott",
     "total_rooms": 100
   }
   ```

2. **Switch to it**:
   ```bash
   POST /properties/api/properties/switch/2
   ```

3. **Create an audit session**:
   - Go to `/rj/native` and create a session
   - The `night_audit_sessions.property_id` will be set to 2

4. **View portfolio**:
   - Go to `/portfolio/` to see the new property in charts

## Troubleshooting

### Property Not Appearing in Sidebar
- Verify property is marked `is_active = True`
- Check that user is logged in
- Refresh browser cache

### Occupancy % Showing as 0 on Portfolio
- Ensure `DailyJourMetrics` records exist for the property
- Check that `occupancy_rate` is being calculated on upload
- Verify property has `total_rooms > 0`

### Old Data Not Appearing
- Check that `property_id` is NULL for legacy records
- Run `apply_property_filter()` on queries to include legacy data

## Future Enhancements

Potential next steps for multi-property support:

1. **User Property Assignment**: Assign users to specific properties (restrict visibility)
2. **Property-Level Roles**: Different roles per property (e.g., GM of Montreal, GSM of Laval)
3. **Bulk Import**: Import audit data for multiple properties at once
4. **Cross-Property Reports**: Compare metrics across all properties in a single view
5. **Per-Property Settings**: Budget targets, thresholds, alert configs per property
6. **Property Hierarchy**: Parent/child property relationships (chain management)

## Support

For issues or questions about multi-property support:
1. Check the backward compatibility section above
2. Verify property is active (`is_active = True`)
3. Confirm user has admin/direction role
4. Review browser console for JavaScript errors

---

**Implementation Date**: February 2026
**Backward Compatible**: YES ✓
**Breaking Changes**: NONE ✓
