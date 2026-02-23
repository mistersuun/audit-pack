# Audit Routes Package

This package contains modular blueprints for RJ (Revenue Journal) and SD (Sommaire Journalier) file management.

## Structure

```
audit/
├── __init__.py           Master blueprint that registers all sub-blueprints
├── rj_core.py           Core RJ file operations (upload, download, read, preview)
├── rj_fill.py           Sheet filling and DueBack data entry
├── rj_macros.py         Reset, sync, and macro operations
├── rj_sd.py             Sommaire Journalier (SD) file operations
├── rj_quasimodo.py      Auto card reconciliation
└── rj_parsers.py        Document parsing and auto-fill
```

## Usage

The master `audit_bp` blueprint is automatically registered by `__init__.py` and handles all registration of sub-blueprints:

```python
# In main.py
from routes.audit import audit_bp
app.register_blueprint(audit_bp)
```

## Shared State

File storage is session-based:

- **RJ_FILES**: Dictionary storing uploaded RJ files, keyed by session_id
- **SD_FILES**: Dictionary storing uploaded SD files, keyed by session_id

Both are defined in `rj_core.py` and imported by dependent modules.

```python
from .rj_core import RJ_FILES, SD_FILES
```

## Module Breakdown

### rj_core.py
Core RJ file operations:
- Upload RJ files
- Download RJ files
- Check upload status
- Read RJ data (all sheets or specific sheets)
- Live preview of Excel data

Key functions:
- `upload_rj()`: Handle file uploads
- `download_rj()`: Generate downloadable file
- `read_rj()`: Read all data
- `read_rj_sheet()`: Read specific sheet
- `preview_rj()`: Live preview

### rj_fill.py
Sheet filling and DueBack operations:
- Fill specific sheets (Recap, Transelect, GEAC, Controle)
- Fill DueBack sheet
- Get DueBack data (names, totals, column B)
- Bulk DueBack operations
- Update controle sheet
- Update deposit sheet

Key functions:
- `fill_rj_sheet()`: Fill sheet with data
- `fill_dueback()`: Fill DueBack day
- `save_dueback_simple()`: Save simplified DueBack workflow
- `update_controle()`: Update audit day
- `update_deposit()`: Update deposit tab

### rj_macros.py
Reset, sync, and macro operations:
- Reset all tabs or specific sheet
- Sync DueBack to SetD
- Execute envoie-jour macro (Recap to jour)
- Execute calcul-carte macro (card totals to jour)
- Send Recap to jour

Key functions:
- `reset_rj_tabs()`: Clear all tabs
- `reset_single_sheet()`: Clear specific sheet
- `sync_duback_setd()`: Sync DueBack amounts
- `macro_envoie_dans_jour()`: Copy Recap
- `macro_calcul_carte()`: Calculate cards
- `send_recap_to_jour()`: Send summary

### rj_sd.py
Sommaire Journalier (SD) file operations:
- Upload SD files
- Read daily entries
- Get daily totals
- Write daily entries
- Download SD files
- Export SD variances to SetD

Key functions:
- `upload_sd()`: Upload SD file
- `get_sd_day()`: Get day entries
- `get_sd_day_totals()`: Get day totals
- `write_sd_day_entries()`: Write entries
- `export_sd_to_setd()`: Export to SetD

### rj_quasimodo.py
Auto card reconciliation:
- Auto-calculate from RJ data (transelect + geac_ux)
- Manual reconciliation from provided data

Key functions:
- `quasimodo_reconcile()`: Auto-calculate
- `quasimodo_manual()`: Manual calculation

### rj_parsers.py
Document parsing and auto-fill:
- Parse uploaded documents
- Parse and auto-fill RJ sheets
- Get available parser types

Key functions:
- `parse_document()`: Parse document
- `parse_and_fill()`: Parse and fill RJ
- `get_parser_types()`: Get available types

## Security

All routes are protected by the `@login_required` decorator imported from `routes.checklist`.

## Error Handling

All endpoints return JSON responses with:
- `success`: Boolean indicating success
- `error`: Error message if failed
- `data`: Response data if successful

Standard error codes:
- 400: Bad request (missing params, validation error)
- 404: Not found (file not uploaded)
- 500: Server error

## Session Management

File storage uses Flask session_id:
```python
session_id = session.get('user_session_id', 'default')
RJ_FILES[session_id] = file_bytes
```

This ensures each user session has isolated file storage.
