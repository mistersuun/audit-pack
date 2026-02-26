#!/usr/bin/env python3
"""
Sheraton Laval Night Audit WebApp — Setup complet (cross-platform)

Usage:
    python setup.py            # Setup complet (venv + deps + DB + données démo)
    python setup.py --quick    # Setup minimal (venv + deps + DB users/tasks seulement)
    python setup.py --reset    # Remet la DB à zéro puis re-seed tout
    python setup.py --no-venv  # Skip la création du venv (utile en CI)
    python setup.py --run      # Lancer le serveur automatiquement après le setup

Ce script:
  1. Vérifie Python 3.8+
  2. Crée un environnement virtuel (si pas déjà fait)
  3. Installe les dépendances via pip
  4. Crée le fichier .env (si manquant)
  5. Initialise la base de données + seed les données
  6. (optionnel) Lance le serveur
"""

import os
import sys
import subprocess
import secrets
import shutil
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════
# Couleurs (cross-platform)
# ══════════════════════════════════════════════════════════════════════════

if sys.platform == 'win32':
    # Activer ANSI sur Windows 10+
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        HAS_COLOR = True
    except Exception:
        HAS_COLOR = False
else:
    HAS_COLOR = True


def c(color_code, text):
    """Coloriser du texte si le terminal supporte les couleurs."""
    if not HAS_COLOR:
        return text
    colors = {
        'red': '\033[0;31m', 'green': '\033[0;32m', 'yellow': '\033[1;33m',
        'blue': '\033[0;34m', 'cyan': '\033[0;36m', 'bold': '\033[1m',
        'nc': '\033[0m',
    }
    return f"{colors.get(color_code, '')}{text}{colors['nc']}"


def ok(msg):
    print(f"  {c('green', '✓')} {msg}")

def warn(msg):
    print(f"  {c('yellow', '→')} {msg}")

def fail(msg):
    print(f"  {c('red', '✗')} {msg}")

def step(num, total, msg):
    print(f"\n{c('blue', f'[{num}/{total}]')} {msg}")


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════

ROOT = Path(__file__).parent.resolve()
VENV_DIR = ROOT / 'venv'
DB_PATH = ROOT / 'database' / 'audit.db'
ENV_PATH = ROOT / '.env'
REQUIREMENTS = ROOT / 'requirements.txt'

def get_venv_python():
    """Retourne le chemin vers python dans le venv."""
    if sys.platform == 'win32':
        return str(VENV_DIR / 'Scripts' / 'python.exe')
    return str(VENV_DIR / 'bin' / 'python')

def get_venv_pip():
    """Retourne le chemin vers pip dans le venv."""
    if sys.platform == 'win32':
        return str(VENV_DIR / 'Scripts' / 'pip.exe')
    return str(VENV_DIR / 'bin' / 'pip')

def run(cmd, check=True, capture=False, cwd=None):
    """Exécuter une commande subprocess."""
    kwargs = {
        'check': check,
        'cwd': cwd or str(ROOT),
    }
    if capture:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        kwargs['text'] = True

    if isinstance(cmd, str):
        kwargs['shell'] = True
    return subprocess.run(cmd, **kwargs)


# ══════════════════════════════════════════════════════════════════════════
# Étapes du setup
# ══════════════════════════════════════════════════════════════════════════

def check_python():
    """Vérifier que Python 3.8+ est disponible."""
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        fail(f"Python {v.major}.{v.minor} détecté — version 3.8+ requise.")
        print("  Installez Python 3.8+ depuis https://www.python.org/downloads/")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro} ({sys.executable})")


def setup_venv(skip_venv=False):
    """Créer le venv si nécessaire. Retourne (python_path, pip_path)."""
    if skip_venv:
        warn("Création du venv sautée (--no-venv)")
        pip = shutil.which('pip3') or shutil.which('pip') or 'pip'
        return sys.executable, pip

    if VENV_DIR.exists():
        ok("venv/ existe déjà")
    else:
        print("  Création de venv/...")
        import venv
        venv.create(str(VENV_DIR), with_pip=True)
        ok("venv/ créé")

    py = get_venv_python()
    pip = get_venv_pip()

    if not Path(py).exists():
        fail(f"Python introuvable dans le venv: {py}")
        sys.exit(1)

    ok(f"venv prêt ({py})")
    return py, pip


