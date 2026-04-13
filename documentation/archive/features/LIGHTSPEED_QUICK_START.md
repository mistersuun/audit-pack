# Lightspeed Integration — Quick Start Guide

## 5-Minute Setup

### 1. Get Credentials from Lightspeed

1. Visit: https://api-portal.lsk.lightspeed.app
2. Create OAuth2 application
3. Copy: Client ID, Client Secret, Property ID

### 2. Set Environment Variables

Edit `.env`:

```bash
LIGHTSPEED_CLIENT_ID=your_client_id
LIGHTSPEED_CLIENT_SECRET=your_client_secret
LIGHTSPEED_PROPERTY_ID=your_property_id
LIGHTSPEED_ENABLED=true
```

### 3. Verify Configuration

```bash
python main.py
```

Navigate to: http://localhost:5000/lightspeed/

Click "Tester la Connexion" button.

---

## Demo Mode (Development)

**Out of the box, no configuration needed:**

```python
from utils.lightspeed_client import LightspeedClient

client = LightspeedClient()  # No credentials

# Still works! Returns demo data
revenue = client.get_daily_revenue('2026-02-25')
print(revenue['total'])  # $23,757.20 (sample)
```

---

## Manual Sync (Any Date)

```bash
python
>>> from utils.lightspeed_sync import LightspeedSync
>>> from utils.lightspeed_client import LightspeedClient
>>>
>>> client = LightspeedClient()
>>> client.authenticate()
>>>
>>> sync = LightspeedSync(client)
>>> result = sync.sync_session('2026-02-25')
>>> print(f"Synced {len(result['synced_tabs'])} tabs")
Synced 5 tabs
```

---

## What Gets Synced

**Automatically from PMS:**

1. **Tab 3: Recap** — Cash, checks, deposits
2. **Tab 4: Transelect** — Card settlements
3. **Tab 5: GEAC** — AR balance, daily revenue
4. **Tab 11: Jour** — F&B, room revenue, occupancy, taxes
5. **Tab 13: DBRS** — Market segments, no-shows

**Auto-calculated (no sync needed):**

6. **Tab 12: Quasimodo** — Global reconciliation
7. **Tab 14: Sommaire** — Validation checks

**Manual entry (no sync):**

8. **Tab 1: Contrôle** — Auditor, weather, chambres_refaire
9. **Tab 2: DueBack** — Receptionist entries
10. **Tab 6: SD/Dépôt** — Expenses, envelopes
11. **Tab 7: SetD** — Personnel set-déjeuner
12. **Tab 8: HP/Admin** — F&B invoices

**Planned (not yet available):**

13. **Tab 9: Internet** — CD 36.1 vs 36.5
14. **Tab 10: Sonifi** — CD 35.2 vs email

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/lightspeed/` | GET | Configuration page |
| `/lightspeed/api/status` | GET | Connection status JSON |
| `/lightspeed/api/connect` | POST | Test/save credentials |
| `/lightspeed/api/sync/<date>` | POST | Sync specific date |
| `/lightspeed/api/sync/status/<date>` | GET | Sync status for date |
| `/lightspeed/api/disconnect` | POST | Clear credentials |

---

## Common Tasks

### Enable Auto-Sync on RJ Creation

In `routes/audit/rj_native.py`:

```python
from utils.lightspeed_sync import LightspeedSync

@rj_native_bp.route('/session/<date>', methods=['GET'])
def get_session(date):
    session = NightAuditSession.query.filter_by(
        audit_date=datetime.strptime(date, '%Y-%m-%d').date()
    ).first()

    if not session:
        session = NightAuditSession(audit_date=...)
        db.session.add(session)
        db.session.commit()

        # Auto-sync if enabled
        if current_app.config.get('LIGHTSPEED_ENABLED'):
            sync = LightspeedSync()
            sync.sync_session(date)

    return session.to_dict()
```

### Check Sync Status

```python
from utils.lightspeed_sync import LightspeedSync

sync = LightspeedSync()
status = sync.get_sync_status('2026-02-25')

print(f"Synced: {status['synced_tabs']}")  # ['recap', 'transelect', ...]
print(f"Completeness: {status['sync_completeness']*100}%")  # 35.7%
```

### Handle Sync Errors

```python
from utils.lightspeed_client import LightspeedAPIError

try:
    client.authenticate()
    revenue = client.get_daily_revenue('2026-02-25')
except LightspeedAPIError as e:
    logger.error(f"API error: {e}")
    # Fall back to manual entry
except LightspeedConfigError as e:
    logger.warning(f"Not configured: {e}")
    # Use demo mode
```

---

## Troubleshooting

### "Connection failed"

1. Check `.env` has all three credentials
2. Verify Client Secret (no special char issues)
3. Check Lightspeed portal for API scopes granted
4. Check rate limits (100 req/min typical)

### "Empty results"

Verify date exists in Lightspeed (no pre-opening dates).

### "Token expired"

Client auto-refreshes. If manual refresh needed:

```python
client.disconnect()
client.authenticate()
```

---

## File Reference

| File | Purpose | Lines |
|------|---------|-------|
| `utils/lightspeed_client.py` | OAuth2 client + 8 API methods | ~500 |
| `utils/lightspeed_sync.py` | Maps API to RJ Natif fields | ~400 |
| `routes/lightspeed.py` | Flask endpoints | ~300 |
| `templates/lightspeed.html` | Configuration UI | ~500 |
| `documentation/LIGHTSPEED_INTEGRATION.md` | Full guide | ~400 |

---

## For More Details

See: `documentation/LIGHTSPEED_INTEGRATION.md`

Complete API reference, field mappings, setup guide, and troubleshooting.

---

## Demo Data Values

Hardcoded realistic sample values when not configured:

```
Room Revenue: $15,235.45
F&B Revenue: $8,070.75 (cafe + piazza + spesa + chambres_svc + banquet)
Total Revenue: $23,757.20
Occupancy: 73.4%
ADR: $82.35
RevPAR: $60.45
House Count: 412 guests
```

Perfect for testing UI before API credentials are available.
