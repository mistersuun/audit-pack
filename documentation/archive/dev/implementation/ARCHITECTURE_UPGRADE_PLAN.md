# Sheraton Laval Night Audit Webapp - Architecture Upgrade Plan

## EXECUTIVE SUMMARY

This document outlines a comprehensive, phased architecture upgrade for the Flask-based Night Audit application. The plan maintains all existing functionality while adding:
1. Multi-user role-based authentication (replacing single PIN)
2. PDF and Excel auto-parsing for Daily Revenue, Advance Deposit, and FreedomPay files
3. Quasimodo automated card reconciliation engine
4. CRM module for guest/corporate tracking and revenue analytics
5. Monolithic template refactoring (5885 lines to component-based)
6. Dedicated API layer with versioning
7. Improved Excel reader accuracy

**Key Constraint**: Keep Flask + SQLite locally-runnable, xlrd/xlutils for .xls manipulation, and the "fill input sheets → fire macros → jour is calculated" pattern.

---

## 1. DATABASE SCHEMA REDESIGN

### 1.1 New User & Auth Models

```python
# database/models.py additions

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Roles: 'night_auditor', 'gm', 'gsm', 'front_desk_supervisor', 'accounting'
    role = db.Column(db.String(50), nullable=False, default='accounting')
    
    full_name_fr = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    audit_sessions = db.relationship('AuditSession', backref='auditor', lazy=True)
    guest_interactions = db.relationship('GuestInteraction', backref='created_by_user', lazy=True)
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, *roles):
        """Check if user has any of the specified roles."""
        return self.role in roles


class AuditSession(db.Model):
    """Audit session metadata (replaces Shift for multi-user context)."""
    __tablename__ = 'audit_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    auditor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    
    # References to uploaded/processed files
    rj_file_path = db.Column(db.String(500))
    rj_upload_time = db.Column(db.DateTime)
    rj_file_hash = db.Column(db.String(64))  # For deduplication
    
    # Auto-parse results
    daily_revenue_pdf_path = db.Column(db.String(500))
    advance_deposit_pdf_path = db.Column(db.String(500))
    freedompay_excel_path = db.Column(db.String(500))
    
    task_completions = db.relationship('TaskCompletion', backref='audit_session', lazy=True)
```

### 1.2 CRM Models

```python
class Guest(db.Model):
    """Core guest profile."""
    __tablename__ = 'crm_guests'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100))  # PMS guest ID
    
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(20))
    
    company = db.Column(db.String(200))
    vip_status = db.Column(db.Boolean, default=False)
    vip_notes = db.Column(db.Text)
    
    # Preferences
    language_pref = db.Column(db.String(10), default='fr')
    allergies = db.Column(db.Text)
    special_requests = db.Column(db.Text)
    
    first_visit = db.Column(db.Date)
    last_visit = db.Column(db.Date)
    total_visits = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    interactions = db.relationship('GuestInteraction', backref='guest', lazy=True)
    reservations = db.relationship('Reservation', backref='guest', lazy=True)
    ar_records = db.relationship('ARRecord', backref='guest', lazy=True)


class CorporateAccount(db.Model):
    """Corporate/group billing entities."""
    __tablename__ = 'crm_corporate_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100))  # PMS account ID
    
    legal_name = db.Column(db.String(255), nullable=False)
    trading_name = db.Column(db.String(255))
    tax_id = db.Column(db.String(50))
    
    primary_contact = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    
    billing_address = db.Column(db.Text)
    payment_terms = db.Column(db.String(100))  # e.g., "Net 30"
    credit_limit = db.Column(db.Float, default=0)
    
    account_type = db.Column(db.String(50))  # 'corporate', 'group', 'travel_agency', 'other'
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reservations = db.relationship('Reservation', backref='corporate_account', lazy=True)
    ar_records = db.relationship('ARRecord', backref='corporate_account', lazy=True)


class GuestInteraction(db.Model):
    """Log of guest interactions (calls, requests, issues, feedback)."""
    __tablename__ = 'crm_guest_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('crm_guests.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    interaction_type = db.Column(db.String(50), nullable=False)
    # Types: 'call', 'visit', 'email', 'feedback', 'complaint', 'request', 'other'
    
    notes = db.Column(db.Text, nullable=False)
    resolution = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Reservation(db.Model):
    """Group bookings and reservations."""
    __tablename__ = 'crm_reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100))  # PMS reservation ID
    
    guest_id = db.Column(db.Integer, db.ForeignKey('crm_guests.id'))
    corporate_account_id = db.Column(db.Integer, db.ForeignKey('crm_corporate_accounts.id'))
    
    reservation_type = db.Column(db.String(50))  # 'individual', 'group', 'package'
    
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    
    rooms_booked = db.Column(db.Integer, default=1)
    room_type = db.Column(db.String(100))  # 'single', 'double', 'suite', etc.
    
    revenue_expected = db.Column(db.Float)
    revenue_actual = db.Column(db.Float)
    
    status = db.Column(db.String(20), default='confirmed')  # confirmed, checked_in, checked_out, cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ARRecord(db.Model):
    """Accounts Receivable tracking."""
    __tablename__ = 'crm_ar_records'
    
    id = db.Column(db.Integer, primary_key=True)
    
    guest_id = db.Column(db.Integer, db.ForeignKey('crm_guests.id'))
    corporate_account_id = db.Column(db.Integer, db.ForeignKey('crm_corporate_accounts.id'))
    
    invoice_number = db.Column(db.String(100), unique=True, index=True)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    
    amount_original = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0)
    amount_outstanding = db.Column(db.Float)
    
    status = db.Column(db.String(20), default='outstanding')
    # outstanding, partial, paid, written_off, disputed
    
    aging_days = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_aging(self):
        """Auto-calculate days since invoice date."""
        self.aging_days = (datetime.utcnow().date() - self.invoice_date).days
        self.amount_outstanding = self.amount_original - self.amount_paid
```

