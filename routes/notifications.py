"""
Notifications Blueprint — User notification preferences and history.

Routes:
- GET /notifications/ — Notification preferences page
- GET /api/notifications/preferences — Get user preferences (JSON)
- POST /api/notifications/preferences — Save user preferences (JSON)
- GET /api/notifications/history — Recent notification log
- POST /api/notifications/test — Send test email
- POST /api/notifications/trigger/<event_type> — Manually trigger alert
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime, timedelta
from database.models import (
    db, User, NotificationPreference, NotificationLog, NightAuditSession
)
from utils.email_service import EmailService
from utils.alert_engine import AlertEngine
import logging

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

# Initialize services
email_service = EmailService()
alert_engine = AlertEngine()


def login_required(f):
    """Require user to be authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth_v2.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_or_gm_required(f):
    """Require user to be admin or GM."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = session.get('user_role_type', '')
        if user_role not in ('admin', 'gm'):
            return jsonify({'error': 'Accès refusé'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# PAGE ROUTES
# ============================================================================

@notifications_bp.route('/', methods=['GET'])
@login_required
def preferences_page():
    """Render notification preferences page."""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)

        if not user:
            return redirect(url_for('auth_v2.login'))

        # Get all preferences for user
        preferences = NotificationPreference.query.filter_by(user_id=user_id).all()

        # Get recent notification history
        recent_logs = NotificationLog.query.filter_by(
            recipient_user_id=user_id
        ).order_by(NotificationLog.sent_at.desc()).limit(20).all()

        # Create preference dict for template
        pref_dict = {p.event_type: p.to_dict() for p in preferences}

        return render_template(
            'notifications.html',
            user=user,
            preferences=pref_dict,
            recent_logs=recent_logs,
            email_configured=email_service.smtp_enabled
        )
    except Exception as e:
        logger.error(f"Error rendering preferences page: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API ROUTES
# ============================================================================

@notifications_bp.route('/api/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user's notification preferences as JSON."""
    try:
        user_id = session.get('user_id')
        preferences = NotificationPreference.query.filter_by(user_id=user_id).all()

        return jsonify({
            'success': True,
            'preferences': [p.to_dict() for p in preferences]
        })
    except Exception as e:
        logger.error(f"Error fetching preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/preferences', methods=['POST'])
@login_required
def save_preferences():
    """Save user's notification preferences."""
    try:
        user_id = session.get('user_id')
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        for event_type, pref_data in data.items():
            pref = NotificationPreference.query.filter_by(
                user_id=user_id,
                event_type=event_type
            ).first()

            if pref:
                # Update existing
                pref.is_enabled = pref_data.get('is_enabled', True)
                pref.threshold_value = pref_data.get('threshold_value')
                pref.delivery_method = pref_data.get('delivery_method', 'email')
                pref.updated_at = datetime.utcnow()
            else:
                # Create new
                pref = NotificationPreference(
                    user_id=user_id,
                    event_type=event_type,
                    is_enabled=pref_data.get('is_enabled', True),
                    threshold_value=pref_data.get('threshold_value'),
                    delivery_method=pref_data.get('delivery_method', 'email')
                )
                db.session.add(pref)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Préférences sauvegardées'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/history', methods=['GET'])
@login_required
def notification_history():
    """Get user's recent notification history."""
    try:
        user_id = session.get('user_id')
        limit = request.args.get('limit', 50, type=int)
        event_type = request.args.get('event_type', None)

        query = NotificationLog.query.filter_by(recipient_user_id=user_id)

        if event_type:
            query = query.filter_by(event_type=event_type)

        logs = query.order_by(NotificationLog.sent_at.desc()).limit(limit).all()

        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs]
        })
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/test', methods=['POST'])
@login_required
def send_test_email():
    """Send a test email to the logged-in user."""
    try:
        user_id = session.get('user_id')
        user = User.query.get(user_id)

        if not user or not user.email:
            return jsonify({
                'error': 'Utilisateur non trouvé ou email manquant'
            }), 400

        # Render test email template
        test_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'user_name': user.full_name_fr or user.username,
            'severity': 'info',
            'message': 'Ceci est un email de test du système d\'alertes de l\'audit de nuit.'
        }

        subject = f"Test Email - {test_data['date']}"
        html_body = email_service.render_template('alert_generic.html', alert=test_data)

        result = email_service.send_email(user.email, subject, html_body)

        return jsonify({
            'success': result.get('success', False),
            'message': result.get('message', ''),
            'status': result.get('status', 'failed')
        })

    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/trigger/<event_type>', methods=['POST'])
@login_required
@admin_or_gm_required
def trigger_alert(event_type):
    """Manually trigger an alert for testing purposes (admin only)."""
    try:
        data = request.get_json() or {}
        audit_date = data.get('audit_date')

        if not audit_date:
            return jsonify({'error': 'audit_date requis'}), 400

        # Get the session
        session_obj = NightAuditSession.query.filter_by(audit_date=audit_date).first()

        if not session_obj:
            return jsonify({'error': 'Session non trouvée'}), 404

        # Generate alert
        if event_type == 'variance_alert':
            alert = alert_engine.check_variance(session_obj)
        elif event_type == 'occupation_low':
            alert = alert_engine.check_occupation(session_obj)
        elif event_type == 'revenue_drop':
            alert = alert_engine.check_revenue(session_obj)
        elif event_type == 'rj_late':
            alert = alert_engine.check_late_submission(audit_date)
        elif event_type == 'daily_summary':
            alert = {
                'triggered': True,
                'severity': 'info',
                'alert_type': 'daily_summary',
                'data': alert_engine.generate_daily_summary(audit_date)
            }
        else:
            return jsonify({'error': 'Type d\'alerte invalide'}), 400

        # Get recipients
        recipients = alert_engine.get_alert_recipients(event_type)

        if not recipients:
            return jsonify({
                'success': False,
                'message': 'Aucun destinataire trouvé pour ce type d\'alerte',
                'alert_sent': 0
            })

        # Send alerts
        results = email_service.send_alert(event_type, alert.get('data', {}), recipients)

        return jsonify({
            'success': True,
            'message': f"Alerte envoyée à {len(results)} destinataire(s)",
            'alert_sent': len([r for r in results if r.get('success')])
        })

    except Exception as e:
        logger.error(f"Error triggering alert: {str(e)}")
        return jsonify({'error': str(e)}), 500
