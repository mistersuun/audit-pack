"""Multi-user authentication blueprint."""
from flask import (
    Blueprint, render_template, request, redirect, url_for, session,
    current_app, jsonify, flash
)
from datetime import datetime
from database import db
from database.models import User
from utils.auth_decorators import login_required, role_required, get_current_user

auth_v2 = Blueprint('auth_v2', __name__, url_prefix='/auth')


@auth_v2.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with username and password."""
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            error = 'Nom d\'utilisateur et mot de passe requis'
        else:
            user = User.query.filter_by(username=username).first()

            if user is None:
                error = 'Identifiants invalides'
            elif not user.is_active:
                error = 'Compte désactivé'
            elif not user.check_password(password):
                error = 'Identifiants invalides'
            else:
                # Validate role_type matches user's actual role
                role_type = request.form.get('role_type', '')
                AUDITOR_ROLES = {'night_auditor', 'front_desk_supervisor'}
                MANAGER_ROLES = {'admin', 'gm', 'gsm', 'accounting'}

                if role_type == 'auditor' and user.role not in AUDITOR_ROLES:
                    error = 'Acces non autorise pour ce profil'
                elif role_type == 'manager' and user.role not in MANAGER_ROLES:
                    error = 'Acces non autorise pour ce profil'
                else:
                    # Login successful
                    session['authenticated'] = True
                    session['user_id'] = user.id
                    session['user_role_type'] = user.role
                    session['user_role'] = 'back' if user.role == 'night_auditor' else (
                        'front' if user.role == 'front_desk_supervisor' else None
                    )
                    session['user_name'] = user.full_name_fr or user.username
                    session['login_role_type'] = role_type

                    # Update last login
                    user.last_login = datetime.utcnow()
                    db.session.commit()

                    # Check if password needs to be changed
                    if user.must_change_password:
                        return redirect(url_for('auth_v2.change_password'))

                    # Route based on selected role type
                    if role_type == 'manager':
                        return redirect(url_for('direction.direction_page'))
                    return redirect(url_for('checklist.index'))

    return render_template('auth/login.html', error=error)


@auth_v2.route('/logout')
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for('auth_v2.login'))


@auth_v2.route('/profile')
@login_required
def profile():
    """Show user profile and settings."""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_v2.login'))

    return render_template('auth/profile.html', user=user)


@auth_v2.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_v2.login'))

    error = None
    success = False

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate inputs
        if not current_password:
            error = 'Mot de passe actuel requis'
        elif not new_password:
            error = 'Nouveau mot de passe requis'
        elif not confirm_password:
            error = 'Confirmation du mot de passe requise'
        elif len(new_password) < 8:
            error = 'Le mot de passe doit contenir au moins 8 caractères'
        elif new_password != confirm_password:
            error = 'Les mots de passe ne correspondent pas'
        elif not user.check_password(current_password):
            error = 'Mot de passe actuel incorrect'
        else:
            # Update password
            user.set_password(new_password)
            user.must_change_password = False
            db.session.commit()
            success = True
            error = None

    return render_template('auth/change_password.html',
                         user=user, error=error, success=success)


@auth_v2.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    """Admin page to manage users."""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@auth_v2.route('/api/admin/users', methods=['POST'])
@login_required
@role_required('admin')
def api_create_user():
    """Create a new user (admin only)."""
    data = request.get_json()

    # Validate
    if not data.get('username'):
        return jsonify({'error': 'Nom d\'utilisateur requis'}), 400
    if not data.get('password'):
        return jsonify({'error': 'Mot de passe requis'}), 400
    if not data.get('role'):
        return jsonify({'error': 'Rôle requis'}), 400

    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Nom d\'utilisateur déjà utilisé'}), 400

    # Create user
    user = User(
        username=data['username'],
        email=data.get('email'),
        full_name_fr=data.get('full_name_fr'),
        role=data['role'],
        is_active=True,
        must_change_password=True
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True, 'user': user.to_dict()}), 201


@auth_v2.route('/api/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def api_toggle_user(user_id):
    """Activate or deactivate a user (admin only)."""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'message': f'Utilisateur {"activé" if user.is_active else "désactivé"}'
    })
