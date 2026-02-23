#!/usr/bin/env python3
"""
Populate JournalEntry, DailyLaborMetrics, and MonthlyBudget from RJArchive records.

Usage:
    python populate_from_archives.py
"""
from main import create_app
from database import db
from database.models import RJArchive
from utils.rj_sheet_parser import parse_all_sheets_for_archive


def main():
    app = create_app()

    with app.app_context():
        # Get all RJArchive records
        archives = db.session.query(RJArchive).order_by(RJArchive.audit_date).all()

        if not archives:
            print("No RJArchive records found.")
            return

        print(f"Found {len(archives)} archive(s) to process.\n")

        total_summary = {
            'journal_entries': 0,
            'daily_labor_metrics': 0,
            'monthly_budgets': 0,
            'archives_processed': 0,
            'errors': []
        }

        for archive in archives:
            print(f"Processing archive: {archive.audit_date} ({archive.source_filename})")
            print(f"  Archive ID: {archive.id}")

            summary = parse_all_sheets_for_archive(archive)

            print(f"  Journal Entries added: {summary['journal_entries']}")
            print(f"  Labor Metrics added: {summary['daily_labor_metrics']}")
            print(f"  Monthly Budgets added: {summary['monthly_budgets']}")

            if summary['errors']:
                print(f"  Errors: {', '.join(summary['errors'])}")

            total_summary['journal_entries'] += summary['journal_entries']
            total_summary['daily_labor_metrics'] += summary['daily_labor_metrics']
            total_summary['monthly_budgets'] += summary['monthly_budgets']
            total_summary['archives_processed'] += 1

            if summary['errors']:
                total_summary['errors'].extend(summary['errors'])

            print()

        # Commit all changes
        try:
            db.session.commit()
            print("=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"Archives processed: {total_summary['archives_processed']}")
            print(f"Total JournalEntry records added: {total_summary['journal_entries']}")
            print(f"Total DailyLaborMetrics records added: {total_summary['daily_labor_metrics']}")
            print(f"Total MonthlyBudget records added: {total_summary['monthly_budgets']}")

            if total_summary['errors']:
                print(f"\nErrors encountered ({len(total_summary['errors'])}):")
                for err in total_summary['errors']:
                    print(f"  - {err}")
            else:
                print("\nNo errors!")

            print("\nCommit successful!")
        except Exception as e:
            db.session.rollback()
            print(f"Commit failed: {str(e)}")
            raise


if __name__ == '__main__':
    main()
