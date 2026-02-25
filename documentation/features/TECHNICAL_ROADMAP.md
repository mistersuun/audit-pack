# Technical Roadmap - High-Value Feature Implementation

**Target**: Enable Marriott corporate deployment across 1,900+ properties
**Timeline**: 12-24 months
**Architecture**: Flask → FastAPI migration + serverless components (optional)

---

## PHASE 1: CORE INTEGRATIONS (Weeks 1-12)
### Investment: $160K | Revenue Potential: $17M/year

#### 1.1 Galaxy Lightspeed PMS Integration (Weeks 1-4)
**Objective**: Auto-pull daily revenue, room occupancy, AR data

```python
# New module: routes/integrations/lightspeed.py
from flask import Blueprint, request, jsonify
from utils.integrations.lightspeed_client import LightspeedAPI
from database.models import NightAuditSession, DailyJourMetrics
from datetime import datetime, timedelta

lightspeed_bp = Blueprint('lightspeed', __name__)

@lightspeed_bp.route('/api/lightspeed/connect', methods=['POST'])
def connect_lightspeed():
    """
    OAuth 2.0 setup for property-specific Lightspeed credentials
    Returns auth URL for user to grant permission
    """
    data = request.json
    property_id = data['property_id']
    callback_url = request.host_url + 'api/lightspeed/callback'

    # Init Lightspeed OAuth flow
    ls_client = LightspeedAPI(property_id=property_id)
    auth_url = ls_client.get_auth_url(callback_url)

    return jsonify({'auth_url': auth_url})

@lightspeed_bp.route('/api/lightspeed/callback', methods=['GET'])
def lightspeed_callback():
    """Handle OAuth callback, store access_token in secure config"""
    code = request.args.get('code')
    property_id = request.args.get('state')  # CSRF protection

    ls_client = LightspeedAPI(property_id=property_id)
    access_token = ls_client.exchange_code(code)

    # Store securely in .env or secrets manager
    save_property_credential(property_id, 'lightspeed_token', access_token)

    return jsonify({'status': 'connected'})

@lightspeed_bp.route('/api/lightspeed/sync/<audit_date>', methods=['POST'])
def sync_daily_data(audit_date):
    """
    Triggered at 03:00 AM (after Part execution in Lightspeed)
    Pulls: Daily Revenue, AR Aging, Room Occupancy, Guest Ledger
    """
    try:
        ls_client = LightspeedAPI(property_id=session['property_id'])

        # Pull daily revenue report
        daily_rev = ls_client.get_daily_revenue(audit_date)
        ar_aging = ls_client.get_ar_aging()
        room_status = ls_client.get_room_occupancy()
        guest_ledger = ls_client.get_guest_ledger_balance()

        # Auto-fill RJ Natif session
        rj_session = NightAuditSession.query.filter_by(
            audit_date=audit_date
        ).first()

        if not rj_session:
            rj_session = NightAuditSession(audit_date=audit_date)
            db.session.add(rj_session)

        # Auto-populate Recap tab
        rj_session.cash_ls_lecture = daily_rev['cash']['lecture']
        rj_session.cheque_ar_lecture = ar_aging['cheques_ar']

        # Auto-populate Jour tab
        rj_session.jour_chambres = room_status['revenue']
        rj_session.jour_occupation_rate = room_status['occupancy_pct']
        rj_session.jour_nb_clients = room_status['guest_count']

        # Mark Quasimodo/GEAC as "ready to calculate"
        rj_session.ls_sync_timestamp = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'status': 'synced',
            'timestamp': rj_session.ls_sync_timestamp,
            'recap_auto_filled': True,
            'jour_auto_filled': True
        })

    except LightspeedAPIError as e:
        return jsonify({'error': str(e), 'retry_in_minutes': 15}), 500

@lightspeed_bp.route('/api/lightspeed/status', methods=['GET'])
def integration_status():
    """Check if Lightspeed connection is active and when last sync occurred"""
    property_id = session['property_id']
    token = get_property_credential(property_id, 'lightspeed_token')

    if not token:
        return jsonify({'status': 'disconnected'})

    ls_client = LightspeedAPI(property_id=property_id)
    is_valid = ls_client.verify_token()

    # Get last sync timestamp
    last_session = NightAuditSession.query.filter_by(
        property_id=property_id
    ).order_by(NightAuditSession.audit_date.desc()).first()

    return jsonify({
        'status': 'connected' if is_valid else 'token_expired',
        'last_sync': last_session.ls_sync_timestamp if last_session else None,
        'requires_re_auth': not is_valid
    })
```

