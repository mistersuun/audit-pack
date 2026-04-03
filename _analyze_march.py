"""
Comprehensive March 2026 Balance Analysis
Checks all 29 days: Diff.Caisse + detailed source-doc comparison where available.
"""

import xlrd
import os

RJ_DIR = "K:/RJ 2026-2027/01-MARS 2026"
AUDIT_DIR = "K:/audition"

# Map day -> source doc directory
AUDIT_DAYS = {
    1:  "1st March",
    8:  "8th March",
    9:  "9th March",
    16: "16th March",
    18: "18th March",
    23: "23rd March",
    24: "24th March",
    25: "25th March",
}

# Column letter -> 0-based index helpers
def col_letter_to_idx(letter):
    letter = letter.upper()
    result = 0
    for ch in letter:
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result - 1

def idx_to_col_letter(idx):
    idx += 1
    result = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        result = chr(ord('A') + rem) + result
    return result

# Key column indices
COL = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3,
    'J': 9,  'K': 10, 'L': 11, 'M': 12, 'N': 13,
    'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18,
    'T': 19, 'U': 20, 'V': 21, 'W': 22, 'X': 23,
    'Y': 24, 'Z': 25,
    'AD': 29, 'AE': 30, 'AF': 31,
    'AG': 32, 'AH': 33, 'AI': 34,
    'AJ': 35, 'AK': 36,
    'AL': 37, 'AM': 38, 'AN': 39, 'AO': 40, 'AP': 41, 'AQ': 42, 'AR': 43,
    'AS': 44, 'AT': 45, 'AU': 46, 'AV': 47,
    'AW': 48, 'AX': 49, 'AY': 50, 'AZ': 51,
    'BA': 52, 'BB': 53, 'BC': 54, 'BD': 55, 'BE': 56, 'BF': 57,
    'BH': 59,
    'BI': 60, 'BJ': 61, 'BK': 62, 'BL': 63, 'BM': 64, 'BN': 65, 'BO': 66, 'BP': 67,
    'BQ': 68, 'BR': 69,
    'BU': 72, 'BV': 73, 'BW': 74, 'BX': 75, 'BY': 76, 'BZ': 77,
    'CA': 78, 'CB': 79, 'CC': 80, 'CD': 81, 'CE': 82, 'CF': 83,
    'CG': 84, 'CH': 85, 'CI': 86,
}

def safe_float(val):
    try:
        return float(val) if val not in (None, '', ' ') else 0.0
    except (ValueError, TypeError):
        return 0.0

def get_jour_row(wb, day):
    """Get the data row for a specific day from the jour sheet. Day 1 = row index 2."""
    jour = None
    for name in wb.sheet_names():
        if name.lower() == 'jour':
            jour = wb.sheet_by_name(name)
            break
    if jour is None:
        return None
    row_idx = day + 1  # row 0=header, row 1=codes, row 2=day1, ...
    if row_idx >= jour.nrows:
        return None
    return [safe_float(jour.cell_value(row_idx, c)) for c in range(min(jour.ncols, 120))]

def compute_diff_caisse(row):
    """Compute Diff.Caisse = D - B - (E:BF - BI:CI)"""
    if row is None:
        return None
    B = row[COL['B']]
    D = row[COL['D']]
    E_to_BF = sum(row[4:58])   # cols 4..57 inclusive
    BI_to_CI = sum(row[60:87]) # cols 60..86 inclusive
    diff = D - B - (E_to_BF - BI_to_CI)
    return round(diff, 2)

