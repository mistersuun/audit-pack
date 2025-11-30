from flask import Blueprint, render_template, request, redirect, url_for, session, current_app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        pin = request.form.get('pin', '')
        if pin == current_app.config['AUDIT_PIN']:
            session['authenticated'] = True
            return redirect(url_for('checklist.index'))
        else:
            error = 'PIN incorrect'
    return render_template('login.html', error=error)

@auth_bp.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('auth.login'))
