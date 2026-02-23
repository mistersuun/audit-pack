"""Role-based access control decorators."""
from functools import wraps
from flask import session, redirect, url_for, abort, jsonify, request
from database.models import User


def login_required(f):
    """Require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Non authentifié'}), 401
            return redirect(url_for('auth_v2.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Restrict route to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('authenticated'):
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Non authentifié'}), 401
                return redirect(url_for('auth_v2.login'))
            user_role = session.get('user_role_type')
            if user_role not in roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Accès non autorisé'}), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """Get current logged-in user from session."""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


# Role visibility config - what each role can see in the sidebar
ROLE_NAV_ITEMS = {
    'night_auditor': ['checklist', 'rj', 'balances', 'reports', 'generators', 'documentation', 'faq'],
    'admin': ['manager', 'direction', 'checklist', 'rj', 'balances', 'reports', 'generators', 'documentation', 'faq', 'crm', 'admin'],
    'gm': ['manager', 'direction', 'reports', 'documentation'],
    'gsm': ['manager', 'direction', 'reports', 'documentation'],
    'front_desk_supervisor': ['checklist', 'reports', 'documentation', 'faq'],
    'accounting': ['reports', 'balances', 'documentation'],
}

ROLE_LABELS_FR = {
    'night_auditor': 'Auditeur de nuit',
    'admin': 'Administrateur',
    'gm': 'Directeur général',
    'gsm': 'Directeur adjoint',
    'front_desk_supervisor': 'Superviseur réception',
    'accounting': 'Comptabilité',
}
