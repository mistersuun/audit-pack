import os
import warnings
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database/audit.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUDIT_PIN = os.getenv('AUDIT_PIN', '1234')

    # ─── Email / SMTP Configuration ───────────────────────────────────────
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@sheraton-laval-audit.com')

    # ─── Alert Thresholds ─────────────────────────────────────────────────
    ALERT_VARIANCE_THRESHOLD = float(os.getenv('ALERT_VARIANCE_THRESHOLD', '5.00'))
    ALERT_OCCUPATION_MIN = float(os.getenv('ALERT_OCCUPATION_MIN', '60.0'))
    ALERT_SUBMISSION_DEADLINE = os.getenv('ALERT_SUBMISSION_DEADLINE', '06:00')

    # ─── Lightspeed Galaxy PMS Integration ─────────────────────────────────
    LIGHTSPEED_CLIENT_ID = os.getenv('LIGHTSPEED_CLIENT_ID', '')
    LIGHTSPEED_CLIENT_SECRET = os.getenv('LIGHTSPEED_CLIENT_SECRET', '')
    LIGHTSPEED_PROPERTY_ID = os.getenv('LIGHTSPEED_PROPERTY_ID', '')
    LIGHTSPEED_BASE_URL = os.getenv('LIGHTSPEED_BASE_URL', 'https://api.lsk.lightspeed.app')
    LIGHTSPEED_ENABLED = os.getenv('LIGHTSPEED_ENABLED', 'false').lower() == 'true'

    @staticmethod
    def validate():
        """Warn about insecure defaults (call at startup)."""
        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            warnings.warn(
                '\u26a0\ufe0f  SECRET_KEY is using the default value. '
                'Set SECRET_KEY in .env for production!',
                stacklevel=2
            )
        if Config.AUDIT_PIN == '1234':
            warnings.warn(
                '\u26a0\ufe0f  AUDIT_PIN is the default "1234". '
                'Set a strong PIN in .env for production!',
                stacklevel=2
            )
