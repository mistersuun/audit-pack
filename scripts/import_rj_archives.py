"""
Import en masse des fichiers RJ Excel historiques dans la base de données.

Usage:
    python -m scripts.import_rj_archives                    # Import depuis RJ 2024-2025/
    python -m scripts.import_rj_archives --dir /path/to/rj  # Dossier personnalisé
    python -m scripts.import_rj_archives --dry-run           # Simuler sans importer

Scanne récursivement les dossiers RJ et importe chaque fichier .xls/.xlsx
dans les tables RJArchive + RJSheetData (avec le binaire original + données parsées).
"""

import os
import sys
import re
from datetime import date

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import create_app
from database import db
from database.models import RJArchive


# ── Date extraction from filename ──────────────────────────────────────

# Patterns: "Rj MM-DD-YYYY", "Rj_MM-DD-YYYY", "Rj DD-MM-YYYY", etc.
DATE_RE = re.compile(r'[Rr][Jj][\s_.-]*(\d{2,4})-(\d{2})-(\d{2,4})')


def extract_date_from_filename(filename):
    """Try to extract audit date from RJ filename.

    Supports: Rj DD-MM-YYYY, Rj MM-DD-YYYY, Rj YYYY-MM-DD
    """
    basename = os.path.basename(filename)
    m = DATE_RE.search(basename)
    if not m:
        return None

    a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))

    candidates = []

    if a >= 2000:
        # YYYY-MM-DD
        candidates.append((a, b, c))
    elif c >= 2000:
        # Could be DD-MM-YYYY or MM-DD-YYYY
        # Try DD-MM-YYYY first (more common in this project)
        candidates.append((c, b, a))  # DD-MM-YYYY → year=c, month=b, day=a
        candidates.append((c, a, b))  # MM-DD-YYYY → year=c, month=a, day=b

    for yyyy, mm, dd in candidates:
        if 1 <= mm <= 12 and 1 <= dd <= 31 and 2000 <= yyyy <= 2030:
            try:
                return date(yyyy, mm, dd)
            except ValueError:
                continue

    return None


def should_skip(filepath):
    """Skip duplicates and non-RJ files."""
    basename = os.path.basename(filepath).lower()
    # Skip copies
    if 'copie de' in basename or 'copie' in basename.split('.')[0].split()[-1:]:
        return True
    # Skip temp files
    if basename.startswith('~') or basename.startswith('.'):
        return True
    return False


def find_rj_files(base_dir):
    """Find all RJ Excel files recursively, sorted by date.

    Handles folder structures:
    - RJ 2024-2025/01-JANVIER/Rj 15-01-2025.xls
    - RJ 2026-2027/01-MARS 2026/Rj 22-03-2026.xls
    - Flat folder with Rj files
    """
    files = []

    # Walk entire tree — handles any nesting depth
    for root, dirs, filenames in os.walk(base_dir):
        for fname in filenames:
            if not (fname.lower().endswith('.xls') or fname.lower().endswith('.xlsx')):
                continue
            filepath = os.path.join(root, fname)
            if should_skip(filepath):
                continue
            audit_date = extract_date_from_filename(fname)
            if audit_date:
                files.append((audit_date, filepath, fname))

    # Sort by date
    files.sort(key=lambda x: x[0])
    return files


def import_archives(base_dir, dry_run=False):
    """Import all RJ files from base_dir into the database."""
    from routes.audit.rj_native import _archive_rj_to_db

    files = find_rj_files(base_dir)
    print(f"\n[SCAN] {len(files)} fichiers RJ trouvés dans {base_dir}")

    if not files:
        print("  Aucun fichier RJ trouvé.")
        return 0

    # Show date range
    print(f"   Période: {files[0][0]} → {files[-1][0]}")

    if dry_run:
        print("\n   Mode simulation (--dry-run) — aucune importation effectuée")
        for audit_date, filepath, fname in files[:10]:
            print(f"   {audit_date} ← {fname}")
        if len(files) > 10:
            print(f"   ... et {len(files) - 10} autres fichiers")
        return len(files)

    imported = 0
    skipped = 0
    errors = 0

    for i, (audit_date, filepath, fname) in enumerate(files):
        # Skip if already archived
        existing = RJArchive.query.filter_by(audit_date=audit_date).first()
        if existing:
            skipped += 1
            continue

        try:
            with open(filepath, 'rb') as f:
                file_bytes = f.read()

            result = _archive_rj_to_db(
                file_bytes=file_bytes,
                audit_date=audit_date,
                source_filename=fname,
                uploaded_by='import_bulk'
            )

            if result and 'error' not in result:
                imported += 1
            else:
                errors += 1
                print(f"  [WARN] {fname}: {result.get('error', 'erreur inconnue')}")

        except Exception as e:
            errors += 1
            print(f"  [WARN] {fname}: {e}")

        # Progress every 50 files
        if (i + 1) % 50 == 0:
            print(f"  ... {i + 1}/{len(files)} traités ({imported} importés, {skipped} existants)")
            db.session.commit()  # Commit in batches

    db.session.commit()
    print(f"\n[OK] Import terminé: {imported} importés, {skipped} déjà existants, {errors} erreurs")
    return imported


