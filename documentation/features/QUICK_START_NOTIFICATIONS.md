# Quick Start - Notifications Sheraton Laval

## 30 secondes pour démarrer

### 1. Copier les fichiers (DÉJÀ FAIT ✅)

Tous les fichiers ont été créés:
- `routes/notifications.py`
- `utils/email_service.py`
- `utils/alert_engine.py`
- `templates/notifications.html`
- `templates/emails/*.html`
- `init_notifications.py`

### 2. Configurer .env (< 1 minute)

```bash
# Ajouter à .env:

# SMTP Gmail (plus simple)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password-16-chars

# Seuils d'alerte
ALERT_VARIANCE_THRESHOLD=5.00
ALERT_OCCUPATION_MIN=60.0
ALERT_SUBMISSION_DEADLINE=06:00
```

**Gmail setup**:
1. Activer 2FA sur Google Account
2. Aller à myaccount.google.com > Security
3. App Passwords > Gmail > Windows/Mac
4. Copier le mot de passe 16 caractères

### 3. Démarrer l'app

```bash
python main.py
```

Tables créées automatiquement ✅

### 4. Initialiser les préférences

```bash
python init_notifications.py
```

Résultat: Chaque utilisateur a ses préférences par rôle ✅

### 5. Tester

1. Se connecter en tant que GM
2. Menu **Support > Notifications**
3. Cliquer **Envoyer un email de test**
4. Vérifier que l'email arrive ✅

## Utilisation courante

### Accéder aux préférences

```
Connecté en tant que GM/Admin
→ Support > Notifications
→ Activer/désactiver alertes
→ Configurer seuils
→ Sauvegarder
```

### Tester une alerte

Via UI:
```
Notifications > "Envoyer un email de test"
```

Via API:
```bash
curl -X POST http://localhost:5000/notifications/api/test \
  -H "X-CSRFToken: $(grep csrf templates/base.html)"
```

### Déclencher une alerte spécifique

```bash
curl -X POST http://localhost:5000/notifications/api/trigger/variance_alert \
  -H "Content-Type: application/json" \
  -d '{"audit_date": "2026-02-25"}'
```

## Architecture en 60 secondes

```
User (GM/Admin)
    ↓
    ├→ Web: Support > Notifications
    │     ↓ (Édite préférences)
    │     → API POST /notifications/api/preferences
    │
    └→ Événement d'audit
          ↓
          → AlertEngine.check_variance()
          → AlertEngine.check_occupation()
          → AlertEngine.get_alert_recipients()
          ↓
          → EmailService.send_alert()
          ↓ (SMTP configuré)
          ├→ Envoyé (email réel)
          └→ Non configuré (logged en BD)
               ↓
               NotificationLog enregistré
```

## Checkliste d'intégration

Pour ajouter une alerte RJ soumis:

```python
# Dans routes/audit/rj_native.py, à la soumission:

from utils.email_service import EmailService
from utils.alert_engine import AlertEngine

# ... code existant ...

# Après session.status = 'submitted'
email_service = EmailService()
alert_engine = AlertEngine()

alert_data = {
    'date': session.audit_date.isoformat(),
    'auditor': session.auditor_name,
    'severity': 'info',
}

recipients = alert_engine.get_alert_recipients('rj_submitted')
email_service.send_alert('rj_submitted', alert_data, recipients)
```

Voir `NOTIFICATIONS_INTEGRATION.md` pour d'autres exemples.

## Configuration type par environnement

### Développement (test sans email)

```bash
# .env
MAIL_SERVER=
MAIL_USERNAME=
MAIL_PASSWORD=
# → Emails loggés en BD seulement
```

### Développement avec Gmail

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=dev@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx
```

### Production avec Office365

```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=audit-bot@company.com
MAIL_PASSWORD=secure-password
MAIL_DEFAULT_SENDER=audit-nuit@sheraton-laval.ca
```

## API endpoints

### Préférences

```
GET  /notifications/api/preferences      # Lire
POST /notifications/api/preferences      # Sauvegarder
```

### Historique

```
GET /notifications/api/history?limit=50&event_type=variance_alert
```

### Test

```
POST /notifications/api/test             # Envoyer test email
```

### Admin

```
POST /notifications/api/trigger/<type>   # Déclencher alerte manuelle
```

## Événements disponibles

```
rj_submitted        → RJ soumis par auditeur
rj_late             → RJ pas soumis avant 6h00
variance_alert      → Quasimodo > seuil
occupation_low      → Occupation < seuil
revenue_drop        → Revenu < -10% vs LY
daily_summary       → Résumé quotidien 7h00
```

## Thresholds par défaut

```
Variance Quasimodo:     $5.00
Occupation minimum:     60.0%
Soumission RJ avant:    06:00
```

Modifiables en `.env` ou dans les préférences utilisateur.

## FAQ rapide

**Q: Les emails ne s'envoient pas**
A: SMTP non configuré → vérifier .env, ou envoyer à `init_notifications.py` et regarder NotificationLog

**Q: Où voir l'historique?**
A: Notifications > Historique, ou requête `SELECT * FROM notification_logs`

**Q: Changer les seuils?**
A:
- Globalement: `.env`
- Par utilisateur: Notifications > page > Configurer seuils

**Q: Ajouter une nouvelle alerte?**
A: Voir `NOTIFICATIONS_INTEGRATION.md`

**Q: Désactiver les emails?**
A: Laisser MAIL_USERNAME/PASSWORD vides dans .env → fallback BD

## Files d'attente (optionnel)

Pour alertes planifiées (6h00, 7h00), installer Celery:

```bash
pip install celery redis
```

Voir `NOTIFICATIONS_INTEGRATION.md` pour setup complet.

## Résumé

✅ Tous les fichiers créés
✅ Configuration .env requise
✅ Base de données automatique
✅ Préférences initialisées
✅ UI accessible Support > Notifications
✅ Fallback sans SMTP
✅ Prêt à intégrer avec RJ Natif

Docs complètes: `NOTIFICATIONS_README.md`, `NOTIFICATIONS_SETUP.md`, `NOTIFICATIONS_INTEGRATION.md`

## Besoin d'aide?

```
1. Lire: NOTIFICATIONS_SETUP.md (Installation détaillée)
2. Intégrer: NOTIFICATIONS_INTEGRATION.md (Ajouter alertes)
3. Référence: NOTIFICATIONS_README.md (Tout ce qu'on peut faire)
4. Code: utils/email_service.py, utils/alert_engine.py (Commenté)
```

Bon courage! 🚀