**New dependencies**:
```
requests>=2.28.0
requests-oauthlib>=1.3.0
python-dateutil>=2.8.2
```

**Database changes**:
```sql
-- New columns in NightAuditSession
ALTER TABLE night_audit_sessions ADD COLUMN ls_sync_timestamp DATETIME;
ALTER TABLE night_audit_sessions ADD COLUMN ls_sync_status VARCHAR(50);  -- 'pending', 'synced', 'failed'

-- New table for property integrations
CREATE TABLE property_integrations (
    id INTEGER PRIMARY KEY,
    property_id INTEGER NOT NULL,
    integration_type VARCHAR(50),  -- 'lightspeed', 'marsha', 'str', etc.
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at DATETIME,
    is_active BOOLEAN DEFAULT 1,
    last_tested_at DATETIME,
    created_at DATETIME,
    UNIQUE(property_id, integration_type)
);
```

**Testing**:
```python
# tests/test_lightspeed_integration.py
import pytest
from unittest.mock import Mock, patch
from routes.integrations.lightspeed import lightspeed_bp
from utils.integrations.lightspeed_client import LightspeedAPI

def test_sync_daily_data_success(app, client):
    """Verify daily revenue is correctly synced to RJ session"""
    with app.app_context():
        # Mock Lightspeed API response
        with patch('utils.integrations.lightspeed_client.LightspeedAPI.get_daily_revenue') as mock_rev:
            mock_rev.return_value = {
                'cash': {'lecture': 5234.50},
                'cheques': {'lecture': 1200.00}
            }

            response = client.post('/api/lightspeed/sync/2026-02-25')
            assert response.status_code == 200

            # Verify RJ session was updated
            session = NightAuditSession.query.filter_by(
                audit_date='2026-02-25'
            ).first()
            assert session.cash_ls_lecture == 5234.50

def test_lightspeed_connection_invalid_token(app):
    """Verify proper handling of expired token"""
    with patch.object(LightspeedAPI, 'verify_token', return_value=False):
        response = client.get('/api/lightspeed/status')
        assert response.json['status'] == 'token_expired'
```

**Lightspeed API Integration Points**:
- `GET /accounts/{accountID}/reports/DailyRevenue` → Recap tab (cash, cheques, cards)
- `GET /accounts/{accountID}/reports/ArAging` → GEAC tab
- `GET /accounts/{accountID}/rooms` → Jour occupancy
- `GET /accounts/{accountID}/receivables` → Guest ledger balance

**Rate Limits**: 60 requests/min per account (sufficient for once-daily pull)

---

#### 1.2 Email & Alert Engine (Weeks 5-6)
**Objective**: Automated alerts + daily digest emails

