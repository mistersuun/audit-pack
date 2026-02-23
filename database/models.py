from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date as date_type
from sqlalchemy import func

db = SQLAlchemy()

TOTAL_ROOMS = 252  # Sheraton Laval property capacity


# ==============================================================================
# USER AUTHENTICATION MODELS
# ==============================================================================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='night_auditor')
    # Roles: 'night_auditor', 'gm', 'gsm', 'front_desk_supervisor', 'accounting', 'admin'
    full_name_fr = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        return self.role in roles

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'full_name_fr': self.full_name_fr,
            'is_active': self.is_active,
        }


class AuditSession(db.Model):
    __tablename__ = 'audit_sessions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    auditor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    rj_file_path = db.Column(db.String(500))


# ==============================================================================
# RAPPORTS & BALANCES MODELS
# ==============================================================================

class DailyReport(db.Model):
    """Stocke les données quotidiennes pour historique et rapports."""
    __tablename__ = 'daily_reports'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)

    # Revenus
    revenue_comptant = db.Column(db.Float, default=0)
    revenue_cartes = db.Column(db.Float, default=0)
    revenue_cheques = db.Column(db.Float, default=0)
    revenue_total = db.Column(db.Float, default=0)

    # Dépôts
    deposit_cdn = db.Column(db.Float, default=0)
    deposit_us = db.Column(db.Float, default=0)

    # Variances et DueBack
    variance = db.Column(db.Float, default=0)
    dueback_total = db.Column(db.Float, default=0)

    # Balances
    ar_balance = db.Column(db.Float, default=0)
    guest_ledger = db.Column(db.Float, default=0)
    city_ledger = db.Column(db.Float, default=0)

    # Métadonnées
    auditor_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'revenue': {
                'comptant': self.revenue_comptant,
                'cartes': self.revenue_cartes,
                'cheques': self.revenue_cheques,
                'total': self.revenue_total,
            },
            'deposits': {
                'cdn': self.deposit_cdn,
                'us': self.deposit_us,
                'total': self.deposit_cdn + self.deposit_us,
            },
            'variance': self.variance,
            'dueback_total': self.dueback_total,
            'balances': {
                'ar': self.ar_balance,
                'guest_ledger': self.guest_ledger,
                'city_ledger': self.city_ledger,
            },
            'auditor': self.auditor_name,
            'notes': self.notes,
        }


class VarianceRecord(db.Model):
    """Historique des variances par réceptionniste."""
    __tablename__ = 'variance_records'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    receptionist = db.Column(db.String(100), nullable=False, index=True)
    expected = db.Column(db.Float, default=0)
    actual = db.Column(db.Float, default=0)
    variance = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Seuil d'alerte (50$ par défaut)
    ALERT_THRESHOLD = 50.0

    @property
    def is_alert(self):
        """Retourne True si variance > seuil."""
        return abs(self.variance) > self.ALERT_THRESHOLD

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'receptionist': self.receptionist,
            'expected': self.expected,
            'actual': self.actual,
            'variance': self.variance,
            'is_alert': self.is_alert,
            'notes': self.notes,
        }


class CashReconciliation(db.Model):
    """Enregistrements de réconciliation de caisse."""
    __tablename__ = 'cash_reconciliations'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    system_total = db.Column(db.Float, default=0)
    counted_total = db.Column(db.Float, default=0)
    variance = db.Column(db.Float, default=0)
    auditor = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'system_total': self.system_total,
            'counted_total': self.counted_total,
            'variance': self.variance,
            'is_balanced': abs(self.variance) < 0.01,
            'auditor': self.auditor,
            'notes': self.notes,
        }


class MonthEndChecklist(db.Model):
    """Checklist de fin de mois."""
    __tablename__ = 'month_end_checklists'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    task_name = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    completed_by = db.Column(db.String(100))
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'month': self.month,
            'task': self.task_name,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by': self.completed_by,
            'notes': self.notes,
        }


# ==============================================================================
# HISTORICAL ANALYTICS MODEL — Rich Jour Sheet Metrics (5-year BI)
# ==============================================================================

class DailyJourMetrics(db.Model):
    """
    Stores daily hotel metrics extracted from RJ Jour sheets.
    One row per calendar day — supports multi-year historical analytics.
    ~45 key metrics covering revenue, occupancy, payments, taxes, KPIs.
    """
    __tablename__ = 'daily_jour_metrics'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False)
    day_of_month = db.Column(db.Integer, nullable=False)

    # ── Revenue ──────────────────────────────────────────────────────────
    room_revenue = db.Column(db.Float, default=0)          # Chambres (col 36)
    fb_revenue = db.Column(db.Float, default=0)             # Sum of all F&B outlets
    cafe_link_total = db.Column(db.Float, default=0)        # Café Link (cols 4-8 sum)
    piazza_total = db.Column(db.Float, default=0)           # Piazza/Cupola (cols 9-13 sum)
    spesa_total = db.Column(db.Float, default=0)            # Marché Spesa (cols 16-17 sum)
    room_svc_total = db.Column(db.Float, default=0)         # Service chambres (cols 19-23 sum)
    banquet_total = db.Column(db.Float, default=0)          # Banquet (cols 14-15 sum)
    tips_total = db.Column(db.Float, default=0)             # Pourboires (col 29)
    tabagie_total = db.Column(db.Float, default=0)          # Tabagie (col 18)
    other_revenue = db.Column(db.Float, default=0)          # Misc (equipement, divers, internet)
    total_revenue = db.Column(db.Float, default=0)          # Grand total

    # ── F&B Breakdown by category ────────────────────────────────────────
    total_nourriture = db.Column(db.Float, default=0)       # All food
    total_boisson = db.Column(db.Float, default=0)          # All beverage/alcohol
    total_bieres = db.Column(db.Float, default=0)           # All beer
    total_vins = db.Column(db.Float, default=0)             # All wine
    total_mineraux = db.Column(db.Float, default=0)         # All non-alcoholic

    # ── Occupancy & Rooms ────────────────────────────────────────────────
    rooms_simple = db.Column(db.Integer, default=0)         # Simple rooms (col 88)
    rooms_double = db.Column(db.Integer, default=0)         # Double rooms (col 89)
    rooms_suite = db.Column(db.Integer, default=0)          # Suite rooms (col 90)
    rooms_comp = db.Column(db.Integer, default=0)           # Comp rooms (col 91)
    total_rooms_sold = db.Column(db.Integer, default=0)     # Total sold
    rooms_available = db.Column(db.Integer, default=TOTAL_ROOMS)
    occupancy_rate = db.Column(db.Float, default=0)         # % (0-100)
    nb_clients = db.Column(db.Integer, default=0)           # Guest count (col 92)
    rooms_hors_usage = db.Column(db.Integer, default=0)     # Out of service (col 93)
    rooms_ch_refaire = db.Column(db.Integer, default=0)     # Rooms to redo (col 94)

    # ── Payments ─────────────────────────────────────────────────────────
    visa_total = db.Column(db.Float, default=0)             # Visa (col 63)
    mastercard_total = db.Column(db.Float, default=0)       # MC (col 62)
    amex_elavon_total = db.Column(db.Float, default=0)      # Amex ELAVON (col 60)
    amex_global_total = db.Column(db.Float, default=0)      # Amex Global (col 65)
    debit_total = db.Column(db.Float, default=0)            # Debit (col 64)
    discover_total = db.Column(db.Float, default=0)         # Discover (col 61)
    total_cards = db.Column(db.Float, default=0)            # Sum of all cards

    # ── Taxes ────────────────────────────────────────────────────────────
    tps_total = db.Column(db.Float, default=0)              # Federal TPS (col 50)
    tvq_total = db.Column(db.Float, default=0)              # Provincial TVQ (col 49)
    tvh_total = db.Column(db.Float, default=0)              # Accommodation TVH (col 51)

    # ── Cash & Reconciliation ────────────────────────────────────────────
    opening_balance = db.Column(db.Float, default=0)        # Bal ouverture (col 1)
    cash_difference = db.Column(db.Float, default=0)        # Diff caisse (col 2)
    closing_balance = db.Column(db.Float, default=0)        # New balance (col 3)

    # ── Computed KPIs (cached for fast queries) ──────────────────────────
    adr = db.Column(db.Float, default=0)                    # Room Revenue / Rooms Sold
    revpar = db.Column(db.Float, default=0)                 # Room Revenue / Available
    trevpar = db.Column(db.Float, default=0)                # Total Revenue / Available
    food_pct = db.Column(db.Float, default=0)               # Food % of F&B
    beverage_pct = db.Column(db.Float, default=0)           # Beverage % of F&B

    # ── Metadata ─────────────────────────────────────────────────────────
    source = db.Column(db.String(20), default='rj_upload')  # 'rj_upload' or 'bulk_import'
    rj_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'year': self.year,
            'month': self.month,
            'day': self.day_of_month,
            'revenue': {
                'room': self.room_revenue,
                'fb': self.fb_revenue,
                'cafe_link': self.cafe_link_total,
                'piazza': self.piazza_total,
                'spesa': self.spesa_total,
                'room_svc': self.room_svc_total,
                'banquet': self.banquet_total,
                'tips': self.tips_total,
                'tabagie': self.tabagie_total,
                'other': self.other_revenue,
                'total': self.total_revenue,
            },
            'fb_categories': {
                'nourriture': self.total_nourriture,
                'boisson': self.total_boisson,
                'bieres': self.total_bieres,
                'vins': self.total_vins,
                'mineraux': self.total_mineraux,
            },
            'occupancy': {
                'simple': self.rooms_simple,
                'double': self.rooms_double,
                'suite': self.rooms_suite,
                'comp': self.rooms_comp,
                'sold': self.total_rooms_sold,
                'available': self.rooms_available,
                'rate': self.occupancy_rate,
                'clients': self.nb_clients,
                'hors_usage': self.rooms_hors_usage,
            },
            'payments': {
                'visa': self.visa_total,
                'mastercard': self.mastercard_total,
                'amex_elavon': self.amex_elavon_total,
                'amex_global': self.amex_global_total,
                'debit': self.debit_total,
                'discover': self.discover_total,
                'total': self.total_cards,
            },
            'taxes': {
                'tps': self.tps_total,
                'tvq': self.tvq_total,
                'tvh': self.tvh_total,
            },
            'kpis': {
                'adr': self.adr,
                'revpar': self.revpar,
                'trevpar': self.trevpar,
                'food_pct': self.food_pct,
                'beverage_pct': self.beverage_pct,
            },
        }


