"""
Email Service — Handles SMTP configuration and email delivery.

Features:
- Support for Gmail, Office365, custom SMTP
- Graceful fallback: if SMTP not configured, log to console + database
- HTML and text email support
- Template rendering
"""

import smtplib
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import render_template, render_template_string, current_app

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP or logging fallback."""

    def __init__(self, app=None):
        self.app = app
        self.smtp_enabled = False
        self.mail_server = None
        self.mail_port = None
        self.mail_use_tls = False
        self.mail_username = None
        self.mail_password = None
        self.mail_default_sender = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize email service with Flask app config."""
        self.mail_server = app.config.get('MAIL_SERVER', '')
        self.mail_port = app.config.get('MAIL_PORT', 587)
        self.mail_use_tls = app.config.get('MAIL_USE_TLS', True)
        self.mail_username = app.config.get('MAIL_USERNAME', '')
        self.mail_password = app.config.get('MAIL_PASSWORD', '')
        self.mail_default_sender = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@sheraton-laval-audit.com')

        # SMTP is enabled only if server and credentials are provided
        self.smtp_enabled = bool(self.mail_server and self.mail_username and self.mail_password)

        if self.smtp_enabled:
            logger.info(f"Email service initialized with SMTP: {self.mail_server}:{self.mail_port}")
        else:
            logger.warning("Email service initialized WITHOUT SMTP. Emails will be logged to console/database only.")

    def send_email(self, to_email, subject, html_body, text_body=None, from_email=None):
        """
        Send an email via SMTP or log it if SMTP is not configured.

        Args:
            to_email (str): Recipient email address
            subject (str): Email subject line
            html_body (str): HTML email body
            text_body (str, optional): Plain text fallback
            from_email (str, optional): Sender email (defaults to MAIL_DEFAULT_SENDER)

        Returns:
            dict: {success: bool, message: str, status: 'sent'|'logged'|'failed'}
        """
        from_email = from_email or self.mail_default_sender

        if self.smtp_enabled:
            try:
                return self._send_via_smtp(to_email, subject, html_body, text_body, from_email)
            except Exception as e:
                error_msg = f"SMTP delivery failed: {str(e)}"
                logger.error(error_msg)
                # Fall back to logging
                self._log_email(to_email, subject, html_body, 'failed', str(e))
                return {'success': False, 'message': error_msg, 'status': 'failed'}
        else:
            # No SMTP configured, log to console and database
            self._log_email(to_email, subject, html_body, 'logged', None)
            return {'success': True, 'message': 'Email logged (SMTP not configured)', 'status': 'logged'}

    def _send_via_smtp(self, to_email, subject, html_body, text_body, from_email):
        """Send email via SMTP server."""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        if text_body:
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            msg.attach(part1)

        part2 = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(part2)

        with smtplib.SMTP(self.mail_server, self.mail_port) as server:
            if self.mail_use_tls:
                server.starttls()
            server.login(self.mail_username, self.mail_password)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}: {subject}")
        self._log_email(to_email, subject, html_body, 'sent', None)

        return {'success': True, 'message': 'Email sent successfully', 'status': 'sent'}

    def _log_email(self, to_email, subject, html_body, status, error=None):
        """Log email to database for auditing."""
        try:
            from database.models import db, NotificationLog
            log = NotificationLog(
                event_type='email_sent',
                severity='info',
                recipient_email=to_email,
                subject=subject,
                message=html_body[:500],  # Truncate for storage
                delivery_status=status,
                error_message=error,
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log email to database: {str(e)}")

    def render_template(self, template_name, **context):
        """
        Render email template from templates/emails/ directory.

        Args:
            template_name (str): Template filename (e.g., 'rj_submitted.html')
            **context: Template variables

        Returns:
            str: Rendered HTML
        """
        try:
            return render_template(f'emails/{template_name}', **context)
        except Exception as e:
            logger.error(f"Failed to render email template {template_name}: {str(e)}")
            raise

    def send_alert(self, alert_type, data, recipients):
        """
        Send an alert email to one or more recipients.

        Args:
            alert_type (str): Type of alert ('rj_submitted', 'variance_alert', etc.)
            data (dict): Alert data for template rendering
            recipients (list): List of email addresses or User objects

        Returns:
            list: List of send results
        """
        results = []

        for recipient in recipients:
            # Handle User objects
            if hasattr(recipient, 'email'):
                to_email = recipient.email
                user_id = recipient.id
            else:
                to_email = recipient
                user_id = None

            if not to_email:
                logger.warning(f"Recipient has no email address")
                continue

            try:
                subject, html_body = self._get_alert_subject_and_body(alert_type, data)
                result = self.send_email(to_email, subject, html_body)

                # Log to notification log
                try:
                    from database.models import db, NotificationLog
                    log = NotificationLog(
                        event_type=alert_type,
                        severity=data.get('severity', 'info'),
                        recipient_email=to_email,
                        recipient_user_id=user_id,
                        subject=subject,
                        message=html_body[:500],
                        data_json=json.dumps(data),
                        delivery_status=result.get('status', 'pending'),
                        error_message=result.get('message') if not result.get('success') else None,
                    )
                    db.session.add(log)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Failed to log alert: {str(e)}")

                results.append({
                    'email': to_email,
                    'alert_type': alert_type,
                    **result
                })
            except Exception as e:
                logger.error(f"Failed to send alert to {to_email}: {str(e)}")
                results.append({
                    'email': to_email,
                    'alert_type': alert_type,
                    'success': False,
                    'message': str(e),
                    'status': 'failed'
                })

        return results

    def _get_alert_subject_and_body(self, alert_type, data):
        """Get subject and body for an alert type."""
        templates = {
            'rj_submitted': {
                'subject': 'Rapport Journalier soumis - {date}',
                'template': 'rj_submitted.html'
            },
            'variance_alert': {
                'subject': 'Alerte: Variance élevée détectée - {date}',
                'template': 'variance_alert.html'
            },
            'daily_summary': {
                'subject': 'Résumé quotidien de l\'audit de nuit - {date}',
                'template': 'daily_summary.html'
            },
            'rj_late': {
                'subject': 'Alerte: RJ non soumis avant 6h00 - {date}',
                'template': 'alert_generic.html'
            },
            'occupation_low': {
                'subject': 'Alerte: Taux d\'occupation faible - {date}',
                'template': 'alert_generic.html'
            },
            'revenue_drop': {
                'subject': 'Alerte: Baisse de revenu détectée - {date}',
                'template': 'alert_generic.html'
            },
        }

        config = templates.get(alert_type, {
            'subject': 'Notification du système d\'audit - {date}',
            'template': 'alert_generic.html'
        })

        subject = config['subject'].format(date=data.get('date', ''))
        html_body = self.render_template(config['template'], alert=data, subject=subject)

        return subject, html_body
