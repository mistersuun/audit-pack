import os
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

    # Create tables
    with app.app_context():
        db.create_all()

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
    app.run(debug=True, host='127.0.0.1', port=5000)