# ==============================================================================
# MONTHLY EXPENSES — For GOPPAR / Break-even calculations
# ==============================================================================

class MonthlyExpense(db.Model):
    """Monthly operating expense data entered by management for profitability analysis."""
    __tablename__ = 'monthly_expenses'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12

    # Labor costs by department
    labor_rooms = db.Column(db.Float, default=0)        # Front office + housekeeping
    labor_fb = db.Column(db.Float, default=0)            # F&B staff
    labor_admin = db.Column(db.Float, default=0)         # Admin/management
    labor_maintenance = db.Column(db.Float, default=0)   # Engineering/maintenance
    labor_other = db.Column(db.Float, default=0)         # Other departments
    labor_total = db.Column(db.Float, default=0)         # Auto-calculated

    # Operating expenses
    utilities = db.Column(db.Float, default=0)           # Electricity, gas, water
    supplies = db.Column(db.Float, default=0)            # Amenities, cleaning, office
    maintenance_costs = db.Column(db.Float, default=0)   # Repairs, preventive maintenance
    marketing = db.Column(db.Float, default=0)           # Marketing & sales
    insurance = db.Column(db.Float, default=0)           # Property insurance
    franchise_fees = db.Column(db.Float, default=0)      # Marriott/Sheraton franchise fees
    technology = db.Column(db.Float, default=0)          # PMS, IT, telecom
    other_expenses = db.Column(db.Float, default=0)      # Miscellaneous

    total_expenses = db.Column(db.Float, default=0)      # Auto-calculated
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('year', 'month', name='uq_monthly_expense_period'),
    )

    def calculate_totals(self):
        self.labor_total = (self.labor_rooms or 0) + (self.labor_fb or 0) + \
                           (self.labor_admin or 0) + (self.labor_maintenance or 0) + \
                           (self.labor_other or 0)
        self.total_expenses = self.labor_total + (self.utilities or 0) + \
                              (self.supplies or 0) + (self.maintenance_costs or 0) + \
                              (self.marketing or 0) + (self.insurance or 0) + \
                              (self.franchise_fees or 0) + (self.technology or 0) + \
                              (self.other_expenses or 0)

    def to_dict(self):
        return {
            'id': self.id, 'year': self.year, 'month': self.month,
            'labor_rooms': self.labor_rooms, 'labor_fb': self.labor_fb,
            'labor_admin': self.labor_admin, 'labor_maintenance': self.labor_maintenance,
            'labor_other': self.labor_other, 'labor_total': self.labor_total,
            'utilities': self.utilities, 'supplies': self.supplies,
            'maintenance_costs': self.maintenance_costs, 'marketing': self.marketing,
            'insurance': self.insurance, 'franchise_fees': self.franchise_fees,
            'technology': self.technology, 'other_expenses': self.other_expenses,
            'total_expenses': self.total_expenses, 'notes': self.notes,
        }


# ==============================================================================
# LABOR ANALYTICS MODEL — Department Labor Costs and Staffing
# ==============================================================================

class DepartmentLabor(db.Model):
    """
    Monthly labor data by department.
    Stores staffing costs, hours, tips, and budget comparisons for each department.
    """
    __tablename__ = 'department_labor'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    # Departments: RECEPTION, KITCHEN, BANQUET, RESTAURANT, ADMINISTRATION, SALES, ROOMS, MAINTENANCE, BAR, OTHER

    # Hours
    regular_hours = db.Column(db.Float, default=0)
    overtime_hours = db.Column(db.Float, default=0)
    total_hours = db.Column(db.Float, default=0)

    # Costs
    regular_wages = db.Column(db.Float, default=0)
    overtime_wages = db.Column(db.Float, default=0)
    benefits = db.Column(db.Float, default=0)
    total_labor_cost = db.Column(db.Float, default=0)

    # Staffing
    headcount = db.Column(db.Integer, default=0)
    avg_hourly_rate = db.Column(db.Float, default=0)

    # Tips (from POURBOIRE data)
    tips_collected = db.Column(db.Float, default=0)
    tips_distributed = db.Column(db.Float, default=0)

    # Budget
    budget_hours = db.Column(db.Float, default=0)
    budget_cost = db.Column(db.Float, default=0)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    __table_args__ = (db.UniqueConstraint('year', 'month', 'department'),)

    def calculate_totals(self):
        """Recalculate derived fields."""
        self.total_hours = (self.regular_hours or 0) + (self.overtime_hours or 0)
        self.total_labor_cost = (self.regular_wages or 0) + (self.overtime_wages or 0) + (self.benefits or 0)
        if self.total_hours > 0:
            self.avg_hourly_rate = self.total_labor_cost / self.total_hours
        else:
            self.avg_hourly_rate = 0

    def get_budget_variance(self):
        """Returns variance between actual and budget (positive = over budget)."""
        return self.total_labor_cost - self.budget_cost

    def get_budget_variance_pct(self):
        """Returns variance as percentage of budget."""
        if self.budget_cost == 0:
            return 0
        return ((self.total_labor_cost - self.budget_cost) / self.budget_cost * 100)

    def get_hours_variance(self):
        """Returns hours variance (positive = over budget)."""
        return self.total_hours - self.budget_hours

    def get_total_compensation(self):
        """Returns total compensation including tips distributed."""
        return self.total_labor_cost + (self.tips_distributed or 0)

    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'month': self.month,
            'department': self.department,
            'regular_hours': self.regular_hours,
            'overtime_hours': self.overtime_hours,
            'total_hours': self.total_hours,
            'regular_wages': self.regular_wages,
            'overtime_wages': self.overtime_wages,
            'benefits': self.benefits,
            'total_labor_cost': self.total_labor_cost,
            'headcount': self.headcount,
            'avg_hourly_rate': round(self.avg_hourly_rate, 2),
            'tips_collected': self.tips_collected,
            'tips_distributed': self.tips_distributed,
            'budget_hours': self.budget_hours,
            'budget_cost': self.budget_cost,
            'budget_variance': round(self.get_budget_variance(), 2),
            'budget_variance_pct': round(self.get_budget_variance_pct(), 1),
            'hours_variance': round(self.get_hours_variance(), 1),
            'total_compensation': round(self.get_total_compensation(), 2),
            'notes': self.notes,
        }


# ==============================================================================
# MONTHLY BUDGET — Direction Reports (Rapp_p1/p2/p3, État rev)
# ==============================================================================

