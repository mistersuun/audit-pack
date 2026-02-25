# Lightspeed Galaxy PMS Integration

## Overview

This document describes the **Lightspeed Galaxy PMS API integration scaffold** for the Sheraton Laval Night Audit WebApp (RJ Natif).

The integration replaces manual report printing and parsing with direct API calls to the Lightspeed PMS, automatically synchronizing hotel data into the 14-tab audit report.

### Key Components

1. **LightspeedClient** (`utils/lightspeed_client.py`) — OAuth2 API client
2. **LightspeedSync** (`utils/lightspeed_sync.py`) — Data mapper to RJ Natif
3. **Flask Blueprint** (`routes/lightspeed.py`) — Configuration & sync endpoints
4. **Configuration Page** (`templates/lightspeed.html`) — Web UI (French)

---

## Architecture

### LightspeedClient — OAuth2 & API Methods

```python
from utils.lightspeed_client import LightspeedClient

# Initialize (demo mode if no creds)
client = LightspeedClient()

# Or with explicit config
client = LightspeedClient(config={
    'LIGHTSPEED_CLIENT_ID': 'xxx',
    'LIGHTSPEED_CLIENT_SECRET': 'yyy',
    'LIGHTSPEED_PROPERTY_ID': 'zzz',
})

# Authenticate
if client.authenticate():
    # Get daily revenue data
    revenue = client.get_daily_revenue('2026-02-25')
    print(revenue)
    # {
    #   'room_revenue': 15235.45,
    #   'fb_revenue': {cafe, piazza, spesa, chambres_svc, banquet},
    #   'total': 23757.20,
    #   'taxes': {tps, tvq, taxe_hebergement},
    #   'sync_date': '2026-02-25T...'
    # }
```

#### Available Methods

| Method | Maps To | Returns |
|--------|---------|---------|
| `get_daily_revenue(date)` | Jour tab | Room + F&B revenue, taxes |
| `get_room_statistics(date)` | Jour tab | Occupancy, ADR, RevPAR, room types |
| `get_ar_balance(date)` | Recap + GEAC tabs | Guest/city ledger, AR balance |
| `get_cashier_report(date)` | Recap tab | Cash CDN/USD, card totals, checks |
| `get_card_settlements(date)` | Transelect tab | Visa, MC, AMEX, Debit, Discover |
| `get_house_guests(date)` | Future use | List of staying guests |
| `get_no_shows(date)` | DBRS tab | No-show names, rates, market segment |
| `get_market_segments(date)` | DBRS tab | Transient/group/contract breakdown |

### Demo Mode

When credentials are not configured, the client automatically returns sample data:

```python
client = LightspeedClient()  # No credentials

# Still returns demo data structure
revenue = client.get_daily_revenue('2026-02-25')
# Returns: DEMO_DATA['daily_revenue'] (realistic sample values)

# Useful for development/testing before API credentials are available
```

### LightspeedSync — Mapping to RJ Natif

The sync service maps API responses to NightAuditSession database fields:

```python
from utils.lightspeed_sync import LightspeedSync

sync = LightspeedSync(lightspeed_client)

# Full sync for a date
result = sync.sync_session('2026-02-25')
# Returns:
# {
#   'synced_tabs': ['recap', 'transelect', 'geac', 'jour', 'dbrs'],
#   'errors': [],
#   'warnings': ['internet sync skipped: not yet available'],
#   'session': {...}  # Updated NightAuditSession dict
# }
```

#### Synced Tabs (14 RJ Natif Tabs)

| # | Tab | Synced? | Fields |
|---|-----|---------|--------|
| 1 | **Contrôle** | ⚠ Partial | Date only (auditor, weather, chambres_refaire = manual) |
| 2 | **DueBack** | ✗ Manual | Receptionist entries (manual only) |
| 3 | **Récapitulatif** | ✓ Yes | Cash LS, POS, checks, deposits |
| 4 | **Transelect** | ✓ Yes | Card settlements (Visa, MC, AMEX, Debit) |
| 5 | **GEAC** | ✓ Yes | AR balance, daily revenue by card |
| 6 | **SD/Dépôt** | ✗ Manual | SD expenses, envelope data (manual) |
| 7 | **SetD** | ✗ Manual | Personnel set-déjeuner entries (manual) |
| 8 | **HP/Admin** | ✗ Manual | F&B invoices (manual) |
| 9 | **Internet** | ⏳ Planned | CD 36.1 vs 36.5 (not yet in API) |
| 10 | **Sonifi** | ⏳ Planned | CD 35.2 vs email (not yet in API) |
| 11 | **Jour** | ✓ Yes | F&B, room revenue, occupancy, taxes, KPIs |
| 12 | **Quasimodo** | ✓ Auto | Global reconciliation (auto-calculated) |
| 13 | **DBRS** | ✓ Yes | Market segments, no-shows, ADR, house count |
| 14 | **Sommaire** | ✓ Auto | Validation checks (auto-calculated) |

