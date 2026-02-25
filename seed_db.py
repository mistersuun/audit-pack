"""
Master seed script — run after a fresh git clone to set up the database.

Usage:
    python seed_db.py          # Seed everything (users, tasks, property, demo RJ)
    python seed_db.py --quick  # Seed only users + tasks + property (no demo data)
    python seed_db.py --reset  # Delete DB and recreate from scratch

Safe to run multiple times — uses upsert logic where possible.
Handles schema migrations automatically (adds missing columns to existing tables).
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, date, timedelta

from main import create_app
from database import db, User, Task, Property, NightAuditSession, MonthlyBudget


# ═══════════════════════════════════════════════════════════════════════════
# 0. AUTO-MIGRATION — Add missing columns to existing tables
# ═══════════════════════════════════════════════════════════════════════════

# Map SQLAlchemy types to SQLite types
_TYPE_MAP = {
    'INTEGER': 'INTEGER',
    'FLOAT': 'REAL',
    'VARCHAR': 'TEXT',
    'TEXT': 'TEXT',
    'BOOLEAN': 'INTEGER',
    'DATE': 'TEXT',
    'DATETIME': 'TEXT',
    'NUMERIC': 'REAL',
}


def _sqlite_type(sa_column):
    """Convert a SQLAlchemy column type to its SQLite equivalent."""
    type_name = sa_column.type.__class__.__name__.upper()
    # Handle String(N) → TEXT
    if type_name == 'STRING':
        return 'TEXT'
    return _TYPE_MAP.get(type_name, 'TEXT')


def _get_default_sql(sa_column):
    """Get DEFAULT clause for a column, if any."""
    if sa_column.default is not None:
        val = sa_column.default.arg
        if val is None:
            return ''
        if callable(val):
            return ''  # Can't express Python callables as SQL defaults
        if isinstance(val, bool):
            return f' DEFAULT {1 if val else 0}'
        if isinstance(val, (int, float)):
            return f' DEFAULT {val}'
        if isinstance(val, str):
            return f" DEFAULT '{val}'"
    return ''


def auto_migrate(app):
    """Compare SQLAlchemy models to actual SQLite schema and add missing columns."""
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
    if not db_path or not os.path.exists(db_path):
        return 0  # No DB yet, create_all will handle it

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {r[0] for r in cursor.fetchall()}

    total_added = 0

    for table in db.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # Table doesn't exist yet, create_all will make it

        # Get existing columns for this table
        cursor.execute(f'PRAGMA table_info("{table.name}")')
        existing_cols = {r[1] for r in cursor.fetchall()}

        # Check each model column
        for col in table.columns:
            if col.name not in existing_cols:
                col_type = _sqlite_type(col)
                default_clause = _get_default_sql(col)
                sql = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type}{default_clause}'
                try:
                    cursor.execute(sql)
                    total_added += 1
                except Exception as e:
                    print(f"  ⚠ Erreur migration {table.name}.{col.name}: {e}")

    conn.commit()
    conn.close()
    return total_added


# ═══════════════════════════════════════════════════════════════════════════
# 1. DEFAULT USERS
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_USERS = [
    {
        'username': 'Auditeur',
        'password': 'audit2026',
        'role': 'night_auditor',
        'full_name_fr': 'Auditeur de nuit',
        'email': None,
        'must_change_password': False,
    },
    {
        'username': 'Manager',
        'password': 'manager2026',
        'role': 'gm',
        'full_name_fr': 'Directeur général',
        'email': None,
        'must_change_password': False,
    },
    {
        'username': 'Admin',
        'password': 'admin2026',
        'role': 'admin',
        'full_name_fr': 'Administrateur système',
        'email': None,
        'must_change_password': True,
    },
    {
        'username': 'Superviseur',
        'password': 'super2026',
        'role': 'front_desk_supervisor',
        'full_name_fr': 'Superviseur réception',
        'email': None,
        'must_change_password': False,
    },
]


def seed_users():
    """Create or update default users."""
    created = 0
    updated = 0

    for u_data in DEFAULT_USERS:
        user = User.query.filter_by(username=u_data['username']).first()
        if user:
            # Update role & full_name but don't overwrite password
            user.role = u_data['role']
            user.full_name_fr = u_data['full_name_fr']
            user.is_active = True
            updated += 1
        else:
            user = User(
                username=u_data['username'],
                role=u_data['role'],
                full_name_fr=u_data['full_name_fr'],
                email=u_data['email'],
                is_active=True,
                must_change_password=u_data['must_change_password'],
            )
            user.set_password(u_data['password'])
            db.session.add(user)
            created += 1

    db.session.commit()
    print(f"  Utilisateurs: {created} créés, {updated} mis à jour")
    return created + updated


# ═══════════════════════════════════════════════════════════════════════════
# 2. DEFAULT PROPERTY
# ═══════════════════════════════════════════════════════════════════════════

def seed_property():
    """Create Sheraton Laval property if it doesn't exist."""
    prop = Property.query.filter_by(code='SHRLVL').first()
    if prop:
        print("  Propriété: Sheraton Laval existe déjà")
        return prop

    prop = Property(
        code='SHRLVL',
        name='Sheraton Laval',
        brand='Marriott',
        total_rooms=340,
        address='2440 Autoroute des Laurentides',
        city='Laval',
        province='Québec',
        country='Canada',
        timezone='America/Montreal',
        currency='CAD',
        is_active=True,
        pms_type='Galaxy Lightspeed',
    )
    db.session.add(prop)
    db.session.commit()
    print("  Propriété: Sheraton Laval créée")
    return prop


