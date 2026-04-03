"""Syntax-check all files modified during bug-fix session."""
import ast
import sys

files = [
    'utils/alert_engine.py',
    'routes/crm_tabs.py',
    'routes/dashboard.py',
    'routes/crm.py',
]

all_ok = True
for path in files:
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            source = fh.read()
        ast.parse(source)
        print(f'OK  {path}')
    except SyntaxError as exc:
        print(f'ERR {path}: line {exc.lineno} — {exc.msg}')
        all_ok = False

sys.exit(0 if all_ok else 1)
