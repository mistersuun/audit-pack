# Guide d'intégration - Système de notifications

## Ajouter une alerte lors de la soumission du RJ

Ce guide montre comment intégrer le système de notifications dans les routes RJ Natif.

### 1. Dans `routes/audit/rj_native.py`

Ajouter à la soumission du RJ:

```python
from utils.email_service import EmailService
from utils.alert_engine import AlertEngine

# À l'intérieur du route handler pour la soumission
@rj_native_bp.route('/submit/<date>', methods=['POST'])
@login_required
def submit_rj(date):
    """Soumit une session RJ et déclenche les alertes."""

    # ... validation et sauvegarde existante ...

    # Après la sauvegarde réussie
    session = NightAuditSession.query.filter_by(audit_date=audit_date).first()
    session.status = 'submitted'
    db.session.commit()

    # Déclencher l'alerte RJ_submitted
    try:
        email_service = EmailService()
        alert_engine = AlertEngine()

        alert_data = {
            'date': session.audit_date.isoformat(),
            'auditor': session.auditor_name,
            'submitted_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'severity': 'info',
            'status': 'submitted',
            'summary': {
                'revenue': float(session.jour_revenu_total or 0),
                'occupancy_rate': float(session.occupancy_rate or 0),
                'adr': float(session.jour_adr or 0),
                'variance': float(session.quasi_variance or 0),
            }
        }

        recipients = alert_engine.get_alert_recipients('rj_submitted')
        email_service.send_alert('rj_submitted', alert_data, recipients)

    except Exception as e:
        # Ne pas bloquer la soumission si l'alerte échoue
        logger.error(f"Failed to send RJ submitted alert: {str(e)}")

    return jsonify({'success': True, 'message': 'RJ soumis'})
```

### 2. Déclencher alerte Variance

Après recalcul Quasimodo:

```python
@rj_native_bp.route('/api/save/quasimodo', methods=['POST'])
@login_required
def save_quasimodo():
    """Sauvegarde Quasimodo et alerte si variance > seuil."""

    # ... sauvegarde existante ...

    # Vérifier la variance
    alert_engine = AlertEngine()
    variance_alert = alert_engine.check_variance(session)

    if variance_alert['triggered']:
        try:
            email_service = EmailService()
            recipients = alert_engine.get_alert_recipients('variance_alert')
            email_service.send_alert('variance_alert', variance_alert['data'], recipients)
        except Exception as e:
            logger.error(f"Failed to send variance alert: {str(e)}")

    return jsonify({'success': True})
```

### 3. Vérifier occupation

Après mise à jour Jour:

```python
@rj_native_bp.route('/api/save/jour', methods=['POST'])
@login_required
def save_jour():
    """Sauvegarde jour et alerte si occupation faible."""

    # ... sauvegarde existante ...

    # Vérifier occupation
    alert_engine = AlertEngine()
    occ_alert = alert_engine.check_occupation(session)

    if occ_alert['triggered']:
        try:
            email_service = EmailService()
            recipients = alert_engine.get_alert_recipients('occupation_low')
            email_service.send_alert('occupation_low', occ_alert['data'], recipients)
        except Exception as e:
            logger.error(f"Failed to send occupation alert: {str(e)}")

    return jsonify({'success': True})
```

## Ajouter une alerte personnalisée

### Exemple: Alerte si dépôt manquant

```python
# Dans alert_engine.py, ajouter une nouvelle méthode:

def check_deposit_missing(self, session_data):
    """Vérifier si le dépôt a été enregistré."""
    try:
        if isinstance(session_data, NightAuditSession):
            deposit_cdn = float(session_data.deposit_cdn or 0)
            deposit_us = float(session_data.deposit_us or 0)
            audit_date = session_data.audit_date
        else:
            deposit_cdn = float(session_data.get('deposit_cdn', 0))
            deposit_us = float(session_data.get('deposit_us', 0))
            audit_date = session_data.get('audit_date')

        total_deposit = deposit_cdn + deposit_us
        triggered = total_deposit == 0

        return {
            'triggered': triggered,
            'severity': self.SEVERITY_WARNING if triggered else self.SEVERITY_INFO,
            'alert_type': 'deposit_missing',
            'message': f"Dépôt: ${total_deposit:.2f}" if total_deposit > 0 else "Aucun dépôt enregistré",
            'data': {
                'date': str(audit_date),
                'deposit_cdn': deposit_cdn,
                'deposit_us': deposit_us,
                'total_deposit': total_deposit,
            }
        }
    except Exception as e:
        logger.error(f"Error checking deposit: {str(e)}")
        return {
            'triggered': False,
            'severity': self.SEVERITY_INFO,
            'message': f"Erreur: {str(e)}",
            'data': {}
        }
```

## Ajouter une tâche planifiée (Celery)

### Configuration Celery

```python
# Dans main.py
from celery import Celery

def create_app():
    app = Flask(__name__)
    # ... configuration existante ...

    # Setup Celery
    celery = Celery(app.import_name)
    celery.conf.update(app.config)

    # Task class to tie in app context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return app, celery

app, celery = create_app()
```

### Ajouter une tâche quotidienne