def read_dr_xls(filepath):
    """Read Daily Revenue XLS and return dict of key values."""
    data = {}
    try:
        wb = xlrd.open_workbook(filepath)
    except Exception as e:
        return {'error': str(e)}

    def get_col(sheet, label_partial, today_col=1):
        """Find row by partial label match, return Today value."""
        label_partial_lower = label_partial.lower()
        for r in range(sheet.nrows):
            cell = str(sheet.cell_value(r, 0)).lower().strip()
            if label_partial_lower in cell:
                val = safe_float(sheet.cell_value(r, today_col))
                return val
        return None

    # --- Revenue Departments ---
    try:
        rev = wb.sheet_by_name('Revenue Departments')
        # Sum all room charge rows (skip Total rows which may be 0 due to formula)
        ROOM_CHARGE_KEYWORDS = [
            'room charge', 'rm chrg', 'room chrg',
            'late checkout', 'guaranteed no show', 'day use',
            'early departure', 'reservation/cancella', 'cancellation fee',
            'attrition', 'resort service fee',
        ]
        chambres_total = 0.0
        in_chambres = False
        for r in range(rev.nrows):
            label = str(rev.cell_value(r, 0)).lower().strip()
            if label == 'chambres':
                in_chambres = True
                continue
            if in_chambres:
                if label in ('telephones', 'autres revenus', 'internet', 'comptabilite', 'givex', 'ar activity', 'balance forward', 'subtotal revenue dep'):
                    in_chambres = False
                    continue
                if label == 'total':
                    continue  # skip formula total (shows 0)
                val = safe_float(rev.cell_value(r, 1))
                chambres_total += val
        data['chambres'] = round(chambres_total, 2)

        data['internet_rev'] = safe_float(get_col(rev, 'internet'))
        data['autres_gl'] = safe_float(get_col(rev, 'autres grand livre') or
                                       get_col(rev, 'autres grand liv'))
        data['autres_payer_taxable'] = safe_float(get_col(rev, 'autres a payer taxabl'))

        # Location de Salle comes from Non-Revenue Banquet section (not Revenue)
    except Exception as e:
        data['rev_error'] = str(e)

    # --- Non-Revenue Departments ---
    try:
        nr = wb.sheet_by_name('Non-Revenue Departments')
        data['taxe_heb'] = safe_float(get_col(nr, 'taxe heb'))
        data['tps_chambres'] = safe_float(get_col(nr, 'tps 14'))
        data['tvq_chambres'] = safe_float(get_col(nr, 'tvq 10'))

        data['piazza_nourr'] = safe_float(get_col(nr, 'nourriture piazza'))
        data['piazza_alcool'] = safe_float(get_col(nr, 'alcool rest piazza'))
        data['piazza_biere'] = safe_float(get_col(nr, 'biere rest piazza'))
        data['piazza_min'] = safe_float(get_col(nr, 'mineraux rest piazza'))
        data['piazza_vin'] = safe_float(get_col(nr, 'vin rest piazza'))
        data['piazza_pourb'] = safe_float(get_col(nr, 'pourboire rest piazz'))
        data['piazza_tps'] = safe_float(get_col(nr, 'tps rest piazza'))
        data['piazza_tvq'] = safe_float(get_col(nr, 'tvq rest piazza'))

        data['servchamb_nourr'] = safe_float(get_col(nr, 'nourriture serv cham'))
        data['servchamb_pourb'] = safe_float(get_col(nr, 'pourboire serv chamb'))
        data['servchamb_tps'] = safe_float(get_col(nr, 'tps serv chamb'))
        data['servchamb_tvq'] = safe_float(get_col(nr, 'tvq serv chamb'))

        data['bqt_location_salle'] = safe_float(get_col(nr, 'location de salle'))
        data['bqt_tps'] = safe_float(get_col(nr, 'tps bqt'))
        data['bqt_tvq'] = safe_float(get_col(nr, 'tvq bqt'))
        data['bqt_nourr'] = safe_float(get_col(nr, 'nourriture banquet'))
        data['bqt_alcool'] = safe_float(get_col(nr, 'alcool banquet'))
        data['bqt_biere'] = safe_float(get_col(nr, 'biere banquet'))
        data['bqt_min'] = safe_float(get_col(nr, 'mineraux banquet'))
        data['bqt_vin'] = safe_float(get_col(nr, 'vin banquet'))
        data['bqt_equip_audio'] = safe_float(get_col(nr, 'equipement audio'))
        data['bqt_equip_divers'] = safe_float(get_col(nr, 'equipement divers'))
        data['bqt_pourb'] = safe_float(get_col(nr, 'pourboire bqt'))
        data['bqt_frais'] = safe_float(get_col(nr, 'pourboire / frais ad'))

        data['spesa_nourr'] = safe_float(get_col(nr, 'la spesa') or get_col(nr, 'spesa'))
        data['spesa_tps'] = safe_float(get_col(nr, 'tps- la spesa') or get_col(nr, 'tps la spesa'))
        data['spesa_tvq'] = safe_float(get_col(nr, 'tvq - la spesa') or get_col(nr, 'tvq la spesa'))

        data['internet_tps'] = safe_float(get_col(nr, 'tps internet'))
        data['internet_tvq'] = safe_float(get_col(nr, 'tvq internet'))

        data['autres_tps'] = safe_float(get_col(nr, 'tps autres'))
        data['autres_tvq'] = safe_float(get_col(nr, 'tvq autres'))

        data['dueback_nourr'] = safe_float(get_col(nr, 'due back nourr'))
        data['remb_serveurs'] = safe_float(get_col(nr, 'remboursement serveu'))

        # Total TVQ/TPS from DR (Chambres + F&B partial)
        dr_tvq = (data.get('tvq_chambres', 0) + data.get('piazza_tvq', 0) +
                  data.get('servchamb_tvq', 0) + data.get('bqt_tvq', 0) +
                  data.get('spesa_tvq', 0) + data.get('internet_tvq', 0) +
                  data.get('autres_tvq', 0))
        dr_tps = (data.get('tps_chambres', 0) + data.get('piazza_tps', 0) +
                  data.get('servchamb_tps', 0) + data.get('bqt_tps', 0) +
                  data.get('spesa_tps', 0) + data.get('internet_tps', 0) +
                  data.get('autres_tps', 0))
        data['dr_tvq_total'] = round(dr_tvq, 2)
        data['dr_tps_total'] = round(dr_tps, 2)

    except Exception as e:
        data['nr_error'] = str(e)

    # --- Settlements ---
    try:
        st = wb.sheet_by_name('Settlements')
        data['balance_today'] = safe_float(get_col(st, 'balance today'))
        data['balance_prev'] = safe_float(get_col(st, 'balance prev'))
        raw_new_balance = safe_float(get_col(st, 'new balance'))
        # Formula cells often read 0; compute manually
        if raw_new_balance == 0.0 and data.get('balance_today', 0) != 0:
            data['new_balance'] = round(data['balance_prev'] + data['balance_today'], 2)
        else:
            data['new_balance'] = raw_new_balance
        data['adv_dep_applied'] = safe_float(get_col(st, 'adv dep applied'))
        data['facture_direct'] = abs(safe_float(get_col(st, 'facture direct')))
        data['amex'] = abs(safe_float(get_col(st, 'american express')))
        data['visa'] = abs(safe_float(get_col(st, 'visa') or get_col(st, '    visa')))
        data['mc'] = abs(safe_float(get_col(st, 'mastercard')))
        data['debit'] = abs(safe_float(get_col(st, 'carte debit')))
    except Exception as e:
        data['st_error'] = str(e)

    return data

