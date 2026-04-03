"""
Full K: drive sync — imports ALL RJ + HP data into the database.
Populates DailyJourMetrics + HPDepartmentSales for all dashboards.

Usage:
    python _import_rj_data.py          # Full sync (all years)
    python _import_rj_data.py --daily  # Last 30 days only
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from main import create_app

app = create_app()

with app.app_context():
    from utils.sync_engine import SyncEngine
    from database.models import DailyJourMetrics, HPDepartmentSales

    print(f"Before: {DailyJourMetrics.query.count()} RJ metrics, {HPDepartmentSales.query.count()} HP records")

    if '--daily' in sys.argv:
        print("\nMode: daily (last 30 days)")
        result = SyncEngine.daily_sync(app)
    else:
        print("\nMode: full sync (all years)")
        result = SyncEngine.full_sync(app)

    rj = result.get('rj', {})
    hp = result.get('hp', {})

    print(f"\nRJ: {rj.get('imported', 0)} imported, {rj.get('updated', 0)} updated, {rj.get('errors', 0)} errors (from {rj.get('total_files', 0)} files)")
    print(f"HP: {hp.get('imported', 0)} imported, {hp.get('errors', 0)} errors (from {hp.get('total_files', 0)} files)")
    print(f"\nAfter: {DailyJourMetrics.query.count()} RJ metrics, {HPDepartmentSales.query.count()} HP records")