class MonthlyBudget(db.Model):
    """Monthly budget targets for Direction reports."""
    __tablename__ = 'monthly_budget'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12

    # Revenue targets
    rooms_target = db.Column(db.Integer, default=0)       # Target rooms sold
    adr_target = db.Column(db.Float, default=0)            # Target ADR
    room_revenue = db.Column(db.Float, default=0)          # Target room revenue
    location_salle = db.Column(db.Float, default=0)        # Location de salle
    giotto = db.Column(db.Float, default=0)
    piazza = db.Column(db.Float, default=0)
    cupola = db.Column(db.Float, default=0)
    banquet = db.Column(db.Float, default=0)
    spesa = db.Column(db.Float, default=0)
    total_revenue = db.Column(db.Float, default=0)

    # Labor budget by department
    labor_reception = db.Column(db.Float, default=0)
    labor_femme_chambre = db.Column(db.Float, default=0)
    labor_equipier = db.Column(db.Float, default=0)
    labor_gouvernante = db.Column(db.Float, default=0)
    labor_buanderie = db.Column(db.Float, default=0)
    labor_cuisine = db.Column(db.Float, default=0)
    labor_piazza = db.Column(db.Float, default=0)
    labor_cupola = db.Column(db.Float, default=0)
    labor_banquet = db.Column(db.Float, default=0)
    labor_banquet_ii = db.Column(db.Float, default=0)
    labor_adm = db.Column(db.Float, default=0)
    labor_marketing = db.Column(db.Float, default=0)
    labor_entretien = db.Column(db.Float, default=0)

    # Fixed costs
    marketing = db.Column(db.Float, default=0)
    admin = db.Column(db.Float, default=0)
    entretien = db.Column(db.Float, default=0)
    energie = db.Column(db.Float, default=0)
    taxes_assurances = db.Column(db.Float, default=0)
    amortissement = db.Column(db.Float, default=0)
    interet = db.Column(db.Float, default=0)
    loyer = db.Column(db.Float, default=0)

    # Cost ratios
    cost_variable_chambres = db.Column(db.Float, default=0.112)
    cost_variable_banquet = db.Column(db.Float, default=0.061)
    cost_variable_resto = db.Column(db.Float, default=0.354)
    benefits_hebergement = db.Column(db.Float, default=0.43)
    benefits_restauration = db.Column(db.Float, default=0.445)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('year', 'month', name='uq_monthly_budget_period'),
    )

    def to_dict(self):
        import calendar
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        ratio_day = 1 / days_in_month
        return {
            'year': self.year, 'month': self.month,
            'rooms_day': round(self.rooms_target * ratio_day),
            'rooms_mtd': self.rooms_target,
            'adr': self.adr_target,
            'room_revenue_day': self.room_revenue * ratio_day,
            'room_revenue_mtd': self.room_revenue,
            'location_day': self.location_salle * ratio_day,
            'location_mtd': self.location_salle,
            'piazza_day': self.piazza * ratio_day,
            'piazza_mtd': self.piazza,
            'banquet_day': self.banquet * ratio_day,
            'banquet_mtd': self.banquet,
            'giotto_day': self.giotto * ratio_day,
            'giotto_mtd': self.giotto,
            'cupola_day': self.cupola * ratio_day,
            'cupola_mtd': self.cupola,
            'spesa_day': self.spesa * ratio_day,
            'spesa_mtd': self.spesa,
            'total_revenue_day': self.total_revenue * ratio_day,
            'total_revenue_mtd': self.total_revenue,
            'cost_variable_chambres': self.cost_variable_chambres,
            'cost_variable_banquet': self.cost_variable_banquet,
            'cost_variable_resto': self.cost_variable_resto,
            'benefits_hebergement': self.benefits_hebergement,
            'benefits_restauration': self.benefits_restauration,
        }


# ==============================================================================
# ORIGINAL MODELS
# ==============================================================================

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer, nullable=False)
    title_fr = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # pre_audit, part1, part2, end_shift
    role = db.Column(db.String(20), nullable=False, default='front')  # front, back
    is_active = db.Column(db.Boolean, default=True)

    # Phase 2: Detailed instructions
    description_fr = db.Column(db.Text, nullable=True)  # Why this task matters
    steps_json = db.Column(db.Text, nullable=True)  # JSON array of step-by-step instructions
    screenshots_json = db.Column(db.Text, nullable=True)  # JSON array of screenshot filenames
    tips_fr = db.Column(db.Text, nullable=True)  # Helpful tips or warnings
    system_used = db.Column(db.String(100), nullable=True)  # Lightspeed, GXP, Espresso, etc.
    estimated_minutes = db.Column(db.Integer, nullable=True)  # Estimated time to complete

    completions = db.relationship('TaskCompletion', backref='task', lazy=True)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'order': self.order,
            'title_fr': self.title_fr,
            'category': self.category,
            'role': self.role,
            'is_active': self.is_active,
            'description_fr': self.description_fr,
            'steps': json.loads(self.steps_json) if self.steps_json else [],
            'screenshots': json.loads(self.screenshots_json) if self.screenshots_json else [],
            'tips_fr': self.tips_fr,
            'system_used': self.system_used,
            'estimated_minutes': self.estimated_minutes,
            'has_details': bool(self.steps_json)
        }


class Shift(db.Model):
    __tablename__ = 'shifts'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_name = db.Column(db.String(100), nullable=True)

    completions = db.relationship('TaskCompletion', backref='shift', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'user_name': self.user_name
        }


class TaskCompletion(db.Model):
    __tablename__ = 'task_completions'

    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'shift_id': self.shift_id,
            'task_id': self.task_id,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by': self.completed_by,
            'notes': self.notes
        }


# ==============================================================================
# DAILY RECONCILIATION MODELS (from RJ sheets: Recap, Transelect, GEAC, DueBack)
# ==============================================================================

class DailyReconciliation(db.Model):
    """Full daily reconciliation snapshot from RJ file (Recap + GEAC + Transelect)."""
    __tablename__ = 'daily_reconciliations'

    id = db.Column(db.Integer, primary_key=True)
    audit_date = db.Column(db.Date, unique=True, nullable=False, index=True)
    auditor_name = db.Column(db.String(100))

    # Recap cash
    cash_lightspeed = db.Column(db.Float, default=0)
    cash_positouch = db.Column(db.Float, default=0)
    cash_correction = db.Column(db.Float, default=0)
    cheque_ar = db.Column(db.Float, default=0)
    cheque_daily_rev = db.Column(db.Float, default=0)
    remb_gratuite = db.Column(db.Float, default=0)
    remb_client = db.Column(db.Float, default=0)
    remb_loterie = db.Column(db.Float, default=0)
    exchange_us = db.Column(db.Float, default=0)
    dueback_reception = db.Column(db.Float, default=0)
    dueback_nb = db.Column(db.Float, default=0)
    surplus_deficit = db.Column(db.Float, default=0)
    total_deposit_net = db.Column(db.Float, default=0)
    deposit_us = db.Column(db.Float, default=0)
    deposit_cdn = db.Column(db.Float, default=0)

    # Card totals (from transelect)
    card_visa_terminal = db.Column(db.Float, default=0)
    card_mc_terminal = db.Column(db.Float, default=0)
    card_amex_terminal = db.Column(db.Float, default=0)
    card_debit_terminal = db.Column(db.Float, default=0)
    card_discover_terminal = db.Column(db.Float, default=0)
    card_visa_bank = db.Column(db.Float, default=0)
    card_mc_bank = db.Column(db.Float, default=0)
    card_amex_bank = db.Column(db.Float, default=0)
    card_debit_bank = db.Column(db.Float, default=0)
    card_discover_bank = db.Column(db.Float, default=0)

    # AR balances (from geac_ux)
    ar_previous = db.Column(db.Float, default=0)
    ar_charges = db.Column(db.Float, default=0)
    ar_payments = db.Column(db.Float, default=0)
    ar_new_balance = db.Column(db.Float, default=0)

    # Computed checks
    card_total_variance = db.Column(db.Float, default=0)
    ar_variance = db.Column(db.Float, default=0)
    is_balanced = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def total_card_terminal(self):
        return (self.card_visa_terminal or 0) + (self.card_mc_terminal or 0) + \
               (self.card_amex_terminal or 0) + (self.card_debit_terminal or 0) + \
               (self.card_discover_terminal or 0)

    @property
    def total_card_bank(self):
        return (self.card_visa_bank or 0) + (self.card_mc_bank or 0) + \
               (self.card_amex_bank or 0) + (self.card_debit_bank or 0) + \
               (self.card_discover_bank or 0)

    def calculate_variances(self):
        self.card_total_variance = round(self.total_card_terminal - self.total_card_bank, 2)
        ar_expected = (self.ar_previous or 0) + (self.ar_charges or 0) - (self.ar_payments or 0)
        self.ar_variance = round(ar_expected - (self.ar_new_balance or 0), 2)
        self.is_balanced = abs(self.card_total_variance) < 0.02 and \
                           abs(self.ar_variance) < 0.02 and \
                           abs(self.surplus_deficit or 0) < 0.02

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# JOURNAL ENTRIES (from RJ EJ sheet — General Ledger daily entries)
# ==============================================================================