def find_dr_file(day, audit_subdir):
    """Find the Daily Revenue XLS for a given day."""
    if audit_subdir is None:
        return None
    dirpath = os.path.join(AUDIT_DIR, audit_subdir)
    if not os.path.isdir(dirpath):
        return None
    for f in os.listdir(dirpath):
        fl = f.lower()
        if 'daily_rev' in fl and fl.endswith('.xls'):
            return os.path.join(dirpath, f)
    return None

def find_adv_dep_file(day, audit_subdir):
    if audit_subdir is None:
        return None
    dirpath = os.path.join(AUDIT_DIR, audit_subdir)
    if not os.path.isdir(dirpath):
        return None
    for f in os.listdir(dirpath):
        fl = f.lower()
        if ('advance' in fl or 'adv_dep' in fl) and fl.endswith('.xls'):
            return os.path.join(dirpath, f)
    return None

# =========================================================
# MAIN ANALYSIS
# =========================================================

print("=" * 70)
print("MARCH 2026 — BALANCE ANALYSIS (29 DAYS)")
print("=" * 70)
print()

results = []

for day in range(1, 30):
    rj_path = os.path.join(RJ_DIR, f"Rj {day:02d}-03-2026.xls")
    if not os.path.isfile(rj_path):
        results.append({'day': day, 'error': 'RJ file not found'})
        continue

    try:
        wb = xlrd.open_workbook(rj_path)
        row = get_jour_row(wb, day)
        if row is None:
            results.append({'day': day, 'error': 'Row not found in jour sheet'})
            continue

        diff = compute_diff_caisse(row)
        B = row[COL['B']]
        D = row[COL['D']]
        E_BF = round(sum(row[4:58]), 2)
        BI_CI = round(sum(row[60:87]), 2)

        # Key E:BF columns
        AG = row[COL['AG']]   # Location de Salle
        AK = row[COL['AK']]   # Chambres
        AX = row[COL['AX']]   # TVQ
        AY = row[COL['AY']]   # TPS
        AZ = row[COL['AZ']]   # Taxe Heb / TVH
        BC = row[COL['BC']]   # Ristournes
        BF = row[COL['BF']]   # Diff Forfait

        res = {
            'day': day, 'diff': diff,
            'B': B, 'D': D, 'E_BF': E_BF, 'BI_CI': BI_CI,
            'AG': AG, 'AK': AK, 'AX': AX, 'AY': AY, 'AZ': AZ, 'BC': BC, 'BF': BF,
        }

        # Compare with DR source docs if available
        audit_subdir = AUDIT_DAYS.get(day)
        dr_path = find_dr_file(day, audit_subdir)
        if dr_path:
            dr = read_dr_xls(dr_path)
            res['dr'] = dr
            res['dr_path'] = dr_path

        results.append(res)

    except Exception as e:
        results.append({'day': day, 'error': str(e)})

