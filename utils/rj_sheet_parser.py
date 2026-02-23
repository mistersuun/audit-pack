"""
RJ Sheet Parser — Extract structured data from RJSheetData raw JSON.

Parses EJ, salaires, and Budget sheets from archived RJ files and populates
JournalEntry, DailyLaborMetrics, and MonthlyBudget models.
"""
import json
from datetime import datetime
from database import db
from database.models import (
    RJSheetData, RJArchive, JournalEntry, DailyLaborMetrics, MonthlyBudget
)


def parse_ej_sheet(archive: RJArchive) -> list:
    """
    Parse EJ (General Ledger) sheet and return JournalEntry records.

    Headers (row 0): ['A/code gl', 'B/cc1', 'C/cc2', 'D/description 1', 'E/description 2', 'F/source', 'G/MONTANT']

    Data rows: ['075001', 2, None, 'VENTES CHAMBRES', '2026-02-07', 's-ej10', 324232.11]

    Maps to:
    - audit_date: archive.audit_date
    - gl_code: row[0]
    - cost_center_1: row[1] (as float)
    - cost_center_2: row[2]
    - description_1: row[3]
    - description_2: row[4]
    - source: row[5]
    - amount: row[6]
    """
    sheet_data = db.session.query(RJSheetData).filter_by(
        archive_id=archive.id, sheet_name='EJ'
    ).first()

    if not sheet_data or not sheet_data.data_json:
        return []

    try:
        rows = json.loads(sheet_data.data_json)
    except json.JSONDecodeError:
        return []

    if not rows or len(rows) < 2:
        return []

    # Skip header row (row 0)
    entries = []
    for row in rows[1:]:
        if not row or not row[0]:  # Skip empty rows or rows without GL code
            continue

        try:
            gl_code = str(row[0]).strip()
            cost_center_1 = float(row[1]) if row[1] is not None else None
            cost_center_2 = str(row[2]).strip() if row[2] else None
            description_1 = str(row[3]).strip() if row[3] else None
            description_2 = str(row[4]).strip() if row[4] else None
            source = str(row[5]).strip() if row[5] else None
            amount = float(row[6]) if row[6] is not None else 0.0

            # Check if already exists (upsert)
            existing = db.session.query(JournalEntry).filter_by(
                audit_date=archive.audit_date, gl_code=gl_code
            ).first()

            if not existing:
                entry = JournalEntry(
                    audit_date=archive.audit_date,
                    gl_code=gl_code,
                    cost_center_1=cost_center_1,
                    cost_center_2=cost_center_2,
                    description_1=description_1,
                    description_2=description_2,
                    source=source,
                    amount=amount
                )
                db.session.add(entry)
                entries.append(entry)
        except (ValueError, IndexError, TypeError) as e:
            # Log and skip malformed rows
            print(f"  [EJ] Skipping row {row}: {str(e)}")
            continue

    return entries


def parse_salaires_sheet(archive: RJArchive) -> list:
    """
    Parse salaires (labor) sheet and return DailyLaborMetrics records.

    Headers are at row 4: ['Departement', None, None, None, None, 'HRES SUP', 'H ESC', ...]

    Data rows start at row 5 (row 4 is subheader):
    ['RECEPTION', 'RECEPTION', 40, 1059.28, None, None, None, None, 0, 0, 0, 0, 40, 1059.28]

    Maps to:
    - date: archive.audit_date
    - year, month: extracted from audit_date
    - department: row[0] (uppercase)
    - regular_hours: row[2]
    - labor_cost: row[3]

    Note: Salaires structure has multiple department sections with nested employee rows.
    For simplicity, take first/main department value and aggregate hours/cost per department.
    """
    sheet_data = db.session.query(RJSheetData).filter_by(
        archive_id=archive.id, sheet_name='salaires'
    ).first()

    if not sheet_data or not sheet_data.data_json:
        return []

    try:
        rows = json.loads(sheet_data.data_json)
    except json.JSONDecodeError:
        return []

    if not rows or len(rows) < 6:
        return []

    # Data starts at row 5 (row 4 is subheader with "Departement" in first column)
    # Collect by department to aggregate
    dept_data = {}

    for row in rows[5:]:
        if not row or not row[0]:  # Skip empty rows or rows without department
            continue

        try:
            department = str(row[0]).strip().upper() if row[0] else None
            if not department or department == 'NONE':
                continue

            # Extract hours and cost
            # Column indices: [0]=Dept, [1]=SubDept, [2]=hours, [3]=cost, [4-12]=other fields
            regular_hours = float(row[2]) if row[2] is not None else 0.0
            labor_cost = float(row[3]) if row[3] is not None else 0.0

            # Aggregate by department (in case there are multiple rows per dept)
            if department not in dept_data:
                dept_data[department] = {
                    'regular_hours': 0.0,
                    'labor_cost': 0.0,
                    'employees_count': 0
                }

            dept_data[department]['regular_hours'] += regular_hours
            dept_data[department]['labor_cost'] += labor_cost
            dept_data[department]['employees_count'] += 1
        except (ValueError, IndexError, TypeError) as e:
            print(f"  [salaires] Skipping row {row}: {str(e)}")
            continue

    # Create DailyLaborMetrics records
    metrics = []
    for department, data in dept_data.items():
        # Check if already exists
        existing = db.session.query(DailyLaborMetrics).filter_by(
            date=archive.audit_date, department=department
        ).first()

        if not existing:
            metric = DailyLaborMetrics(
                date=archive.audit_date,
                year=archive.audit_date.year,
                month=archive.audit_date.month,
                department=department,
                regular_hours=data['regular_hours'],
                overtime_hours=0.0,  # Not available in sheet
                employees_count=data['employees_count'],
                labor_cost=data['labor_cost'],
                source='rj_sheet_parser'
            )
            db.session.add(metric)
            metrics.append(metric)

    return metrics


