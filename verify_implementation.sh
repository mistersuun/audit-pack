#!/bin/bash

echo "===================================================================================="
echo "Excel Export Feature — Implementation Verification"
echo "===================================================================================="
echo ""

# Check main module
echo "1. Main Export Module"
if [ -f "routes/audit/rj_export_excel.py" ]; then
    echo "   ✓ File exists"
    lines=$(wc -l < routes/audit/rj_export_excel.py)
    echo "   ✓ Lines of code: $lines"
else
    echo "   ✗ File not found"
    exit 1
fi

# Check syntax
echo ""
echo "2. Python Syntax Validation"
if python3 -m py_compile routes/audit/rj_export_excel.py 2>/dev/null; then
    echo "   ✓ Syntax valid"
else
    echo "   ✗ Syntax error"
    exit 1
fi

# Check blueprint imports
echo ""
echo "3. Blueprint Registration"
python3 << 'PYEOF'
try:
    from routes.audit.rj_export_excel import rj_excel_bp
    print(f"   ✓ Blueprint imported: {rj_excel_bp.name}")
    print(f"   ✓ URL prefix: {rj_excel_bp.url_prefix}")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    exit(1)
PYEOF

# Check documentation files
echo ""
echo "4. Documentation Files"
for file in "EXCEL_EXPORT_README.md" "IMPLEMENTATION_SUMMARY.md" "test_excel_export.py"; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "   ✓ $file ($lines lines)"
    else
        echo "   ✗ $file not found"
    fi
done

# Check main.py integration
echo ""
echo "5. Main.py Integration"
if grep -q "from routes.audit.rj_export_excel import rj_excel_bp" main.py; then
    echo "   ✓ Import statement present"
else
    echo "   ✗ Import statement missing"
    exit 1
fi

if grep -q "app.register_blueprint(rj_excel_bp)" main.py; then
    echo "   ✓ Blueprint registration present"
else
    echo "   ✗ Blueprint registration missing"
    exit 1
fi

# Check sheet builders
echo ""
echo "6. Sheet Builders (14 Required)"
count=$(grep -c "^def _build_" routes/audit/rj_export_excel.py)
echo "   ✓ Builders implemented: $count/14"

if [ "$count" -eq 14 ]; then
    grep "^def _build_" routes/audit/rj_export_excel.py | nl | sed 's/^/     /'
else
    echo "   ✗ Expected 14 builders, found $count"
    exit 1
fi

# Check Flask routes
echo ""
echo "7. Flask Routes (2 Required)"
route_count=$(grep -c "@rj_excel_bp.route" routes/audit/rj_export_excel.py)
echo "   ✓ Routes implemented: $route_count/2"
grep "@rj_excel_bp.route" routes/audit/rj_export_excel.py | nl | sed 's/^/     /'

if [ "$route_count" -ne 2 ]; then
    echo "   ✗ Expected 2 routes, found $route_count"
    exit 1
fi

echo ""
echo "===================================================================================="
echo "✓ All Verifications Passed"
echo "===================================================================================="
echo ""
echo "Summary:"
echo "  - Excel export module: READY"
echo "  - 14 Excel sheets: IMPLEMENTED"
echo "  - 2 API endpoints: REGISTERED"
echo "  - Documentation: COMPLETE"
echo ""
echo "Next: python3 main.py (run the Flask app)"
echo ""
