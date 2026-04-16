# Système de notifications - Audit de nuit Sheraton Laval

## Vue d'ensemble

Un système complet de notifications et d'alertes pour la webapp d'audit de nuit. Les utilisateurs (GM, GSM, comptabilité) peuvent configurer leurs préférences d'alerte et recevoir des notifications par email sur les événements critiques.

## Architecture

### Composants principaux

1. **Email Service** (`utils/email_service.py`)
   - Gère l'envoi des emails via SMTP
   - Support pour Gmail, Office365, SMTP personnalisé
   - Fallback gracieux: si SMTP non configuré, enregistrement en BD
   - Template rendering HTML/texte

2. **Alert Engine** (`utils/alert_engine.py`)
   - Évalue les conditions d'audit contre les seuils
   - Vérifications disponibles:
     - Variance Quasimodo
     - Taux d'occupation
     - Baisse de revenu
     - Soumission tardive du RJ
   - Génération de résumés quotidiens

3. **Routes de notification** (`routes/notifications.py`)
   - API pour gérer les préférences utilisateur
   - Page de configuration des alertes
   - Historique des notifications
   - Email de test

4. **Modèles de base de données**
   - `NotificationPreference` - Préférences par utilisateur/événement
   - `NotificationLog` - Journal complet des notifications

5. **Templates email** (`templates/emails/`)
   - `base_email.html` - Template de base avec branding
   - `alert_generic.html` - Alerte générique
   - `rj_submitted.html` - Confirmation de soumission RJ
   - `variance_alert.html` - Alerte variance Quasimodo
   - `daily_summary.html` - Résumé quotidien 7h00

## Types d'événements

### 1. `rj_submitted` - RJ soumis
- **Déclenché par**: Soumission manuelle du RJ par l'auditeur
- **Destinataires**: GM, comptabilité, admin
- **Contenu**: Confirmation + résumé KPIs (revenu, occupation, ADR, variance)

### 2. `rj_late` - RJ non soumis avant 6h00
- **Déclenché**: 6h00+ si RJ non soumis
- **Destinataires**: GM, admin
- **Sévérité**: CRITIQUE
- **Contenu**: Rappel urgent de soumission

### 3. `variance_alert` - Variance Quasimodo élevée
- **Déclenché par**: Quasimodo > seuil (défaut: 5.00$)
- **Destinataires**: GM, comptabilité, admin
- **Sévérité**: WARNING ou CRITICAL si > 2× seuil
- **Contenu**: Détails variance + points de vérification

### 4. `occupation_low` - Faible taux d'occupation
- **Déclenché par**: Occupation < seuil (défaut: 60%)
- **Destinataires**: GM, GSM, admin
- **Sévérité**: WARNING
- **Contenu**: Taux réel vs seuil

### 5. `revenue_drop` - Baisse significative revenu
- **Déclenché par**: Revenu < -10% vs année précédente
- **Destinataires**: GM, GSM, admin
- **Sévérité**: WARNING
- **Contenu**: Revenu comparé vs LY

### 6. `daily_summary` - Résumé quotidien
- **Horaire**: Tous les jours à 7h00 (planifié)
- **Destinataires**: GM, GSM, admin
- **Contenu**: KPIs complets + alertes du jour

## Configuration

### 1. Variables d'environnement (.env)

```bash
# SMTP Configuration
MAIL_SERVER=smtp.gmail.com              # Serveur SMTP
MAIL_PORT=587                           # Port (587 TLS, 465 SSL)
MAIL_USE_TLS=true                       # Utiliser TLS
MAIL_USERNAME=your-email@gmail.com      # Username SMTP
MAIL_PASSWORD=your-app-password         # App password (NOT regular password)
MAIL_DEFAULT_SENDER=noreply@sheraton-laval-audit.com

# Seuils d'alerte
ALERT_VARIANCE_THRESHOLD=5.00           # $ pour Quasimodo
ALERT_OCCUPATION_MIN=60.0               # % minimum
ALERT_SUBMISSION_DEADLINE=06:00         # HH:MM
```

### 2. Gmail SMTP Setup

Pour configurer Google Workspace/Gmail:

1. Activer 2FA sur le compte Gmail
2. Générer un "App Password" (16 caractères)
3. Utiliser dans MAIL_PASSWORD (ne PAS utiliser le mot de passe Google)

