"""
Lightweight CSRF protection for Flask routes.
Generates a token per session and validates it on POST requests.
"""

import secrets
from functools import wraps
from flask import session, request, jsonify, abort


def get_csrf_token():
    """Get or generate CSRF token for the current session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def csrf_protect(f):
    """
    Decorator to validate CSRF token on POST/PUT/DELETE requests.

    The token can be sent as:
    - Header: X-CSRF-Token
    - JSON body field: _csrf_token
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'DELETE'):
            token = session.get('_csrf_token')

            # Check header first, then JSON body
            sent_token = request.headers.get('X-CSRF-Token', '')
            if not sent_token:
                data = request.get_json(silent=True)
                if data and isinstance(data, dict):
                    sent_token = data.pop('_csrf_token', '')

            if not token or not sent_token or token != sent_token:
                return jsonify({'success': False, 'error': 'CSRF token invalide ou manquant'}), 403

        return f(*args, **kwargs)
    return decorated
