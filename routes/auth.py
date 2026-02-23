"""Legacy auth routes - redirects to auth_v2 for backward compatibility."""
from flask import Blueprint, redirect, url_for

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Redirect to new login system."""
    return redirect(url_for('auth_v2.login'))


@auth_bp.route('/logout')
def logout():
    """Redirect to new logout."""
    return redirect(url_for('auth_v2.logout'))