```
Gmail SMTP:
  Server: smtp.gmail.com
  Port: 587
  TLS: true
  Username: your-email@gmail.com
  Password: xxxx xxxx xxxx xxxx (app password)
```

### 3. Office365/Outlook

```
Outlook SMTP:
  Server: smtp-mail.outlook.com
  Port: 587
  TLS: true
  Username: your-email@company.com
  Password: your-password
```

### 4. Initialiser les préférences utilisateur

Après créer des utilisateurs dans la base de données, initialiser leurs préférences:

```bash
python init_notifications.py
```

Cela crée des préférences par défaut pour chaque utilisateur selon son rôle.

## Utilisation

### Interface utilisateur

Accès: **Support > Notifications** (visible pour admin/GM seulement)

Features:
- ✅ Activer/désactiver chaque type d'alerte
- ✅ Configurer les seuils (variance, occupation, etc.)
- ✅ Choisir canal de livraison (email, in-app, les deux)
- ✅ Envoyer email de test
- ✅ Consulter historique des notifications

### API

```bash
# Récupérer préférences
GET /notifications/api/preferences

# Sauvegarder préférences
POST /notifications/api/preferences
{
  "variance_alert": {
    "is_enabled": true,
    "threshold_value": 7.50,
    "delivery_method": "email"
  },
  "occupation_low": {
    "is_enabled": true,
    "threshold_value": 55.0,
    "delivery_method": "both"
  }
}

# Historique
GET /notifications/api/history?limit=50&event_type=variance_alert

# Email de test
POST /notifications/api/test

# Déclencher alerte manuelle (admin/GM seulement)
POST /notifications/api/trigger/variance_alert
{
  "audit_date": "2026-02-25"
}
```

### Intégration avec RJ Natif

Pour déclencher une alerte RJ_submitted après soumission:

```python
from utils.email_service import EmailService
from utils.alert_engine import AlertEngine

email_service = EmailService()
alert_engine = AlertEngine()

# Après soumission du RJ
alert_data = {
    'date': session.audit_date.isoformat(),
    'auditor': session.auditor_name,
    'severity': 'info',
    'status': 'submitted',
    'summary': {
        'revenue': session.jour_revenu_total,
        'occupancy_rate': session.occupancy_rate,
        'adr': session.jour_adr,
        'variance': session.quasi_variance,
    }
}

recipients = alert_engine.get_alert_recipients('rj_submitted')
results = email_service.send_alert('rj_submitted', alert_data, recipients)
```

## Enregistrement et audit

Toutes les notifications sont enregistrées dans `NotificationLog`:
- Date/heure d'envoi
- Type d'événement et sévérité
- Email destinataire
- Statut (sent, failed, logged)
- Message d'erreur (le cas échéant)

### Requêtes SQL utiles

```sql
-- Notifications envoyées aujourd'hui
SELECT * FROM notification_logs
WHERE DATE(sent_at) = CURDATE()
ORDER BY sent_at DESC;

-- Emails échoués
SELECT * FROM notification_logs
WHERE delivery_status = 'failed'
ORDER BY sent_at DESC;

-- Préférences d'un utilisateur
SELECT * FROM notification_preferences
WHERE user_id = 1;

-- Alertes variance > 10$ (30 derniers jours)
SELECT * FROM notification_logs
WHERE event_type = 'variance_alert'
AND sent_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
AND data_json LIKE '%"variance": [^0-9]?[1-9][0-9]%';
```

## Fallback sans SMTP

Si SMTP n'est pas configuré:
1. Les emails sont enregistrés dans `NotificationLog` avec status `logged`
2. Un message est imprimé dans les logs console
3. Aucun email réel n'est envoyé
4. Parfait pour développement/test

```python
# Logs console
[2026-02-25 07:15:23] Email logged (SMTP not configured)
  To: gm@sheraton.com
  Subject: Rapport Journalier soumis - 2026-02-25
```

## Tests

### Test manuel via UI

1. Aller à **Support > Notifications**
2. Cliquer **Envoyer un email de test**
3. Vérifier que l'email arrive (ou que le fallback s'affiche)

### Test API