# ═══════════════════════════════════════════════════════════════════════════
# 3. TASKS (delegates to existing seed_tasks.py logic)
# ═══════════════════════════════════════════════════════════════════════════

def seed_tasks():
    """Seed front + back checklist tasks."""
    from scripts.seed_tasks_front import TASKS_DETAILED as TASKS_FRONT
    from seed_tasks import TASKS_BACK, _upsert_task

    created = 0
    updated = 0

    for task_data in TASKS_FRONT:
        result = _upsert_task(task_data, 'front')
        created += 1 if result == 'created' else 0
        updated += 1 if result == 'updated' else 0

    for task_data in TASKS_BACK:
        result = _upsert_task(task_data, 'back')
        created += 1 if result == 'created' else 0
        updated += 1 if result == 'updated' else 0

    # Deactivate orphaned tasks
    front_orders = {t["order"] for t in TASKS_FRONT}
    back_orders = {t["order"] for t in TASKS_BACK}
    deactivated = 0

    orphans = Task.query.filter(
        ((Task.role == 'front') & (~Task.order.in_(front_orders))) |
        ((Task.role == 'back') & (~Task.order.in_(back_orders)))
    ).all()
    for t in orphans:
        t.is_active = False
        deactivated += 1

    db.session.commit()
    total = len(TASKS_FRONT) + len(TASKS_BACK)
    print(f"  Tâches: {total} total ({created} créées, {updated} mises à jour, {deactivated} désactivées)")


# ═══════════════════════════════════════════════════════════════════════════
# 4. SAMPLE RJ SESSION (one realistic night for demo/testing)
# ═══════════════════════════════════════════════════════════════════════════