### 1.3 Enhanced Audit Data Models

```python
# Extend existing DailyReport with parsing metadata

class ParsedPDFData(db.Model):
    """Cache parsed PDF data to avoid re-parsing."""
    __tablename__ = 'parsed_pdf_data'
    
    id = db.Column(db.Integer, primary_key=True)
    audit_session_id = db.Column(db.Integer, db.ForeignKey('audit_sessions.id'), nullable=False)
    
    pdf_type = db.Column(db.String(50), nullable=False)
    # Types: 'daily_revenue', 'advance_deposit', 'freedompay_export'
    
    file_hash = db.Column(db.String(64))
    source_filename = db.Column(db.String(255))
    
    # Extracted data (JSON to allow flexibility)
    extracted_data = db.Column(db.JSON)
    
    # Confidence/validation
    extraction_confidence = db.Column(db.Float)  # 0.0 to 1.0
    validation_errors = db.Column(db.JSON)  # List of warnings/errors
    
    parsed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QuasimodoParsing(db.Model):
    """Stores Quasimodo reconciliation results."""
    __tablename__ = 'quasimodo_parsings'
    
    id = db.Column(db.Integer, primary_key=True)
    audit_session_id = db.Column(db.Integer, db.ForeignKey('audit_sessions.id'), nullable=False)
    
    # Input data (terminal vs bank)
    transelect_data = db.Column(db.JSON)  # From transelect sheet
    geac_ux_data = db.Column(db.JSON)    # From geac_ux sheet
    
    # Output reconciliation
    card_reconciliation = db.Column(db.JSON)  # By card type (visa, master, amex, debit)
    
    total_terminal = db.Column(db.Float)
    total_bank = db.Column(db.Float)
    variance = db.Column(db.Float)
    
    status = db.Column(db.String(20), default='pending')  # pending, reconciled, discrepancy
    discrepancy_notes = db.Column(db.Text)
    
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 2. AUTHENTICATION SYSTEM REDESIGN

### 2.1 Overview

Replace single PIN with multi-user role-based authentication:
- Login with username + password (werkzeug hashing)
- 5 roles with specific permissions:
  - **Night Auditor**: Full access to audit tools, reports, CRM dashboards
  - **GM/GSM**: Reports, CRM, dashboards (NO task lists, no Excel editing)
  - **Front Desk Supervisor**: Limited task visibility, no audit editing
  - **Accounting**: Reports, AR aging, balance reconciliation (no guest data)
  - **Admin**: User management, system configuration

### 2.2 New Routes (routes/auth_v2.py)

```python
# routes/auth_v2.py

@auth_v2_bp.route('/register', methods=['GET', 'POST'])
# Admin-only user registration

@auth_v2_bp.route('/login', methods=['GET', 'POST'])
# Username + password login

@auth_v2_bp.route('/profile')
# View/edit profile

@auth_v2_bp.route('/change-password', methods=['POST'])
# Change password
```

### 2.3 Role-Based Decorators

```python
# utils/auth_decorators.py