```bash
# Déclencher alerte variance pour test
curl -X POST http://localhost:5000/notifications/api/trigger/variance_alert \
  -H "Content-Type: application/json" \
  -d '{"audit_date": "2026-02-25"}'
```

### Test code

```python
from utils.email_service import EmailService
from utils.alert_engine import AlertEngine

email = EmailService()
engine = AlertEngine()

# Test variance check
session = NightAuditSession.query.first()
alert = engine.check_variance(session)
print(f"Alert triggered: {alert['triggered']}")
print(f"Severity: {alert['severity']}")
```

## Tâches planifiées (futures)

Ces fonctionnalités nécessitent Celery ou APScheduler:

1. **Alerte RJ tardif** - Vérifier à 6h00 si RJ soumis
2. **Résumé quotidien** - Envoyer à 7h00 chaque matin
3. **Rapport hebdo** - Synthèse weekly le lundi 8h00

Exemple avec APScheduler:

```python
from apscheduler.schedulers.background import BackgroundScheduler

def check_rj_late():
    from datetime import date
    engine = AlertEngine()
    alert = engine.check_late_submission(date.today())
    if alert['triggered']:
        # Send alert
        pass

scheduler = BackgroundScheduler()
scheduler.add_job(check_rj_late, 'cron', hour=6, minute=0)
scheduler.start()
```

## Dépannage

### Les emails ne s'envoient pas

1. **Vérifier SMTP_ENABLED**:
   ```python
   from utils.email_service import EmailService
   from flask import current_app

   email = EmailService(current_app)
   print(f"SMTP enabled: {email.smtp_enabled}")
   ```

2. **Vérifier les logs**:
   ```bash
   # Requête au journal
   SELECT * FROM notification_logs
   WHERE event_type = 'email_sent'
   AND delivery_status IN ('failed', 'logged')
   ORDER BY sent_at DESC LIMIT 10;
   ```

3. **Test SMTP credentials**:
   ```python
   import smtplib
   try:
       server = smtplib.SMTP('smtp.gmail.com', 587)
       server.starttls()
       server.login('your-email@gmail.com', 'app-password')
       print("SMTP connection OK")
   except Exception as e:
       print(f"SMTP Error: {e}")
   ```

### Les préférences ne sauvegardent pas

1. Vérifier que l'utilisateur est connecté (session valide)
2. Vérifier les logs de la requête POST
3. S'assurer que user_id est dans la session

### Les emails arrivent en spam

1. Ajouter l'adresse d'expédition à Contacts
2. Vérifier les en-têtes Reply-To dans les templates
3. Implémenter SPF/DKIM/DMARC pour le domaine (infrastructure)

## Structure des fichiers

```
routes/
  notifications.py                      # Routes des préférences et API

utils/
  email_service.py                      # Service SMTP + fallback
  alert_engine.py                       # Logique de vérification alerte

database/
  models.py                             # NotificationPreference + NotificationLog

templates/
  notifications.html                    # Page de configuration UI
  emails/
    base_email.html                     # Template base
    alert_generic.html                  # Alerte générique
    rj_submitted.html                   # Confirmation RJ
    variance_alert.html                 # Alerte variance
    daily_summary.html                  # Résumé quotidien

init_notifications.py                   # Script initialisation
```

## Considérations de sécurité

1. **Données sensibles**: Les adresses email ne contiennent pas de PII autre que l'email
2. **CSRF**: Toutes les requêtes POST utilisent les tokens CSRF
3. **Authentification**: Accès restreint aux rôles admin/GM
4. **Pas de mots de passe en logs**: Les erreurs SMTP ne divulguent pas de credentials

## Performance

- Auto-save des préférences: debounce 500ms côté client
- Interrogations de base de données optimisées (indexes sur user_id, event_type)
- Templates rendus en cache (Jinja2)
- Logs de notification archivés après 90 jours (à implémenter)

## Futures améliorations

- [ ] Intégration Slack/Teams
- [ ] SMS pour alertes critiques
- [ ] Webhooks personnalisés
- [ ] Template HTML en markdown
- [ ] Groupage d'alertes (digest quotidien)
- [ ] Interface de configuration admin par event
- [ ] Analytics sur engagement (ouvrir email, cliquer)
- [ ] Retry automatique des emails échoués