def seed_sample_rj():
    """Create a sample RJ session for demonstration."""
    sample_date = date(2026, 2, 24)  # Yesterday
    existing = NightAuditSession.query.filter_by(audit_date=sample_date).first()
    if existing:
        print(f"  RJ: Session {sample_date} existe déjà")
        return

    session = NightAuditSession(
        audit_date=sample_date,
        auditor_name='Auditeur',
        status='draft',
        temperature=-8.0,
        weather_condition='Neige légère',
        chambres_refaire=12,

        # ── Recap ──
        cash_ls_lecture=2450.00, cash_ls_corr=0,
        cash_pos_lecture=1875.50, cash_pos_corr=0,
        cheque_ar_lecture=0, cheque_ar_corr=0,
        cheque_dr_lecture=340.00, cheque_dr_corr=0,
        remb_gratuite_lecture=0, remb_gratuite_corr=0,
        remb_client_lecture=-125.00, remb_client_corr=0,
        dueback_reception_lecture=45.00, dueback_reception_corr=0,
        dueback_nb_lecture=-30.00, dueback_nb_corr=0,
        deposit_cdn=4555.50,
        deposit_us=0,

        # ── DueBack ──
        dueback_entries=json.dumps([
            {"name": "Marie-Josée", "previous": -45.00, "nouveau": 62.50},
            {"name": "Philippe", "previous": -30.00, "nouveau": 45.00},
            {"name": "Samira", "previous": 0, "nouveau": -18.75},
        ]),

        # ── Jour — F&B ──
        jour_cafe_nourriture=1245.80,
        jour_cafe_boisson=387.50,
        jour_cafe_bieres=210.00,
        jour_cafe_mineraux=45.00,
        jour_cafe_vins=165.30,

        jour_piazza_nourriture=2890.40,
        jour_piazza_boisson=645.20,
        jour_piazza_bieres=425.00,
        jour_piazza_mineraux=78.50,
        jour_piazza_vins=520.75,

        jour_spesa_nourriture=1580.60,
        jour_spesa_boisson=320.40,
        jour_spesa_bieres=185.00,
        jour_spesa_mineraux=32.00,
        jour_spesa_vins=275.50,

        jour_chambres_svc_nourriture=680.25,
        jour_chambres_svc_boisson=125.00,
        jour_chambres_svc_bieres=45.00,
        jour_chambres_svc_mineraux=12.00,
        jour_chambres_svc_vins=88.50,

        jour_banquet_nourriture=4250.00,
        jour_banquet_boisson=890.00,
        jour_banquet_bieres=560.00,
        jour_banquet_mineraux=120.00,
        jour_banquet_vins=1450.00,

        # ── Jour — Hébergement ──
        jour_room_revenue=38750.00,
        jour_tel_local=85.50,
        jour_tel_interurbain=35.00,
        jour_tel_publics=5.00,
        jour_tvq=5812.50,
        jour_tps=1937.50,
        jour_taxe_hebergement=1162.50,

        # ── Jour — Occupation ──
        jour_rooms_simple=85,
        jour_rooms_double=142,
        jour_rooms_suite=8,
        jour_rooms_comp=3,
        jour_rooms_hors_usage=5,
        jour_nb_clients=412,

        # ── Jour — Autres revenus ──
        jour_nettoyeur=45.00,
        jour_machine_distrib=28.50,
        jour_sonifi=85.00,
        jour_internet=0,
        jour_lit_pliant=0,
        jour_boutique=0,
        jour_massage=0,
        jour_autres_gl=15.00,

        # ── Internet & Sonifi ──
        internet_ls_361=0,
        internet_ls_365=0,
        internet_variance=0,
        sonifi_cd_352=85.00,
        sonifi_email=85.00,
        sonifi_variance=0,

        # ── Transelect (restaurant — simplified) ──
        transelect_restaurant=json.dumps({
            "terminal_1": {"debit": 1250.00, "visa": 2340.50, "mc": 1560.25, "amex": 890.00},
            "terminal_2": {"debit": 680.00, "visa": 1120.75, "mc": 780.50, "amex": 420.00},
        }),
        transelect_reception=json.dumps({
            "debit": {"freedom": 3450.00, "moneris": 0},
            "visa": {"freedom": 12560.00, "moneris": 0},
            "mc": {"freedom": 8750.00, "moneris": 0},
            "amex": {"freedom": 4520.00, "moneris": 0},
        }),

        # ── GEAC ──
        geac_cashout=json.dumps({
            "debit": 5380.00, "visa": 16021.25, "mc": 11091.25,
            "amex": 5830.00, "discover": 0,
        }),
        geac_daily_rev=json.dumps({
            "debit": 5380.00, "visa": 16021.25, "mc": 11091.25,
            "amex": 5830.00, "discover": 0,
        }),

        # ── Quasimodo ──
        quasi_fb_debit=1930.00,
        quasi_fb_visa=3461.25,
        quasi_fb_mc=2340.75,
        quasi_fb_amex=1310.00,
        quasi_rec_debit=3450.00,
        quasi_rec_visa=12560.00,
        quasi_rec_mc=8750.00,
        quasi_rec_amex=4520.00,
        quasi_amex_factor=0.9735,
        quasi_cash_cdn=4555.50,
        quasi_cash_usd=0,

        # ── SD ──
        sd_entries=json.dumps([
            {"department": "Réception", "name": "Marie-Josée", "currency": "CAD",
             "amount": 2450.00, "verified": True, "reimbursement": 0},
            {"department": "Réception", "name": "Philippe", "currency": "CAD",
             "amount": 1875.50, "verified": True, "reimbursement": 0},
            {"department": "Bar", "name": "Serveur 1", "currency": "CAD",
             "amount": 340.00, "verified": True, "reimbursement": 0},
        ]),

        # ── SetD ──
        setd_personnel=json.dumps([
            {"name": "Samira", "amount": 12.50},
            {"name": "Jean-Marc", "amount": 8.75},
        ]),

        # ── HP Admin ──
        hp_admin_entries=json.dumps([
            {"area": "Piazza", "nourriture": 125.00, "boisson": 45.00,
             "biere": 18.00, "vin": 32.00, "mineraux": 0, "autre": 0,
             "pourboire": 8.00, "raison": "Réunion direction",
             "autorise_par": "M. Tremblay"},
        ]),

        # ── DBRS ──
        dbrs_daily_rev_today=38750.00,
        dbrs_adr=162.39,
        dbrs_house_count=412,
        dbrs_noshow_count=2,
        dbrs_noshow_revenue=324.78,
        dbrs_market_segments=json.dumps({
            "transient": 145, "group": 72, "contract": 18, "other": 3,
        }),
    )

    db.session.add(session)
    db.session.commit()
    print(f"  RJ: Session exemple {sample_date} créée (draft)")


