# Audit Pack - Sheraton Laval Night Audit System

Web-based system for filling and reconciling the nightly RJ (Rapport de Jour) Excel workbook used in hotel financial auditing.

## What It Does

Replaces manual Excel data entry with a structured web interface that:
- Parses uploaded documents (PDFs, Excel files, text reports) to auto-fill sheets
- Validates data and highlights variances in real-time
- Syncs values between sheets via macro equivalents
- Exports a completed .xls workbook ready for submission

## Quick Start

```bash
git clone https://github.com/mistersuun/audit-pack.git
cd audit-pack
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python setup.py     # Initialize database
python main.py      # Start server at http://localhost:5000
```

See [documentation/guides/quickstart.md](documentation/guides/quickstart.md) for details.

## Documentation

All documentation lives in [`documentation/`](documentation/README.md):

| Section | Contents |
|---------|----------|
| [**sheets/**](documentation/sheets/) | Per-sheet reference: fields, formulas, macros, data flow (9 files) |
| [**guides/**](documentation/guides/) | Night audit procedure, installation, quickstart |
| [**dev/**](documentation/dev/) | Parsers, mappers, macros, auth, database, API reference |
| [**architecture.md**](documentation/architecture.md) | Tech stack, file layout, parser pipeline |

## RJ Sheets

| Sheet | UI Tab | Purpose |
|-------|--------|---------|
| controle | Nouveau Jour | Audit date and metadata setup |
| Recap | Recap | Cash reconciliation (balance must = $0) |
| DUBACK# | DueBack | Receptionist cash float tracking |
| SetD | SD | Employee settlement journal (135 personnel) |
| depot | Depot | Bank deposits (CDN + US accounts) |
| transelect | Transelect | Credit card terminal reconciliation |
| geac_ux | GEAC/UX | PMS balance + card variance (must = $0) |
| jour | (computed) | Master daily output (117 columns) |

## Tech Stack

- **Backend:** Python 3 / Flask
- **Frontend:** HTML/JS with lazy-loaded tab fragments
- **Database:** PostgreSQL / SQLAlchemy
- **Excel:** xlrd + xlutils/xlwt (.xls format)
- **Parsers:** pdfplumber, openpyxl, built-in text parsers