```python
# routes/notifications/email_engine.py
from flask import Blueprint, request, jsonify, current_app
from flask_mail import Mail, Message
from celery import Celery
from datetime import datetime, timedelta
from database.models import NightAuditSession, User, EmailPreference
import json

mail = Mail()
celery = Celery(__name__)

email_bp = Blueprint('email', __name__)

@celery.task
def send_variance_alert(session_id, variance_amount, receptionist_name):
    """
    Triggered when receptionist variance > threshold
    Sends to: Auditor, GM, Accounting Manager
    """
    session = NightAuditSession.query.get(session_id)

    # Get recipients based on role
    recipients = User.query.filter(
        User.role.in_(['gm', 'gsm', 'accounting', 'night_auditor']),
        User.property_id == session.property_id,
        User.is_active == True
    ).all()

    # Check email preferences
    recipients = [u for u in recipients if not has_opted_out(u, 'variance_alerts')]

    subject = f"⚠️ Cash Variance Alert: {receptionist_name}"

    body = f"""
    <h2>Cash Variance Detected</h2>
    <p><strong>Receptionist:</strong> {receptionist_name}</p>
    <p><strong>Variance:</strong> CAD ${variance_amount:,.2f}</p>
    <p><strong>Date:</strong> {session.audit_date}</p>

    <p><a href="{current_app.config['APP_URL']}/rj/native/{session.audit_date}">
        View RJ Session →
    </a></p>

    <p style="color: #666; font-size: 12px;">
        <a href="{current_app.config['APP_URL']}/notifications/preferences">
            Manage email preferences
        </a>
    </p>
    """

    msg = Message(
        subject=subject,
        recipients=[u.email for u in recipients],
        html=body
    )

    mail.send(msg)

@celery.task
def send_daily_digest(property_id, delivery_hour=8):
    """
    Scheduled daily (8:00 AM)
    Summary of: variances, anomalies, opportunities, KPIs
    Sent to: GMs only
    """
    gms = User.query.filter_by(
        property_id=property_id,
        role='gm',
        is_active=True
    ).all()

    # Get yesterday's RJ session
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    session = NightAuditSession.query.filter_by(
        property_id=property_id,
        audit_date=yesterday
    ).first()

    if not session or session.status != 'submitted':
        return  # No submitted session to digest

    # Compile digest data
    revenue_vs_ytd = calculate_revenue_variance(property_id, yesterday)
    labor_vs_budget = calculate_labor_variance(property_id, yesterday)
    anomalies = detect_anomalies(session)

    subject = f"Daily Digest - {yesterday.strftime('%A, %B %d, %Y')}"

    body = f"""
    <h2>Morning Executive Brief</h2>

    <h3>Revenue Performance</h3>
    <ul>
        <li>Total Revenue: CAD ${session.jour_total_revenue:,.2f}</li>
        <li>vs. YTD Average: {revenue_vs_ytd['variance_pct']:.1f}%</li>
        <li>Room Revenue: CAD ${session.jour_chambres:,.2f} (ADR: ${session.jour_adr:.2f})</li>
        <li>Occupancy: {session.jour_occupation_rate:.1f}%</li>
    </ul>

    <h3>Labor Performance</h3>
    <ul>
        <li>Total Labor Cost: CAD ${labor_vs_budget['actual']:,.2f}</li>
        <li>vs. Budget: {labor_vs_budget['variance_pct']:.1f}%</li>
    </ul>

    <h3>⚠️ Alerts & Anomalies</h3>
    {render_anomalies(anomalies)}

    <p><a href="{current_app.config['APP_URL']}/dashboard">
        Full Dashboard →
    </a></p>
    """

    for gm in gms:
        msg = Message(
            subject=subject,
            recipients=[gm.email],
            html=body
        )
        mail.send(msg)

@email_bp.route('/api/notifications/setup', methods=['POST'])
def setup_notifications():
    """Property admin configures alert thresholds and recipients"""
    data = request.json
    property_id = session['property_id']

    config = {
        'variance_threshold': data.get('variance_threshold', 50.0),
        'revenue_variance_threshold': data.get('revenue_variance', 15.0),
        'labor_variance_threshold': data.get('labor_variance', 20.0),
        'recipients': {
            'variance_alerts': data.get('variance_recipients', ['gm', 'accounting']),
            'daily_digest': data.get('digest_recipients', ['gm', 'gsm']),
            'weekly_summary': data.get('weekly_recipients', ['gm', 'controller']),
        },
        'delivery_times': {
            'daily_digest_hour': data.get('digest_hour', 8),
            'variance_alert_immediate': True,
        }
    }

    save_notification_config(property_id, config)

    return jsonify({'status': 'configured'})

@email_bp.route('/api/notifications/test', methods=['POST'])
def test_email():
    """Send test email to user"""
    user = get_current_user()

    msg = Message(
        subject='Test Email from Night Audit Platform',
        recipients=[user.email],
        html='<p>This is a test email. Notifications are working!</p>'
    )

    mail.send(msg)

    return jsonify({'status': 'sent'})

@email_bp.route('/api/notifications/preferences', methods=['GET', 'POST'])
def manage_preferences():
    """User can opt-out of specific email types"""
    user = get_current_user()

    if request.method == 'POST':
        prefs = request.json
        save_user_email_preferences(user.id, prefs)
        return jsonify({'status': 'saved'})

    # GET - return current preferences
    prefs = get_user_email_preferences(user.id)

    return jsonify({
        'variance_alerts': prefs.get('variance_alerts', True),
        'daily_digest': prefs.get('daily_digest', True),
        'weekly_summary': prefs.get('weekly_summary', True),
        'anomaly_alerts': prefs.get('anomaly_alerts', True),
    })

# Scheduled tasks (via APScheduler)
def schedule_notifications():
    """Initialize background scheduler"""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()

    # Daily digest at 8:00 AM
    scheduler.add_job(
        send_daily_digest,
        'cron',
        hour=8,
        minute=0,
        args=[current_app.config['PROPERTY_ID']]
    )

    scheduler.start()
```