def parse_budget_sheet(archive: RJArchive) -> list:
    """
    Parse Budget sheet and return MonthlyBudget records.

    Row 0 and onwards: each row is a revenue category with annual and monthly budget
    ['Chambres', 1311825, None, None, 'BU_VE_CHAMBRE', 327956.25, ...]

    Maps to:
    - year, month: extracted from archive.audit_date
    - room_revenue_budget: value from "Chambres" row
    - fb_revenue_budget: sum of F&B related rows
    - other_revenue_budget: other categories
    - total_revenue_budget: sum
    - labor_cost_budget: if available
    - operating_expense_budget: if available
    - occupancy_budget: if available
    - adr_budget: if available

    For now, we'll do a simple upsert: one Budget record per year/month,
    extracting what we can from the sheet.
    """
    sheet_data = db.session.query(RJSheetData).filter_by(
        archive_id=archive.id, sheet_name='Budget'
    ).first()

    if not sheet_data or not sheet_data.data_json:
        return []

    try:
        rows = json.loads(sheet_data.data_json)
    except json.JSONDecodeError:
        return []

    if not rows:
        return []

    # For MonthlyBudget, we need year/month and totals
    # Budget sheet has rows like ['Chambres', 1311825, ..., 327956.25, ...]
    # We'll aggregate the budget columns

    budget_fields = {
        'room_revenue_budget': 0.0,
        'fb_revenue_budget': 0.0,
        'other_revenue_budget': 0.0,
        'total_revenue_budget': 0.0,
        'labor_cost_budget': 0.0,
        'operating_expense_budget': 0.0,
        'occupancy_budget': 0.0,
        'adr_budget': 0.0
    }

    # Simple heuristic: first column is category, second column is annual budget
    for row in rows:
        if not row or not row[0]:
            continue

        category = str(row[0]).strip().lower()

        # Try to extract annual budget (column 1)
        annual_budget = 0.0
        if len(row) > 1 and row[1] is not None:
            try:
                annual_budget = float(row[1])
            except (ValueError, TypeError):
                pass

        # Try to extract monthly budget (column 5, roughly)
        monthly_budget = 0.0
        if len(row) > 5 and row[5] is not None:
            try:
                monthly_budget = float(row[5])
            except (ValueError, TypeError):
                pass

        # Categorize based on keyword
        if 'chambre' in category or 'room' in category:
            budget_fields['room_revenue_budget'] += monthly_budget if monthly_budget else annual_budget / 12
        elif 'nour' in category or 'bar' in category or 'banquet' in category or 'piazza' in category:
            budget_fields['fb_revenue_budget'] += monthly_budget if monthly_budget else annual_budget / 12
        else:
            budget_fields['other_revenue_budget'] += monthly_budget if monthly_budget else annual_budget / 12

    budget_fields['total_revenue_budget'] = (
        budget_fields['room_revenue_budget'] +
        budget_fields['fb_revenue_budget'] +
        budget_fields['other_revenue_budget']
    )

    # Check if already exists (upsert)
    year = archive.audit_date.year
    month = archive.audit_date.month

    existing = db.session.query(MonthlyBudget).filter_by(
        year=year, month=month
    ).first()

    records = []
    if not existing:
        budget = MonthlyBudget(
            year=year,
            month=month,
            room_revenue_budget=budget_fields['room_revenue_budget'],
            fb_revenue_budget=budget_fields['fb_revenue_budget'],
            other_revenue_budget=budget_fields['other_revenue_budget'],
            total_revenue_budget=budget_fields['total_revenue_budget'],
            labor_cost_budget=budget_fields['labor_cost_budget'],
            operating_expense_budget=budget_fields['operating_expense_budget'],
            occupancy_budget=budget_fields['occupancy_budget'],
            adr_budget=budget_fields['adr_budget'],
            source='rj_sheet_parser'
        )
        db.session.add(budget)
        records.append(budget)

    return records


def parse_all_sheets_for_archive(archive: RJArchive) -> dict:
    """
    Parse all relevant sheets for a single archive and populate models.
    Returns summary dict.
    """
    summary = {
        'archive_id': archive.id,
        'audit_date': archive.audit_date.isoformat(),
        'journal_entries': 0,
        'daily_labor_metrics': 0,
        'monthly_budgets': 0,
        'errors': []
    }

    try:
        ej_entries = parse_ej_sheet(archive)
        summary['journal_entries'] = len(ej_entries)
    except Exception as e:
        summary['errors'].append(f"EJ sheet error: {str(e)}")

    try:
        labor_metrics = parse_salaires_sheet(archive)
        summary['daily_labor_metrics'] = len(labor_metrics)
    except Exception as e:
        summary['errors'].append(f"Salaires sheet error: {str(e)}")

    try:
        budgets = parse_budget_sheet(archive)
        summary['monthly_budgets'] = len(budgets)
    except Exception as e:
        summary['errors'].append(f"Budget sheet error: {str(e)}")

    return summary