def extract_metrics_from_archives():
    """
    Extract DailyJourMetrics from all archived RJ files in RJArchive table.
    This populates the metrics used by all dashboards.
    """
    from utils.jour_importer import JourImporter
    from database.models import DailyJourMetrics
    import io

    archives = RJArchive.query.order_by(RJArchive.audit_date).all()
    if not archives:
        print("  Aucune archive RJ à traiter.")
        return 0

    # Check existing metrics
    existing_dates = {d[0] for d in db.session.query(DailyJourMetrics.date).all()}
    print(f"  {len(archives)} archives, {len(existing_dates)} métriques existantes")

    total_extracted = 0
    errors = 0

    for i, archive in enumerate(archives):
        if not archive.file_binary:
            continue

        try:
            file_bytes = io.BytesIO(archive.file_binary)
            metrics, info = JourImporter.extract_from_rj(file_bytes, archive.source_filename)

            if metrics:
                # Filter out dates we already have
                new_metrics = [m for m in metrics if m.date not in existing_dates]
                if new_metrics:
                    result = JourImporter.persist_batch(new_metrics, source='archive_extract')
                    total_extracted += result.get('inserted', 0) + result.get('updated', 0)
                    for m in new_metrics:
                        existing_dates.add(m.date)

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  [WARN] {archive.source_filename}: {e}")

        if (i + 1) % 100 == 0:
            print(f"  ... {i + 1}/{len(archives)} traités ({total_extracted} métriques extraites)")
            db.session.commit()

    db.session.commit()
    print(f"  [OK] {total_extracted} métriques extraites, {errors} erreurs")
    return total_extracted


def extract_metrics_from_files(base_dir):
    """
    Extract DailyJourMetrics directly from RJ Excel files on disk.
    Fallback when archives don't have binary data.
    """
    from utils.jour_importer import JourImporter
    from database.models import DailyJourMetrics
    import io

    files = find_rj_files(base_dir)
    if not files:
        print("  Aucun fichier RJ trouvé.")
        return 0

    existing_dates = {d[0] for d in db.session.query(DailyJourMetrics.date).all()}
    print(f"  {len(files)} fichiers RJ, {len(existing_dates)} métriques existantes")

    total_extracted = 0
    errors = 0

    for i, (audit_date, filepath, fname) in enumerate(files):
        try:
            with open(filepath, 'rb') as f:
                file_bytes = io.BytesIO(f.read())

            metrics, info = JourImporter.extract_from_rj(file_bytes, fname)
            if metrics:
                new_metrics = [m for m in metrics if m.date not in existing_dates]
                if new_metrics:
                    result = JourImporter.persist_batch(new_metrics, source='file_extract')
                    total_extracted += result.get('inserted', 0) + result.get('updated', 0)
                    for m in new_metrics:
                        existing_dates.add(m.date)

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  [WARN] {fname}: {e}")

        if (i + 1) % 100 == 0:
            print(f"  ... {i + 1}/{len(files)} traités ({total_extracted} métriques)")
            db.session.commit()

    db.session.commit()
    print(f"  [OK] {total_extracted} métriques extraites depuis fichiers, {errors} erreurs")
    return total_extracted


def main():
    dry_run = '--dry-run' in sys.argv
    metrics_only = '--metrics-only' in sys.argv
    custom_dir = None

    for i, arg in enumerate(sys.argv):
        if arg == '--dir' and i + 1 < len(sys.argv):
            custom_dir = sys.argv[i + 1]

    # Default: look for RJ folder in project root
    project_root = os.path.join(os.path.dirname(__file__), '..')
    base_dir = custom_dir or os.path.join(project_root, 'RJ 2024-2025')

    app = create_app()
    with app.app_context():
        if not metrics_only:
            if not os.path.exists(base_dir):
                print(f"[WARN] Dossier non trouvé: {base_dir}")
                print("  Utilisez --dir /chemin/vers/dossier/rj pour spécifier le dossier")
            else:
                import_archives(base_dir, dry_run=dry_run)

        # Always extract metrics (from archives in DB or from files)
        if not dry_run:
            print("\n[SYNC] Extraction des métriques DailyJourMetrics...")
            total = extract_metrics_from_archives()
            if total == 0 and os.path.exists(base_dir):
                print("  Tentative depuis les fichiers sur disque...")
                extract_metrics_from_files(base_dir)


if __name__ == '__main__':
    main()
