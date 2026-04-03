"""
K: Drive Sync Engine — Scans RJ/SD/HP folders and updates the database.

Supports:
- Full sync: Import ALL files from ALL year folders (initial load)
- Daily sync: Import only last N days (scheduled 9AM refresh)

Usage:
    from utils.sync_engine import SyncEngine

    # Full sync (all years)
    result = SyncEngine.full_sync()

    # Daily refresh (last 30 days)
    result = SyncEngine.daily_sync(lookback_days=30)

    # Sync status
    status = SyncEngine.get_sync_status()
"""

import os
import io
import re
import logging
from datetime import date, timedelta, datetime
from database.models import db, DailyJourMetrics, HPDepartmentSales

logger = logging.getLogger(__name__)


# ─── File discovery helpers ──────────────────────────────────────────────

DATE_RE = re.compile(r'[Rr][Jj][\s_.-]*(\d{2,4})-(\d{2})-(\d{2,4})')
SD_DATE_RE = re.compile(r'SD\.?\s*(\w+)\s*(\d{4})', re.IGNORECASE)
HP_DATE_RE = re.compile(r'HP\s*(\d{2})\s*(\d{4})', re.IGNORECASE)

MONTH_FR = {
    'janvier': 1, 'fevrier': 2, 'février': 2, 'mars': 3, 'avril': 4,
    'mai': 5, 'juin': 6, 'juillet': 7, 'aout': 8, 'août': 8,
    'septembre': 9, 'octobre': 10, 'novembre': 11, 'decembre': 12, 'décembre': 12,
}


def _extract_rj_date(filename):
    """Extract audit date from RJ filename (DD-MM-YYYY or MM-DD-YYYY)."""
    basename = os.path.basename(filename)
    m = DATE_RE.search(basename)
    if not m:
        return None

    a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
    candidates = []

    if a >= 2000:
        candidates.append((a, b, c))
    elif c >= 2000:
        candidates.append((c, b, a))  # DD-MM-YYYY
        candidates.append((c, a, b))  # MM-DD-YYYY

    for yyyy, mm, dd in candidates:
        if 1 <= mm <= 12 and 1 <= dd <= 31 and 2000 <= yyyy <= 2030:
            try:
                return date(yyyy, mm, dd)
            except ValueError:
                continue
    return None


def _extract_sd_date(filename):
    """Extract month/year from SD filename like 'SD. Mars 2026.xls'."""
    basename = os.path.basename(filename)
    m = SD_DATE_RE.search(basename)
    if not m:
        return None
    month_name = m.group(1).lower().strip()
    year = int(m.group(2))
    month = MONTH_FR.get(month_name)
    if month and 2000 <= year <= 2030:
        return date(year, month, 1)
    return None


def _extract_hp_date(filename):
    """Extract month/year from HP filename like 'HP 03 2026.xlsx'."""
    basename = os.path.basename(filename)
    m = HP_DATE_RE.search(basename)
    if not m:
        return None
    month = int(m.group(1))
    year = int(m.group(2))
    if 1 <= month <= 12 and 2000 <= year <= 2030:
        return date(year, month, 1)
    return None


def _should_skip(filepath):
    """Skip temp files, copies, and monthly summary files."""
    basename = os.path.basename(filepath).lower()
    if basename.startswith('~') or basename.startswith('.'):
        return True
    if 'copie' in basename or 'copy' in basename:
        return True
    if 'vierge' in basename or 'template' in basename:
        return True
    # Skip monthly RJ summary files (e.g., "Rj 03-2026.xls" — only 2 groups)
    if re.match(r'rj[\s_.-]*\d{2}-\d{4}\.xls', basename):
        return True
    return False


