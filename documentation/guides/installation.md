# Installation Guide

## Prerequisites

- **Python 3.8+** (3.11 recommended)
- **pip** package manager
- **Git** (to clone the repository)

No separate database server is required -- audit-pack uses SQLite by default.

---

## 1. Clone the Repository

```bash
git clone <repository-url> audit-pack
cd audit-pack
```

## 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Verify the key packages installed:

```bash
python -c "import flask; import openpyxl; import xlrd; print('OK')"
```

## 4. Configure Environment Variables

Copy the example file and edit it:

```bash
cp env.example .env
```

Edit `.env` with your values:

```
SECRET_KEY=generate-a-random-string-here
AUDIT_PIN=1234
OPENWEATHER_API_KEY=your-key        # optional
LIGHTSPEED_ENABLED=false            # set true only if you have API credentials
```

At minimum, set `SECRET_KEY` and `AUDIT_PIN`.

## 5. Initialize the Database

```bash
python setup.py
```

This creates the SQLite database and seeds initial data.

## 6. Run the Application

```bash
python main.py
```

The app starts on `http://localhost:5000`. Open it in your browser and enter your audit PIN.

---

## Common Issues

### "ModuleNotFoundError: No module named 'flask'"
You are not inside the virtual environment. Run `source venv/bin/activate` first.

### "Address already in use" on port 5000
Another process is using port 5000. Either stop it or run on a different port:
```bash
FLASK_RUN_PORT=5001 python main.py
```

### Excel import errors (xlrd / openpyxl)
- `.xls` files require `xlrd` (included in requirements).
- `.xlsx` files require `openpyxl` (included in requirements).
- If you get "Unsupported format" errors, check the file extension matches the actual format.

### Permission denied on Linux/macOS
```bash
chmod +x main.py setup.py
python3 main.py
```

### Python version too old
Check your version with `python3 --version`. If below 3.8, install a newer version from https://www.python.org/downloads/ or via your system package manager.