**New dependencies**:
```
Flask-Mail>=0.9.1
celery>=5.2.0
redis>=4.3.0  (for celery broker)
APScheduler>=3.10.0
```

**Configuration (.env)**:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=audit@sheraton-laval.com
MAIL_PASSWORD=***
MAIL_DEFAULT_SENDER=audit@sheraton-laval.com

# Or use SendGrid (recommended for scaling)
SENDGRID_API_KEY=SG.***
```

**Database changes**:
```sql
-- New table for email preferences
CREATE TABLE email_preferences (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    variance_alerts BOOLEAN DEFAULT 1,
    daily_digest BOOLEAN DEFAULT 1,
    weekly_summary BOOLEAN DEFAULT 1,
    anomaly_alerts BOOLEAN DEFAULT 1,
    updated_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- New table for notification config
CREATE TABLE notification_config (
    id INTEGER PRIMARY KEY,
    property_id INTEGER NOT NULL,
    variance_threshold FLOAT DEFAULT 50.0,
    revenue_variance_threshold FLOAT DEFAULT 15.0,
    labor_variance_threshold FLOAT DEFAULT 20.0,
    config_json TEXT,  -- JSON: recipients, timing, etc.
    updated_at DATETIME,
    UNIQUE(property_id)
);
```

---

#### 1.3 Marriott MARSHA Integration (Weeks 7-12)
**Objective**: Real-time data sync to Marriott corporate system

```python
# routes/integrations/marsha.py
from flask import Blueprint, request, jsonify, session
from utils.integrations.marsha_client import MarshaAPI
from database.models import NightAuditSession, MarshaSyncLog
from datetime import datetime
import logging

marsha_bp = Blueprint('marsha', __name__)
logger = logging.getLogger(__name__)

@marsha_bp.route('/api/marsha/connect', methods=['POST'])
def connect_marsha():
    """
    Marriott IT provides: client_id, client_secret, tenant_id
    Stored securely in secrets manager (AWS Secrets Manager)
    """
    data = request.json
    property_id = session['property_id']

    marsha = MarshaAPI(
        client_id=data['client_id'],
        client_secret=data['client_secret'],
        tenant_id=data['tenant_id']
    )

    # Verify credentials
    if not marsha.verify_credentials():
        return jsonify({'error': 'Invalid credentials'}), 401

    # Save securely
    save_marsha_credentials(property_id, data)

    return jsonify({
        'status': 'connected',
        'property_code': marsha.get_property_code()
    })

@marsha_bp.route('/api/marsha/submit/<audit_date>', methods=['POST'])
def submit_rj_to_marsha(audit_date):
    """
    Called after RJ session is submitted (status='submitted')
    Transforms RJ data to MARSHA DBRS format
    Bi-directional: Send RJ data, receive benchmarks
    """
    try:
        property_id = session['property_id']
        rj_session = NightAuditSession.query.filter_by(
            audit_date=audit_date,
            property_id=property_id
        ).first()

        if not rj_session or rj_session.status != 'submitted':
            return jsonify({'error': 'Session not submitted'}), 400

        # Initialize MARSHA client
        marsha_creds = get_marsha_credentials(property_id)
        marsha = MarshaAPI(**marsha_creds)

        # Transform RJ to MARSHA DBRS format
        dbrs_payload = transform_rj_to_dbrs(rj_session)

        # Submit to MARSHA
        response = marsha.submit_dbrs(
            property_code=marsha_creds['property_code'],
            audit_date=audit_date,
            data=dbrs_payload
        )

        # Log successful submission
        sync_log = MarshaSyncLog(
            property_id=property_id,
            audit_date=audit_date,
            direction='upload',
            status='success',
            payload_size=len(json.dumps(dbrs_payload)),
            response=response,
            timestamp=datetime.utcnow()
        )
        db.session.add(sync_log)

        # Also receive comp-set benchmarks from MARSHA
        benchmarks = marsha.get_comp_set_benchmarks(
            property_code=marsha_creds['property_code'],
            audit_date=audit_date
        )

        rj_session.marsha_comp_set = json.dumps(benchmarks)
        rj_session.marsha_sync_timestamp = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'status': 'submitted_to_marsha',
            'marsha_response_id': response.get('id'),
            'comp_set_benchmarks': benchmarks
        })

    except MarshaAPIError as e:
        logger.error(f"MARSHA sync failed: {str(e)}")

        # Log failed submission for retry
        sync_log = MarshaSyncLog(
            property_id=property_id,
            audit_date=audit_date,
            direction='upload',
            status='failed',
            error_message=str(e),
            timestamp=datetime.utcnow()
        )
        db.session.add(sync_log)
        db.session.commit()

        return jsonify({'error': str(e), 'retry_available': True}), 500