class JournalEntry(db.Model):
    """Daily GL journal entries from EJ sheet in RJ files."""
    __tablename__ = 'journal_entries'
    __table_args__ = (
        db.UniqueConstraint('audit_date', 'gl_code', name='uq_journal_date_gl'),
    )

    id = db.Column(db.Integer, primary_key=True)
    audit_date = db.Column(db.Date, nullable=False, index=True)
    gl_code = db.Column(db.String(10), nullable=False, index=True)
    cost_center_1 = db.Column(db.Float)
    cost_center_2 = db.Column(db.String(10))
    description_1 = db.Column(db.String(200))
    description_2 = db.Column(db.String(200))
    source = db.Column(db.String(20))
    amount = db.Column(db.Float, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# DEPOSIT VARIANCES (from SD files — per employee per day)
# ==============================================================================

class DepositVariance(db.Model):
    """Daily deposit variance by employee from SD files."""
    __tablename__ = 'deposit_variances'
    __table_args__ = (
        db.UniqueConstraint('audit_date', 'employee_name', name='uq_deposit_date_emp'),
    )

    id = db.Column(db.Integer, primary_key=True)
    audit_date = db.Column(db.Date, nullable=False, index=True)
    department = db.Column(db.String(50))
    employee_name = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(5), default='CDN')
    amount_declared = db.Column(db.Float, default=0)
    amount_verified = db.Column(db.Float, default=0)
    reimbursement = db.Column(db.Float, default=0)
    variance = db.Column(db.Float, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_variance(self):
        self.variance = round((self.amount_declared or 0) - (self.amount_verified or 0), 2)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# TIP DISTRIBUTION (from POURBOIRE files — per employee per pay period)
# ==============================================================================

class TipDistribution(db.Model):
    """Tip distribution per employee per pay period from POURBOIRE files."""
    __tablename__ = 'tip_distributions'
    __table_args__ = (
        db.UniqueConstraint('period_start', 'employee_id', name='uq_tip_period_emp'),
    )

    id = db.Column(db.Integer, primary_key=True)
    company_code = db.Column(db.Integer)
    employee_id = db.Column(db.String(10), nullable=False, index=True)
    employee_name = db.Column(db.String(100), nullable=False)
    period_start = db.Column(db.Date, nullable=False, index=True)
    total_sales = db.Column(db.Float, default=0)
    tip_amount = db.Column(db.Float, default=0)

    # Work periods (bi-weekly breakdown)
    work_period_1 = db.Column(db.Float, default=0)
    work_period_2 = db.Column(db.Float, default=0)
    work_period_3 = db.Column(db.Float, default=0)
    work_period_4 = db.Column(db.Float, default=0)
    work_period_5 = db.Column(db.Float, default=0)
    work_period_6 = db.Column(db.Float, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# HP DEPARTMENTAL SALES (from HP files — monthly F&B by department & category)
# ==============================================================================

class HPDepartmentSales(db.Model):
    """Monthly F&B sales breakdown by department from HP files."""
    __tablename__ = 'hp_department_sales'
    __table_args__ = (
        db.UniqueConstraint('year', 'month', 'department', name='uq_hp_ym_dept'),
    )

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False, index=True)
    department = db.Column(db.String(50), nullable=False)

    food_sales = db.Column(db.Float, default=0)      # NOURR
    beverage_sales = db.Column(db.Float, default=0)   # BOISSON
    beer_sales = db.Column(db.Float, default=0)       # BIERE
    wine_sales = db.Column(db.Float, default=0)       # VIN
    mineral_sales = db.Column(db.Float, default=0)    # MIN
    tips = db.Column(db.Float, default=0)             # POURB
    tobacco_sales = db.Column(db.Float, default=0)    # TABAGIE
    total_sales = db.Column(db.Float, default=0)      # TOTAL

    # Payment breakdown
    admin_payment = db.Column(db.Float, default=0)    # Administration (14)
    hp_payment = db.Column(db.Float, default=0)       # Hotel Promotion (15)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def calculated_total(self):
        return round(sum(filter(None, [
            self.food_sales, self.beverage_sales, self.beer_sales,
            self.wine_sales, self.mineral_sales, self.tips, self.tobacco_sales
        ])), 2)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# DUEBACK (from RJ DUEBACK# sheet — per receptionist per day)
# ==============================================================================

class DueBack(db.Model):
    """Daily due-back balance per receptionist."""
    __tablename__ = 'due_backs'
    __table_args__ = (
        db.UniqueConstraint('audit_date', 'receptionist_name', name='uq_dueback_date_rec'),
    )

    id = db.Column(db.Integer, primary_key=True)
    audit_date = db.Column(db.Date, nullable=False, index=True)
    receptionist_name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0)
    entry_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# DAILY LABOR METRICS — Daily labor hours/cost by department
# ==============================================================================

class DailyLaborMetrics(db.Model):
    """Daily labor hours from RJ 'salaires' sheet — by department per day."""
    __tablename__ = 'daily_labor_metrics'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    # Departments: RECEPTION, RESERVATION, AUDIT, PORTIER, COMMIS, CLUB_LOUNGE, GOUVERNANTE, CUISINE, BANQUET, BAR, ROOM_SERVICE, MAINTENANCE, ADMIN
    regular_hours = db.Column(db.Float, default=0)
    overtime_hours = db.Column(db.Float, default=0)
    employees_count = db.Column(db.Integer, default=0)
    labor_cost = db.Column(db.Float, default=0)
    source = db.Column(db.String(20), default='demo_seed')
    __table_args__ = (db.UniqueConstraint('date', 'department', name='uq_daily_labor'),)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# DAILY TIP METRICS — Daily gratuities from Nettoyeur sheet
# ==============================================================================

class DailyTipMetrics(db.Model):
    """Daily tip data from RJ 'Nettoyeur' and 'somm_nettoyeur' sheets."""
    __tablename__ = 'daily_tip_metrics'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    # Departments: CHAMBRE, PIAZZA, BANQUET, BAR, ROOM_SERVICE
    tips_brut = db.Column(db.Float, default=0)
    tips_net = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    employees_tipped = db.Column(db.Integer, default=0)
    source = db.Column(db.String(20), default='demo_seed')
    __table_args__ = (db.UniqueConstraint('date', 'department', name='uq_daily_tip'),)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# MONTHLY BUDGET — Budget data from 'Budget' sheet
# ==============================================================================

class MonthlyBudget(db.Model):
    """Monthly budget targets from RJ 'Budget' sheet."""
    __tablename__ = 'monthly_budgets'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    room_revenue_budget = db.Column(db.Float, default=0)
    fb_revenue_budget = db.Column(db.Float, default=0)
    other_revenue_budget = db.Column(db.Float, default=0)
    total_revenue_budget = db.Column(db.Float, default=0)
    labor_cost_budget = db.Column(db.Float, default=0)
    operating_expense_budget = db.Column(db.Float, default=0)
    occupancy_budget = db.Column(db.Float, default=0)  # target %
    adr_budget = db.Column(db.Float, default=0)
    source = db.Column(db.String(20), default='demo_seed')
    __table_args__ = (db.UniqueConstraint('year', 'month', name='uq_monthly_budget'),)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# DAILY CASH RECONCILIATION — From Diff.Caisse# and Recap
# ==============================================================================

class DailyCashRecon(db.Model):
    """Daily cash reconciliation from Diff.Caisse# and Recap."""
    __tablename__ = 'daily_cash_recon'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    cash_ls_lecture = db.Column(db.Float, default=0)
    cash_ls_correction = db.Column(db.Float, default=0)
    cash_pos_lecture = db.Column(db.Float, default=0)
    cash_pos_correction = db.Column(db.Float, default=0)
    cheque_ar = db.Column(db.Float, default=0)
    cheque_dr = db.Column(db.Float, default=0)
    remb_gratuite = db.Column(db.Float, default=0)
    remb_client = db.Column(db.Float, default=0)
    dueback_total = db.Column(db.Float, default=0)
    surplus_deficit = db.Column(db.Float, default=0)
    deposit_cdn = db.Column(db.Float, default=0)
    deposit_usd = db.Column(db.Float, default=0)
    diff_caisse = db.Column(db.Float, default=0)  # POS variance
    quasimodo_variance = db.Column(db.Float, default=0)  # Global reconciliation
    auditor_name = db.Column(db.String(100))
    source = db.Column(db.String(20), default='demo_seed')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# DAILY CARD METRICS — From Transelect, per card type
# ==============================================================================

class DailyCardMetrics(db.Model):
    """Daily card transaction data from Transelect sheet, by card type."""
    __tablename__ = 'daily_card_metrics'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    card_type = db.Column(db.String(20), nullable=False)  # VISA, MC, AMEX, DEBIT, DISCOVER
    pos_total = db.Column(db.Float, default=0)  # POS reported
    bank_total = db.Column(db.Float, default=0)  # Bank confirmed
    discount_rate = db.Column(db.Float, default=0)  # e.g. 0.02 for 2%
    discount_amount = db.Column(db.Float, default=0)
    net_amount = db.Column(db.Float, default=0)
    transaction_count = db.Column(db.Integer, default=0)
    source = db.Column(db.String(20), default='demo_seed')
    __table_args__ = (db.UniqueConstraint('date', 'card_type', name='uq_daily_card'),)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ==============================================================================
# NIGHT AUDIT SESSION — Native web form (replaces in-memory Excel RJ)
# ==============================================================================

