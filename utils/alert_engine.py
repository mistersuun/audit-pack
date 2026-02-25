"""
Alert Engine — Evaluates audit session data against thresholds and generates alerts.

Features:
- Quasimodo variance checking
- Occupation rate monitoring
- Revenue comparison vs. budget/LY
- Late submission detection
- Daily summary generation
"""

import logging
from datetime import datetime, date as date_type, timedelta
from database.models import NightAuditSession, User, NotificationPreference, DailyReport
from flask import current_app

logger = logging.getLogger(__name__)


class AlertEngine:
    """Engine for checking audit conditions and generating alerts."""

    # Alert severity levels
    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_CRITICAL = 'critical'

    def __init__(self, app=None):
        self.app = app

    def check_all_alerts(self, session_data):
        """
        Run all checks against a NightAuditSession.

        Args:
            session_data: NightAuditSession object or dict

        Returns:
            list: List of alerts (dict with triggered, severity, message, data)
        """
        alerts = []

        alerts.append(self.check_variance(session_data))
        alerts.append(self.check_occupation(session_data))
        alerts.append(self.check_revenue(session_data))

        # Filter out None/non-triggered alerts
        return [a for a in alerts if a and a.get('triggered')]

    def check_variance(self, session_data):
        """
        Check Quasimodo variance against threshold.

        Returns:
            dict: {triggered: bool, severity, message, data}
        """
        try:
            threshold = current_app.config.get('ALERT_VARIANCE_THRESHOLD', 5.00)

            # Extract variance from session
            if isinstance(session_data, NightAuditSession):
                variance = abs(float(session_data.quasi_variance or 0))
                audit_date = session_data.audit_date
            else:
                variance = abs(float(session_data.get('quasi_variance', 0)))
                audit_date = session_data.get('audit_date')

            triggered = variance > threshold

            return {
                'triggered': triggered,
                'severity': self.SEVERITY_CRITICAL if variance > threshold * 2 else self.SEVERITY_WARNING,
                'alert_type': 'variance_alert',
                'message': f"Variance Quasimodo: ${variance:.2f} (seuil: ${threshold:.2f})",
                'data': {
                    'date': str(audit_date),
                    'variance': variance,
                    'threshold': threshold,
                    'exceeded_by': max(0, variance - threshold),
                }
            }
        except Exception as e:
            logger.error(f"Error checking variance: {str(e)}")
            return {
                'triggered': False,
                'severity': self.SEVERITY_INFO,
                'message': f"Erreur lors de la vérification de variance: {str(e)}",
                'data': {}
            }

    def check_occupation(self, session_data):
        """
        Check occupancy rate against minimum threshold.

        Returns:
            dict: {triggered: bool, severity, message, data}
        """
        try:
            min_occupancy = current_app.config.get('ALERT_OCCUPATION_MIN', 60.0)

            # Extract occupancy from session
            if isinstance(session_data, NightAuditSession):
                occupancy = float(session_data.jour_occupancy_rate or 0)
                audit_date = session_data.audit_date
            else:
                occupancy = float(session_data.get('jour_occupancy_rate', 0))
                audit_date = session_data.get('audit_date')

            triggered = occupancy < min_occupancy

            return {
                'triggered': triggered,
                'severity': self.SEVERITY_WARNING if triggered else self.SEVERITY_INFO,
                'alert_type': 'occupation_low',
                'message': f"Taux d'occupation: {occupancy:.1f}% (minimum: {min_occupancy:.1f}%)",
                'data': {
                    'date': str(audit_date),
                    'occupancy_rate': occupancy,
                    'minimum_threshold': min_occupancy,
                    'below_by': max(0, min_occupancy - occupancy),
                }
            }
        except Exception as e:
            logger.error(f"Error checking occupation: {str(e)}")
            return {
                'triggered': False,
                'severity': self.SEVERITY_INFO,
                'message': f"Erreur lors de la vérification d'occupation: {str(e)}",
                'data': {}
            }

    def check_revenue(self, session_data):
        """
        Check revenue against budget/last year.

        Returns:
            dict: {triggered: bool, severity, message, data}
        """
        try:
            # Extract revenue and date from session
            if isinstance(session_data, NightAuditSession):
                revenue = float(session_data.jour_total_revenue or 0)
                audit_date = session_data.audit_date
            else:
                revenue = float(session_data.get('jour_total_revenue', 0))
                audit_date = session_data.get('audit_date')

            # Compare with last year same date
            if audit_date:
                last_year_date = audit_date - timedelta(days=365)
                last_year = DailyReport.query.filter_by(date=last_year_date).first()

                if last_year:
                    ly_revenue = float(last_year.revenue_total or 0)
                    variance = ((revenue - ly_revenue) / ly_revenue * 100) if ly_revenue > 0 else 0

                    triggered = variance < -10  # Alert if 10% below LY

                    return {
                        'triggered': triggered,
                        'severity': self.SEVERITY_WARNING if triggered else self.SEVERITY_INFO,
                        'alert_type': 'revenue_drop',
                        'message': f"Revenu: ${revenue:.2f} ({variance:+.1f}% vs LY)",
                        'data': {
                            'date': str(audit_date),
                            'revenue': revenue,
                            'ly_revenue': ly_revenue,
                            'variance_percent': variance,
                        }
                    }

            # No comparison data available
            return {
                'triggered': False,
                'severity': self.SEVERITY_INFO,
                'alert_type': 'revenue_drop',
                'message': "Pas de données de comparaison disponibles",
                'data': {
                    'date': str(audit_date),
                    'revenue': revenue,
                }
            }

        except Exception as e:
            logger.error(f"Error checking revenue: {str(e)}")
            return {
                'triggered': False,
                'severity': self.SEVERITY_INFO,
                'message': f"Erreur lors de la vérification de revenu: {str(e)}",
                'data': {}
            }

    def check_late_submission(self, audit_date):
        """
        Check if RJ session for date was not submitted by deadline.

        Args:
            audit_date: datetime.date

        Returns:
            dict: {triggered: bool, severity, message, data}
        """
        try:
            session = NightAuditSession.query.filter_by(audit_date=audit_date).first()

            if not session:
                return {
                    'triggered': True,
                    'severity': self.SEVERITY_WARNING,
                    'alert_type': 'rj_late',
                    'message': f"Rapport Journalier non trouvé pour {audit_date}",
                    'data': {'date': str(audit_date)}
                }

            # Check if submitted
            is_submitted = session.status in ('submitted', 'locked')

            if not is_submitted:
                deadline = current_app.config.get('ALERT_SUBMISSION_DEADLINE', '06:00')
                now = datetime.utcnow()

                return {
                    'triggered': True,
                    'severity': self.SEVERITY_CRITICAL,
                    'alert_type': 'rj_late',
                    'message': f"RJ non soumis avant {deadline}",
                    'data': {
                        'date': str(audit_date),
                        'status': session.status,
                        'deadline': deadline,
                        'checked_at': now.isoformat(),
                    }
                }

            return {
                'triggered': False,
                'severity': self.SEVERITY_INFO,
                'alert_type': 'rj_late',
                'message': "RJ soumis à temps",
                'data': {'date': str(audit_date), 'status': session.status}
            }

        except Exception as e:
            logger.error(f"Error checking late submission: {str(e)}")
            return {
                'triggered': False,
                'severity': self.SEVERITY_INFO,
                'message': f"Erreur lors de la vérification de soumission: {str(e)}",
                'data': {}
            }

    def generate_daily_summary(self, audit_date):
        """
        Generate a comprehensive daily summary for morning email to GM.

        Args:
            audit_date: datetime.date

        Returns:
            dict: Summary data for template rendering
        """
        try:
            session = NightAuditSession.query.filter_by(audit_date=audit_date).first()

            if not session:
                return {
                    'date': str(audit_date),
                    'available': False,
                    'message': 'Session non trouvée'
                }

            # Extract KPIs
            summary = {
                'date': str(audit_date),
                'available': True,
                'auditor': session.auditor_name,
                'status': session.status,
                'revenue': {
                    'room': float(session.jour_room_revenue or 0),
                    'fb': float(session.jour_total_fb or 0),
                    'total': float(session.jour_total_revenue or 0),
                },
                'occupancy': {
                    'rate': float(session.jour_occupancy_rate or 0),
                    'rooms_sold': session.jour_rooms_simple + session.jour_rooms_double + session.jour_rooms_suite + session.jour_rooms_comp,
                    'total_available': 252,  # TOTAL_ROOMS from models
                },
                'payments': {
                    'cash': float(session.deposit_cdn or 0),
                    'cards': float(session.quasi_total or 0),
                    'total': float(session.jour_total_revenue or 0),
                },
                'reconciliation': {
                    'quasimodo_variance': float(session.quasi_variance or 0),
                    'dueback_total': float(session.dueback_total or 0),
                },
                'kpis': {
                    'adr': float(session.jour_adr or 0),
                    'revpar': float(session.jour_revpar or 0),
                    'fb_percent': round(float(session.jour_total_fb or 0) / float(session.jour_total_revenue or 1) * 100, 1),
                },
                'alerts': self.check_all_alerts(session),
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating daily summary: {str(e)}")
            return {
                'date': str(audit_date),
                'available': False,
                'message': f"Erreur: {str(e)}"
            }

    def get_alert_recipients(self, alert_type):
        """
        Get list of users who should receive an alert based on role and preferences.

        Args:
            alert_type (str): Type of alert

        Returns:
            list: List of User objects
        """
        try:
            # Default roles for each alert type
            role_map = {
                'rj_submitted': ['gm', 'accounting', 'admin'],
                'rj_late': ['gm', 'admin'],
                'variance_alert': ['gm', 'accounting', 'admin'],
                'occupation_low': ['gm', 'gsm', 'admin'],
                'revenue_drop': ['gm', 'gsm', 'admin'],
                'daily_summary': ['gm', 'gsm', 'admin'],
            }

            roles = role_map.get(alert_type, ['admin'])
            users = User.query.filter(User.role.in_(roles), User.is_active == True).all()

            # Filter by preferences
            eligible = []
            for user in users:
                pref = NotificationPreference.query.filter_by(
                    user_id=user.id,
                    event_type=alert_type
                ).first()

                # Include if no preference set (default), or if preference is enabled
                if not pref or pref.is_enabled:
                    eligible.append(user)

            return eligible

        except Exception as e:
            logger.error(f"Error getting alert recipients: {str(e)}")
            return []
