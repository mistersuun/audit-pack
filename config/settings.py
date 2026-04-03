import os
import warnings
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database/audit.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUDIT_PIN = os.getenv('AUDIT_PIN', '1234')

    # ─── Upload & Session Security ──────────────────────────────────────
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max upload
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = 28800  # 8 hours

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

    # ─── K: Drive Data Sync ────────────────────────────────────────────────
    KDRIVE_RJ_DIRS = [
        r'K:\RJ 2022-2023',
        r'K:\RJ 2023-2024',
        r'K:\RJ 2024-2025',
        r'K:\RJ 2025-2026',
        r'K:\RJ 2026-2027',
    ]
    KDRIVE_SD_DIRS = [
        r'K:\SD 2022',
        r'K:\SD 2023',
        r'K:\SD 2024',
        r'K:\SD 2025',
        r'K:\SD 2026',
    ]
    KDRIVE_HP_DIRS = [
        r'K:\HP 2022-2023',
        r'K:\HP 2023-2024',
        r'K:\HP 2024-2025',
        r'K:\HP 2025-2026',
        r'K:\HP 2026-2027',
    ]
    SYNC_HOUR = int(os.getenv('SYNC_HOUR', '9'))       # 9 AM Canada/Eastern
    SYNC_MINUTE = int(os.getenv('SYNC_MINUTE', '0'))
    SYNC_TIMEZONE = os.getenv('SYNC_TIMEZONE', 'America/Toronto')
    SYNC_LOOKBACK_DAYS = int(os.getenv('SYNC_LOOKBACK_DAYS', '30'))

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