@marsha_bp.route('/api/marsha/benchmarks/<audit_date>', methods=['GET'])
def get_benchmarks(audit_date):
    """
    Returns comp-set benchmarks for audit date
    Cached in RJ session after MARSHA sync
    """
    property_id = session['property_id']
    rj_session = NightAuditSession.query.filter_by(
        audit_date=audit_date,
        property_id=property_id
    ).first()

    if not rj_session:
        return jsonify({'error': 'Session not found'}), 404

    benchmarks = json.loads(rj_session.marsha_comp_set or '{}')

    return jsonify({
        'audit_date': audit_date,
        'your_adr': rj_session.jour_adr,
        'comp_set_adr': benchmarks.get('comp_adr'),
        'comp_adr_variance_pct': (
            (rj_session.jour_adr - benchmarks.get('comp_adr', 0))
            / benchmarks.get('comp_adr', 1) * 100
        ),
        'comp_occupancy': benchmarks.get('comp_occupancy'),
        'comp_revpar': benchmarks.get('comp_revpar'),
        'market_rank': benchmarks.get('market_rank'),  # e.g., 3rd of 5 hotels
    })

def transform_rj_to_dbrs(rj_session):
    """
    Maps RJ Natif data to Marriott DBRS API schema
    DBRS = Daily Business Review Summary
    """
    return {
        'audit_date': rj_session.audit_date.isoformat(),
        'property_code': rj_session.property_id,
        'segments': {
            'transient': json.loads(rj_session.dbrs_market_segments or '{}').get('transient', 0),
            'group': json.loads(rj_session.dbrs_market_segments or '{}').get('group', 0),
            'contract': json.loads(rj_session.dbrs_market_segments or '{}').get('contract', 0),
            'other': json.loads(rj_session.dbrs_market_segments or '{}').get('other', 0),
        },
        'revenue': {
            'room': rj_session.jour_chambres,
            'food_beverage': rj_session.jour_cafe_nourriture + rj_session.jour_cafe_boisson +
                           rj_session.jour_piazza_nourriture + rj_session.jour_piazza_boisson,
            'other': rj_session.jour_nettoyeur + rj_session.jour_internet,
            'total': rj_session.jour_total_revenue,
        },
        'occupancy': {
            'rooms_sold': rj_session.jour_rooms_simple + rj_session.jour_rooms_double +
                         rj_session.jour_rooms_suite,
            'occupancy_rate': rj_session.jour_occupation_rate,
            'adr': rj_session.jour_adr,
            'revpar': rj_session.jour_revpar,
            'guest_count': rj_session.jour_nb_clients,
        },
        'variances': {
            'quasimodo_variance': rj_session.quasi_variance,
            'cash_variance': rj_session.dueback_entries.get('total_variance', 0) if rj_session.dueback_entries else 0,
        },
        'on_the_books': json.loads(rj_session.dbrs_otb_data or '{}'),
    }