class NightAuditSession(db.Model):
    """Native night audit session — replaces the Excel RJ file.

    Stores all audit data directly in the database. JSON fields are used
    for variable-structure data (terminal breakdowns, receptionist lists)
    that don't need individual column querying.
    """
    __tablename__ = 'night_audit_sessions'

    id = db.Column(db.Integer, primary_key=True)
    audit_date = db.Column(db.Date, unique=True, nullable=False, index=True)
    auditor_name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='draft')  # draft|in_progress|submitted|locked
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, default='')

    # ── Contrôle ──
    temperature = db.Column(db.String(20), default='')
    weather_condition = db.Column(db.String(50), default='')
    chambres_refaire = db.Column(db.Integer, default=0)
    jours_dans_mois = db.Column(db.Integer, default=0)  # Auto-calculated from audit_date

    # ── Recap — Lecture / Correction (Net = Lecture + Corr, computed) ──
    cash_ls_lecture = db.Column(db.Float, default=0)
    cash_ls_corr = db.Column(db.Float, default=0)
    cash_pos_lecture = db.Column(db.Float, default=0)
    cash_pos_corr = db.Column(db.Float, default=0)
    cheque_ar_lecture = db.Column(db.Float, default=0)
    cheque_ar_corr = db.Column(db.Float, default=0)
    cheque_dr_lecture = db.Column(db.Float, default=0)
    cheque_dr_corr = db.Column(db.Float, default=0)
    remb_gratuite_lecture = db.Column(db.Float, default=0)
    remb_gratuite_corr = db.Column(db.Float, default=0)
    remb_client_lecture = db.Column(db.Float, default=0)
    remb_client_corr = db.Column(db.Float, default=0)
    dueback_reception_lecture = db.Column(db.Float, default=0)
    dueback_reception_corr = db.Column(db.Float, default=0)
    dueback_nb_lecture = db.Column(db.Float, default=0)
    dueback_nb_corr = db.Column(db.Float, default=0)
    deposit_cdn = db.Column(db.Float, default=0)
    deposit_us = db.Column(db.Float, default=0)
    recap_balance = db.Column(db.Float, default=0)

    # ── Transelect (JSON: variable terminal structure) ──
    transelect_restaurant = db.Column(db.Text, default='{}')
    transelect_reception = db.Column(db.Text, default='{}')
    transelect_quasimodo = db.Column(db.Text, default='{}')
    transelect_variance = db.Column(db.Float, default=0)

    # ── GEAC/UX ──
    geac_cashout = db.Column(db.Text, default='{}')
    geac_daily_rev = db.Column(db.Text, default='{}')
    geac_balance_sheet = db.Column(db.Text, default='{}')  # JSON: {prev_daily, prev_ledger, today_daily, today_ledger, ...}
    geac_ar_previous = db.Column(db.Float, default=0)
    geac_ar_charges = db.Column(db.Float, default=0)
    geac_ar_payments = db.Column(db.Float, default=0)
    geac_ar_new_balance = db.Column(db.Float, default=0)
    geac_ar_variance = db.Column(db.Float, default=0)

    # ── DueBack (JSON: variable receptionist list) ──
    dueback_entries = db.Column(db.Text, default='[]')
    dueback_total = db.Column(db.Float, default=0)

    # ── SD — Sommaire Journalier des Dépôts ──
    sd_entries = db.Column(db.Text, default='[]')  # [{department,name,currency,amount,verified,reimbursement}]
    sd_total_verified = db.Column(db.Float, default=0)

    # ── Depot ──
    depot_data = db.Column(db.Text, default='{}')  # {client6:{date,amounts:[]},client8:{date,amounts:[]}}
    depot_total = db.Column(db.Float, default=0)

    # ── SetD ──
    setd_rj_balance = db.Column(db.Float, default=0)  # auto = recap_balance
    setd_personnel = db.Column(db.Text, default='[]')  # [{name,column_letter,amount}]

    # ── Jour — F&B Restauration (5 depts × 5 catégories) ──
    jour_cafe_nourriture = db.Column(db.Float, default=0)
    jour_cafe_boisson = db.Column(db.Float, default=0)
    jour_cafe_bieres = db.Column(db.Float, default=0)
    jour_cafe_mineraux = db.Column(db.Float, default=0)
    jour_cafe_vins = db.Column(db.Float, default=0)

    jour_piazza_nourriture = db.Column(db.Float, default=0)
    jour_piazza_boisson = db.Column(db.Float, default=0)
    jour_piazza_bieres = db.Column(db.Float, default=0)
    jour_piazza_mineraux = db.Column(db.Float, default=0)
    jour_piazza_vins = db.Column(db.Float, default=0)

    jour_spesa_nourriture = db.Column(db.Float, default=0)
    jour_spesa_boisson = db.Column(db.Float, default=0)
    jour_spesa_bieres = db.Column(db.Float, default=0)
    jour_spesa_mineraux = db.Column(db.Float, default=0)
    jour_spesa_vins = db.Column(db.Float, default=0)

    jour_chambres_svc_nourriture = db.Column(db.Float, default=0)
    jour_chambres_svc_boisson = db.Column(db.Float, default=0)
    jour_chambres_svc_bieres = db.Column(db.Float, default=0)
    jour_chambres_svc_mineraux = db.Column(db.Float, default=0)
    jour_chambres_svc_vins = db.Column(db.Float, default=0)

    jour_banquet_nourriture = db.Column(db.Float, default=0)
    jour_banquet_boisson = db.Column(db.Float, default=0)
    jour_banquet_bieres = db.Column(db.Float, default=0)
    jour_banquet_mineraux = db.Column(db.Float, default=0)
    jour_banquet_vins = db.Column(db.Float, default=0)

    # ── Jour — F&B Extra ──
    jour_pourboires = db.Column(db.Float, default=0)
    jour_tabagie = db.Column(db.Float, default=0)
    jour_location_salle = db.Column(db.Float, default=0)

    # ── Jour — Ajustements manuels caissier (codes 50, vérification détails) ──
    jour_adj_cafe = db.Column(db.Float, default=0)
    jour_adj_piazza = db.Column(db.Float, default=0)
    jour_adj_spesa = db.Column(db.Float, default=0)
    jour_adj_chambres_svc = db.Column(db.Float, default=0)
    jour_adj_banquet = db.Column(db.Float, default=0)
    jour_adj_tabagie = db.Column(db.Float, default=0)
    jour_adj_notes = db.Column(db.Text, default='[]')  # JSON: [{dept, montant, raison}]

    # ── Jour — Hébergement ──
    jour_room_revenue = db.Column(db.Float, default=0)
    jour_tel_local = db.Column(db.Float, default=0)
    jour_tel_interurbain = db.Column(db.Float, default=0)
    jour_tel_publics = db.Column(db.Float, default=0)

    # ── Jour — Autres revenus ──
    jour_nettoyeur = db.Column(db.Float, default=0)
    jour_machine_distrib = db.Column(db.Float, default=0)
    jour_autres_gl = db.Column(db.Float, default=0)
    jour_sonifi = db.Column(db.Float, default=0)
    jour_lit_pliant = db.Column(db.Float, default=0)
    jour_boutique = db.Column(db.Float, default=0)
    jour_internet = db.Column(db.Float, default=0)
    jour_massage = db.Column(db.Float, default=0)
    jour_diff_forfait = db.Column(db.Float, default=0)  # Différence forfaitaire (auto-calculated: -forfait + G4)
    jour_forfait_sj = db.Column(db.Float, default=0)    # Forfait from Sales Journal (auto-filled, negative)
    g4_montant = db.Column(db.Float, default=0)          # G4 montant (manual entry, propagates to diff_forfait + room_revenue)

    # ── Jour — Taxes ──
    jour_tvq = db.Column(db.Float, default=0)
    jour_tps = db.Column(db.Float, default=0)
    jour_taxe_hebergement = db.Column(db.Float, default=0)

    # ── Jour — Règlements ──
    jour_gift_cards = db.Column(db.Float, default=0)
    jour_certificats = db.Column(db.Float, default=0)

    # ── Jour — Occupation ──
    jour_rooms_simple = db.Column(db.Integer, default=0)
    jour_rooms_double = db.Column(db.Integer, default=0)
    jour_rooms_suite = db.Column(db.Integer, default=0)
    jour_rooms_comp = db.Column(db.Integer, default=0)
    jour_nb_clients = db.Column(db.Integer, default=0)
    jour_rooms_hors_usage = db.Column(db.Integer, default=0)

    # ── Jour — Valeurs spéciales ──
    jour_club_lounge = db.Column(db.Float, default=0)
    jour_deposit_on_hand = db.Column(db.Float, default=0)
    jour_ar_misc = db.Column(db.Float, default=0)

    # ── Jour — Totaux calculés ──
    jour_total_fb = db.Column(db.Float, default=0)
    jour_total_revenue = db.Column(db.Float, default=0)
    jour_adr = db.Column(db.Float, default=0)
    jour_revpar = db.Column(db.Float, default=0)
    jour_occupancy_rate = db.Column(db.Float, default=0)

    # ── Balance flags ──
    is_recap_balanced = db.Column(db.Boolean, default=False)
    is_transelect_balanced = db.Column(db.Boolean, default=False)
    is_ar_balanced = db.Column(db.Boolean, default=False)
    is_fully_balanced = db.Column(db.Boolean, default=False)

    # ── HP/Admin ──
    hp_admin_entries = db.Column(db.Text, default='[]')  # [{area,nourriture,boisson,biere,vin,mineraux,altro,pourboire,raison,autorise_par}]
    hp_admin_total = db.Column(db.Float, default=0)

    # ── Internet ──
    internet_ls_361 = db.Column(db.Float, default=0)  # Cashier Detail 36.1
    internet_ls_365 = db.Column(db.Float, default=0)  # Cashier Detail 36.5
    internet_variance = db.Column(db.Float, default=0)

    # ── Sonifi ──
    sonifi_cd_352 = db.Column(db.Float, default=0)  # Cashier Detail 35.2
    sonifi_email = db.Column(db.Float, default=0)     # montant courriel Sonifi 03h00
    sonifi_variance = db.Column(db.Float, default=0)

    # ── Quasimodo ──
    quasi_fb_debit = db.Column(db.Float, default=0)
    quasi_fb_visa = db.Column(db.Float, default=0)
    quasi_fb_mc = db.Column(db.Float, default=0)
    quasi_fb_amex = db.Column(db.Float, default=0)
    quasi_fb_discover = db.Column(db.Float, default=0)
    quasi_rec_debit = db.Column(db.Float, default=0)
    quasi_rec_visa = db.Column(db.Float, default=0)
    quasi_rec_mc = db.Column(db.Float, default=0)
    quasi_rec_amex = db.Column(db.Float, default=0)
    quasi_rec_discover = db.Column(db.Float, default=0)
    quasi_amex_factor = db.Column(db.Float, default=0.9735)
    quasi_cash_cdn = db.Column(db.Float, default=0)
    quasi_cash_usd = db.Column(db.Float, default=0)
    quasi_total = db.Column(db.Float, default=0)
    quasi_rj_total = db.Column(db.Float, default=0)
    quasi_variance = db.Column(db.Float, default=0)

    # ── DBRS ──
    dbrs_market_segments = db.Column(db.Text, default='{}')  # {transient, group, contract, other}
    dbrs_daily_rev_today = db.Column(db.Float, default=0)
    dbrs_adr = db.Column(db.Float, default=0)
    dbrs_house_count = db.Column(db.Integer, default=0)
    dbrs_otb_data = db.Column(db.Text, default='{}')
    dbrs_noshow_count = db.Column(db.Integer, default=0)
    dbrs_noshow_revenue = db.Column(db.Float, default=0)

    # ── Analyse GL 101100 (Autres revenus — suspense account reconciliation) ──
    gl_101100_previous = db.Column(db.Float, default=0)
    gl_101100_additions = db.Column(db.Float, default=0)
    gl_101100_deductions = db.Column(db.Float, default=0)
    gl_101100_new_balance = db.Column(db.Float, default=0)
    gl_101100_variance = db.Column(db.Float, default=0)
    gl_101100_notes = db.Column(db.Text, default='')

    # ── Analyse GL 100401 (Cash/Bank account reconciliation) ──
    gl_100401_previous = db.Column(db.Float, default=0)
    gl_100401_additions = db.Column(db.Float, default=0)
    gl_100401_deductions = db.Column(db.Float, default=0)
    gl_100401_new_balance = db.Column(db.Float, default=0)
    gl_100401_variance = db.Column(db.Float, default=0)
    gl_100401_notes = db.Column(db.Text, default='')

    # ── Diff.Caisse# (Cash register variance by department/register) ──
    diff_caisse_entries = db.Column(db.Text, default='[]')  # [{register, system, physical, difference, notes}]
    diff_caisse_total = db.Column(db.Float, default=0)
    diff_caisse_reconciled = db.Column(db.Boolean, default=False)

    # ── SOCAN (Music royalties — monthly tracking) ──
    socan_charge = db.Column(db.Float, default=0)
    socan_allocation_resto = db.Column(db.Float, default=0)
    socan_allocation_bar = db.Column(db.Float, default=0)
    socan_allocation_banquet = db.Column(db.Float, default=0)
    socan_notes = db.Column(db.Text, default='')

    # ── Résonne (Conference/AV system charges) ──
    resonne_entries = db.Column(db.Text, default='[]')  # [{department, event, usage_hours, rate, charge}]
    resonne_total = db.Column(db.Float, default=0)

    # ── Vestiaire# (Coat check revenue & variance) ──
    vestiaire_entries = db.Column(db.Text, default='[]')  # [{station, expected, actual, variance}]
    vestiaire_total_revenue = db.Column(db.Float, default=0)
    vestiaire_total_variance = db.Column(db.Float, default=0)

    # ── AD — Administration (admin charges & cost allocations) ──
    admin_entries = db.Column(db.Text, default='[]')  # [{description, amount, cost_center, department, gl_account}]
    admin_total = db.Column(db.Float, default=0)

    # ── Massage (detailed spa/massage breakdown — jour_massage = summary) ──
    massage_entries = db.Column(db.Text, default='[]')  # [{therapist, service_type, revenue, tips}]
    massage_total_revenue = db.Column(db.Float, default=0)
    massage_total_tips = db.Column(db.Float, default=0)

    # ── Ristourne (Rebates/Discounts — guest rebate detail & analysis) ──
    ristourne_entries = db.Column(db.Text, default='[]')  # [{guest, folio, department, original_amount, rebate_amount, reason, authorized_by}]
    ristourne_total = db.Column(db.Float, default=0)
    ristourne_by_dept = db.Column(db.Text, default='{}')  # {ROOM: x, RESTAURANT: y, BAR: z, ...}
    ristourne_analysis_notes = db.Column(db.Text, default='')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_json(self, field):
        import json
        val = getattr(self, field, '{}')
        try:
            return json.loads(val) if val else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_json(self, field, data):
        import json
        setattr(self, field, json.dumps(data, ensure_ascii=False))

    def calculate_all(self):
        """Run all balance calculations and update flags."""
        import calendar as cal_mod
        # 0. Contrôle — auto-calculate jours_dans_mois from audit_date
        if self.audit_date:
            _, days = cal_mod.monthrange(self.audit_date.year, self.audit_date.month)
            self.jours_dans_mois = days

        # 0b. G4 propagation — auto-calculate jour_diff_forfait from forfait + G4
        # Formula: diff_forfait = forfait_sj (already negative) + g4_montant
        forfait = self.jour_forfait_sj or 0
        g4 = self.g4_montant or 0
        if forfait != 0 or g4 != 0:
            self.jour_diff_forfait = round(forfait + g4, 2)

        # 1. Recap balance
        recap_rows = [
            (self.cash_ls_lecture or 0) + (self.cash_ls_corr or 0),
            (self.cash_pos_lecture or 0) + (self.cash_pos_corr or 0),
            (self.cheque_ar_lecture or 0) + (self.cheque_ar_corr or 0),
            (self.cheque_dr_lecture or 0) + (self.cheque_dr_corr or 0),
        ]
        recap_remb = [
            (self.remb_gratuite_lecture or 0) + (self.remb_gratuite_corr or 0),
            (self.remb_client_lecture or 0) + (self.remb_client_corr or 0),
        ]
        recap_dueback = [
            (self.dueback_reception_lecture or 0) + (self.dueback_reception_corr or 0),
            (self.dueback_nb_lecture or 0) + (self.dueback_nb_corr or 0),
        ]
        cash_in = sum(recap_rows)
        cash_out = sum(recap_remb) + sum(recap_dueback)
        deposits = (self.deposit_cdn or 0) + (self.deposit_us or 0)
        self.recap_balance = round(cash_in - cash_out - deposits, 2)
        self.is_recap_balanced = abs(self.recap_balance) < 0.02

        # 2. Transelect variance (expanded structure)
        rest = self.get_json('transelect_restaurant')
        recep = self.get_json('transelect_reception')
        card_types = ['debit', 'visa', 'mc', 'amex', 'discover']

        # Restaurant: each terminal has {debit, visa, mc, amex, discover, total2, positouch, esc_pct}
        # Variance per terminal = sum(cards) - total2
        rest_variance = 0
        rest_card_totals = {c: 0 for c in card_types}
        for term_data in rest.values():
            if not isinstance(term_data, dict):
                continue
            total1 = sum(term_data.get(c, 0) for c in card_types)
            total2 = term_data.get('total2', 0)
            rest_variance += total1 - total2
            for c in card_types:
                rest_card_totals[c] += term_data.get(c, 0)

        # Reception: keyed by card type {fusebox, term8, k053, daily_rev, esc_pct}
        # total per card = fusebox + term8 + k053; variance = total - daily_rev
        rec_variance = 0
        quasi = {}
        for ct in card_types:
            ct_data = recep.get(ct, {})
            if not isinstance(ct_data, dict):
                continue
            rec_total = (ct_data.get('fusebox', 0) or 0) + \
                        (ct_data.get('term8', 0) or 0) + \
                        (ct_data.get('k053', 0) or 0)
            dr = ct_data.get('daily_rev', 0) or 0
            rec_variance += rec_total - dr
            # Quasimodo = restaurant card total + reception total for this card
            quasi[ct] = round(rest_card_totals.get(ct, 0) + rec_total, 2)
        self.set_json('transelect_quasimodo', quasi)

        self.transelect_variance = round(rest_variance + rec_variance, 2)
        self.is_transelect_balanced = abs(self.transelect_variance) < 1.00

        # 3. GEAC AR variance
        ar_expected = (self.geac_ar_previous or 0) + (self.geac_ar_charges or 0) \
                      - (self.geac_ar_payments or 0)
        self.geac_ar_variance = round(ar_expected - (self.geac_ar_new_balance or 0), 2)
        self.is_ar_balanced = abs(self.geac_ar_variance) < 0.02

        # 4. DueBack total
        entries = self.get_json('dueback_entries')
        if isinstance(entries, list):
            self.dueback_total = round(sum(e.get('nouveau', 0) for e in entries), 2)

        # 5. SD total verified
        sd = self.get_json('sd_entries')
        if isinstance(sd, list):
            self.sd_total_verified = round(sum(e.get('verified', 0) or 0 for e in sd), 2)

        # 6. Depot total
        depot = self.get_json('depot_data')
        c6_amounts = depot.get('client6', {}).get('amounts', [])
        c8_amounts = depot.get('client8', {}).get('amounts', [])
        self.depot_total = round(
            sum(a for a in c6_amounts if isinstance(a, (int, float))) +
            sum(a for a in c8_amounts if isinstance(a, (int, float))), 2)

        # 7. SetD RJ balance = recap balance
        self.setd_rj_balance = self.recap_balance

        # 8. Jour totaux
        fb_depts = ['cafe', 'piazza', 'spesa', 'chambres_svc', 'banquet']
        fb_cats = ['nourriture', 'boisson', 'bieres', 'mineraux', 'vins']
        total_fb = 0
        for dept in fb_depts:
            for cat in fb_cats:
                total_fb += getattr(self, f'jour_{dept}_{cat}', 0) or 0
            # Include manual cashier adjustments (codes 50) per department
            total_fb += getattr(self, f'jour_adj_{dept}', 0) or 0
        total_fb += (self.jour_pourboires or 0) + (self.jour_tabagie or 0) + (self.jour_location_salle or 0)
        # Tabagie adjustment
        total_fb += (self.jour_adj_tabagie or 0)
        self.jour_total_fb = round(total_fb, 2)

        # G4 is added to room revenue (Daily Rev doesn't include it)
        room_rev_with_g4 = (self.jour_room_revenue or 0) + (self.g4_montant or 0)
        hebergement = room_rev_with_g4 + (self.jour_tel_local or 0) + \
                      (self.jour_tel_interurbain or 0) + (self.jour_tel_publics or 0)
        autres = sum(getattr(self, f'jour_{f}', 0) or 0 for f in
                     ['nettoyeur', 'machine_distrib', 'autres_gl', 'sonifi',
                      'lit_pliant', 'boutique', 'internet', 'massage', 'diff_forfait'])
        taxes = (self.jour_tvq or 0) + (self.jour_tps or 0) + (self.jour_taxe_hebergement or 0)
        reglements = (self.jour_gift_cards or 0) + (self.jour_certificats or 0)
        special = (self.jour_club_lounge or 0) + (self.jour_deposit_on_hand or 0) + (self.jour_ar_misc or 0)
        self.jour_total_revenue = round(total_fb + hebergement + autres + taxes + reglements + special, 2)

        # Occupation KPIs
        rooms_sold = (self.jour_rooms_simple or 0) + (self.jour_rooms_double or 0) + \
                     (self.jour_rooms_suite or 0) + (self.jour_rooms_comp or 0)
        available = TOTAL_ROOMS - (self.jour_rooms_hors_usage or 0)
        self.jour_occupancy_rate = round((rooms_sold / available * 100) if available > 0 else 0, 1)
        self.jour_adr = round(room_rev_with_g4 / rooms_sold, 2) if rooms_sold > 0 else 0
        self.jour_revpar = round(room_rev_with_g4 / available, 2) if available > 0 else 0


        # 9. HP/Admin total
        hp_entries = self.get_json('hp_admin_entries')
        if isinstance(hp_entries, list):
            hp_total = 0
            for e in hp_entries:
                hp_total += sum(e.get(f, 0) or 0 for f in
                    ['nourriture', 'boisson', 'biere', 'vin', 'mineraux', 'autre', 'pourboire'])
            self.hp_admin_total = round(hp_total, 2)

        # 10. Internet — auto-pull RJ column from Jour (like Excel =+jour!AW{row})
        # internet_ls_365 (CD 36.5 / RJ column) = jour_internet value
        if self.jour_internet is not None and self.jour_internet != 0:
            self.internet_ls_365 = self.jour_internet
        self.internet_variance = round((self.internet_ls_361 or 0) - (self.internet_ls_365 or 0), 2)

        # 11. Sonifi — auto-pull RJ column from Jour (like Excel =+jour!AT{row})
        # sonifi_email (RJ column) = jour_sonifi value
        if self.jour_sonifi is not None and self.jour_sonifi != 0:
            self.sonifi_email = self.jour_sonifi
        self.sonifi_variance = round((self.sonifi_cd_352 or 0) - (self.sonifi_email or 0), 2)

        # 12. Quasimodo — auto-fill from Transelect + Recap (like autoFillQuasimodo button)
        # Pull card totals from transelect_quasimodo (restaurant + reception per card)
        quasi_data = self.get_json('transelect_quasimodo')
        if quasi_data:
            # Split quasi totals into fb (restaurant) and rec (reception) using Transelect data
            for c in card_types:
                total_card = quasi_data.get(c, 0) or 0
                # Restaurant totals
                fb_val = rest_card_totals.get(c, 0) or 0
                # Reception totals = total - restaurant
                rec_val = total_card - fb_val
                setattr(self, f'quasi_fb_{c}', round(fb_val, 2))
                setattr(self, f'quasi_rec_{c}', round(rec_val, 2))
            # Cash from Recap deposits
            self.quasi_cash_cdn = self.deposit_cdn or 0
            self.quasi_cash_usd = self.deposit_us or 0

        fb_total = sum(getattr(self, f'quasi_fb_{c}', 0) or 0 for c in card_types)
        rec_total_q = sum(getattr(self, f'quasi_rec_{c}', 0) or 0 for c in card_types)
        amex_net = round(((self.quasi_fb_amex or 0) + (self.quasi_rec_amex or 0)) * (self.quasi_amex_factor or 0.9735), 2)
        amex_gross = (self.quasi_fb_amex or 0) + (self.quasi_rec_amex or 0)
        non_amex = fb_total + rec_total_q - amex_gross
        self.quasi_total = round(non_amex + amex_net + (self.quasi_cash_cdn or 0) + (self.quasi_cash_usd or 0), 2)
        self.quasi_rj_total = self.jour_total_revenue
        self.quasi_variance = round(self.quasi_total - self.quasi_rj_total, 2)

        # 13. DBRS auto-values from Jour
        self.dbrs_daily_rev_today = self.jour_room_revenue or 0
        self.dbrs_adr = self.jour_adr
        self.dbrs_house_count = rooms_sold

        # 14. Analyse GL variances
        self.gl_101100_variance = round(
            (self.gl_101100_previous or 0) + (self.gl_101100_additions or 0)
            - (self.gl_101100_deductions or 0) - (self.gl_101100_new_balance or 0), 2)
        self.gl_100401_variance = round(
            (self.gl_100401_previous or 0) + (self.gl_100401_additions or 0)
            - (self.gl_100401_deductions or 0) - (self.gl_100401_new_balance or 0), 2)

        # 15. Diff.Caisse total
        dc = self.get_json('diff_caisse_entries')
        if isinstance(dc, list):
            self.diff_caisse_total = round(sum(e.get('difference', 0) or 0 for e in dc), 2)
            self.diff_caisse_reconciled = abs(self.diff_caisse_total) < 0.02

        # 16. Résonne total
        res_entries = self.get_json('resonne_entries')
        if isinstance(res_entries, list):
            self.resonne_total = round(sum(e.get('charge', 0) or 0 for e in res_entries), 2)

        # 17. Vestiaire totals
        vest = self.get_json('vestiaire_entries')
        if isinstance(vest, list):
            self.vestiaire_total_revenue = round(sum(e.get('actual', 0) or 0 for e in vest), 2)
            self.vestiaire_total_variance = round(sum(e.get('variance', 0) or 0 for e in vest), 2)

        # 18. Admin total
        adm = self.get_json('admin_entries')
        if isinstance(adm, list):
            self.admin_total = round(sum(e.get('amount', 0) or 0 for e in adm), 2)

        # 19. Massage totals
        mass = self.get_json('massage_entries')
        if isinstance(mass, list):
            self.massage_total_revenue = round(sum(e.get('revenue', 0) or 0 for e in mass), 2)
            self.massage_total_tips = round(sum(e.get('tips', 0) or 0 for e in mass), 2)
            # Sync with jour_massage summary
            if self.massage_total_revenue > 0:
                self.jour_massage = self.massage_total_revenue

        # 20. Ristourne totals
        rist = self.get_json('ristourne_entries')
        if isinstance(rist, list):
            self.ristourne_total = round(sum(e.get('rebate_amount', 0) or 0 for e in rist), 2)
            # Build by-department summary
            by_dept = {}
            for e in rist:
                dept = e.get('department', 'Autre')
                by_dept[dept] = round(by_dept.get(dept, 0) + (e.get('rebate_amount', 0) or 0), 2)
            self.set_json('ristourne_by_dept', by_dept)

        # 21. SOCAN total (sum of allocations)
        self.socan_charge = round(
            (self.socan_allocation_resto or 0) + (self.socan_allocation_bar or 0)
            + (self.socan_allocation_banquet or 0), 2)

        # Overall
        self.is_fully_balanced = (self.is_recap_balanced and
                                  self.is_transelect_balanced and
                                  self.is_ar_balanced)

    def to_dict(self):
        import json
        d = {}
        for c in self.__table__.columns:
            val = getattr(self, c.name)
            if hasattr(val, 'isoformat'):
                d[c.name] = val.isoformat() if val else None
            else:
                d[c.name] = val
        json_fields = ['transelect_restaurant', 'transelect_reception', 'transelect_quasimodo',
                       'geac_cashout', 'geac_daily_rev', 'geac_balance_sheet', 'dueback_entries',
                       'sd_entries', 'depot_data', 'setd_personnel',
                       'hp_admin_entries', 'dbrs_market_segments', 'dbrs_otb_data',
                       'jour_adj_notes',
                       'diff_caisse_entries', 'resonne_entries', 'vestiaire_entries',
                       'admin_entries', 'massage_entries', 'ristourne_entries',
                       'ristourne_by_dept']
        list_json_fields = ('dueback_entries', 'sd_entries', 'setd_personnel', 'hp_admin_entries', 'jour_adj_notes',
                            'diff_caisse_entries', 'resonne_entries', 'vestiaire_entries',
                            'admin_entries', 'massage_entries', 'ristourne_entries')
        for jf in json_fields:
            try:
                raw = d.get(jf) or ('[]' if jf in list_json_fields else '{}')
                d[jf] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                d[jf] = [] if jf in list_json_fields else {}
        return d


