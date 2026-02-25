"""
Database migration script — adds new columns to existing SQLite DB.

Run this ONCE after updating to a version with new features:
    python migrate_db.py

Safe to run multiple times — skips columns that already exist.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'audit.db')


def migrate():
    if not os.path.exists(DB_PATH):
        print("No database found. Run 'python main.py' first to create it.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── New columns for multi-property support ───────────────────────────
    migrations = [
        ('users', 'default_property_id', 'INTEGER'),
        ('daily_reports', 'property_id', 'INTEGER'),
        ('daily_jour_metrics', 'property_id', 'INTEGER'),
        ('monthly_budget', 'property_id', 'INTEGER'),
        ('night_audit_sessions', 'property_id', 'INTEGER'),
    ]

    print("=== Migration de la base de données ===\n")

    for table, column, col_type in migrations:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            existing = [row[1] for row in cursor.fetchall()]
            if column not in existing:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                print(f"  ✓ Ajouté: {table}.{column}")
            else:
                print(f"  · Existe: {table}.{column}")
        except Exception as e:
            print(f"  ✗ Erreur {table}.{column}: {e}")

    conn.commit()

    # ── Verify new tables exist (created by db.create_all in main.py) ────
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    expected_new = ['properties', 'str_comp_set', 'otb_forecasts',
                    'notification_preferences', 'notification_logs']
    print("\n=== Tables nouvelles ===\n")
    for t in expected_new:
        status = "✓" if t in tables else "✗ (sera créée au démarrage de l'app)"
        print(f"  {status} {t}")

    conn.close()

    print(f"\n=== Total: {len(tables)} tables dans la BD ===")
    print("\nMigration terminée. Lancez 'python main.py' pour démarrer.")


if __name__ == '__main__':
    migrate()
