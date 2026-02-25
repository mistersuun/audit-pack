"""
Initialize notification preferences for all users.

This script creates default notification preferences for all existing users
and all available event types.

Usage:
    python init_notifications.py
"""

from main import create_app
from database.models import db, User, NotificationPreference
from datetime import datetime

# Default preferences for each event type
DEFAULT_PREFERENCES = {
    'rj_submitted': {
        'roles': ['gm', 'accounting', 'admin'],
        'is_enabled': True,
        'threshold_value': None,
        'delivery_method': 'email',
    },
    'rj_late': {
        'roles': ['gm', 'admin'],
        'is_enabled': True,
        'threshold_value': None,
        'delivery_method': 'email',
    },
    'variance_alert': {
        'roles': ['gm', 'accounting', 'admin'],
        'is_enabled': True,
        'threshold_value': 5.00,
        'delivery_method': 'email',
    },
    'occupation_low': {
        'roles': ['gm', 'gsm', 'admin'],
        'is_enabled': True,
        'threshold_value': 60.0,
        'delivery_method': 'email',
    },
    'revenue_drop': {
        'roles': ['gm', 'gsm', 'admin'],
        'is_enabled': True,
        'threshold_value': None,
        'delivery_method': 'email',
    },
    'daily_summary': {
        'roles': ['gm', 'gsm', 'admin'],
        'is_enabled': True,
        'threshold_value': None,
        'delivery_method': 'email',
    },
}


def init_preferences():
    """Initialize notification preferences for all users."""
    app = create_app()

    with app.app_context():
        # Get all users
        users = User.query.all()
        created = 0
        skipped = 0

        for user in users:
            for event_type, config in DEFAULT_PREFERENCES.items():
                # Only create preference if user role is in the allowed list
                if user.role not in config['roles']:
                    continue

                # Check if preference already exists
                existing = NotificationPreference.query.filter_by(
                    user_id=user.id,
                    event_type=event_type
                ).first()

                if existing:
                    print(f"⏭️  Skipped {user.username} - {event_type} (already exists)")
                    skipped += 1
                    continue

                # Create preference
                pref = NotificationPreference(
                    user_id=user.id,
                    event_type=event_type,
                    is_enabled=config['is_enabled'],
                    threshold_value=config['threshold_value'],
                    delivery_method=config['delivery_method'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.session.add(pref)
                print(f"✅ Created {user.username} - {event_type}")
                created += 1

        # Commit all changes
        db.session.commit()

        print(f"\n{'='*60}")
        print(f"Initialization complete!")
        print(f"  Created: {created} preferences")
        print(f"  Skipped: {skipped} (already exist)")
        print(f"{'='*60}")


if __name__ == '__main__':
    print("Initializing notification preferences...")
    print()
    init_preferences()
