"""
Seed 5 years of realistic hotel demo data into all reporting models:
- DailyJourMetrics (room/F&B/other revenue, occupancy, cards, taxes)
- DailyLaborMetrics (labor hours/cost by 13 departments)
- DailyTipMetrics (tips by 5 departments)
- MonthlyBudget (60 months of budgets)
- DailyCashRecon (daily cash reconciliation data)
- DailyCardMetrics (daily card breakdown by 5 card types)
- MonthlyExpense (labor, utilities, franchise fees)
- DepartmentLabor (monthly department labor summaries)

Data from 2021-01-01 to 2026-02-22 with seasonal patterns,
weekend/weekday variations, growth trends, and realistic noise.

Usage:
    python seed_crm_demo.py
"""

import sys
import os
import random
import math
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from database.models import (
    db, DailyJourMetrics, DailyLaborMetrics, DailyTipMetrics,
    MonthlyBudget, DailyCashRecon, DailyCardMetrics, MonthlyExpense, DepartmentLabor
)

TOTAL_ROOMS = 252

# ── Seasonal occupancy base curves (monthly avg %) ──
# Laval/Montreal hotel: low winter, high summer, decent fall
SEASONAL_OCC = {
    1: 52, 2: 55, 3: 60, 4: 65, 5: 72, 6: 82,
    7: 88, 8: 90, 9: 78, 10: 72, 11: 62, 12: 55
}

# Weekend bump (Fri/Sat higher)
DOW_FACTOR = {
    0: 0.95,  # Mon
    1: 0.93,  # Tue
    2: 0.95,  # Wed
    3: 1.00,  # Thu
    4: 1.10,  # Fri
    5: 1.12,  # Sat
    6: 0.98,  # Sun
}

# Year-over-year growth in ADR (compounding)
YEARLY_ADR_GROWTH = {
    2021: 1.00,  # base year (COVID recovery)
    2022: 1.08,  # strong recovery
    2023: 1.14,  # continued growth
    2024: 1.18,  # stabilizing
    2025: 1.22,  # mature
    2026: 1.25,  # current
}

YEARLY_OCC_BOOST = {
    2021: -8,   # COVID tail
    2022: -3,
    2023: 0,
    2024: 2,
    2025: 3,
    2026: 3,
}

BASE_ADR = 142.0  # Base ADR in 2021


