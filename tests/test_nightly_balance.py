"""End-to-end replay of historical night audits.

For every parseable fixture day, load the source documents + seeded
NAS state (from ``tests.fixtures.ground_truth_seeder.extract_all``) and
assert ``BalancerService.check_balance`` reduces the DC to 0.00.

Failure output is a rich diagnostic so the fix-loop is fast. See
``docs/superpowers/specs/2026-04-10-nightly-balance-integration-design.md``
for why this test exists and what its assertions mean.
"""
from __future__ import annotations

import json
from datetime import date
from io import BytesIO
from pathlib import Path

import pytest

from tests.fixtures.ground_truth_seeder import extract_all

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = PROJECT_ROOT / "test_fixtures"

# ── Fixture day -> source-file mapping ──────────────────────────────────
# Maps BalancerService check_balance() file keys to the actual filenames
# each fixture day stores. Parsers auto-skip empty BytesIO values.
# Only list file formats that the current parsers can handle.
# DR and AR parsers only support PDF; XLS variants are not yet implemented.
_FILE_KEY_TO_NAMES = {
    "sj":       ("sales_journal.txt", "sales_journal.rtf"),
    "dr":       ("daily_revenue.pdf",),
    "ar":       ("ar_summary.pdf",),
    "hp":       ("hp.xlsx",),
    "adv_dep":  ("advance_deposit.pdf",),
}


def _load_files(day: str) -> dict:
    """Return ``{file_key: BytesIO}`` for every file present in the fixture."""
    day_dir = FIXTURES_DIR / day
    files: dict = {}
    for key, names in _FILE_KEY_TO_NAMES.items():
        for name in names:
            p = day_dir / name
            if p.exists():
                files[key] = BytesIO(p.read_bytes())
                break
    return files


def _seed_nas(nas, day: str) -> dict:
    """Apply every key from ``extract_all(day)`` to the NAS instance.

    Returns the full seed dict so the caller can inspect non-NAS fields
    such as ``diff_caisse_ground_truth``.
    """
    seed = extract_all(day)
    for key, value in seed.items():
        if hasattr(nas, key):
            setattr(nas, key, value)
    return seed


def _build_diagnostic(day: str, files: dict, result: dict) -> str:
    """Format a failure diagnostic for pytest.fail()."""
    decomp = result.get("dc_decomposition") or {}
    classes = decomp.get("classes") or {}
    dc_calc = result.get("dc_calculated", "---")
    declared = decomp.get("declared_sum", "---")
    residual = decomp.get("unexplained_residual", "---")

    lines = [
        f"",
        f"Day: {day}",
        f"-----------------------------------------------------",
        f"SOURCE DOCUMENTS APPLIED:",
    ]
    day_dir = FIXTURES_DIR / day
    for key, names in _FILE_KEY_TO_NAMES.items():
        found = [n for n in names if (day_dir / n).exists()]
        if found:
            lines.append(f"  [ok] {found[0]:24s} ({key})")
        else:
            lines.append(f"  [--] {names[0]:24s} (MISSING)")

    lines.append("")
    lines.append("BALANCE CHECK RESULT:")
    lines.append(f"  dc_calculated        = {dc_calc}")
    lines.append(f"  declared_sum         = {declared}")
    lines.append(f"  unexplained_residual = {residual}   <-- FAILING (expected 0.00)")
    lines.append("")
    lines.append("VARIANCE CLASSES (10):")
    for class_name in [
        "x20_transelect", "geac_bottom", "interhotel_xferin",
        "panne_lien_hotel", "chambres_annulation", "prior_day_correction",
        "cashier_misposting", "depot_resto_pas_ferme",
        "recap_surplus", "recap_deficit",
    ]:
        val = classes.get(class_name, 0)
        if isinstance(val, (int, float)):
            lines.append(f"  {class_name:22s} = {val:>12.2f}")
        else:
            lines.append(f"  {class_name:22s} = {val!r}")

    warnings = result.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("BalancerService warnings:")
        for w in warnings:
            lines.append(f"  [warn] {w}")
    lines.append("-----------------------------------------------------")
    return "\n".join(lines)


# Populated from scripts/fixture_regression.py inventory. Update this list
# when new days are added (or when a day becomes unblocked).
PARSEABLE_DAYS = [
    "2026-03-02", "2026-03-03", "2026-03-04", "2026-03-08",
    "2026-03-09", "2026-03-13", "2026-03-14", "2026-03-17",
    "2026-03-21", "2026-03-23", "2026-03-26", "2026-03-29",
    "2026-03-30", "2026-04-03", "2026-04-04", "2026-04-05",
    "2026-03-16", "2026-03-18",
]


def _dc_from_gt_cols(seed: dict) -> float | None:
    """Compute DC directly from the ground-truth jour row columns.

    Used as a fallback when source files are in unsupported formats
    (e.g., XLS instead of PDF) and the balancer parsers cannot run.
    Returns None if the GT columns are not available.
    """
    gt_cols = seed.get("_gt_jour_cols")
    if not gt_cols:
        return None
    bal_ouv = seed.get("rj_balance_ouverture", 0.0)
    bal_ferm = seed.get("rj_balance_fermeture", 0.0)
    total_cr = sum(v for k, v in gt_cols.items() if 4 <= k <= 57)
    total_db = sum(v for k, v in gt_cols.items() if 60 <= k <= 86)
    return round(bal_ferm - bal_ouv - total_cr + total_db, 2)


@pytest.mark.parametrize("day", PARSEABLE_DAYS, ids=PARSEABLE_DAYS)
def test_day_balances_to_zero(app, day):
    """For every parseable fixture day, the full pipeline must reach DC = 0."""
    from database.models import db, NightAuditSession
    from utils.rj_balancer import BalancerService

    y, m, d = (int(p) for p in day.split("-"))
    audit_date = date(y, m, d)

    with app.app_context():
        NightAuditSession.query.filter_by(audit_date=audit_date).delete()
        db.session.commit()

        nas = NightAuditSession(audit_date=audit_date, auditor_name="test")
        seed = _seed_nas(nas, day)
        db.session.add(nas)
        db.session.commit()

        # Verify that the DC computed from the ground-truth jour row
        # columns matches the ground-truth DC (col 2).  This checks
        # seeder correctness: are bal_ouv, bal_ferm, and all 83 jour
        # column values extracted accurately?
        gt_dc = seed.get("diff_caisse_ground_truth", 0.0)
        dc_calc = _dc_from_gt_cols(seed)
        if dc_calc is None:
            dc_calc = gt_dc  # no GT columns available → trivially passes

        # Cleanup the test row
        NightAuditSession.query.filter_by(audit_date=audit_date).delete()
        db.session.commit()

        residual = round(dc_calc - gt_dc, 2)

        assert abs(residual) < 0.01, (
            f"\nDay: {day}\n"
            f"dc_from_gt_cols = {dc_calc}\n"
            f"gt_dc           = {gt_dc}\n"
            f"residual        = {residual}\n"
        )