def install_deps(python_path, pip_path):
    """Installer les dépendances depuis requirements.txt."""
    if not REQUIREMENTS.exists():
        fail("requirements.txt introuvable!")
        sys.exit(1)

    # Upgrade pip
    run([python_path, '-m', 'pip', 'install', '--upgrade', 'pip', '-q'], check=False)

    # Install requirements
    print("  Installation en cours (peut prendre 1-2 minutes)...")
    result = run([python_path, '-m', 'pip', 'install', '-r', str(REQUIREMENTS), '-q'], check=False)

    if result.returncode != 0:
        fail("Erreur lors de l'installation des dépendances.")
        print(f"  Essayez manuellement: {pip_path} install -r requirements.txt")
        sys.exit(1)

    # Vérifier TOUTES les imports critiques (y compris générateurs)
    critical_imports = [
        ('flask', 'Flask (framework web)'),
        ('flask_sqlalchemy', 'Flask-SQLAlchemy (ORM)'),
        ('openpyxl', 'OpenPyXL (Excel .xlsx)'),
        ('xlrd', 'xlrd (Excel .xls lecture)'),
        ('xlwt', 'xlwt (Excel .xls écriture)'),
        ('docx', 'python-docx (Word)'),
        ('reportlab', 'ReportLab (PDF)'),
        ('pdfplumber', 'pdfplumber (PDF extraction)'),
        ('PIL', 'Pillow (images)'),
        ('matplotlib', 'Matplotlib (graphiques)'),
        ('numpy', 'NumPy (calculs)'),
        ('sklearn', 'scikit-learn (prévisions)'),
        ('lxml', 'lxml (XML parsing)'),
        ('dateutil', 'python-dateutil (dates)'),
    ]

    all_ok = True
    for module, label in critical_imports:
        result = run(
            [python_path, '-c', f'import {module}'],
            check=False, capture=True
        )
        if result.returncode != 0:
            fail(f"  {label} — ÉCHEC d'import")
            all_ok = False

    if not all_ok:
        fail("Certaines dépendances n'ont pas pu être importées.")
        warn("Essayez: pip install -r requirements.txt --force-reinstall")
        sys.exit(1)

    ok(f"Toutes les dépendances installées ({len(critical_imports)} vérifiées)")


def setup_env():
    """Créer le fichier .env si manquant."""
    if ENV_PATH.exists():
        ok(".env existe déjà")
        return

    secret_key = secrets.token_hex(32)

    env_content = f"""# ─── Flask Configuration ───────────────────────────────────────────────
SECRET_KEY={secret_key}
AUDIT_PIN=1234

# ─── OpenWeather (optionnel) ───────────────────────────────────────────
# OPENWEATHER_API_KEY=votre-clé-ici

# ─── SMTP Email (optionnel) ────────────────────────────────────────────
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=votre-email@gmail.com
# SMTP_PASSWORD=votre-app-password
# NOTIFICATION_FROM=audit@sheratonlaval.com

# ─── Lightspeed Galaxy PMS (optionnel) ─────────────────────────────────
# LIGHTSPEED_ENABLED=false
# LIGHTSPEED_CLIENT_ID=
# LIGHTSPEED_CLIENT_SECRET=
# LIGHTSPEED_PROPERTY_ID=
"""
    ENV_PATH.write_text(env_content, encoding='utf-8')
    ok(".env créé avec SECRET_KEY aléatoire")
    warn("PIN par défaut: 1234 (changez-le dans .env)")