---

## Field Mappings

### Tab 3: Recap (Cash & Deposits)

| NightAuditSession Field | Source API | Notes |
|-------------------------|-----------|-------|
| `cash_ls_lecture` | cashier_report.cash_cdn | Lightspeed system cash |
| `cash_pos_lecture` | cashier_report.cash_usd | US cash if applicable |
| `cheque_ar_lecture` | ar_balance.total_ar | Total AR balance |
| `deposit_cdn` | cashier_report.cash_cdn | Calculated from cashier |
| `deposit_us` | (manual) | Entered manually |

### Tab 4: Transelect (Card Settlements)

| NightAuditSession Field | Source API | Notes |
|-------------------------|-----------|-------|
| `transelect_restaurant` | card_settlements (JSON) | {visa, mastercard, amex, debit, discover, total} |
| `transelect_variance` | 0 | No variance if synced from PMS |

### Tab 5: GEAC (AR & Daily Revenue)

| NightAuditSession Field | Source API | Notes |
|-------------------------|-----------|-------|
| `geac_ar_previous` | ar_balance.ar_previous | Beginning balance |
| `geac_ar_charges` | ar_balance.ar_charges | Charges posted today |
| `geac_ar_payments` | ar_balance.ar_payments | Payments received |
| `geac_ar_new_balance` | ar_balance.ar_new_balance | Ending balance |
| `geac_ar_variance` | calculated | previous + charges - payments - new = variance |
| `geac_daily_rev` | daily_revenue (JSON) | By card type breakdown |

### Tab 11: Jour (Daily Hotel Report)

| NightAuditSession Field | Source API | Notes |
|-------------------------|-----------|-------|
| `jour_room_revenue` | daily_revenue.room_revenue | Chambres total |
| `jour_cafe_nourriture` | daily_revenue.fb_revenue.cafe | ~50% estimated as food |
| `jour_piazza_nourriture` | daily_revenue.fb_revenue.piazza | Piazza restaurant |
| `jour_spesa_nourriture` | daily_revenue.fb_revenue.spesa | Market café |
| `jour_chambres_svc_nourriture` | daily_revenue.fb_revenue.chambres_svc | Room service |
| `jour_banquet_nourriture` | daily_revenue.fb_revenue.banquet | Banquet F&B |
| `jour_rooms_simple` | room_statistics.room_types.simple | Simple rooms sold |
| `jour_rooms_double` | room_statistics.room_types.double | Double rooms sold |
| `jour_rooms_suite` | room_statistics.room_types.suite | Suite rooms sold |
| `jour_rooms_comp` | room_statistics.room_types.comp | Complimentary rooms |
| `jour_nb_clients` | room_statistics.house_count | Total guests |
| `jour_adr` | room_statistics.adr | Average daily rate |
| `jour_revpar` | room_statistics.revpar | Revenue per available room |
| `jour_occupancy_rate` | room_statistics.occupancy_pct | % occupancy |
| `jour_tps` | daily_revenue.taxes.tps | Federal tax |
| `jour_tvq` | daily_revenue.taxes.tvq | Provincial tax |
| `jour_taxe_hebergement` | daily_revenue.taxes.taxe_hebergement | Room tax |
| `jour_total_revenue` | daily_revenue.total | Grand total |

### Tab 13: DBRS (Daily Business Review Summary)