# ==============================================================================
# POD (POURBOIRES) — Persistent tip distribution data
# ==============================================================================

class PODPeriod(db.Model):
    """One bi-weekly tip distribution period."""
    __tablename__ = 'pod_periods'

    id = db.Column(db.Integer, primary_key=True)
    period_start = db.Column(db.Date, nullable=False, index=True)
    period_end = db.Column(db.Date, nullable=True)
    source_filename = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entries = db.relationship('PODEntry', backref='period', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'source_filename': self.source_filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'entry_count': len(self.entries),
        }


class PODEntry(db.Model):
    """One employee × one day of tip data within a POD period."""
    __tablename__ = 'pod_entries'

    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('pod_periods.id'), nullable=False)
    emp_id = db.Column(db.String(50), nullable=True)
    emp_name = db.Column(db.String(200), nullable=False)
    day_index = db.Column(db.Integer, nullable=False)  # 0-13
    day_date = db.Column(db.Date, nullable=True)
    ventes = db.Column(db.Float, default=0)
    pourb = db.Column(db.Float, default=0)
    dist = db.Column(db.Float, default=0)
    recus = db.Column(db.Float, default=0)
    # Summary fields (per employee, duplicated for each day but only meaningful once)
    ventes_total = db.Column(db.Float, default=0)
    pourb_bruts = db.Column(db.Float, default=0)
    pourb_redist = db.Column(db.Float, default=0)
    pourb_recus = db.Column(db.Float, default=0)
    pourb_nets = db.Column(db.Float, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'emp_id': self.emp_id,
            'emp_name': self.emp_name,
            'day_index': self.day_index,
            'day_date': self.day_date.isoformat() if self.day_date else None,
            'ventes': self.ventes,
            'pourb': self.pourb,
            'dist': self.dist,
            'recus': self.recus,
        }