# =========================================================
# REPORT
# =========================================================

balanced = []
unbalanced = []
errors = []

for r in results:
    day = r['day']
    if 'error' in r:
        errors.append(r)
    elif abs(r['diff']) < 0.01:
        balanced.append(r)
    else:
        unbalanced.append(r)

print(f"SUMMARY: {len(balanced)} balanced, {len(unbalanced)} unbalanced, {len(errors)} errors")
print()

print("-" * 70)
print("DAILY DIFF.CAISSE OVERVIEW")
print(f"{'Day':<5} {'Diff.Caisse':>12}  {'B':>14}  {'D':>14}  {'E:BF':>12}  {'BI:CI':>12}")
print("-" * 70)
for r in results:
    day = r['day']
    if 'error' in r:
        print(f"  {day:2d}   ERROR: {r['error']}")
        continue
    diff = r['diff']
    flag = " ***" if abs(diff) > 0.01 else ""
    print(f"  {day:2d}   {diff:>12.2f}  {r['B']:>14.2f}  {r['D']:>14.2f}  {r['E_BF']:>12.2f}  {r['BI_CI']:>12.2f}{flag}")

print()
print("=" * 70)
print("DETAILED ANALYSIS — DAYS WITH SOURCE DOCS")
print("=" * 70)

for r in results:
    day = r['day']
    if 'error' in r or 'dr' not in r:
        continue

    dr = r['dr']
    diff = r['diff']
    balanced_str = "BALANCED" if abs(diff) < 0.01 else f"GAP = {diff:+.2f}"

    print(f"\n--- DAY {day:02d} ({balanced_str}) ---")
    print(f"  Jour: B={r['B']:.2f}  D={r['D']:.2f}  E:BF={r['E_BF']:.2f}  BI:CI={r['BI_CI']:.2f}")

    # DR comparison
    if 'chambres' in dr:
        diff_ak = r['AK'] - dr['chambres']
        flag = f"  *** OFF by {diff_ak:+.2f}" if abs(diff_ak) > 0.5 else "  OK"
        print(f"  AK Chambres:      Jour={r['AK']:.2f}  DR={dr['chambres']:.2f}{flag}")

    if 'bqt_location_salle' in dr:
        diff_ag = r['AG'] - dr['bqt_location_salle']
        flag = f"  *** OFF by {diff_ag:+.2f}" if abs(diff_ag) > 0.5 else "  OK"
        print(f"  AG Loc.Salle:     Jour={r['AG']:.2f}  DR={dr['bqt_location_salle']:.2f}{flag}")

    if 'taxe_heb' in dr:
        diff_az = r['AZ'] - dr['taxe_heb']
        flag = f"  *** OFF by {diff_az:+.2f}" if abs(diff_az) > 0.5 else "  OK"
        print(f"  AZ Taxe Heb:      Jour={r['AZ']:.2f}  DR={dr['taxe_heb']:.2f}{flag}")

    if 'dr_tvq_total' in dr:
        implied_sj_tvq = r['AX'] - dr['dr_tvq_total']
        print(f"  AX TVQ:           Jour={r['AX']:.2f}  DR-only={dr['dr_tvq_total']:.2f}  implied SJ TVQ={implied_sj_tvq:.2f}")

    if 'dr_tps_total' in dr:
        implied_sj_tps = r['AY'] - dr['dr_tps_total']
        print(f"  AY TPS:           Jour={r['AY']:.2f}  DR-only={dr['dr_tps_total']:.2f}  implied SJ TPS={implied_sj_tps:.2f}")

    if 'internet_rev' in dr:
        diff_aw = r.get('AW', row[COL['AW']] if 'row' in r else 0)
        # Re-read from results row
        pass

    print(f"  BF Diff.Forfait:  Jour={r['BF']:.2f}")

    # Column-by-column gaps for unbalanced days
    if abs(diff) > 0.5:
        print(f"  >> Root cause analysis:")
        identified_gap = 0.0
        if 'chambres' in dr and abs(r['AK'] - dr['chambres']) > 0.5:
            g = dr['chambres'] - r['AK']
            identified_gap += g
            print(f"     AK short by {g:+.2f} (should be {dr['chambres']:.2f})")
        if 'bqt_location_salle' in dr and abs(r['AG'] - dr['bqt_location_salle']) > 0.5:
            g = dr['bqt_location_salle'] - r['AG']
            identified_gap += g
            print(f"     AG short by {g:+.2f} (should be {dr['bqt_location_salle']:.2f})")
        if abs(identified_gap) > 0.01:
            residual = diff - identified_gap
            print(f"     Identified gap from DR checks: {identified_gap:+.2f}")
            print(f"     Remaining unexplained gap: {residual:+.2f} (likely SJ-sourced columns)")

print()
print("=" * 70)
print("ALL 29 DAYS — COLUMN SNAPSHOT (E:BF key cols)")
print(f"{'Day':<5} {'Diff':>8}  {'AG(Salle)':>10}  {'AK(Chbr)':>10}  {'AX(TVQ)':>9}  {'AY(TPS)':>9}  {'AZ(TaxHb)':>9}  {'BF(Forf)':>9}")
print("-" * 80)
for r in results:
    if 'error' in r:
        print(f"  {r['day']:2d}   ERROR")
        continue
    flag = " *" if abs(r['diff']) > 0.01 else ""
    print(f"  {r['day']:2d}   {r['diff']:>8.2f}  {r['AG']:>10.2f}  {r['AK']:>10.2f}  {r['AX']:>9.2f}  {r['AY']:>9.2f}  {r['AZ']:>9.2f}  {r['BF']:>9.2f}{flag}")
