"""Shared fixtures for all tests."""

import os
import sys
import io
import pytest

# Fix corrupted http.server on this system
sys.path.insert(0, '/tmp/http_fix')

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# ── Test RJ file paths ──────────────────────────────────────────
RJ_DIR = os.path.join(PROJECT_ROOT, 'RJ 2024-2025', 'RJ 2025-2026', '12-Février 2026')
RJ_07_PATH = os.path.join(RJ_DIR, 'Rj 07-02-2026.xls')
RJ_08_PATH = os.path.join(RJ_DIR, 'Rj 08-02-2026.xls')
RJ_VIERGE_PATH = os.path.join(RJ_DIR, 'Rj Vierge.xls')

DAILY_REV_PDF = os.path.join(PROJECT_ROOT, 'test_data', 'Daily_Rev_4th_Feb.pdf')
SALES_JOURNAL_RTF = os.path.join(PROJECT_ROOT, 'test_data', 'Sales_Journal_4th_Feb.rtf')
AR_SUMMARY_PDF = os.path.join(PROJECT_ROOT, 'test_data', 'AR_SUMMARY_DOCUMENT_4th.pdf')


@pytest.fixture
def rj07_bytes():
    """Raw bytes of Rj 07-02-2026.xls"""
    if not os.path.exists(RJ_07_PATH):
        pytest.skip("Rj 07 file not available")
    with open(RJ_07_PATH, 'rb') as f:
        return f.read()


@pytest.fixture
def rj08_bytes():
    """Raw bytes of Rj 08-02-2026.xls"""
    if not os.path.exists(RJ_08_PATH):
        pytest.skip("Rj 08 file not available")
    with open(RJ_08_PATH, 'rb') as f:
        return f.read()


@pytest.fixture
def app():
    """Flask test application."""
    os.environ.setdefault('AUDIT_PIN', '9337')
    from main import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Flask test client with auth."""
    with app.app_context():
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess['authenticated'] = True
                sess['user_id'] = 1
            yield c


@pytest.fixture
def fresh_db(app):
    """Ensure clean DB state for session tests."""
    from database.models import db, NightAuditSession
    with app.app_context():
        # Remove test sessions
        for d in ['2026-02-08', '2026-02-09', '2026-02-10']:
            NightAuditSession.query.filter_by(audit_date=d).delete()
        db.session.commit()
        yield db
        # Cleanup
        for d in ['2026-02-08', '2026-02-09', '2026-02-10']:
            NightAuditSession.query.filter_by(audit_date=d).delete()
        db.session.commit()