def _find_files(dirs, extension_filter=('.xls', '.xlsx'), date_extractor=None):
    """Walk directories and find files with dates."""
    files = []
    for base_dir in dirs:
        if not os.path.exists(base_dir):
            continue
        for root, _, filenames in os.walk(base_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in extension_filter:
                    continue
                filepath = os.path.join(root, fname)
                if _should_skip(filepath):
                    continue
                if date_extractor:
                    file_date = date_extractor(fname)
                    if file_date:
                        files.append((file_date, filepath, fname))
                else:
                    files.append((None, filepath, fname))
    files.sort(key=lambda x: x[0] or date.min)
    return files


class SyncEngine:
    """Orchestrates data sync from K: drive to database."""

    @staticmethod
    def sync_rj(dirs, since_date=None):
        """
        Import RJ files → DailyJourMetrics.

        Args:
            dirs: List of RJ directory paths
            since_date: Only import files on or after this date (None = all)

        Returns:
            dict with imported, updated, errors, total_files
        """
        from utils.jour_importer import JourImporter

        files = _find_files(dirs, ('.xls', '.xlsx'), _extract_rj_date)

        if since_date:
            files = [(d, p, f) for d, p, f in files if d >= since_date]

        logger.info(f"RJ sync: {len(files)} files found")

        imported = 0
        updated = 0
        errors = 0

        for i, (audit_date, filepath, fname) in enumerate(files):
            try:
                with open(filepath, 'rb') as f:
                    file_bytes = io.BytesIO(f.read())

                metrics, info = JourImporter.extract_from_rj(file_bytes, fname)
                if metrics:
                    result = JourImporter.persist_batch(metrics, source='k_drive_sync')
                    imported += result.get('inserted', 0)
                    updated += result.get('updated', 0)

            except Exception as e:
                errors += 1
                if errors <= 10:
                    logger.warning(f"RJ sync error {fname}: {e}")

            if (i + 1) % 50 == 0:
                db.session.commit()

        db.session.commit()
        return {'imported': imported, 'updated': updated, 'errors': errors, 'total_files': len(files)}

    @staticmethod
    def sync_hp(dirs, since_date=None):
        """
        Import HP files → HPDepartmentSales.

        Args:
            dirs: List of HP directory paths
            since_date: Only import files on or after this date (None = all)
        """
        from utils.parsers.hp_excel_parser import HPExcelParser

        files = _find_files(dirs, ('.xls', '.xlsx'), _extract_hp_date)

        if since_date:
            files = [(d, p, f) for d, p, f in files if d >= since_date]

        logger.info(f"HP sync: {len(files)} files found")

        imported = 0
        errors = 0

        for hp_date, filepath, fname in files:
            try:
                # Check if already imported
                existing = HPDepartmentSales.query.filter_by(
                    year=hp_date.year, month=hp_date.month
                ).first()
                if existing:
                    continue

                with open(filepath, 'rb') as f:
                    file_bytes = f.read()

                parser = HPExcelParser(file_bytes, fname)
                if parser.parse():
                    result = parser.get_result()
                    departments = result.get('departments', {})

                    for dept_name, dept_data in departments.items():
                        entry = HPDepartmentSales(
                            year=hp_date.year,
                            month=hp_date.month,
                            department=dept_name,
                            food_sales=dept_data.get('nourriture', 0),
                            beverage_sales=dept_data.get('boisson', 0),
                            beer_sales=dept_data.get('biere', 0),
                            wine_sales=dept_data.get('vin', 0),
                            mineral_sales=dept_data.get('mineraux', 0),
                            tips=dept_data.get('pourboire', 0),
                            total_sales=dept_data.get('total', 0),
                        )
                        db.session.add(entry)

                    db.session.commit()
                    imported += 1

            except Exception as e:
                errors += 1
                if errors <= 10:
                    logger.warning(f"HP sync error {fname}: {e}")
                db.session.rollback()

        return {'imported': imported, 'errors': errors, 'total_files': len(files)}

    @staticmethod
    def full_sync(app=None):
        """
        Full sync: import ALL RJ + HP files from all K: drive year folders.
        Called on first run or manual trigger.
        """
        from config.settings import Config

        ctx = None
        if app:
            ctx = app.app_context()
            ctx.push()

        try:
            results = {}

            logger.info("=== FULL SYNC START ===")

            # RJ sync
            rj_result = SyncEngine.sync_rj(Config.KDRIVE_RJ_DIRS)
            results['rj'] = rj_result
            logger.info(f"RJ: {rj_result['imported']} imported, {rj_result['updated']} updated, {rj_result['errors']} errors")

            # HP sync
            hp_result = SyncEngine.sync_hp(Config.KDRIVE_HP_DIRS)
            results['hp'] = hp_result
            logger.info(f"HP: {hp_result['imported']} imported, {hp_result['errors']} errors")

            results['timestamp'] = datetime.now().isoformat()
            logger.info("=== FULL SYNC COMPLETE ===")

            return results
        finally:
            if ctx:
                ctx.pop()

    @staticmethod
    def daily_sync(app=None, lookback_days=None):
        """
        Daily sync: import only recent files (last N days).
        Scheduled to run at 9 AM Canada/Eastern.
        """
        from config.settings import Config

        if lookback_days is None:
            lookback_days = Config.SYNC_LOOKBACK_DAYS

        since_date = date.today() - timedelta(days=lookback_days)

        ctx = None
        if app:
            ctx = app.app_context()
            ctx.push()

        try:
            results = {}

            logger.info(f"=== DAILY SYNC START (since {since_date}) ===")

            # Only sync from the most recent RJ and HP folders
            recent_rj_dirs = Config.KDRIVE_RJ_DIRS[-2:]  # Last 2 year folders
            recent_hp_dirs = Config.KDRIVE_HP_DIRS[-2:]

            rj_result = SyncEngine.sync_rj(recent_rj_dirs, since_date=since_date)
            results['rj'] = rj_result
            logger.info(f"RJ: {rj_result['imported']} new, {rj_result['updated']} updated")

            hp_result = SyncEngine.sync_hp(recent_hp_dirs, since_date=since_date)
            results['hp'] = hp_result
            logger.info(f"HP: {hp_result['imported']} new")

            # OTB projections — refresh daily forecast from historical data
            otb_result = SyncEngine.refresh_otb_projections()
            results['otb'] = otb_result
            if otb_result.get('created'):
                logger.info(f"OTB: {otb_result['created']} jours generes")
            elif otb_result.get('skipped'):
                logger.info("OTB: skipped -- %s", otb_result.get('reason', ''))

            results['timestamp'] = datetime.now().isoformat()
            results['since_date'] = since_date.isoformat()
            logger.info("=== DAILY SYNC COMPLETE ===")

            return results
        finally:
            if ctx:
                ctx.pop()

    @staticmethod
    def refresh_otb_projections():
        """
        Regenerate OTB projections for today using historical DailyJourMetrics.

        Called as part of the daily sync cycle.  Clears any existing
        auto_forecast rows for today before generating fresh ones.
        """
        from database.models import OTBForecast
        try:
            from routes.compset import generate_otb_projections
        except ImportError:
            logger.warning("OTB: could not import generate_otb_projections")
            return {'skipped': True, 'reason': 'import_error'}

        today = date.today()

        try:
            # Clear today's auto-generated rows so we get a clean snapshot
            OTBForecast.query.filter(
                OTBForecast.snapshot_date == today,
                OTBForecast.source == 'auto_forecast',
            ).delete(synchronize_session='fetch')
            db.session.commit()

            result = generate_otb_projections(today, 90)
            return {
                'created': result['created'],
                'historical_days': result['historical_days_used'],
                'summary': result['summary'],
            }
        except ValueError as e:
            logger.info("OTB generation skipped: %s", e)
            return {'skipped': True, 'reason': str(e)}
        except Exception as e:
            logger.error("OTB generation error: %s", e)
            db.session.rollback()
            return {'skipped': True, 'reason': str(e)}

    @staticmethod
    def get_sync_status():
        """Get current database data status."""
        from sqlalchemy import func

        rj_count = DailyJourMetrics.query.count()
        hp_count = HPDepartmentSales.query.count()

        rj_range = {}
        if rj_count > 0:
            min_date = db.session.query(func.min(DailyJourMetrics.date)).scalar()
            max_date = db.session.query(func.max(DailyJourMetrics.date)).scalar()
            rj_range = {'from': min_date.isoformat(), 'to': max_date.isoformat()}

        return {
            'rj_metrics': rj_count,
            'hp_records': hp_count,
            'rj_date_range': rj_range,
        }