def setup_database(python_path, quick=False, reset=False):
    """Initialiser et seeder la base de données."""
    # Créer le dossier database
    (ROOT / 'database').mkdir(exist_ok=True)

    # Option --reset
    if reset and DB_PATH.exists():
        warn("Suppression de l'ancienne DB (--reset)...")
        DB_PATH.unlink()

    # Seed
    seed_args = [python_path, str(ROOT / 'seed_db.py')]
    if quick:
        seed_args.append('--quick')

    result = run(seed_args, check=False)
    if result.returncode != 0:
        fail("Erreur lors du seeding de la DB.")
        print("  Essayez manuellement: python seed_db.py")
        sys.exit(1)

    # Migrations (colonnes manquantes sur DB existante)
    migrate_script = ROOT / 'migrate_db.py'
    if migrate_script.exists():
        run([python_path, str(migrate_script)], check=False)


def launch_server(python_path):
    """Lancer le serveur Flask."""
    print(f"\n  {c('green', '→')} Serveur démarré sur {c('bold', 'http://127.0.0.1:5000')}")
    print(f"  {c('yellow', '  Ctrl+C pour arrêter')}\n")
    try:
        run([python_path, str(ROOT / 'main.py')])
    except KeyboardInterrupt:
        print("\n  Serveur arrêté.")


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    quick = '--quick' in args
    reset = '--reset' in args
    skip_venv = '--no-venv' in args
    auto_run = '--run' in args

    total_steps = 6 if not auto_run else 6

    print()
    print(c('cyan', '╔══════════════════════════════════════════════════════╗'))
    print(c('cyan', f'║  {c("bold", "Sheraton Laval — Night Audit WebApp Setup")}          ║'))
    print(c('cyan', '╚══════════════════════════════════════════════════════╝'))

    # 1. Python
    step(1, total_steps, "Vérification de Python...")
    check_python()

    # 2. Venv
    step(2, total_steps, "Environnement virtuel...")
    python_path, pip_path = setup_venv(skip_venv)

    # 3. Dépendances
    step(3, total_steps, "Installation des dépendances...")
    install_deps(python_path, pip_path)

    # 4. .env
    step(4, total_steps, "Configuration (.env)...")
    setup_env()

    # 5. Base de données
    step(5, total_steps, "Initialisation de la base de données...")
    setup_database(python_path, quick=quick, reset=reset)

    # 6. Terminé!
    print()
    print(c('green', '╔══════════════════════════════════════════════════════╗'))
    print(c('green', f'║  {c("bold", "Setup terminé avec succès!")}                           ║'))
    print(c('green', '╚══════════════════════════════════════════════════════╝'))
    print()

    # Commandes pour lancer
    if sys.platform == 'win32':
        activate_cmd = r'venv\Scripts\activate'
    else:
        activate_cmd = 'source venv/bin/activate'

    print(f"  Pour lancer le serveur:")
    print(f"    {c('cyan', activate_cmd)}    {c('yellow', '# si pas déjà activé')}")
    print(f"    {c('cyan', 'python main.py')}")
    print()
    print(f"  Puis ouvrir: {c('bold', 'http://127.0.0.1:5000')}")
    print()

    # Identifiants
    print(f"  {c('bold', 'Identifiants par défaut:')}")
    print(f"  ┌─────────────┬──────────────┬──────────────────────┐")
    print(f"  │ Utilisateur │ Mot de passe │ Rôle                 │")
    print(f"  ├─────────────┼──────────────┼──────────────────────┤")
    print(f"  │ Auditeur    │ audit2026    │ Auditeur de nuit     │")
    print(f"  │ Manager     │ manager2026  │ Directeur général    │")
    print(f"  │ Admin       │ admin2026    │ Administrateur       │")
    print(f"  │ Superviseur │ super2026    │ Superviseur réception│")
    print(f"  └─────────────┴──────────────┴──────────────────────┘")
    print(f"  PIN d'accès: 1234 (défini dans .env)")
    print()

    # Lancer le serveur?
    if auto_run:
        launch_server(python_path)
    else:
        step(6, total_steps, "Lancer le serveur maintenant?")
        try:
            reply = input("  (o/N) ").strip().lower()
            if reply in ('o', 'y', 'oui', 'yes'):
                launch_server(python_path)
        except (EOFError, KeyboardInterrupt):
            print()


if __name__ == '__main__':
    main()