```python
# Dans routes/notifications.py ou un nouveau fichier tasks.py

from celery import shared_task
from celery.schedules import crontab
from datetime import date

@shared_task
def send_daily_summary():
    """Envoyer résumé quotidien à 7h00."""
    from utils.email_service import EmailService
    from utils.alert_engine import AlertEngine

    email_service = EmailService()
    alert_engine = AlertEngine()

    # Générer résumé d'aujourd'hui
    summary = alert_engine.generate_daily_summary(date.today())

    # Envoyer à tous les recipients
    recipients = alert_engine.get_alert_recipients('daily_summary')
    if recipients:
        email_service.send_alert('daily_summary', summary, recipients)

# Configuration du cron job
app.conf.beat_schedule = {
    'send-daily-summary': {
        'task': 'routes.notifications.send_daily_summary',
        'schedule': crontab(hour=7, minute=0),
    },
}
```

### Lancer Celery

```bash
# Terminal 1: Celery Worker
celery -A main.celery worker --loglevel=info

# Terminal 2: Celery Beat (scheduler)
celery -A main.celery beat --loglevel=info
```

## Ajouter une alerte par SMS (Twilio)

### Installation

```bash
pip install twilio
```

### Configuration .env

```bash
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Étendre EmailService

```python
# Dans utils/email_service.py

class EmailService:
    # ... existing code ...

    def send_sms(self, phone, message):
        """Envoyer SMS via Twilio."""
        try:
            from twilio.rest import Client
            from flask import current_app

            client = Client(
                current_app.config['TWILIO_ACCOUNT_SID'],
                current_app.config['TWILIO_AUTH_TOKEN']
            )

            msg = client.messages.create(
                body=message,
                from_=current_app.config['TWILIO_PHONE_NUMBER'],
                to=phone
            )

            logger.info(f"SMS sent to {phone}: {msg.sid}")
            return {'success': True, 'status': 'sent'}

        except Exception as e:
            logger.error(f"SMS send failed: {str(e)}")
            return {'success': False, 'status': 'failed', 'error': str(e)}
```

### Utiliser dans une alerte critique

```python
# Quand variance > 2× seuil, envoyer SMS au GM

if alert['severity'] == 'critical':
    gm = User.query.filter_by(role='gm').first()
    if gm and gm.phone:
        email_service.send_sms(
            gm.phone,
            f"🚨 Alerte critique: Variance ${alert['data']['variance']:.2f}"
        )
```

## Template email personnalisé

Créer un nouveau template:

```html
<!-- templates/emails/custom_alert.html -->
{% extends "emails/base_email.html" %}

{% block body %}
<h2 style="margin-top: 0; color: #1e40af;">Mon alerte personnalisée</h2>

<p>{{ alert.custom_message }}</p>

<div class="kpi-item">
    <div class="kpi-label">Métrique personnalisée</div>
    <div class="kpi-value">{{ alert.custom_value }}</div>
</div>
{% endblock %}
```

Puis l'utiliser:

```python
# Dans email_service.py, ajouter à _get_alert_subject_and_body()

'custom_alert': {
    'subject': 'Alerte personnalisée - {date}',
    'template': 'custom_alert.html'
}
```

## Logging avancé

### Générer rapport de notifications

```python
# Script pour générer rapport

from database.models import NotificationLog
from datetime import datetime, timedelta

def report_notifications(days=7):
    """Rapport des notifications des 7 derniers jours."""

    since = datetime.utcnow() - timedelta(days=days)
    logs = NotificationLog.query.filter(
        NotificationLog.sent_at >= since
    ).all()

    report = {
        'period': f"Derniers {days} jours",
        'total': len(logs),
        'by_type': {},
        'by_status': {},
    }

    for log in logs:
        # Count by type
        if log.event_type not in report['by_type']:
            report['by_type'][log.event_type] = 0
        report['by_type'][log.event_type] += 1

        # Count by status
        if log.delivery_status not in report['by_status']:
            report['by_status'][log.delivery_status] = 0
        report['by_status'][log.delivery_status] += 1

    return report

# Afficher rapport
report = report_notifications()
print(f"Total: {report['total']} notifications")
print("Par type:", report['by_type'])
print("Par statut:", report['by_status'])
```

## Webhooks externes

Intégrer avec des systèmes externes (Slack, Teams, etc):

```python
# Dans utils/email_service.py

def send_to_webhook(self, webhook_url, alert_data):
    """Envoyer alerte à un webhook externe."""
    import requests

    try:
        response = requests.post(
            webhook_url,
            json=alert_data,
            timeout=5
        )
        response.raise_for_status()
        return {'success': True, 'status': 'sent'}
    except Exception as e:
        logger.error(f"Webhook delivery failed: {str(e)}")
        return {'success': False, 'status': 'failed', 'error': str(e)}
```

Utiliser avec Slack:

```python
# Envoyer variance alert à Slack
alert_data = {
    'type': 'variance_alert',
    'severity': 'critical',
    'message': 'Variance Quasimodo élevée',
    'data': {...}
}

slack_webhook = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
email_service.send_to_webhook(slack_webhook, alert_data)
```

## Conclusion

Le système de notifications est flexible et extensible. Vous pouvez:
- Ajouter de nouveaux types d'événements
- Créer des templates email personnalisés
- Intégrer des canaux de communication externes
- Mettre en œuvre des alertes conditionnelles complexes
- Automatiser des tâches via des planificateurs de tâches

Pour plus de détails, voir `NOTIFICATIONS_README.md`.