# ==============================================================================
# HP (HOTEL PROMOTION / ADMIN) — Persistent comped meal data
# ==============================================================================

class HPPeriod(db.Model):
    """One monthly HP period (file upload)."""
    __tablename__ = 'hp_periods'

    id = db.Column(db.Integer, primary_key=True)
    period_label = db.Column(db.String(100), nullable=True)  # e.g. "Février 2026"
    month = db.Column(db.Integer, nullable=True)  # 1-12
    year = db.Column(db.Integer, nullable=True)
    source_filename = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entries = db.relationship('HPEntry', backref='period', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'period_label': self.period_label,
            'month': self.month,
            'year': self.year,
            'source_filename': self.source_filename,
            'entry_count': len(self.entries),
        }


class HPEntry(db.Model):
    """One comped meal / F&B invoice entry."""
    __tablename__ = 'hp_entries'

    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('hp_periods.id'), nullable=False)
    day = db.Column(db.Integer, nullable=False)  # 1-31
    area = db.Column(db.String(100), nullable=True)
    nourriture = db.Column(db.Float, default=0)
    boisson = db.Column(db.Float, default=0)
    biere = db.Column(db.Float, default=0)
    vin = db.Column(db.Float, default=0)
    mineraux = db.Column(db.Float, default=0)
    autre = db.Column(db.Float, default=0)
    pourboire = db.Column(db.Float, default=0)
    paiement = db.Column(db.String(100), nullable=True)
    total = db.Column(db.Float, default=0)
    raison = db.Column(db.String(300), nullable=True)
    qui = db.Column(db.String(100), nullable=True)
    autorise_par = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'day': self.day,
            'area': self.area,
            'nourriture': self.nourriture,
            'boisson': self.boisson,
            'biere': self.biere,
            'vin': self.vin,
            'mineraux': self.mineraux,
            'autre': self.autre,
            'pourboire': self.pourboire,
            'paiement': self.paiement,
            'total': self.total,
            'raison': self.raison,
            'qui': self.qui,
            'autorise_par': self.autorise_par,
        }