```

**MARSHA API Integration Points**:
- `POST /api/v1/properties/{propertyCode}/dbrs` → Submit daily DBRS
- `GET /api/v1/properties/{propertyCode}/comp-set/benchmarks` → Receive comp-set data
- `GET /api/v1/properties/{propertyCode}/market-position` → Get market rank
- Webhook: `POST /webhooks/marsha/validation` → Receive corporate validation results

**Rate Limits**: 10 requests/min per property (sufficient for daily batch)

**Database changes**:
```sql
ALTER TABLE night_audit_sessions ADD COLUMN marsha_sync_timestamp DATETIME;
ALTER TABLE night_audit_sessions ADD COLUMN marsha_comp_set TEXT;  -- JSON benchmarks
ALTER TABLE night_audit_sessions ADD COLUMN marsha_response_id VARCHAR(100);

CREATE TABLE marsha_sync_log (
    id INTEGER PRIMARY KEY,
    property_id INTEGER NOT NULL,
    audit_date DATE NOT NULL,
    direction VARCHAR(20),  -- 'upload' or 'download'
    status VARCHAR(20),  -- 'success', 'failed', 'pending'
    payload_size INTEGER,
    response TEXT,  -- JSON response from MARSHA
    error_message TEXT,
    timestamp DATETIME,
    INDEX(property_id, audit_date)
);
```

---

## PHASE 2: INTELLIGENCE & ANALYTICS (Weeks 13-28)
### Investment: $150K | Revenue Potential: $12M/year

#### 2.1 Revenue Management Integration (STR, Pace)
#### 2.2 Predictive Analytics (ML models)
#### 2.3 Compliance & Audit Logging

*(Implementation details follow similar patterns to Phase 1)*

---

## PHASE 3: OPERATIONAL AUTOMATION (Weeks 29-46)
### Investment: $175K | Revenue Potential: $12M/year

#### 3.1 Housekeeping Integration
#### 3.2 Staff Scheduling
#### 3.3 Multi-Property Management

---

## PHASE 4: MOBILE & UX (Weeks 47-62)
### Investment: $100K | Revenue Potential: $2.85M/year

#### 4.1 Native Mobile App (React Native)
#### 4.2 Offline Sync

---

## TECHNICAL DEBT & MIGRATIONS

### Current Architecture Issues
1. **Monolithic Flask app** → Migrate to FastAPI for better async/async
2. **SQLite → PostgreSQL** (for multi-tenant scaling)
3. **Vanilla JS → React/Vue** (for complex UI, Phase 4)
4. **Email synchronously** → Move to Celery async queues

### Migration Plan
- **Month 9-10**: PostgreSQL migration (0-downtime blue-green deployment)
- **Month 15-16**: FastAPI endpoint creation (gradual, not all-at-once)
- **Month 20-21**: Frontend framework introduction (start with new features only)

---

## TESTING & QUALITY ASSURANCE

### Unit Test Coverage Target
- Phase 1: 60% (core integrations critical)
- Phase 2: 70% (analytics needs validation)
- Phase 3: 75% (operations critical path)
- Phase 4: 80% (mobile reliability)

### Integration Test Strategy
```python
# tests/integration/test_lightspeed_to_rj.py
"""End-to-end test: Lightspeed → RJ auto-fill → MARSHA submission"""