| NightAuditSession Field | Source API | Notes |
|-------------------------|-----------|-------|
| `dbrs_market_segments` | market_segments (JSON) | {transient, group, contract, other} |
| `dbrs_daily_rev_today` | daily_revenue.total | Total revenue (same as jour) |
| `dbrs_adr` | room_statistics.adr | Room average rate |
| `dbrs_house_count` | room_statistics.house_count | Guest count |
| `dbrs_noshow_count` | no_shows length | # of no-shows |
| `dbrs_noshow_revenue` | sum(no_shows[].rate) | Lost revenue from no-shows |
| `dbrs_otb_data` | (JSON) | On-the-books summary |

---

## Setup & Configuration

### 1. Environment Variables

Add to `.env`:

```bash
# Lightspeed Galaxy PMS OAuth2 Credentials
LIGHTSPEED_CLIENT_ID=your_client_id_here
LIGHTSPEED_CLIENT_SECRET=your_client_secret_here
LIGHTSPEED_PROPERTY_ID=your_property_id_here
LIGHTSPEED_BASE_URL=https://api.lsk.lightspeed.app
LIGHTSPEED_ENABLED=true
```

### 2. Get Credentials from Lightspeed

1. Go to https://api-portal.lsk.lightspeed.app
2. Create an OAuth2 application
3. Get:
   - Client ID
   - Client Secret
   - Property ID (from your property in Lightspeed)
4. Request the following scopes:
   - `reports:read` — For report data (revenue, occupancy)
   - `ar:read` — For AR balance data
   - `payments:read` — For card settlement data

### 3. Configuration Page

Navigate to: **http://localhost:5000/lightspeed/**

(Requires GM or Admin role)

1. **Enter Credentials**: Paste Client ID, Client Secret, Property ID
2. **Test Connection**: Verify API access
3. **Set Auto-Sync**: Toggle automatic sync on RJ session creation
4. **View Status**: See recent syncs and completeness

### 4. Manual Testing

```bash
# In Flask shell
from utils.lightspeed_client import LightspeedClient
from utils.lightspeed_sync import LightspeedSync

client = LightspeedClient()
client.authenticate()

# Test API call
revenue = client.get_daily_revenue('2026-02-25')
print(f"Daily revenue: ${revenue['total']}")

# Test sync
sync = LightspeedSync(client)
result = sync.sync_session('2026-02-25')
print(f"Synced {len(result['synced_tabs'])} tabs")
```

---

## API Behavior

### Demo Mode (Default)

When no credentials are configured:

```python
client = LightspeedClient()
client.is_configured()  # False
client.is_connected()   # False

# Still returns realistic sample data
data = client.get_daily_revenue('2026-02-25')
# Returns DEMO_DATA — useful for frontend development
```

### Live Mode (Configured)

```python
client = LightspeedClient()
# With LIGHTSPEED_* env vars set

client.is_configured()  # True
client.authenticate()   # Performs OAuth2 handshake
client.is_connected()   # True (if token valid)

# Makes real API calls
data = client.get_daily_revenue('2026-02-25')
# Returns actual PMS data
```

### Error Handling

```python
from utils.lightspeed_client import LightspeedAPIError, LightspeedAuthError, LightspeedConfigError

try:
    client.authenticate()
except LightspeedConfigError:
    # Credentials missing
    pass
except LightspeedAuthError:
    # OAuth2 failed
    pass
except LightspeedAPIError:
    # API call failed
    pass
```

### Token Management

Tokens are automatically refreshed before expiry:

```python
client.authenticate()         # Get new token
client.is_connected()         # Check if valid
client.refresh_token()        # Manual refresh
client.disconnect()           # Clear token
```

---

## Integration with RJ Natif

### Auto-Sync on Session Creation

When enabled, Lightspeed data is automatically synced when a new RJ session is created:

```python
# In routes/audit/rj_native.py (future enhancement)
from utils.lightspeed_sync import LightspeedSync

@rj_native_bp.route('/session/<date>', methods=['GET'])
def get_or_create_session(date):
    session = NightAuditSession.query.filter_by(
        audit_date=datetime.strptime(date, '%Y-%m-%d').date()
    ).first()

    if not session:
        session = NightAuditSession(audit_date=...)
        db.session.add(session)

        # Auto-sync if enabled
        if Config.LIGHTSPEED_ENABLED:
            sync = LightspeedSync()
            sync.sync_session(date)

    return session.to_dict()
```

### Frontend Integration

The RJ Natif frontend (JavaScript) can:

1. **Detect synced fields** — Read `session.source` flags
2. **Show sync status** — Visual indicator per tab
3. **Allow manual override** — User can edit any synced field
4. **Sync on demand** — Button to re-sync specific date

Example in rj_native.html:

```html
<div class="sync-status">
  <button onclick="syncCurrentDate()">Synchroniser Lightspeed</button>
  <div id="sync-progress">
    <span class="synced-count">5 onglets synchronisés</span>
  </div>
</div>

<script>
async function syncCurrentDate() {
  const date = document.getElementById('audit-date').value;
  const response = await fetch(`/lightspeed/api/sync/${date}`, {
    method: 'POST',
  });
  const result = await response.json();
  if (result.success) {
    location.reload(); // Refresh to show synced data
  }
}
</script>
```

---

## Limitations & Future Work

### Current Limitations

1. **Cashier Details (CD codes)** — Internet (36.1, 36.5) and Sonifi (35.2) fields not yet available in Lightspeed API
   - These require integration with Lightspeed's "Cashier Detail" reports
   - Workaround: Manual entry or parse PDF exports

2. **F&B by Outlet** — Lightspeed aggregates F&B by outlet, not by category (food/beverage/beer/wine)
   - Current sync estimates food % based on total outlet revenue
   - Future: Request itemized breakdown from Lightspeed or Micros

3. **Market Segments** — Requires Lightspeed to expose market segment data in API
   - Currently fetched from `/reports/market-segments` (hypothetical endpoint)
   - May need custom integration with Lightspeed reporting

4. **On-The-Books (OTB)** — DBRS tab OTB fields require corporate Marriott data
   - Not directly available from PMS
   - Manual entry or corporate system integration needed

### Planned Enhancements

- [ ] Real-time sync during audit (not just daily)
- [ ] Sync history & audit trail
- [ ] Conditional sync (sync only if PMS data changed)
- [ ] Export synced session back to Lightspeed
- [ ] Integration with Micros POS for itemized F&B
- [ ] Webhook support (PMS notifies audit app of data changes)

---

## Testing

### Unit Tests

```python
# tests/test_lightspeed_client.py
def test_demo_mode():
    client = LightspeedClient()
    assert not client.is_configured()

    data = client.get_daily_revenue('2026-02-25')
    assert data['total'] == DEMO_DATA['daily_revenue']['total']

def test_auth():
    client = LightspeedClient(config={...})
    assert client.authenticate()
    assert client.is_connected()

def test_sync():
    sync = LightspeedSync(client)
    result = sync.sync_session('2026-02-25')
    assert len(result['synced_tabs']) > 0
```

### Integration Tests

```bash
# Manual test against sandbox Lightspeed instance
python -m flask shell
>>> from utils.lightspeed_client import LightspeedClient
>>> client = LightspeedClient()
>>> client.authenticate()
>>> revenue = client.get_daily_revenue('2026-02-25')
>>> print(f"${revenue['total']:.2f}")
```

---

## Troubleshooting

### "Credentials not configured"

Check `.env` for:
```bash
LIGHTSPEED_CLIENT_ID=
LIGHTSPEED_CLIENT_SECRET=
LIGHTSPEED_PROPERTY_ID=
```

All three must be set.

### "OAuth2 failed"

1. Verify credentials are correct (copy from Lightspeed portal)
2. Check if Client Secret has special characters (URL-encode if needed)
3. Verify OAuth2 scopes are granted in Lightspeed app settings
4. Check API rate limits (Lightspeed typically allows 100 req/min)

### "API returned 401 Unauthorized"

Token expired. Client will automatically refresh. If issue persists:
```python
client.disconnect()
client.authenticate()
```

### "Empty results"

Verify the date exists in Lightspeed (no pre-opening or post-closing dates).

---

## References

- **Lightspeed API Portal**: https://api-portal.lsk.lightspeed.app
- **OAuth2 Spec**: https://tools.ietf.org/html/rfc6749
- **RJ Natif Docs**: See `documentation/RJ/00_INDEX.md`
- **Sheraton Laval PMS**: Galaxy Lightspeed (property: YULLS)

---

## Support

For issues or questions:

1. Check logs: `tail -f logs/app.log | grep lightspeed`
2. Test connection: `/lightspeed/api/status`
3. Review sync history: `/lightspeed/` → Historique section
4. Contact: PMS admin or Lightspeed support