# ==============================================================================
# RJ ARCHIVE — Raw data from ALL 38 Excel sheets stored in DB
# ==============================================================================

class RJArchive(db.Model):
    """Full archive of an uploaded RJ Excel workbook.
    Stores raw cell data from every sheet so nothing is ever lost."""
    __tablename__ = 'rj_archives'

    id = db.Column(db.Integer, primary_key=True)
    audit_date = db.Column(db.Date, nullable=False, index=True)
    source_filename = db.Column(db.String(200), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.String(100), nullable=True)
    file_binary = db.Column(db.LargeBinary, nullable=True)  # Original .xls/.xlsx bytes
    sheet_names = db.Column(db.Text, nullable=True)  # JSON list
    total_sheets = db.Column(db.Integer, default=0)
    total_rows = db.Column(db.Integer, default=0)

    sheets = db.relationship('RJSheetData', backref='archive', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        import json as _json
        return {
            'id': self.id,
            'audit_date': self.audit_date.isoformat() if self.audit_date else None,
            'source_filename': self.source_filename,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'uploaded_by': self.uploaded_by,
            'sheet_names': _json.loads(self.sheet_names) if self.sheet_names else [],
            'total_sheets': self.total_sheets,
            'total_rows': self.total_rows,
            'has_binary': self.file_binary is not None,
        }


class RJSheetData(db.Model):
    """Individual sheet data from an RJ archive — one row per sheet.
    Allows querying specific sheets without loading the entire archive."""
    __tablename__ = 'rj_sheet_data'

    id = db.Column(db.Integer, primary_key=True)
    archive_id = db.Column(db.Integer, db.ForeignKey('rj_archives.id'), nullable=False)
    audit_date = db.Column(db.Date, nullable=False, index=True)
    sheet_name = db.Column(db.String(100), nullable=False)
    sheet_index = db.Column(db.Integer, default=0)
    row_count = db.Column(db.Integer, default=0)
    col_count = db.Column(db.Integer, default=0)
    data_json = db.Column(db.Text, nullable=True)  # JSON: [[cell, cell, ...], ...]
    headers_json = db.Column(db.Text, nullable=True)  # JSON: first row as list

    def to_dict(self):
        import json as _json
        return {
            'id': self.id,
            'audit_date': self.audit_date.isoformat() if self.audit_date else None,
            'sheet_name': self.sheet_name,
            'row_count': self.row_count,
            'col_count': self.col_count,
            'headers': _json.loads(self.headers_json) if self.headers_json else [],
        }