def test_full_audit_workflow():
    # 1. Mock Lightspeed daily revenue pull
    # 2. Verify RJ Recap auto-filled
    # 3. Auditor submits RJ
    # 4. Verify MARSHA sync triggered
    # 5. Verify email alert sent
    pass
```

### Load Testing
- Target: 50 concurrent properties syncing daily
- Tool: Locust.io for performance testing

---

## DEPLOYMENT & INFRASTRUCTURE

### Current (SQLite, Flask)
- Single server: $50/month
- Manual backups
- No auto-scaling

### Phase 1 Target (PostgreSQL, Flask + Celery)
```
AWS Architecture:
- RDS PostgreSQL (Multi-AZ): $300/month
- ElastiCache Redis (Celery broker): $50/month
- EC2 (t3.medium Flask + Celery workers): $100/month
- S3 (logs, backups, PDFs): $20/month
- CloudFront CDN: $20/month
- RDS backup snapshots: $30/month
---
Total: ~$520/month for 1,900 properties
= $0.27/property/month infrastructure cost
```

### Optional: Serverless Approach (Phase 2+)
```
AWS Serverless (for analytics/forecasting):
- Lambda: $0.0000002 per request
- DynamoDB (if needed): $1.25/GB/month
- API Gateway: $3.50 per million requests
```

---

## SECURITY CHECKLIST

- [ ] Lightspeed API credentials in AWS Secrets Manager (not .env)
- [ ] MARSHA OAuth 2.0 with PKCE for web flows
- [ ] Rate limiting: 100 requests/min per API key
- [ ] Request signing: All MARSHA requests signed with HMAC
- [ ] Audit logging: All data access logged to immutable table
- [ ] SOC 2 Type II certification (Year 2)
- [ ] HIPAA compliance (if handling guest health info)
- [ ] PCI DSS partial compliance (credit card data handled minimally)
- [ ] Encryption: TLS 1.3 for all API calls, AES-256 for data at rest
- [ ] Penetration testing: Annual P-tests + vulnerability scans

---

## SUCCESS METRICS (By Phase)

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| **API Success Rate** | 95% | 98% | 99% | 99.5% |
| **Data Sync Latency** | <5 min | <2 min | Real-time | Real-time |
| **Data Accuracy** | 99.5% | 99.8% | 99.9% | 99.9% |
| **Audit Time Reduction** | 40% | 50% | 60% | 75% |
| **Error Rate (bugs/month)** | <5 | <2 | <1 | <1 |
| **Feature Adoption** | 60% | 80% | 85% | 70% |
| **NPS Score** | 45 | 55 | 65 | 70 |
| **Customer Churn** | 5% | 2% | <1% | <1% |

---

## CRITICAL DEPENDENCIES & RISKS

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Lightspeed API blocked by Marriott IT | 6-8 week delay | Start with Sheraton Laval only; negotiate early |
| MARSHA API documentation unavailable | Jeopardizes core feature | Request from Marriott IT sponsor before Phase 1 |
| Celery/Redis complexity for small team | Operational overhead | Consider using managed ElastiCache, start simple |
| Multi-tenant database design mistakes | Expensive to refactor later | Prototype multi-tenant schema before Phase 3 |
| PII data exposure (guest names in logs) | GDPR/privacy violations | Implement data masking in logs immediately |

---

**For questions or clarifications, contact the development team.**
