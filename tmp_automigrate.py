"""Run auto_migrate to sync DB schema with models."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from main import create_app
from seed_db import auto_migrate

app = create_app()
added = auto_migrate(app)
print(f'Columns added: {added}')
