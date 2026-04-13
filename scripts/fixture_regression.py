#!/usr/bin/env python3
"""Fixture regression tool.

Walks test_fixtures/YYYY-MM-DD/ and reports:
  1. Inventory: which doc types each day has, ground-truth status, parseability
  2. Parser regression: for each day with parseable inputs + ground truth, run
     the rj_balancer pipeline and score the resulting jour columns against the
     ground-truth Rj XX-XX-2026.xls.

Usage:
    python -m scripts.fixture_regression [--inventory-only] [--day YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import sys
from io import BytesIO
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "test_fixtures"
sys.path.insert(0, str(REPO_ROOT))


# ── XLS→text adapter ────────────────────────────────────────────────────────
# The SAVI/Galaxy GEAC system exports the same daily reports as both PDF and
# .xls. The .xls has the same labels and "Today is column 1" layout, just
# split across multiple sheets. We flatten all sheets into a single text blob
# that the PDF regex parsers can match against.
def xls_to_text(xls_path: Path) -> bytes:
    """Read an .xls and return text bytes mimicking the PDF text layout.

    Emits only the label and Today (column 1) for each data row so the
    parse_dr_pdf regex always finds Today as the first decimal number.
    Integer Today values are formatted with .2f to ensure they are
    matchable by the regex ``([\\d,]+\\.\\d{2})``.

    Header/section rows (col 0 non-empty, col 1 empty or non-numeric) are
    emitted verbatim so section markers like "Chambres" and "Total" are
    preserved for the in_chambres state machine.
    """
    import xlrd
    wb = xlrd.open_workbook(str(xls_path), formatting_info=False)
    lines = []
    for sname in wb.sheet_names():
        sh = wb.sheet_by_name(sname)
        for r in range(sh.nrows):
            label_raw = sh.cell_value(r, 0)
            label = str(label_raw).strip() if label_raw != "" else ""

            # Determine if col 1 holds a numeric Today value
            today_raw = sh.cell_value(r, 1) if sh.ncols > 1 else ""
            today_is_num = isinstance(today_raw, float)

            if not label:
                # Blank label row — skip (row is empty or purely numeric header)
                continue

            if not today_is_num or label.strip().lower() == "total":
                # Section header / title / Total row: emit label only so the
                # in_chambres state machine stops on "Total" without overriding
                # the accumulated chambres sum (XLS Total rows store 0, not the
                # pre-computed sum that the PDF carries).
                lines.append(label)
            else:
                # Data row: emit "Label  Today.2f" with correct GEAC sign convention
                today_val = float(today_raw)
                if today_val < 0:
                    formatted = f"{abs(today_val):,.2f}-"
                else:
                    formatted = f"{today_val:,.2f}"
                lines.append(f"{label}  {formatted}")
    return ("\n".join(lines)).encode("utf-8")


def _make_pdf_like_bytes(day_dir: Path, kind: str) -> Optional[BytesIO]:
    """Return a BytesIO that the rj_balancer PDF parsers can consume.

    Tries .pdf first. Falls back to .xls flattened to text-bytes — but note the
    rj_balancer PDF parsers use pdfplumber, so the fallback only works if we
    monkeypatch them. We return None for .xls so the caller knows to skip.
    For .pdf, we return the raw bytes."""
    pdf = day_dir / f"{kind}.pdf"
    if pdf.exists():
        return BytesIO(pdf.read_bytes())
    return None


def _xls_text_blob(day_dir: Path, kind: str) -> Optional[str]:
    xls = day_dir / f"{kind}.xls"
    if xls.exists():
        return xls_to_text(xls).decode("utf-8")
    return None


class _FakePage:
    def __init__(self, text): self._t = text
    def extract_text(self): return self._t


class _FakePDF:
    def __init__(self, text):
        self.pages = [_FakePage(text)]
    def __enter__(self): return self
    def __exit__(self, *a): pass


def _patch_pdfplumber_for_text(text: str):
    """Return a context manager that makes pdfplumber.open() yield a fake PDF
    containing the given text. Used so the rj_balancer PDF parsers can ingest
    text we extracted from .xls source documents."""
    import pdfplumber
    orig = pdfplumber.open

    class _Ctx:
        def __enter__(self):
            pdfplumber.open = lambda *a, **kw: _FakePDF(text)
            return self
        def __exit__(self, *a):
            pdfplumber.open = orig
    return _Ctx()

# ── Doc types ────────────────────────────────────────────────────────────────
REQUIRED_DOCS = [
    "sales_journal.txt",
    "daily_revenue",  # .pdf preferred, .xls fallback
    "ar_summary",     # .pdf preferred, .xls fallback
    "advance_deposit.xls",
    "hp.xlsx",
]
OPTIONAL_DOCS = [
    "market_segment",
    "cashier_cashout.txt",
    "gledger.xls",
    "ground_truth_rj.xls",
]


def doc_status(day_dir: Path) -> dict:
    """Return what docs exist and which formats."""
    files = {f.name for f in day_dir.iterdir() if f.is_file()}
    return {
        "sj":          "sales_journal.txt"   in files,
        "dr_pdf":      "daily_revenue.pdf"   in files,
        "dr_xls":      "daily_revenue.xls"   in files,
        "ar_pdf":      "ar_summary.pdf"      in files,
        "ar_xls":      "ar_summary.xls"      in files,
        "ad":          "advance_deposit.xls" in files,
        "hp":          "hp.xlsx"             in files,
        "ms_pdf":      "market_segment.pdf"  in files,
        "ms_xls":      "market_segment.xls"  in files,
        "cashout":     "cashier_cashout.txt" in files,
        "gledger":     "gledger.xls"         in files,
        "ground_truth":"ground_truth_rj.xls" in files,
    }


def parseable(s: dict) -> tuple[bool, list[str]]:
    """Can the parser pipeline (with .xls→text adapter) handle this day?
    Returns (ok, missing_reasons)."""
    missing = []
    if not s["sj"]:                                  missing.append("sales_journal.txt")
    if not (s["dr_pdf"] or s["dr_xls"]):             missing.append("daily_revenue (pdf or xls)")
    if not (s["ar_pdf"] or s["ar_xls"]):             missing.append("ar_summary (pdf or xls)")
    if not s["hp"]:                                  missing.append("hp.xlsx")
    # advance_deposit is needed for Bal_Ferm but not for the 35+ jour columns,
    # so it is *optional* — runs without it will score lower on BF only.
    return (len(missing) == 0, missing)


def cmd_inventory(args):
    days = sorted(d for d in FIXTURES.iterdir() if d.is_dir())
    rows = []
    for d in days:
        s = doc_status(d)
        ok, missing = parseable(s)
        rows.append((d.name, s, ok, missing))

    # Markdown table
    print("# Fixture Inventory\n")
    print(f"**Total days:** {len(rows)}\n")
    print("| Day | SJ | DR | AR | AD | HP | MS | Cashout | GT | Parseable |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for day, s, ok, _ in rows:
        def mark(present, alt=False):
            if present and alt: return "📄"  # pdf
            if present: return "📊" if alt is False else "✓"
            return "—"
        sj   = "✓" if s["sj"]   else "—"
        dr   = "📄" if s["dr_pdf"] else ("📊" if s["dr_xls"] else "—")
        ar   = "📄" if s["ar_pdf"] else ("📊" if s["ar_xls"] else "—")
        ad   = "✓" if s["ad"]   else "—"
        hp   = "✓" if s["hp"]   else "—"
        ms   = "📄" if s["ms_pdf"] else ("📊" if s["ms_xls"] else "—")
        co   = "✓" if s["cashout"] else "—"
        gt   = "✓" if s["ground_truth"] else "—"
        par  = "✅" if ok else "❌"
        print(f"| {day} | {sj} | {dr} | {ar} | {ad} | {hp} | {ms} | {co} | {gt} | {par} |")
    print("\nLegend: 📄 PDF · 📊 XLS · ✓ present · — missing\n")

    parseable_days = [r for r in rows if r[2]]
    blocked_days = [r for r in rows if not r[2]]
    print(f"## Summary")
    print(f"- ✅ Parseable today: **{len(parseable_days)}** days")
    print(f"- ❌ Blocked: **{len(blocked_days)}** days")
    print(f"- 🎯 With ground truth: **{sum(1 for _,s,_,_ in rows if s['ground_truth'])}** days")
    print()

    if blocked_days:
        print("## Blocked days (and why)")
        for day, _, _, missing in blocked_days:
            print(f"- **{day}**: missing {', '.join(missing)}")
        print()


# ── Parser regression ────────────────────────────────────────────────────────
def _read_bytes(p: Path) -> BytesIO:
    return BytesIO(p.read_bytes())


def run_one_day(day_dir: Path, day_name: str) -> dict:
    """Run rj_balancer.calculate_jour for one day, compare to ground truth."""
    from utils import rj_balancer as rb

    s = doc_status(day_dir)
    if not parseable(s)[0]:
        return {"day": day_name, "skipped": True, "reason": "not parseable"}

    try:
        # Day number for HP parser (extract from YYYY-MM-DD)
        day_num = int(day_name.split("-")[2])

        sj = rb.parse_sj(_read_bytes(day_dir / "sales_journal.txt"))

        # Daily Revenue: prefer PDF, fall back to .xls→text adapter
        dr_pdf = day_dir / "daily_revenue.pdf"
        if dr_pdf.exists():
            dr = rb.parse_dr_pdf(_read_bytes(dr_pdf))
        else:
            text = xls_to_text(day_dir / "daily_revenue.xls").decode("utf-8")
            with _patch_pdfplumber_for_text(text):
                dr = rb.parse_dr_pdf(BytesIO(b""))

        # AR Summary: same fallback pattern
        ar_pdf = day_dir / "ar_summary.pdf"
        if ar_pdf.exists():
            ar = rb.parse_ar_pdf(_read_bytes(ar_pdf))
        else:
            text = xls_to_text(day_dir / "ar_summary.xls").decode("utf-8")
            with _patch_pdfplumber_for_text(text):
                ar = rb.parse_ar_pdf(BytesIO(b""))

        hp = rb.parse_hp(_read_bytes(day_dir / "hp.xlsx"), day_num)

        # Advance Deposit is optional — without it, Bal_Ferm won't be accurate
        ad_path = day_dir / "advance_deposit.xls"
        if ad_path.exists():
            ad = rb.parse_adv_dep(_read_bytes(ad_path))
        else:
            ad = rb.AdvDepData()

        # Read ground-truth jour row from the actual completed RJ
        gt_jour_row = rb.JourRow()
        gt_path = day_dir / "ground_truth_rj.xls"
        if gt_path.exists():
            try:
                gt_jour_row = rb.parse_rj_jour(_read_bytes(gt_path), day_num)
            except Exception as e:
                return {"day": day_name, "error": f"parse_rj_jour failed: {e}"}

        # calculate_jour also needs Transelect/GEAC/Recap/Jour from prev day RJ.
        # We don't have those in the fixture, so pass empty instances. This means
        # Bal_Ouv-dependent columns won't score, but the 30+ data-driven columns
        # (taxes, F&B, room revenue, settlements) will.
        if not s["ground_truth"]:
            return {"day": day_name, "calc_ok": True, "score": None, "reason": "no ground truth"}

        try:
            result = rb.calculate_jour(
                sj=sj, dr=dr, ar=ar, hp=hp, adv=ad,
                tr=rb.TranselectData(), geac=rb.GeacData(),
                recap=rb.RecapData(), jour=gt_jour_row,
            )
        except TypeError as e:
            return {"day": day_name, "error": f"calculate_jour signature mismatch: {e}"}

        # Score from the result['columns'] list
        cols = result.get("columns", [])
        match = sum(1 for c in cols if c["status"] == "ok" and (c["rj"] != 0 or c["calc"] != 0))
        total = sum(1 for c in cols if c["rj"] != 0 or c["calc"] != 0)
        diffs = [(c["col"], c["name"], c["rj"], c["calc"], round(c["diff"], 2))
                 for c in cols if c["status"] != "ok" and (c["rj"] != 0 or c["calc"] != 0)]
        return {
            "day": day_name,
            "calc_ok": True,
            "score": (match, total),
            "diffs": diffs[:15],
            "bal_ferm_calc": result.get("bal_ferm_calc"),
            "bal_ferm_rj": result.get("bal_ferm_rj"),
            "dc_calc": result.get("dc_calc"),
        }
    except Exception as e:
        import traceback
        return {"day": day_name, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-500:]}


def _read_jour_row(rj_path: Path) -> Optional[dict]:
    """Open the ground-truth Rj .xls and read the jour row values into {col_idx: value}."""
    try:
        import xlrd
        wb = xlrd.open_workbook(str(rj_path), formatting_info=False)
    except Exception:
        return None

    # Find the 'jour' sheet (case-insensitive)
    jour_sheet = None
    for name in wb.sheet_names():
        if name.lower().strip() == "jour":
            jour_sheet = wb.sheet_by_name(name)
            break
    if jour_sheet is None:
        return None

    # The jour row of interest is typically the last data row. Without knowing
    # the schema for sure, return all rows so the scorer can pick the right one.
    # For now: return row index -> {col: value} for the row with the most numeric cells.
    best_row, best_count = None, 0
    for r in range(jour_sheet.nrows):
        nums = sum(1 for c in range(jour_sheet.ncols)
                   if isinstance(jour_sheet.cell_value(r, c), (int, float))
                   and jour_sheet.cell_value(r, c) != 0)
        if nums > best_count:
            best_count = nums
            best_row = r
    if best_row is None:
        return None
    return {c: jour_sheet.cell_value(best_row, c) for c in range(jour_sheet.ncols)}


def _score(calc: dict, gt: dict, tol: float = 0.05) -> tuple[int, int, list]:
    """Compare a calc dict {col_idx: value} to gt dict {col_idx: value}."""
    diffs = []
    match = 0
    total = 0
    for col, gv in gt.items():
        if not isinstance(gv, (int, float)) or gv == 0:
            continue
        cv = calc.get(col, 0) if isinstance(calc, dict) else 0
        total += 1
        if abs(float(cv) - float(gv)) <= tol:
            match += 1
        else:
            diffs.append((col, gv, cv, round(float(cv) - float(gv), 2)))
    return match, total, diffs


def cmd_regression(args):
    days = sorted(d for d in FIXTURES.iterdir() if d.is_dir())
    if args.day:
        days = [d for d in days if d.name == args.day]

    print("# Parser Regression\n")
    results = []
    for d in days:
        r = run_one_day(d, d.name)
        results.append(r)

    print("| Day | Status | Score | Notes |")
    print("|---|---|---|---|")
    for r in results:
        if r.get("skipped"):
            print(f"| {r['day']} | ⏭ skipped | — | {r['reason']} |")
        elif r.get("error"):
            print(f"| {r['day']} | ❌ error | — | `{r['error'][:80]}` |")
        elif r.get("score"):
            m, t = r["score"]
            pct = round(100 * m / t, 1) if t else 0
            emoji = "✅" if pct >= 95 else ("🟡" if pct >= 80 else "🔴")
            print(f"| {r['day']} | {emoji} | {m}/{t} ({pct}%) | |")
        else:
            print(f"| {r['day']} | ℹ️ no GT | — | {r.get('reason','')} |")
    print()

    # Detail per day with diffs
    detailed = [r for r in results if r.get("score") and r.get("diffs")]
    if detailed:
        print("## Top diffs per day\n")
        for r in detailed:
            print(f"### {r['day']}")
            print(f"  Bal_Ferm: calc={r.get('bal_ferm_calc')} rj={r.get('bal_ferm_rj')} | DC={r.get('dc_calc')}")
            print("| Col | Name | RJ (truth) | Calc | Diff |")
            print("|---|---|---|---|---|")
            for col, name, rj_v, calc_v, d in r["diffs"]:
                print(f"| {col} | {name} | {rj_v} | {calc_v} | {d} |")
            print()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("inventory")
    rp = sub.add_parser("regression")
    rp.add_argument("--day", help="Limit to one day (YYYY-MM-DD)")
    args = ap.parse_args()

    if args.cmd == "regression":
        cmd_regression(args)
    else:
        cmd_inventory(args)


if __name__ == "__main__":
    main()