# ═══════════════════════════════════════════════════════════════════════════
# 5. SAMPLE MONTHLY BUDGET (current month)
# ═══════════════════════════════════════════════════════════════════════════

def seed_sample_budget():
    """Create sample monthly budgets for current and next month."""
    months = [(2026, 2), (2026, 3)]
    for year, month in months:
        existing = MonthlyBudget.query.filter_by(year=year, month=month).first()
        if existing:
            print(f"  Budget: {month:02d}/{year} existe déjà")
            continue

        budget = MonthlyBudget(
            year=year,
            month=month,
            room_revenue=1_100_000.00,
            adr_target=155.00,
            rooms_target=7140,  # ~255 rooms/day * 28 days
            total_revenue=1_425_000.00,
            piazza=85_000.00,
            spesa=55_000.00,
            banquet=95_000.00,
        )
        db.session.add(budget)
        print(f"  Budget: {month:02d}/{year} créé")

    db.session.commit()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    quick = '--quick' in sys.argv
    reset = '--reset' in sys.argv

    # Handle --reset before creating the app (avoids SQLite lock)
    if reset:
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'audit.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"  Base de données supprimée: {os.path.basename(db_path)}")

    app = create_app()

    with app.app_context():
        # Auto-migrate: add missing columns to existing tables
        migrated = auto_migrate(app)
        if migrated:
            print(f"\n── Migration automatique ──")
            print(f"  {migrated} colonne(s) ajoutée(s) aux tables existantes")

        # Ensure all tables exist (creates new tables, but won't add columns)
        db.create_all()

        print("\n╔══════════════════════════════════════════╗")
        print("║   Sheraton Laval — Initialisation BD     ║")
        print("╚══════════════════════════════════════════╝\n")

        # Always seed these
        print("── Utilisateurs ──")
        seed_users()

        print("\n── Propriété ──")
        seed_property()

        print("\n── Tâches (checklist front + back) ──")
        seed_tasks()

        if not quick:
            print("\n── Session RJ exemple ──")
            seed_sample_rj()

            print("\n── Budget mensuel exemple ──")
            seed_sample_budget()

            # Seed CRM demo data if available
            try:
                print("\n── Données CRM (5 ans de métriques) ──")
                from scripts.seed_crm_demo import main as seed_crm_main
                seed_crm_main()
            except ImportError:
                print("  (scripts/seed_crm_demo.py non trouvé — sauté)")
            except Exception as e:
                print(f"  ⚠ Erreur CRM demo: {e}")
        else:
            print("\n(Mode --quick: données démo non chargées)")

        print("\n✅ Initialisation terminée!")
        print("   Lancez 'python main.py' pour démarrer le serveur.\n")
        print("   Identifiants par défaut:")
        print("   ┌─────────────┬──────────────┬─────────────────────┐")
        print("   │ Utilisateur │ Mot de passe │ Rôle                │")
        print("   ├─────────────┼──────────────┼─────────────────────┤")
        print("   │ Auditeur    │ audit2026    │ Auditeur de nuit    │")
        print("   │ Manager     │ manager2026  │ Directeur général   │")
        print("   │ Admin       │ admin2026    │ Administrateur      │")
        print("   │ Superviseur │ super2026    │ Superviseur réception│")
        print("   └─────────────┴──────────────┴─────────────────────┘")
        print(f"   PIN d'accès: défini dans .env (défaut: 1234)\n")


if __name__ == '__main__':
    main()
