import os
import sys
import threading
import logging
from logging.handlers import RotatingFileHandler

# Bootstrap file logging before any other import so pythonw startup failures
# (missing modules, syntax errors, DB locks) actually land on disk.
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(_LOG_DIR, exist_ok=True)
_handler = RotatingFileHandler(
    os.path.join(_LOG_DIR, 'app.log'),
    maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8',
)
_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[_handler])

# Under pythonw.exe sys.stdout/stderr are None — existing print() calls would
# crash with AttributeError. Route them through logging instead.
# A lock guards _buf because APScheduler's daemon thread and Flask's threaded
# request handlers both call print() concurrently in this deployment.
class _StreamToLog:
    def __init__(self, level):
        self.level = level
        self._buf = ''
        self._lock = threading.Lock()
    def write(self, msg):
        with self._lock:
            self._buf += msg
            while '\n' in self._buf:
                line, self._buf = self._buf.split('\n', 1)
                if line.strip():
                    logging.log(self.level, line)
    def flush(self):
        with self._lock:
            if self._buf.strip():
                logging.log(self.level, self._buf)
            self._buf = ''

if sys.stdout is None:
    sys.stdout = _StreamToLog(logging.INFO)
if sys.stderr is None:
    sys.stderr = _StreamToLog(logging.ERROR)

def _excepthook(exc_type, exc_value, exc_tb):
    logging.critical('Uncaught exception', exc_info=(exc_type, exc_value, exc_tb))
sys.excepthook = _excepthook

logging.info('=== audit-pack starting (pid=%s) ===', os.getpid())

from flask import Flask, redirect, url_for, session
from config.settings import Config
from database import db
from routes import auth_bp, auth_v2, checklist_bp
from routes.generators import generators_bp
from routes.audit import audit_bp
from routes.reports import reports_bp
from routes.balances import balances_bp
from routes.crm import crm_bp
from routes.crm_tabs import crm_tabs_bp
from routes.dashboard import dashboard_bp
from routes.manager import manager_bp
from routes.balance_checker import balance_checker_bp
from routes.audit.rj_native import rj_native_bp
from routes.audit.rj_export_pdf import rj_export_bp
from routes.audit.rj_export_excel import rj_excel_bp
from routes.audit.rj_correction import rj_correction_bp
from routes.pod import pod_bp
from routes.hp import hp_bp
from routes.direction import direction_bp
from routes.budget import budget_bp
from routes.notifications import notifications_bp
from routes.forecasting import forecasting_bp
from routes.lightspeed import lightspeed_bp
from routes.properties import properties_bp
from routes.portfolio import portfolio_bp
from routes.compset import compset_bp
from routes.balancer import balancer_bp
from utils.auth_decorators import get_current_user, ROLE_LABELS_FR
from utils.csrf import get_csrf_token
from utils.email_service import EmailService


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.validate()

    # Fix database path for absolute reference
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database", "audit.db")}'

    db.init_app(app)

    # Initialize email service
    email_service = EmailService(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(auth_v2)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(generators_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(balances_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(crm_tabs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(balance_checker_bp)
    app.register_blueprint(rj_native_bp)
    app.register_blueprint(rj_export_bp)
    app.register_blueprint(rj_excel_bp)
    app.register_blueprint(rj_correction_bp)
    app.register_blueprint(pod_bp)
    app.register_blueprint(hp_bp)
    app.register_blueprint(direction_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(forecasting_bp)
    app.register_blueprint(lightspeed_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(compset_bp)
    app.register_blueprint(balancer_bp)

    # Create tables + auto-seed if empty
    with app.app_context():
        db.create_all()

        # Auto-seed on first run (empty DB)
        from database.models import User, DailyJourMetrics
        if not User.query.first():
            try:
                from seed_db import auto_migrate, seed_users, seed_property, seed_tasks
                print("\n[INIT] Première exécution détectée — initialisation automatique...")
                auto_migrate(app)
                seed_users()
                seed_property()
                seed_tasks()
                print("[OK] Base de données initialisée avec succès.")
            except Exception as e:
                print(f"[WARN] Erreur auto-seed: {e}")

        # Auto-import from K: drive if DailyJourMetrics is empty
        if DailyJourMetrics.query.count() == 0:
            try:
                from utils.sync_engine import SyncEngine
                print("\n[SYNC] Import automatique depuis K: drive...")
                result = SyncEngine.full_sync(app)
                rj = result.get('rj', {})
                final_count = DailyJourMetrics.query.count()
                print(f"[OK] {final_count} métriques importées ({rj.get('errors', 0)} erreurs)\n")
            except Exception as e:
                print(f"[WARN] Erreur auto-import: {e}\n")

    # ── Scheduled daily sync (9 AM Canada/Eastern) ─────────────────────
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler(daemon=True)

        def _daily_sync_job():
            """Run daily K: drive sync inside app context."""
            from utils.sync_engine import SyncEngine
            try:
                result = SyncEngine.daily_sync(app)
                rj = result.get('rj', {})
                print(f"[SYNC] Daily sync: {rj.get('imported', 0)} new, {rj.get('updated', 0)} updated RJ metrics")
            except Exception as e:
                print(f"[WARN] Daily sync error: {e}")

        scheduler.add_job(
            _daily_sync_job,
            CronTrigger(
                hour=Config.SYNC_HOUR,
                minute=Config.SYNC_MINUTE,
                timezone=Config.SYNC_TIMEZONE,
            ),
            id='daily_kdrive_sync',
            name='Daily K: drive sync (9 AM ET)',
            replace_existing=True,
        )
        scheduler.start()
        print(f"[SYNC] Planifie: {Config.SYNC_HOUR}:{Config.SYNC_MINUTE:02d} ({Config.SYNC_TIMEZONE})")
    except ImportError:
        print("[WARN] APScheduler non installe - sync automatique desactive (pip install APScheduler)")
    except Exception as e:
        print(f"[WARN] Scheduler error: {e}")

    # Handle upload size limit errors
    from werkzeug.exceptions import RequestEntityTooLarge

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(e):
        from flask import jsonify as j
        return j({'success': False, 'error': 'Fichier trop volumineux (max 32 MB)'}), 413

    # Context processor to inject user info and CSRF token into templates
    @app.context_processor
    def inject_user_info():
        user = get_current_user()
        user_role_label = ROLE_LABELS_FR.get(session.get('user_role_type'), 'Utilisateur')
        return {
            'current_user': user,
            'user_role_label': user_role_label,
            'csrf_token': get_csrf_token
        }

    return app


if __name__ == '__main__':
    app = create_app()
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, host='127.0.0.1', port=5000)
