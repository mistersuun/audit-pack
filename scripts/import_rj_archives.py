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
DATE_PATTERNS = [
    # MM-DD-YYYY (most common: "Rj 09-14-2025.xls")
    re.compile(r'[Rr][Jj][\s_.-]*(\d{2})-(\d{2})-(\d{4})'),
    # YYYY-MM-DD
    re.compile(r'[Rr][Jj][\s_.-]*(\d{4})-(\d{2})-(\d{2})'),
]


def extract_date_from_filename(filename):
    """Try to extract audit date from RJ filename."""
    basename = os.path.basename(filename)

    # Pattern 1: Rj MM-DD-YYYY
    m = DATE_PATTERNS[0].search(basename)
    if m:
        mm, dd, yyyy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mm <= 12 and 1 <= dd <= 31 and 2000 <= yyyy <= 2030:
            try:
                return date(yyyy, mm, dd)
            except ValueError:
                pass

    # Pattern 2: Rj YYYY-MM-DD
    m = DATE_PATTERNS[1].search(basename)
    if m:
        yyyy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            try:
                return date(yyyy, mm, dd)
            except ValueError:
                pass

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
    """Find all RJ Excel files recursively, sorted by date."""
    files = []
    rj_dirs = []

    # Look for RJ year folders
    for item in os.listdir(base_dir):
        full = os.path.join(base_dir, item)
        if os.path.isdir(full) and item.startswith('RJ '):
            rj_dirs.append(full)

    if not rj_dirs:
        # Try base_dir itself
        rj_dirs = [base_dir]

    for rj_dir in rj_dirs:
        for root, dirs, filenames in os.walk(rj_dir):
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
    print(f"\n📁 {len(files)} fichiers RJ trouvés dans {base_dir}")

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
                print(f"  ⚠ {fname}: {result.get('error', 'erreur inconnue')}")

        except Exception as e:
            errors += 1
            print(f"  ⚠ {fname}: {e}")

        # Progress every 50 files
        if (i + 1) % 50 == 0:
            print(f"  ... {i + 1}/{len(files)} traités ({imported} importés, {skipped} existants)")
            db.session.commit()  # Commit in batches

    db.session.commit()
    print(f"\n✅ Import terminé: {imported} importés, {skipped} déjà existants, {errors} erreurs")
    return imported


def main():
    dry_run = '--dry-run' in sys.argv
    custom_dir = None

    for i, arg in enumerate(sys.argv):
        if arg == '--dir' and i + 1 < len(sys.argv):
            custom_dir = sys.argv[i + 1]

    # Default: look for RJ folder in project root
    project_root = os.path.join(os.path.dirname(__file__), '..')
    base_dir = custom_dir or os.path.join(project_root, 'RJ 2024-2025')

    if not os.path.exists(base_dir):
        print(f"❌ Dossier non trouvé: {base_dir}")
        print("   Utilisez --dir /chemin/vers/dossier/rj pour spécifier le dossier")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        import_archives(base_dir, dry_run=dry_run)


if __name__ == '__main__':
    main()
