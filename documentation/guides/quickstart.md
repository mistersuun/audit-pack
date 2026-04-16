# Quick Start -- Running in 10 Minutes

## 1. Clone and install (3 minutes)

```bash
git clone <repository-url> audit-pack
cd audit-pack
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure (1 minute)

```bash
cp env.example .env
```

Edit `.env` and set at minimum:

```
SECRET_KEY=any-random-string
AUDIT_PIN=1234
```

## 3. Initialize the database (1 minute)

```bash
python setup.py
```

## 4. Start the app (30 seconds)

```bash
python main.py
```

Open `http://localhost:5000` in your browser. Enter the PIN you set.

## 5. Run your first audit (5 minutes)

1. Click **New Audit** and confirm today's date.
2. Upload your source files (ZIP or individual Excel/PDF files).
3. The app parses and dispatches data to the correct tabs automatically.
4. Work through each tab in order: DueBack, SD, Recap, Depot, Transelect, GEAC, Jour.
5. Green checkmarks appear as each section balances.
6. Export the completed RJ when all sections are green.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "ModuleNotFoundError" | Activate the venv: `source venv/bin/activate` |
| Port 5000 in use | `FLASK_RUN_PORT=5001 python main.py` |
| Excel parse errors | Check file is `.xls` (not renamed `.xlsx`) |

## Next Steps

- Full setup details: [installation.md](installation.md)
- Night audit walkthrough: [night_audit_procedure.md](night_audit_procedure.md)