def role_required(*roles):
    """Restrict route to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('authenticated'):
                return redirect(url_for('auth_v2.login'))
            if current_user.role not in roles:
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage in routes:
@rj_bp.route('/api/rj/upload', methods=['POST'])
@role_required('night_auditor', 'accounting')
def upload_rj():
    # Only Night Auditor and Accounting can upload
    ...
```

### 2.4 Session & User Context

- Use Flask-Login (add to requirements)
- session['user_id'], session['user_role'] in every request
- AuditSession tracks auditor_id → full audit trail

---

## 3. PDF & EXCEL PARSING ARCHITECTURE

### 3.1 Parser Module Structure

```
utils/
├── parsers/
│   ├── __init__.py
│   ├── base_parser.py          # Abstract base for all parsers
│   ├── daily_revenue_parser.py # Daily Revenue PDF parser
│   ├── advance_deposit_parser.py # Advance Deposit PDF parser
│   ├── freedompay_parser.py    # FreedomPay Excel parser
│   ├── hp_excel_parser.py      # HP (Hotel Promotion) Excel parser
│   └── validation.py           # Data validation utilities
└── ...
```

### 3.2 Base Parser Class

```python
# utils/parsers/base_parser.py

class BaseParser(ABC):
    """Abstract base for all document parsers."""
    
    def __init__(self, file_path_or_bytes, parser_config=None):
        self.source = file_path_or_bytes
        self.config = parser_config or {}
        self.extracted_data = {}
        self.validation_errors = []
        self.confidence_score = 0.0
    
    @abstractmethod
    def parse(self) -> dict:
        """Parse document and return extracted data."""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate extracted data. Return True if valid."""
        pass
    
    def get_result(self) -> dict:
        """Return parse result with metadata."""
        return {
            'data': self.extracted_data,
            'valid': self.validate(),
            'confidence': self.confidence_score,
            'errors': self.validation_errors,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def cache_result(self, session_id: str) -> None:
        """Store result in database for later reference."""
        # Implementation in subclasses
        pass
```

### 3.3 Daily Revenue PDF Parser

```python
# utils/parsers/daily_revenue_parser.py

class DailyRevenueParser(BaseParser):
    """Parse Daily Revenue PDF (manual layout recognition)."""
    
    # Field mapping: (pdf_key) -> (recap_sheet_cell)
    FIELD_MAPPINGS = {
        'comptant_positouch': 'B7',      # Cash from POS
        'comptant_lightspeed': 'B6',     # Cash from Lightspeed
        'cheque_payment_register': 'B8',  # Cheques
        'cheque_daily_revenue': 'B9',
        'tips_total': 'B18',             # Tips (if on PDF)
    }
    
    def parse(self) -> dict:
        # Use pdfplumber to extract text/tables
        # Match patterns to known field layouts
        # Return dict: { 'comptant_positouch': 1234.56, ... }
        pass
    
    def validate(self) -> bool:
        # Check required fields present
        # Check numeric ranges (revenue > 0, < max hotel daily revenue)
        # Cross-validate totals
        pass
```

### 3.4 FreedomPay Excel Parser

```python
# utils/parsers/freedompay_parser.py

class FreedomPayParser(BaseParser):
    """Parse FreedomPay Excel export (bank-side card settlement)."""
    
    # Maps FreedomPay sheet structure to geac_ux cells
    FIELD_MAPPINGS = {
        'amex_cash_out': 'B6',
        'visa_cash_out': 'J6',
        'mastercard_cash_out': 'G6',
        'diners_cash_out': 'E6',
        'discover_cash_out': 'K6',
    }
    
    def parse(self) -> dict:
        # Use xlrd to read FreedomPay export
        # Match row/column structure
        # Extract settlement amounts by card type
        pass
```

### 3.5 Parser Registry & Factory

```python
# utils/parsers/__init__.py

class ParserFactory:
    """Factory to instantiate correct parser by document type."""
    
    PARSERS = {
        'daily_revenue_pdf': DailyRevenueParser,
        'advance_deposit_pdf': AdvanceDepositParser,
        'freedompay_excel': FreedomPayParser,
        'hp_excel': HPExcelParser,
    }
    
    @staticmethod
    def create_parser(doc_type: str, file_path_or_bytes, config=None):
        parser_class = ParserFactory.PARSERS.get(doc_type)
        if not parser_class:
            raise ValueError(f"Unknown document type: {doc_type}")
        return parser_class(file_path_or_bytes, config)
    
    @staticmethod
    def parse_and_cache(audit_session_id, doc_type, file_path_or_bytes):
        """Parse document and cache result."""
        parser = ParserFactory.create_parser(doc_type, file_path_or_bytes)
        result = parser.get_result()
        
        # Cache in database
        if result['valid']:
            pdf_data = ParsedPDFData(
                audit_session_id=audit_session_id,
                pdf_type=doc_type,
                extracted_data=result['data'],
                extraction_confidence=result['confidence'],
                validation_errors=result['errors']
            )
            db.session.add(pdf_data)
            db.session.commit()
        
        return result
```

### 3.6 Auto-Fill Integration

```python
# routes/rj.py - New endpoint

@rj_bp.route('/api/rj/auto-fill-from-pdf', methods=['POST'])
@role_required('night_auditor')
def auto_fill_from_pdf():
    """
    Upload PDF, parse it, auto-fill relevant RJ cells.
    
    Request:
    {
        'pdf_type': 'daily_revenue_pdf',
        'pdf_file': <file>,
        'rj_file': <file>  # Current RJ to fill
    }
    
    Response:
    {
        'success': True,
        'parsed_data': { ... },
        'filled_cells': ['B6', 'B7', 'B8', ...],
        'confidence': 0.95,
        'rj_file_url': '/download/rj_...'
    }
    """
    
    # 1. Parse PDF
    parsed = ParserFactory.parse_and_cache(
        audit_session_id=session['audit_session_id'],
        doc_type=request.form.get('pdf_type'),
        file_path_or_bytes=request.files['pdf_file']
    )
    
    if not parsed['valid']:
        return jsonify({
            'success': False,
            'errors': parsed['errors'],
            'confidence': parsed['confidence']
        }), 400
    
    # 2. Fill RJ file with parsed data
    rj_file = request.files['rj_file']
    rj_filler = RJFiller(rj_file)
    
    filled_cells = []
    for source_key, cell_ref in DailyRevenueParser.FIELD_MAPPINGS.items():
        if source_key in parsed['data']:
            rj_filler.fill_cell('Recap', cell_ref, parsed['data'][source_key])
            filled_cells.append(cell_ref)
    
    # 3. Return modified file
    output = io.BytesIO()
    rj_filler.save(output)
    output.seek(0)
    
    return jsonify({
        'success': True,
        'parsed_data': parsed['data'],
        'filled_cells': filled_cells,
        'confidence': parsed['confidence']
    })
```

---

## 4. QUASIMODO AUTO-RECONCILIATION ENGINE

### 4.1 Conceptual Design

Quasimodo automatically reconciles terminal card totals (transelect) vs. bank settlement amounts (geac_ux) by card type.

### 4.2 Implementation

```python
# utils/quasimodo.py

class QuasimodoReconciler:
    """Automated card reconciliation (terminal vs. bank)."""
    
    CARD_TYPES = ['visa', 'mastercard', 'amex', 'discover', 'debit']
    TOLERANCE = 0.01  # Allow $0.01 variance
    
    def __init__(self, audit_session_id):
        self.audit_session_id = audit_session_id
        self.transelect_data = {}
        self.geac_ux_data = {}
        self.reconciliation = {}
    
    def load_data_from_rj(self, rj_file_bytes):
        """Read transelect and geac_ux sheets."""
        reader = RJReader(rj_file_bytes)
        
        # Read transelect data
        self.transelect_data = reader.read_transelect()  # { 'visa': 1234.56, ... }
        
        # Read geac_ux data (bank settlement)
        self.geac_ux_data = reader.read_geac_ux()       # { 'visa': 1200.00, ... }
    
    def reconcile(self) -> dict:
        """Calculate reconciliation by card type."""
        
        self.reconciliation = {
            'card_type': {},
            'summary': {
                'total_terminal': 0,
                'total_bank': 0,
                'total_variance': 0,
                'status': 'reconciled'
            }
        }
        
        for card_type in self.CARD_TYPES:
            terminal = self.transelect_data.get(card_type, 0)
            bank = self.geac_ux_data.get(card_type, 0)
            variance = terminal - bank
            
            self.reconciliation['card_type'][card_type] = {
                'terminal': terminal,
                'bank': bank,
                'variance': variance,
                'reconciled': abs(variance) < self.TOLERANCE
            }
            
            self.reconciliation['summary']['total_terminal'] += terminal
            self.reconciliation['summary']['total_bank'] += bank
            self.reconciliation['summary']['total_variance'] += abs(variance)
            
            # If any card type has significant variance, mark as discrepancy
            if abs(variance) >= self.TOLERANCE:
                self.reconciliation['summary']['status'] = 'discrepancy'
        
        return self.reconciliation
    
    def save_result(self):
        """Store reconciliation in database."""
        result = QuasimodoParsing(
            audit_session_id=self.audit_session_id,
            transelect_data=self.transelect_data,
            geac_ux_data=self.geac_ux_data,
            card_reconciliation=self.reconciliation['card_type'],
            total_terminal=self.reconciliation['summary']['total_terminal'],
            total_bank=self.reconciliation['summary']['total_bank'],
            variance=self.reconciliation['summary']['total_variance'],
            status=self.reconciliation['summary']['status']
        )
        db.session.add(result)
        db.session.commit()
        return result


# routes/rj.py - New endpoint

@rj_bp.route('/api/rj/quasimodo/auto-reconcile', methods=['POST'])
@role_required('night_auditor')
def auto_reconcile_quasimodo():
    """
    Auto-calculate Quasimodo reconciliation from transelect + geac_ux.
    
    Request:
    {
        'rj_file': <file>
    }
    
    Response:
    {
        'success': True,
        'reconciliation': {
            'card_type': {
                'visa': { 'terminal': 5000.00, 'bank': 5000.00, 'variance': 0.00, 'reconciled': true },
                ...
            },
            'summary': {
                'total_terminal': 25000.00,
                'total_bank': 24999.50,
                'total_variance': 0.50,
                'status': 'discrepancy'
            }
        }
    }
    """
    
    rj_file = request.files['rj_file']
    
    reconciler = QuasimodoReconciler(session['audit_session_id'])
    reconciler.load_data_from_rj(rj_file)
    reconciliation = reconciler.reconcile()
    
    # Only save if fully reconciled or user confirms
    if reconciliation['summary']['status'] == 'reconciled':
        reconciler.save_result()
    
    return jsonify({
        'success': True,
        'reconciliation': reconciliation
    })
```

---

## 5. ROUTE RESTRUCTURING & API VERSIONING

### 5.1 New Blueprint Organization

Current: 6 blueprints
New: 10+ blueprints with versioned API

```
routes/
├── __init__.py
├── auth_v2.py                # Multi-user authentication
├── 
│ # Night Audit (CORE)
├── audit/
│   ├── __init__.py
│   ├── checklist.py          # Task management (from checklist.py)
│   ├── rj_upload.py          # RJ file handling
│   ├── rj_fill.py            # Auto-fill logic (split from rj.py:1428)
│   ├── quasimodo.py          # Card reconciliation
│   └── parsers.py            # PDF/Excel parsing routes
│
│ # Reporting (Analytics)
├── reports/
│   ├── __init__.py
│   ├── audit_reports.py      # Daily/variance reports
│   ├── balance_reports.py    # Balance reconciliation
│   └── analytics.py          # Trend analysis
│
│ # CRM (Guest & AR)
├── crm/
│   ├── __init__.py
│   ├── guests.py             # Guest CRUD + interactions
│   ├── corporate.py          # Corporate accounts
│   ├── ar.py                 # Accounts Receivable aging
│   └── reservations.py       # Booking management
│
│ # Admin
└── admin/
    ├── __init__.py
    └── users.py              # User management

api/
├── __init__.py
├── v1.py                     # API v1.0 (initial endpoints)
└── v2.py                     # API v2.0 (new PDF/Quasimodo endpoints)
```

### 5.2 Split rj.py (1428 lines) into Modules

```python
# routes/audit/rj_upload.py (300 lines)
@rj_upload_bp.route('/api/rj/upload', methods=['POST'])
@rj_upload_bp.route('/api/rj/download', methods=['GET'])
@rj_upload_bp.route('/api/rj/status', methods=['GET'])

# routes/audit/rj_fill.py (400 lines)
@rj_fill_bp.route('/api/rj/fill/dueback', methods=['POST'])
@rj_fill_bp.route('/api/rj/fill/recap', methods=['POST'])
@rj_fill_bp.route('/api/rj/fill/transelect', methods=['POST'])
# ... mapped to existing RJFiller logic

# routes/audit/quasimodo.py (250 lines)
@quasimodo_bp.route('/api/quasimodo/auto-reconcile', methods=['POST'])
@quasimodo_bp.route('/api/quasimodo/result', methods=['GET'])

# routes/audit/parsers.py (200 lines)
@parsers_bp.route('/api/parsers/daily-revenue', methods=['POST'])
@parsers_bp.route('/api/parsers/advance-deposit', methods=['POST'])
@parsers_bp.route('/api/parsers/freedompay', methods=['POST'])
```

---

## 6. TEMPLATE RESTRUCTURING

### 6.1 Component Strategy

Current monolithic rj.html (5885 lines) → Component-based architecture

```
templates/
├── base.html                           # (unchanged)
├── auth/
│   ├── login.html
│   └── profile.html
│
├── audit/
│   ├── checklist.html                  # Task lists
│   ├── rj/
│   │   ├── rj_layout.html              # Main container
│   │   ├── tabs/
│   │   │   ├── nouveau_jour.html
│   │   │   ├── sd.html
│   │   │   ├── depot.html
│   │   │   ├── dueback.html
│   │   │   ├── recap.html
│   │   │   ├── transelect.html
│   │   │   └── geac.html
│   │   ├── components/
│   │   │   ├── file_upload.html
│   │   │   ├── status_card.html
│   │   │   └── reconciliation_summary.html
│   │   └── modals/
│   │       ├── confirm_fill.html
│   │       └── error_details.html
│   │
│   └── quasimodo/
│       ├── reconciliation_dashboard.html
│       └── discrepancy_report.html
│
├── crm/
│   ├── guests/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── interaction_form.html
│   ├── corporate/
│   │   └── account_detail.html
│   └── ar/
│       ├── aging_report.html
│       └── invoice_detail.html
│
└── reports/
    ├── daily_summary.html
    ├── variance_trends.html
    └── balance_reconciliation.html
```

### 6.2 JavaScript Modularization

```
static/js/
├── main.js                     # App initialization
├── auth/
│   └── login.js
├── audit/
│   ├── rj.js                   # Main RJ page logic (split from monolith)
│   ├── rj_tabs.js              # Tab switching
│   ├── rj_upload.js            # File upload handling
│   ├── rj_fill.js              # Form fill logic
│   ├── quasimodo.js            # Reconciliation logic
│   └── parsers.js              # PDF/Excel parser UI
├── crm/
│   ├── guests.js
│   └── ar.js
└── utils/
    ├── api.js                  # Centralized API calls
    ├── validation.js           # Form validation
    └── notifications.js        # Toast/alert system
```

### 6.3 Lazy-Loading Tabs

```html
<!-- templates/audit/rj/rj_layout.html -->

<div class="rj-tabs-container">
  <div class="rj-tabs-nav">
    <button class="rj-tab-btn active" onclick="loadTab('nouveau-jour')">
      Nouveau Jour
    </button>
    <button class="rj-tab-btn" onclick="loadTab('sd')">
      SD
    </button>
    <!-- More tabs... -->
  </div>
  
  <div class="rj-tabs-content">
    <div id="tab-nouveau-jour" class="rj-tab-content" data-loaded="false"></div>
    <div id="tab-sd" class="rj-tab-content" data-loaded="false"></div>
    <!-- etc. -->
  </div>
</div>

<script>
async function loadTab(tabName) {
  const tab = document.getElementById(`tab-${tabName}`);
  
  // Load only once
  if (tab.dataset.loaded === 'true') {
    showTab(tabName);
    return;
  }
  
  // Fetch and insert component
  const response = await fetch(`/templates/rj/tabs/${tabName}.html`);
  const html = await response.text();
  tab.innerHTML = html;
  tab.dataset.loaded = 'true';
  
  // Load tab-specific JS
  const script = document.createElement('script');
  script.src = `/static/js/audit/rj_${tabName}.js`;
  document.head.appendChild(script);
  
  showTab(tabName);
}
</script>
```

---

## 7. CRM MODULE DESIGN

### 7.1 Features

- **Guest Directory**: Full name, email, phone, company, visit history
- **Interactions**: Calls, requests, complaints, feedback (audit trail)
- **Corporate Accounts**: Billing entities, payment terms, credit limits
- **Group Bookings**: Track block reservations with revenue forecast
- **AR Aging**: Days outstanding, payment status, trend analysis
- **Revenue Analytics**: By guest segment, by booking source

### 7.2 Routes

```python
# routes/crm/guests.py

@crm_guests_bp.route('/guests', methods=['GET'])
@role_required('night_auditor', 'gm', 'gsm')
def list_guests():
    """List all guests with search/filter."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'last_visit')
    
    query = Guest.query
    if search:
        query = query.filter(
            (Guest.first_name.ilike(f"%{search}%")) |
            (Guest.last_name.ilike(f"%{search}%")) |
            (Guest.email.ilike(f"%{search}%"))
        )
    
    guests = query.order_by(getattr(Guest, sort).desc()).paginate(page=page, per_page=50)
    return render_template('crm/guests/list.html', guests=guests.items, pagination=guests)


@crm_guests_bp.route('/guests/<int:guest_id>', methods=['GET'])
@role_required('night_auditor', 'gm', 'gsm')
def view_guest(guest_id):
    """View guest profile + interaction history."""
    guest = Guest.query.get_or_404(guest_id)
    interactions = GuestInteraction.query.filter_by(guest_id=guest_id).order_by(
        GuestInteraction.created_at.desc()
    ).all()
    reservations = Reservation.query.filter_by(guest_id=guest_id).all()
    ar_records = ARRecord.query.filter_by(guest_id=guest_id).all()
    
    return render_template(
        'crm/guests/detail.html',
        guest=guest,
        interactions=interactions,
        reservations=reservations,
        ar_records=ar_records
    )


@crm_guests_bp.route('/guests/<int:guest_id>/interaction', methods=['POST'])
@role_required('night_auditor')
def log_interaction(guest_id):
    """Log a guest interaction."""
    guest = Guest.query.get_or_404(guest_id)
    
    interaction = GuestInteraction(
        guest_id=guest_id,
        created_by_id=current_user.id,
        interaction_type=request.form.get('type'),
        notes=request.form.get('notes'),
        resolution=request.form.get('resolution')
    )
    db.session.add(interaction)
    db.session.commit()
    
    return jsonify({'success': True, 'interaction_id': interaction.id})


# routes/crm/ar.py

@crm_ar_bp.route('/ar/aging', methods=['GET'])
@role_required('accounting', 'gm', 'gsm')
def ar_aging_report():
    """Accounts Receivable aging report."""
    
    # Calculate aging buckets
    today = datetime.utcnow().date()
    
    current = ARRecord.query.filter(
        ARRecord.status != 'paid',
        ARRecord.due_date >= today
    ).all()
    
    days_30 = ARRecord.query.filter(
        ARRecord.status != 'paid',
        ARRecord.due_date < today,
        ARRecord.due_date >= today - timedelta(days=30)
    ).all()
    
    days_60 = ARRecord.query.filter(
        ARRecord.status != 'paid',
        ARRecord.due_date < today - timedelta(days=30),
        ARRecord.due_date >= today - timedelta(days=60)
    ).all()
    
    days_90 = ARRecord.query.filter(
        ARRecord.status != 'paid',
        ARRecord.due_date < today - timedelta(days=60)
    ).all()
    
    # Calculate totals
    totals = {
        'current': sum(r.amount_outstanding for r in current),
        'days_30': sum(r.amount_outstanding for r in days_30),
        'days_60': sum(r.amount_outstanding for r in days_60),
        'days_90': sum(r.amount_outstanding for r in days_90),
    }
    totals['total'] = sum(totals.values())
    
    return render_template(
        'crm/ar/aging_report.html',
        current=current,
        days_30=days_30,
        days_60=days_60,
        days_90=days_90,
        totals=totals
    )
```

---

## 8. FILE STRUCTURE

```
audit-pack/
│
├── main.py                          # Flask app factory
├── config/
│   └── settings.py                  # Config (update for new models)
│
├── database/
│   ├── __init__.py
│   └── models.py                    # User, CRM, Audit models
│
├── routes/
│   ├── __init__.py
│   ├── auth_v2.py                   # New multi-user auth
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── checklist.py
│   │   ├── rj_upload.py
│   │   ├── rj_fill.py
│   │   ├── quasimodo.py
│   │   └── parsers.py
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── audit_reports.py
│   │   ├── balance_reports.py
│   │   └── analytics.py
│   ├── crm/
│   │   ├── __init__.py
│   │   ├── guests.py
│   │   ├── corporate.py
│   │   ├── ar.py
│   │   └── reservations.py
│   └── admin/
│       ├── __init__.py
│       └── users.py
│
├── utils/
│   ├── __init__.py
│   ├── rj_reader.py                 # (existing, updated)
│   ├── rj_filler.py                 # (existing, updated)
│   ├── rj_mapper.py                 # (existing)
│   ├── sd_reader.py                 # (existing)
│   ├── sd_writer.py                 # (existing)
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py
│   │   ├── daily_revenue_parser.py
│   │   ├── advance_deposit_parser.py
│   │   ├── freedompay_parser.py
│   │   ├── hp_excel_parser.py
│   │   └── validation.py
│   ├── quasimodo.py                 # Card reconciliation engine
│   ├── auth_decorators.py           # Role-based decorators
│   ├── weather_api.py               # (existing)
│   └── weather_capture.py           # (existing)
│
├── static/
│   ├── css/
│   │   ├── style.css                # (existing, enhanced)
│   │   └── crm.css                  # New CRM styles
│   └── js/
│       ├── main.js
│       ├── auth/
│       │   └── login.js
│       ├── audit/
│       │   ├── rj.js
│       │   ├── rj_tabs.js
│       │   ├── rj_upload.js
│       │   ├── rj_fill.js
│       │   ├── quasimodo.js
│       │   └── parsers.js
│       ├── crm/
│       │   ├── guests.js
│       │   └── ar.js
│       └── utils/
│           ├── api.js
│           ├── validation.js
│           └── notifications.js
│
├── templates/
│   ├── base.html
│   ├── auth/
│   │   ├── login.html               # New multi-user login
│   │   ├── register.html            # Admin-only registration
│   │   └── profile.html
│   ├── audit/
│   │   ├── checklist.html           # (update existing)
│   │   └── rj/
│   │       ├── rj_layout.html
│   │       ├── tabs/
│   │       │   ├── nouveau_jour.html
│   │       │   ├── sd.html
│   │       │   ├── depot.html
│   │       │   ├── dueback.html
│   │       │   ├── recap.html
│   │       │   ├── transelect.html
│   │       │   └── geac.html
│   │       └── components/
│   │           ├── file_upload.html
│   │           └── status_card.html
│   ├── crm/
│   │   ├── guests/
│   │   │   ├── list.html
│   │   │   ├── detail.html
│   │   │   └── interaction_form.html
│   │   ├── corporate/
│   │   │   └── account_detail.html
│   │   └── ar/
│   │       ├── aging_report.html
│   │       └── invoice_detail.html
│   └── reports/
│       ├── daily_summary.html
│       └── variance_trends.html
│
├── database/
│   └── audit.db                     # SQLite (existing)
│
├── requirements.txt                 # (update dependencies)
├── README.md                        # (update docs)
└── MIGRATION_GUIDE.md               # Single-PIN to multi-user migration
```

---

## 9. IMPLEMENTATION PHASES

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Establish new auth system and database structure

1. Add User model, AuditSession model to database/models.py
2. Implement auth_v2.py with password hashing, Flask-Login
3. Create role-based decorators (utils/auth_decorators.py)
4. Update main.py to register new auth blueprint
5. Create new login.html, profile.html templates
6. Migrate existing shift tracking from Shift → AuditSession

**Deliverables**:
- Users table with hashing
- Multi-user login functional
- All existing routes protected with role checks
- Backward compatibility: Night Auditor role sees everything

### Phase 2: CRM Foundation (Weeks 3-4)
**Goal**: Build guest/corporate account database layer

1. Add CRM models (Guest, CorporateAccount, GuestInteraction, Reservation, ARRecord)
2. Create crm/guests.py routes (list, view, add interaction)
3. Create crm/ar.py routes (aging report)
4. Create CRM templates (guests/list.html, guests/detail.html, ar/aging_report.html)
5. Add crm.css for styling
6. Basic JS for guest search, interaction logging

**Deliverables**:
- CRM database tables
- Guest CRUD operations
- AR aging report functional
- Guest interaction logging

### Phase 3: PDF/Excel Parsing (Weeks 5-6)
**Goal**: Implement auto-parsing infrastructure

1. Create parsers/ module with base_parser.py
2. Implement DailyRevenueParser (with pdfplumber dependency)
3. Implement AdvanceDepositParser
4. Implement FreedomPayParser
5. Create ParserFactory in parsers/__init__.py
6. Add ParsedPDFData model to database/models.py
7. Create routes/audit/parsers.py with upload endpoints
8. Create UI for PDF upload (templates/audit/rj/components/pdf_upload.html)

**Dependencies**: Add to requirements.txt:
- pdfplumber
- Flask-Login

**Deliverables**:
- PDF parsing functional with test samples
- Parser results cached in database
- Auto-fill integration points prepared

### Phase 4: Quasimodo Engine (Weeks 7-8)
**Goal**: Implement card reconciliation automation

1. Implement QuasimodoReconciler in utils/quasimodo.py
2. Add QuasimodoParsing model to database/models.py
3. Enhance RJReader.read_transelect() and read_geac_ux() for completeness
4. Create routes/audit/quasimodo.py with auto-reconcile endpoint
5. Create Quasimodo dashboard template (templates/audit/quasimodo/reconciliation_dashboard.html)
6. Create reconciliation JS (static/js/audit/quasimodo.js)

**Deliverables**:
- Auto-reconciliation fully working
- Discrepancy reporting
- Results stored in database
- Dashboard showing card-by-card breakdown

### Phase 5: Template Refactoring (Weeks 9-10)
**Goal**: Split monolithic rj.html into components

1. Create rj/rj_layout.html as main container
2. Create rj/tabs/ directory with individual tab templates
3. Implement lazy-loading logic in static/js/audit/rj_tabs.js
4. Refactor rj/components/ for reusable parts
5. Update CSS in style.css for component layout
6. Test all tab switching with lazy loading

**Deliverables**:
- rj.html split into ~10 manageable files
- Each tab loads on-demand
- JS modularized in static/js/audit/
- Same visual appearance, better maintainability

### Phase 6: Route Restructuring (Week 11)
**Goal**: Reorganize routes into audit/, reports/, crm/, admin/

1. Create audit/checklist.py, audit/rj_upload.py, audit/rj_fill.py (refactored from routes/rj.py)
2. Create reports/audit_reports.py, reports/balance_reports.py (from routes/reports.py)
3. Move existing reports.py logic
4. Verify all API endpoints still functional
5. Update imports in main.py

**Deliverables**:
- rj.py (1428 lines) split into 4 modules (~300 lines each)
- All existing functionality preserved
- Clearer code organization

### Phase 7: Migration & Testing (Week 12)
**Goal**: Data migration from single-PIN to multi-user

1. Create MIGRATION_GUIDE.md with instructions
2. Write migration script to create admin user
3. Test on sample data
4. Verify backward compatibility
5. Update README.md with new setup instructions

**Deliverables**:
- Migration script (migrate_to_multiuser.py)
- All tests passing
- Documentation updated

---

## 10. MIGRATION STRATEGY

### 10.1 Database Migration Script

```python
# migrate_to_multiuser.py

from main import create_app, db
from database.models import User
from datetime import datetime

def migrate():
    """Migrate from single-PIN to multi-user."""
    app = create_app()
    
    with app.app_context():
        # 1. Create admin user
        admin = User(
            username='admin',
            email='admin@sheraton-laval.local',
            full_name_fr='Administrateur',
            role='admin',
            is_active=True
        )
        admin.set_password('ChangeMe123!')  # Must be changed on first login
        db.session.add(admin)
        
        # 2. Create default Night Auditor user
        auditor = User(
            username='night_auditor',
            email='auditor@sheraton-laval.local',
            full_name_fr='Auditeur de Nuit',
            role='night_auditor',
            is_active=True
        )
        auditor.set_password('DefaultAuditor123!')  # Must be changed
        db.session.add(auditor)
        
        # 3. Migrate existing Shift records to AuditSession
        from database.models import Shift, AuditSession
        
        shifts = Shift.query.all()
        for shift in shifts:
            session = AuditSession(
                date=shift.date,
                auditor_id=auditor.id,
                started_at=shift.started_at,
                completed_at=shift.completed_at
            )
            db.session.add(session)
        
        db.session.commit()
        
        print("Migration complete!")
        print("Default credentials:")
        print("  Admin: admin / ChangeMe123!")
        print("  Auditor: night_auditor / DefaultAuditor123!")
        print("\nIMPORTANT: Change these passwords on first login!")

if __name__ == '__main__':
    migrate()
```

### 10.2 Backward Compatibility

- Keep existing `Shift` table (don't delete, just unused)
- Single-PIN mode can be re-enabled via config if needed
- Old session['authenticated'] + session['user_role'] still work (mapped to new User model)

---

## 11. DEPENDENCIES UPDATE

### Current (from requirements.txt):
```
Flask
Flask-SQLAlchemy
xlrd==2.0.1
xlutils
Werkzeug
python-dotenv
```

### New (to add):
```
Flask-Login           # Session management
pdfplumber            # PDF text extraction
pillow                # Image processing (for PDF screenshots)
PyPDF2                # PDF manipulation (if needed)
openpyxl              # Modern Excel reader (for .xlsx)
numpy                 # For data analysis (optional)
```

---

## 12. CRITICAL FILES FOR IMPLEMENTATION

Based on the architecture plan, here are the files most critical to create/modify:

### Create (New Files):
1. **database/models.py** — Add User, CRM, AuditSession, parsing models (expanded from ~236 lines to ~800 lines)
2. **routes/auth_v2.py** — Multi-user auth (250 lines)
3. **utils/auth_decorators.py** — Role-based decorators (50 lines)
4. **utils/quasimodo.py** — Card reconciliation engine (300 lines)
5. **utils/parsers/base_parser.py** — Abstract parser (100 lines)
6. **utils/parsers/daily_revenue_parser.py** — PDF parser (250 lines)
7. **utils/parsers/__init__.py** — ParserFactory (150 lines)
8. **routes/audit/rj_upload.py** — Split from rj.py (300 lines)
9. **routes/audit/rj_fill.py** — Split from rj.py (400 lines)
10. **routes/audit/quasimodo.py** — Quasimodo endpoints (200 lines)
11. **routes/crm/guests.py** — Guest management (300 lines)
12. **routes/crm/ar.py** — AR aging (250 lines)
13. **templates/auth/login.html** — Multi-user login (150 lines)
14. **templates/crm/guests/list.html** — Guest directory (200 lines)
15. **templates/audit/rj/rj_layout.html** — Component container (100 lines)
16. **static/js/audit/quasimodo.js** — Reconciliation UI (400 lines)
17. **MIGRATION_GUIDE.md** — Setup documentation

### Modify (Existing Files):
1. **database/models.py** — Add new models (keep existing Task, Shift, etc.)
2. **routes/rj.py** — Extract logic into audit/ submodules
3. **routes/auth.py** — Keep for backward compatibility, redirect to auth_v2
4. **main.py** — Register new blueprints
5. **config/settings.py** — Update DB URI, add new config options
6. **templates/base.html** — Update sidebar for new routes
7. **requirements.txt** — Add dependencies
8. **static/css/style.css** — Add CRM, component styles

---

## 13. SUCCESS CRITERIA

- [ ] Multi-user login functional with password hashing
- [ ] All 5 roles (night_auditor, gm, gsm, front_desk_supervisor, accounting) working
- [ ] PDF parsing works for Daily Revenue (sample provided)
- [ ] FreedomPay Excel parsing extracts card settlement amounts
- [ ] Quasimodo reconciliation auto-calculates and stores results
- [ ] rj.html split into components with lazy loading
- [ ] CRM module tracks guests, interactions, AR aging
- [ ] All existing RJ workflows preserved (fill input → fire macros → jour calculated)
- [ ] Backward compatibility for existing features
- [ ] Database migrates from single-PIN without data loss
- [ ] User documentation complete

---

## 14. ESTIMATED EFFORT

**Total: ~12 weeks (3 months)**

- Phase 1 (Auth Foundation): 2 weeks
- Phase 2 (CRM Foundation): 2 weeks
- Phase 3 (PDF Parsing): 2 weeks
- Phase 4 (Quasimodo): 2 weeks
- Phase 5 (Template Refactoring): 2 weeks
- Phase 6 (Route Restructuring): 1 week
- Phase 7 (Migration & Testing): 1 week

**With concurrent work**: Can compress to 8-10 weeks

---

## 15. ROLLOUT PLAN

1. **Week 1-2**: Deploy new auth system to staging
2. **Week 3-4**: Test CRM with sample guest data
3. **Week 5-6**: Validate PDF parsing with real hotel documents
4. **Week 7-8**: Validate Quasimodo with 10 days of real RJ data
5. **Week 9-10**: User acceptance testing on rj.html refactor
6. **Week 11**: Full system test on production environment
7. **Week 12**: Staged rollout to night auditor, monitoring for issues

**Fallback**: Keep old system running in parallel for 2 weeks after launch
