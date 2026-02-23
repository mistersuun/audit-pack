# Enregistrement Automatique des Impressions

## Question
L'utilisateur souhaite enregistrer automatiquement les rapports imprimés depuis l'ordinateur lors de l'audit de nuit.

## Options Possibles

### Option 1: Surveillance du Dossier d'Impression (Recommandé)
**Fonctionnement:**
- Surveiller le dossier où les imprimantes sauvegardent les fichiers PDF temporaires
- Sur macOS: `~/Library/Printers/` ou `/private/var/spool/cups/`
- Sur Windows: `C:\Windows\System32\spool\PRINTERS\`

**Avantages:**
- Relativement simple à implémenter
- Fonctionne avec toutes les imprimantes
- Pas besoin de permissions système spéciales

**Inconvénients:**
- Les fichiers peuvent être supprimés rapidement
- Nécessite de surveiller plusieurs dossiers possibles
- Peut capturer des impressions non liées à l'audit

**Implémentation:**
```python
import os
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PrintFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.pdf') or event.src_path.endswith('.ps'):
            # Copier le fichier vers un dossier d'archive
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            dest = f'/path/to/audit_prints/{timestamp}_{os.path.basename(event.src_path)}'
            shutil.copy2(event.src_path, dest)
            print(f"Impression enregistrée: {dest}")

observer = Observer()
observer.schedule(PrintFileHandler(), '/path/to/print/spool', recursive=False)
observer.start()
```

### Option 2: Hook d'Impression via CUPS (macOS/Linux)
**Fonctionnement:**
- Utiliser les filtres CUPS pour intercepter les jobs d'impression
- Créer un script qui copie automatiquement les fichiers avant impression

**Avantages:**
- Capture toutes les impressions
- Peut extraire des métadonnées (nom du document, date, etc.)

**Inconvénients:**
- Nécessite des permissions root/admin
- Plus complexe à configurer
- Spécifique à CUPS (macOS/Linux)

**Implémentation:**
- Créer un filtre CUPS personnalisé dans `/etc/cups/filters/`
- Le filtre copie le fichier avant de l'envoyer à l'imprimante

### Option 3: API d'Impression Windows (Windows uniquement)
**Fonnement:**
- Utiliser l'API Windows Print Spooler
- Surveiller les jobs d'impression via `win32print`

**Avantages:**
- Intégration native Windows
- Peut capturer les métadonnées complètes

**Inconvénients:**
- Windows uniquement
- Nécessite des permissions administrateur

**Implémentation:**
```python
import win32print
import win32api

def monitor_print_jobs():
    printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
    for printer in printers:
        # Surveiller les jobs d'impression
        # Enregistrer les fichiers
        pass
```

### Option 4: Extension Navigateur (Pour impressions web)
**Fonctionnement:**
- Créer une extension Chrome/Firefox qui intercepte les impressions
- Enregistrer automatiquement les PDF générés

**Avantages:**
- Simple pour les impressions depuis le navigateur
- Pas besoin de permissions système

**Inconvénients:**
- Ne fonctionne que pour les impressions web
- Nécessite l'installation d'une extension

### Option 5: Script Python avec Watchdog (Solution Recommandée)
**Fonctionnement:**
- Utiliser la bibliothèque `watchdog` pour surveiller les dossiers d'impression
- Enregistrer automatiquement les fichiers dans un dossier d'archive avec métadonnées

**Avantages:**
- Cross-platform (macOS, Windows, Linux)
- Facile à intégrer dans l'application Flask
- Peut être lancé comme service en arrière-plan

**Implémentation Complète:**

```python
# utils/print_monitor.py
import os
import shutil
import time
import json
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AuditPrintHandler(FileSystemEventHandler):
    def __init__(self, archive_dir):
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        # Attendre que le fichier soit complètement écrit
        time.sleep(1)
        
        src_path = Path(event.src_path)
        
        # Filtrer les fichiers d'impression
        if src_path.suffix.lower() in ['.pdf', '.ps', '.prn']:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{src_path.name}"
            dest_path = self.archive_dir / filename
            
            try:
                shutil.copy2(src_path, dest_path)
                
                # Enregistrer les métadonnées
                metadata = {
                    'original_path': str(src_path),
                    'archived_path': str(dest_path),
                    'timestamp': datetime.now().isoformat(),
                    'size': src_path.stat().st_size
                }
                
                metadata_path = dest_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                print(f"✅ Impression enregistrée: {dest_path}")
            except Exception as e:
                print(f"❌ Erreur lors de l'enregistrement: {e}")

def start_print_monitor(archive_dir='./audit_prints'):
    """Démarrer le moniteur d'impressions"""
    # Dossiers à surveiller selon l'OS
    if os.name == 'nt':  # Windows
        watch_dirs = [
            Path(os.environ.get('TEMP', 'C:/Windows/Temp')),
            Path('C:/Windows/System32/spool/PRINTERS')
        ]
    else:  # macOS/Linux
        watch_dirs = [
            Path.home() / 'Library' / 'Printers',
            Path('/private/var/spool/cups'),
            Path('/var/spool/cups')
        ]
    
    handler = AuditPrintHandler(archive_dir)
    observer = Observer()
    
    for watch_dir in watch_dirs:
        if watch_dir.exists():
            observer.schedule(handler, str(watch_dir), recursive=True)
            print(f"👀 Surveillance de: {watch_dir}")
    
    observer.start()
    return observer
```

**Intégration dans Flask:**

```python
# routes/print_monitor.py
from flask import Blueprint, jsonify, send_file
from utils.print_monitor import start_print_monitor
import threading

print_monitor_bp = Blueprint('print_monitor', __name__)

# Démarrer le moniteur au démarrage de l'app
observer = None

@print_monitor_bp.before_app_first_request
def init_print_monitor():
    global observer
    if observer is None:
        observer = start_print_monitor()
        print("📄 Moniteur d'impressions démarré")

@print_monitor_bp.route('/api/prints/list')
def list_prints():
    """Lister toutes les impressions enregistrées"""
    archive_dir = Path('./audit_prints')
    prints = []
    for file in archive_dir.glob('*.pdf'):
        metadata_file = file.with_suffix('.json')
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                prints.append(metadata)
    return jsonify({'prints': prints})
```

## Recommandation

**Option 5 (Script Python avec Watchdog)** est la meilleure solution car:
1. ✅ Cross-platform
2. ✅ Facile à intégrer
3. ✅ Peut être lancé comme service
4. ✅ Capture automatique avec métadonnées
5. ✅ Pas besoin de permissions root

## Prochaines Étapes

1. Installer la dépendance: `pip install watchdog`
2. Créer le module `utils/print_monitor.py`
3. Intégrer dans l'application Flask
4. Créer une interface web pour visualiser les impressions enregistrées
5. Ajouter une option pour filtrer par date/nom de document

## Notes Importantes

- ⚠️ Certains systèmes peuvent supprimer rapidement les fichiers temporaires d'impression
- ⚠️ Il faudra peut-être configurer l'imprimante pour sauvegarder les fichiers PDF
- ⚠️ Sur macOS, il peut être nécessaire d'activer l'option "PDF" dans les préférences d'impression
- ⚠️ Les impressions depuis des applications spécifiques (Lightspeed, etc.) peuvent nécessiter une configuration spéciale