def generate_day(d):
    """Generate one day of realistic hotel metrics."""
    year = d.year
    month = d.month
    dow = d.weekday()

    # ── Occupancy ──
    base_occ = SEASONAL_OCC[month] + YEARLY_OCC_BOOST.get(year, 0)
    occ_pct = base_occ * DOW_FACTOR[dow]
    # Add noise ±8pts
    occ_pct += random.gauss(0, 4)
    occ_pct = max(25, min(99, occ_pct))

    hors_usage = random.choice([0, 0, 0, 1, 1, 2, 3, 5])
    available = TOTAL_ROOMS - hors_usage
    rooms_sold = int(available * occ_pct / 100)
    rooms_sold = max(0, min(available, rooms_sold))

    # Room type mix
    comp = random.choice([0, 0, 0, 1, 1, 2])
    suite = random.randint(0, min(5, rooms_sold // 10))
    double_r = int(rooms_sold * random.uniform(0.35, 0.50))
    simple = rooms_sold - double_r - suite - comp
    simple = max(0, simple)

    clients = int(simple * 1.0 + double_r * 1.8 + suite * 2.2 + comp * 1.5)
    clients += random.randint(-3, 5)
    clients = max(rooms_sold, clients)

    # ── ADR ──
    adr_growth = YEARLY_ADR_GROWTH.get(year, 1.25)
    adr = BASE_ADR * adr_growth
    # Weekend premium
    if dow in (4, 5):
        adr *= random.uniform(1.05, 1.15)
    elif dow in (0, 1):
        adr *= random.uniform(0.90, 0.97)
    # Summer premium
    if month in (6, 7, 8):
        adr *= random.uniform(1.08, 1.18)
    elif month in (12, 1, 2):
        adr *= random.uniform(0.88, 0.95)
    adr += random.gauss(0, 8)
    adr = max(95, adr)

    room_revenue = round(adr * rooms_sold, 2)
    revpar = round(room_revenue / available, 2) if available else 0

    # ── F&B Revenue ──
    fb_per_client = random.uniform(18, 35) * adr_growth
    if dow in (4, 5):
        fb_per_client *= 1.15
    if month in (6, 7, 8):
        fb_per_client *= 1.10

    total_fb = round(fb_per_client * clients, 2)

    # F&B outlet split (realistic proportions)
    cafe_pct = random.uniform(0.28, 0.38)
    piazza_pct = random.uniform(0.22, 0.32)
    banquet_pct = random.uniform(0.10, 0.25)
    room_svc_pct = random.uniform(0.05, 0.12)
    spesa_pct = 1.0 - cafe_pct - piazza_pct - banquet_pct - room_svc_pct
    spesa_pct = max(0.05, spesa_pct)

    cafe_total = round(total_fb * cafe_pct, 2)
    piazza_total = round(total_fb * piazza_pct, 2)
    banquet_total = round(total_fb * banquet_pct, 2)
    room_svc_total = round(total_fb * room_svc_pct, 2)
    spesa_total = round(total_fb * spesa_pct, 2)

    # F&B category split
    nour_pct = random.uniform(0.55, 0.65)
    total_nourriture = round(total_fb * nour_pct, 2)
    remaining = total_fb - total_nourriture
    boi_pct = random.uniform(0.30, 0.45)
    total_boisson = round(remaining * boi_pct, 2)
    bie_pct = random.uniform(0.15, 0.25)
    total_bieres = round(remaining * bie_pct, 2)
    vin_pct = random.uniform(0.10, 0.20)
    total_vins = round(remaining * vin_pct, 2)
    total_mineraux = round(remaining - total_boisson - total_bieres - total_vins, 2)
    total_mineraux = max(0, total_mineraux)

    tips = round(total_fb * random.uniform(0.12, 0.18), 2)
    tabagie = round(random.uniform(50, 250), 2)

    # ── Other Revenue ──
    other_revenue = round(
        random.uniform(200, 800) +  # internet
        random.uniform(50, 200) +   # sonifi
        random.uniform(0, 150) +    # misc
        random.uniform(0, 100),     # parking/valet
        2
    )

    total_revenue = round(room_revenue + total_fb + other_revenue + tips + tabagie, 2)
    trevpar = round(total_revenue / available, 2) if available else 0

    # ── Payments (card split) ──
    card_total = round(total_revenue * random.uniform(0.82, 0.92), 2)
    visa_pct = random.uniform(0.35, 0.45)
    mc_pct = random.uniform(0.20, 0.28)
    amex_pct = random.uniform(0.12, 0.20)
    debit_pct = random.uniform(0.08, 0.15)
    discover_pct = 1.0 - visa_pct - mc_pct - amex_pct - debit_pct
    discover_pct = max(0.01, discover_pct)

    visa_total = round(card_total * visa_pct, 2)
    mc_total = round(card_total * mc_pct, 2)
    amex_e = round(card_total * amex_pct * 0.6, 2)
    amex_g = round(card_total * amex_pct * 0.4, 2)
    debit_total = round(card_total * debit_pct, 2)
    discover = round(card_total * discover_pct, 2)

    # ── Taxes ──
    taxable_rev = room_revenue + total_fb + other_revenue
    tps = round(taxable_rev * 0.05, 2)
    tvq = round(taxable_rev * 0.09975, 2)
    tvh = round(room_revenue * 0.035, 2)

    # ── Cash ──
    opening = round(random.uniform(800, 1200), 2)
    cash_diff = round(random.gauss(0, 15), 2)
    closing = round(opening + cash_diff, 2)

    food_pct_val = round(total_nourriture / total_fb * 100, 1) if total_fb else 0
    bev_pct_val = round((total_boisson + total_bieres + total_vins + total_mineraux) / total_fb * 100, 1) if total_fb else 0

    return DailyJourMetrics(
        date=d,
        year=d.year,
        month=d.month,
        day_of_month=d.day,
        room_revenue=room_revenue,
        fb_revenue=total_fb,
        cafe_link_total=cafe_total,
        piazza_total=piazza_total,
        spesa_total=spesa_total,
        room_svc_total=room_svc_total,
        banquet_total=banquet_total,
        tips_total=tips,
        tabagie_total=tabagie,
        other_revenue=other_revenue,
        total_revenue=total_revenue,
        total_nourriture=total_nourriture,
        total_boisson=total_boisson,
        total_bieres=total_bieres,
        total_vins=total_vins,
        total_mineraux=total_mineraux,
        rooms_simple=simple,
        rooms_double=double_r,
        rooms_suite=suite,
        rooms_comp=comp,
        total_rooms_sold=rooms_sold,
        rooms_available=available,
        occupancy_rate=round(rooms_sold / available * 100, 1) if available else 0,
        nb_clients=clients,
        rooms_hors_usage=hors_usage,
        rooms_ch_refaire=random.randint(0, 8),
        visa_total=visa_total,
        mastercard_total=mc_total,
        amex_elavon_total=amex_e,
        amex_global_total=amex_g,
        debit_total=debit_total,
        discover_total=discover,
        total_cards=card_total,
        tps_total=tps,
        tvq_total=tvq,
        tvh_total=tvh,
        opening_balance=opening,
        cash_difference=cash_diff,
        closing_balance=closing,
        adr=round(adr, 2),
        revpar=revpar,
        trevpar=trevpar,
        food_pct=food_pct_val,
        beverage_pct=bev_pct_val,
        source='demo_seed',
        rj_filename='seed_crm_demo.py',
    )


# ──────────────────────────────────────────────────────────────────────
# LABOR METRICS GENERATION
# ──────────────────────────────────────────────────────────────────────

DEPARTMENTS = [
    'RECEPTION', 'RESERVATION', 'AUDIT', 'PORTIER', 'COMMIS',
    'CLUB_LOUNGE', 'GOUVERNANTE', 'CUISINE', 'BANQUET', 'BAR',
    'ROOM_SERVICE', 'MAINTENANCE', 'ADMIN'
]

# Average hourly rates by department (CAD)
DEPT_RATES = {
    'RECEPTION': 22.50, 'RESERVATION': 21.00, 'AUDIT': 23.00,
    'PORTIER': 20.00, 'COMMIS': 18.50, 'CLUB_LOUNGE': 21.50,
    'GOUVERNANTE': 19.50, 'CUISINE': 24.00, 'BANQUET': 20.00,
    'BAR': 22.00, 'ROOM_SERVICE': 19.00, 'MAINTENANCE': 25.00,
    'ADMIN': 26.00
}

# Base hours per department (variable by day)
DEPT_BASE_HOURS = {
    'GOUVERNANTE': (40, 60),  # min, max (biggest dept)
    'CUISINE': (25, 40),
    'RECEPTION': (16, 24),
    'BANQUET': (0, 40),  # highly variable
    'BAR': (8, 16),
    'ROOM_SERVICE': (8, 16),
    'MAINTENANCE': (12, 20),
    'ADMIN': (4, 16),  # weekday only
    'PORTIER': (8, 12),
    'RESERVATION': (8, 12),
    'AUDIT': (8, 12),
    'COMMIS': (6, 12),
    'CLUB_LOUNGE': (6, 12),
}


def generate_labor_day(d):
    """Generate daily labor metrics for all 13 departments."""
    dow = d.weekday()
    month = d.month
    year = d.year

    labor_records = []

    for dept in DEPARTMENTS:
        min_h, max_h = DEPT_BASE_HOURS[dept]

        # Admin only weekdays
        if dept == 'ADMIN' and dow >= 5:
            regular = 0
        else:
            regular = random.uniform(min_h, max_h)

        # Seasonal adjustment for GOUVERNANTE (more in summer)
        if dept == 'GOUVERNANTE':
            if month in (6, 7, 8):
                regular *= random.uniform(1.10, 1.20)
            elif month in (12, 1, 2):
                regular *= random.uniform(0.90, 1.00)

        # Weekend/Friday bump for BAR, BANQUET
        if dept in ('BAR', 'BANQUET') and dow in (4, 5):
            regular *= random.uniform(1.15, 1.30)

        # Banquet is event-driven (40% of days have events)
        if dept == 'BANQUET':
            if random.random() > 0.40:
                regular = 0
            else:
                regular = random.uniform(25, 50)

        # Overtime (typically 5-10% of regular hours)
        overtime = regular * random.uniform(0.00, 0.10)

        # Employees: roughly hours / 8 (full shift)
        employees = max(1, int((regular + overtime) / 8.0))

        # Labor cost with yearly wage growth ~2%
        growth_factor = 1.0 + (year - 2021) * 0.02
        rate = DEPT_RATES[dept] * growth_factor
        labor_cost = (regular + overtime) * rate

        record = DailyLaborMetrics(
            date=d,
            year=year,
            month=month,
            department=dept,
            regular_hours=round(regular, 2),
            overtime_hours=round(overtime, 2),
            employees_count=employees,
            labor_cost=round(labor_cost, 2),
            source='demo_seed',
        )
        labor_records.append(record)

    return labor_records


# ──────────────────────────────────────────────────────────────────────
# TIP METRICS GENERATION
# ──────────────────────────────────────────────────────────────────────

TIP_DEPARTMENTS = ['CHAMBRE', 'PIAZZA', 'BANQUET', 'BAR', 'ROOM_SERVICE']


def generate_tips_day(d, jour_metrics):
    """Generate daily tip metrics for 5 F&B departments."""
    dow = d.weekday()
    month = d.month

    tip_records = []

    # CHAMBRE tips proportional to rooms sold
    chambre_tips_brut = round(jour_metrics.total_rooms_sold * random.uniform(0.80, 1.20), 2)
    chambre_employees = max(1, jour_metrics.total_rooms_sold // 25)

    # PIAZZA (bar/restaurant) proportional to F&B
    piazza_tips_brut = round(jour_metrics.piazza_total * random.uniform(0.12, 0.18), 2)
    piazza_employees = max(2, int(jour_metrics.piazza_total / 300))

    # BANQUET (only if events ~40% of days)
    banquet_tips_brut = 0
    banquet_employees = 0
    if random.random() < 0.40:
        banquet_tips_brut = round(random.uniform(50, 800), 2)
        banquet_employees = max(1, int(banquet_tips_brut / 80))

    # BAR tips, higher Fri/Sat
    bar_tips_base = random.uniform(80, 200)
    if dow in (4, 5):
        bar_tips_base *= 1.20
    bar_tips_brut = round(bar_tips_base, 2)
    bar_employees = max(2, int(bar_tips_base / 50))

    # ROOM_SERVICE tips
    room_svc_tips_brut = round(jour_metrics.room_svc_total * random.uniform(0.12, 0.18), 2)
    room_svc_employees = max(1, int(room_svc_tips_brut / 30))

    tip_data = [
        ('CHAMBRE', chambre_tips_brut, chambre_employees),
        ('PIAZZA', piazza_tips_brut, piazza_employees),
        ('BANQUET', banquet_tips_brut, banquet_employees),
        ('BAR', bar_tips_brut, bar_employees),
        ('ROOM_SERVICE', room_svc_tips_brut, room_svc_employees),
    ]

    for dept, tips_brut, employees in tip_data:
        # Deductions ~35%
        deductions = round(tips_brut * 0.35, 2)
        tips_net = round(tips_brut - deductions, 2)

        record = DailyTipMetrics(
            date=d,
            year=d.year,
            month=month,
            department=dept,
            tips_brut=tips_brut,
            tips_net=tips_net,
            deductions=deductions,
            employees_tipped=employees,
            source='demo_seed',
        )
        tip_records.append(record)

    return tip_records


# ──────────────────────────────────────────────────────────────────────
# MONTHLY BUDGET GENERATION (once per month)
# ──────────────────────────────────────────────────────────────────────

def generate_monthly_budgets(jour_data_by_month):
    """Generate monthly budgets based on actuals with ~5% variance."""
    start = date(2021, 1, 1)
    end = date(2026, 2, 1)

    budgets = []
    current = start

    while current <= end:
        year = current.year
        month = current.month

        # Get all days in this month from jour_data
        month_days = [d for d in jour_data_by_month.get((year, month), [])]

        if not month_days:
            # No data, skip
            current = current.replace(day=1) + timedelta(days=32)
            current = current.replace(day=1)
            continue

        # Average the month's actuals
        avg_room_rev = sum(d.room_revenue for d in month_days) / len(month_days)
        avg_fb_rev = sum(d.fb_revenue for d in month_days) / len(month_days)
        avg_other = sum(d.other_revenue for d in month_days) / len(month_days)
        avg_occ = sum(d.occupancy_rate for d in month_days) / len(month_days)
        avg_adr = sum(d.adr for d in month_days) / len(month_days)

        # Budget = actual * (0.95 to 1.05) with slight optimism
        budget = MonthlyBudget(
            year=year,
            month=month,
            room_revenue_budget=round(avg_room_rev * random.uniform(0.97, 1.04), 2),
            fb_revenue_budget=round(avg_fb_rev * random.uniform(0.97, 1.04), 2),
            other_revenue_budget=round(avg_other * random.uniform(0.95, 1.05), 2),
            total_revenue_budget=round((avg_room_rev + avg_fb_rev + avg_other) * random.uniform(0.97, 1.04), 2),
            labor_cost_budget=round((avg_room_rev + avg_fb_rev) * random.uniform(0.28, 0.35), 2),
            operating_expense_budget=round((avg_room_rev + avg_fb_rev) * random.uniform(0.25, 0.32), 2),
            occupancy_budget=round(min(99, avg_occ * random.uniform(0.98, 1.02)), 1),
            adr_budget=round(avg_adr * random.uniform(0.97, 1.04), 2),
            source='demo_seed',
        )
        budgets.append(budget)

        # Next month
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    return budgets


# ──────────────────────────────────────────────────────────────────────
# CASH RECONCILIATION GENERATION
# ──────────────────────────────────────────────────────────────────────

AUDITOR_NAMES = ["Tristan", "Frederic", "Karl", "Stéphane", "David"]


def generate_cash_recon_day(d, jour_metrics):
    """Generate daily cash reconciliation from Recap + Diff.Caisse."""

    # Cash amounts (random, typical range)
    cash_ls_lecture = round(random.uniform(500, 2000), 2)
    cash_ls_correction = round(random.gauss(0, 50), 2)  # small adjustment
    cash_pos_lecture = round(random.uniform(300, 1500), 2)
    cash_pos_correction = round(random.gauss(0, 40), 2)

    # Cheques
    cheque_ar = round(random.uniform(0, 500), 2)
    cheque_dr = round(random.uniform(0, 300), 2)

    # Reimbursements
    remb_gratuite = round(random.uniform(0, 200), 2)
    remb_client = round(random.uniform(0, 300), 2)

    # DueBack from receptionist sheets
    dueback_total = round(random.uniform(50, 500), 2)

    # Surplus/deficit (should be small, gaussian noise)
    surplus_deficit = round(random.gauss(0, 15), 2)

    # Deposits (proportional to room revenue)
    deposit_cdn = round(jour_metrics.room_revenue * random.uniform(0.08, 0.12), 2)
    deposit_usd = round(jour_metrics.room_revenue * random.uniform(0.02, 0.06), 2)

    # POS variance (Diff.Caisse)
    diff_caisse = round(random.gauss(0, 20), 2)

    # Quasimodo variance (cards vs jour total) — should be TIGHT
    quasimodo_variance = round(random.gauss(0, 2), 2)

    auditor = random.choice(AUDITOR_NAMES)

    record = DailyCashRecon(
        date=d,
        year=d.year,
        month=d.month,
        cash_ls_lecture=cash_ls_lecture,
        cash_ls_correction=cash_ls_correction,
        cash_pos_lecture=cash_pos_lecture,
        cash_pos_correction=cash_pos_correction,
        cheque_ar=cheque_ar,
        cheque_dr=cheque_dr,
        remb_gratuite=remb_gratuite,
        remb_client=remb_client,
        dueback_total=dueback_total,
        surplus_deficit=surplus_deficit,
        deposit_cdn=deposit_cdn,
        deposit_usd=deposit_usd,
        diff_caisse=diff_caisse,
        quasimodo_variance=quasimodo_variance,
        auditor_name=auditor,
        source='demo_seed',
    )
    return record


# ──────────────────────────────────────────────────────────────────────
# CARD METRICS GENERATION
# ──────────────────────────────────────────────────────────────────────

def generate_card_metrics_day(d, jour_metrics):
    """Generate daily card breakdown for 5 card types from Transelect."""

    card_records = []
    total_cards = jour_metrics.total_cards

    # Card mix percentages (from seed_crm_demo patterns)
    card_split = {
        'VISA': random.uniform(0.38, 0.42),
        'MC': random.uniform(0.22, 0.28),
        'AMEX': random.uniform(0.14, 0.20),
        'DEBIT': random.uniform(0.10, 0.15),
        'DISCOVER': random.uniform(0.02, 0.05),
    }

    # Normalize to sum to 1.0
    total_split = sum(card_split.values())
    card_split = {k: v / total_split for k, v in card_split.items()}

    # Discount rates (processor fees)
    discount_rates = {
        'VISA': 0.02,
        'MC': 0.01,
        'AMEX': 0.03,
        'DEBIT': 0.00,
        'DISCOVER': 0.03,
    }

    # Average ticket $80-150
    avg_ticket = random.uniform(80, 150)

    for card_type in ['VISA', 'MC', 'AMEX', 'DEBIT', 'DISCOVER']:
        pos_total = round(total_cards * card_split[card_type], 2)
        bank_total = round(pos_total * (1 - discount_rates[card_type]), 2)
        discount_amount = round(pos_total * discount_rates[card_type], 2)
        net_amount = bank_total
        transaction_count = max(1, int(pos_total / avg_ticket))

        record = DailyCardMetrics(
            date=d,
            year=d.year,
            month=d.month,
            card_type=card_type,
            pos_total=pos_total,
            bank_total=bank_total,
            discount_rate=discount_rates[card_type],
            discount_amount=discount_amount,
            net_amount=net_amount,
            transaction_count=transaction_count,
            source='demo_seed',
        )
        card_records.append(record)

    return card_records


# ──────────────────────────────────────────────────────────────────────
# MONTHLY EXPENSE GENERATION (once per month)
# ──────────────────────────────────────────────────────────────────────

def generate_monthly_expenses(jour_data_by_month, labor_data_by_month):
    """Generate monthly expenses from labor + utilities + franchise fees."""

    start = date(2021, 1, 1)
    end = date(2026, 2, 1)

    expenses = []
    current = start

    while current <= end:
        year = current.year
        month = current.month

        month_days = jour_data_by_month.get((year, month), [])
        if not month_days:
            current = current.replace(day=1) + timedelta(days=32)
            current = current.replace(day=1)
            continue

        # Total revenue for the month
        total_revenue = sum(d.total_revenue for d in month_days)
        room_revenue = sum(d.room_revenue for d in month_days)
        fb_revenue = sum(d.fb_revenue for d in month_days)

        # Labor cost (sum daily labor costs)
        daily_labor = labor_data_by_month.get((year, month), [])
        labor_rooms = round(sum(
            sum(l.labor_cost for l in daily_labor if l.department in
                ('RECEPTION', 'RESERVATION', 'AUDIT', 'PORTIER', 'CLUB_LOUNGE', 'MAINTENANCE', 'ADMIN'))
            for _ in [1]
        ) if daily_labor else 0, 2)

        labor_fb = round(sum(
            sum(l.labor_cost for l in daily_labor if l.department in
                ('GOUVERNANTE', 'CUISINE', 'BANQUET', 'BAR', 'ROOM_SERVICE'))
            for _ in [1]
        ) if daily_labor else 0, 2)

        # If no labor data, estimate from revenue
        if labor_rooms == 0:
            labor_rooms = round((room_revenue + fb_revenue) * random.uniform(0.12, 0.18), 2)
        if labor_fb == 0:
            labor_fb = round((room_revenue + fb_revenue) * random.uniform(0.18, 0.25), 2)

        labor_admin = round((room_revenue + fb_revenue) * random.uniform(0.05, 0.08), 2)

        # Utilities (higher in winter)
        if month in (12, 1, 2):
            utilities = round(random.uniform(30000, 45000), 2)
        else:
            utilities = round(random.uniform(20000, 30000), 2)

        # Franchise fees (~5% of revenue)
        franchise_fees = round(total_revenue * 0.05, 2)

        # Yearly inflation ~2%
        inflation = 1.0 + (year - 2021) * 0.02
        labor_rooms *= inflation
        labor_fb *= inflation
        labor_admin *= inflation
        utilities *= inflation
        franchise_fees *= inflation

        record = MonthlyExpense(
            year=year,
            month=month,
            labor_rooms=round(labor_rooms, 2),
            labor_fb=round(labor_fb, 2),
            labor_admin=round(labor_admin, 2),
            labor_maintenance=0,
            labor_other=0,
            utilities=round(utilities, 2),
            supplies=0,
            maintenance_costs=0,
            marketing=0,
            insurance=0,
            franchise_fees=round(franchise_fees, 2),
            technology=0,
            other_expenses=0,
        )
        expenses.append(record)

        # Next month
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    return expenses


# ──────────────────────────────────────────────────────────────────────
# DEPARTMENT LABOR AGGREGATION (monthly summaries)
# ──────────────────────────────────────────────────────────────────────

def generate_department_labor(labor_data_by_month):
    """Aggregate daily labor data into monthly department summaries."""

    records = []

    for (year, month), month_days in labor_data_by_month.items():
        for dept in DEPARTMENTS:
            dept_days = [d for d in month_days if d.department == dept]

            if not dept_days:
                continue

            total_regular = sum(d.regular_hours for d in dept_days)
            total_overtime = sum(d.overtime_hours for d in dept_days)
            total_cost = sum(d.labor_cost for d in dept_days)
            avg_employees = sum(d.employees_count for d in dept_days) / len(dept_days)

            record = DepartmentLabor(
                year=year,
                month=month,
                department=dept,
                regular_hours=round(total_regular, 2),
                overtime_hours=round(total_overtime, 2),
                total_hours=round(total_regular + total_overtime, 2),
                regular_wages=round(total_cost * 0.85, 2),  # 85% is regular wages
                overtime_wages=round(total_cost * 0.15, 2),  # 15% is overtime
                benefits=0,
                total_labor_cost=round(total_cost, 2),
                headcount=max(1, int(avg_employees)),
                avg_hourly_rate=round(total_cost / max(1, total_regular + total_overtime), 2) if (total_regular + total_overtime) > 0 else 0,
            )
            records.append(record)

    return records


# ──────────────────────────────────────────────────────────────────────
# MAIN SEEDING FUNCTION
# ──────────────────────────────────────────────────────────────────────

def main():
    app = create_app()
    with app.app_context():
        print("Clearing existing demo data...")

        # Clear demo data from models that have a 'source' column
        models_with_source = [DailyJourMetrics, DailyLaborMetrics, DailyTipMetrics,
                              MonthlyBudget, DailyCashRecon, DailyCardMetrics]
        for model in models_with_source:
            existing = model.query.filter_by(source='demo_seed').count()
            if existing > 0:
                print(f"  Deleting {existing} {model.__tablename__} demo records...")
                model.query.filter_by(source='demo_seed').delete()
                db.session.commit()

        # Clear MonthlyExpense and DepartmentLabor (no source column, delete all)
        for model in [MonthlyExpense, DepartmentLabor]:
            existing = model.query.count()
            if existing > 0:
                print(f"  Deleting all {existing} {model.__tablename__} records...")
                model.query.delete()
                db.session.commit()

        start = date(2021, 1, 1)
        end = date(2026, 2, 22)
        current = start
        batch_jour = []
        batch_labor = []
        batch_tips = []
        batch_cash = []
        batch_cards = []
        total = 0

        # Storage for monthly aggregations
        jour_data_by_month = {}
        labor_data_by_month = {}

        print(f"\nGenerating daily data from {start} to {end}...")
        random.seed(42)  # Reproducible

        while current <= end:
            # Skip if real data exists for this date
            exists = DailyJourMetrics.query.filter_by(date=current).first()
            if exists and exists.source != 'demo_seed':
                current += timedelta(days=1)
                continue

            # Delete if demo data exists for this date
            if exists and exists.source == 'demo_seed':
                db.session.delete(exists)

            # Generate DailyJourMetrics
            jour = generate_day(current)
            batch_jour.append(jour)

            # Store by month for budget generation
            key = (current.year, current.month)
            if key not in jour_data_by_month:
                jour_data_by_month[key] = []
            jour_data_by_month[key].append(jour)

            # Generate DailyLaborMetrics
            labor_records = generate_labor_day(current)
            batch_labor.extend(labor_records)

            if key not in labor_data_by_month:
                labor_data_by_month[key] = []
            labor_data_by_month[key].extend(labor_records)

            # Generate DailyTipMetrics
            tip_records = generate_tips_day(current, jour)
            batch_tips.extend(tip_records)

            # Generate DailyCashRecon
            cash_record = generate_cash_recon_day(current, jour)
            batch_cash.append(cash_record)

            # Generate DailyCardMetrics
            card_records = generate_card_metrics_day(current, jour)
            batch_cards.extend(card_records)

            total += 1

            # Batch commit every 100 days
            if total % 100 == 0:
                db.session.add_all(batch_jour)
                db.session.add_all(batch_labor)
                db.session.add_all(batch_tips)
                db.session.add_all(batch_cash)
                db.session.add_all(batch_cards)
                db.session.commit()
                print(f"  ... {total} days generated ({current})")
                batch_jour = []
                batch_labor = []
                batch_tips = []
                batch_cash = []
                batch_cards = []

            current += timedelta(days=1)

        # Final batch commit
        if batch_jour or batch_labor or batch_tips or batch_cash or batch_cards:
            db.session.add_all(batch_jour)
            db.session.add_all(batch_labor)
            db.session.add_all(batch_tips)
            db.session.add_all(batch_cash)
            db.session.add_all(batch_cards)
            db.session.commit()

        print(f"\n  Seeded {total} days of daily metrics.")

        # Generate monthly aggregates
        print("\nGenerating monthly budgets...")
        budgets = generate_monthly_budgets(jour_data_by_month)
        for i in range(0, len(budgets), 100):
            db.session.add_all(budgets[i:i+100])
            db.session.commit()
        print(f"  Seeded {len(budgets)} monthly budgets.")

        print("\nGenerating monthly expenses...")
        expenses = generate_monthly_expenses(jour_data_by_month, labor_data_by_month)
        for i in range(0, len(expenses), 100):
            db.session.add_all(expenses[i:i+100])
            db.session.commit()
        print(f"  Seeded {len(expenses)} monthly expense records.")

        print("\nGenerating department labor summaries...")
        dept_labor = generate_department_labor(labor_data_by_month)
        for i in range(0, len(dept_labor), 100):
            db.session.add_all(dept_labor[i:i+100])
            db.session.commit()
        print(f"  Seeded {len(dept_labor)} department labor records.")

        print(f"\n{'='*70}")
        print(f"✓ Done! All demo data seeded successfully.")
        print(f"{'='*70}")
        print(f"Date range: {start} → {end}")
        print(f"Years covered: 2021-2026 ({(end - start).days} days)")
        print(f"\nTables populated:")
        print(f"  - DailyJourMetrics:     {total} days")
        print(f"  - DailyLaborMetrics:    {total * len(DEPARTMENTS)} day-dept records")
        print(f"  - DailyTipMetrics:      {total * 5} day-dept records")
        print(f"  - MonthlyBudget:        {len(budgets)} months")
        print(f"  - DailyCashRecon:       {total} days")
        print(f"  - DailyCardMetrics:     {total * 5} day-card records")
        print(f"  - MonthlyExpense:       {len(expenses)} months")
        print(f"  - DepartmentLabor:      {len(dept_labor)} month-dept records")
        print(f"{'='*70}")


if __name__ == '__main__':
    main()
