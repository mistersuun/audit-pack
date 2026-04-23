"""Backfill DailyCashRecon + DailyCardMetrics from DailyJourMetrics for dates that don't exist yet.

The auto-import only populates DailyJourMetrics. This one-shot script mirrors
those rows into the two CRM analytics tables so the Cash & Récon and Paiements
tabs show recent data.
"""
from main import create_app
from database.models import db, DailyJourMetrics, DailyCashRecon, DailyCardMetrics

app = create_app()

CARD_TYPES = [
    ('amex_elavon_total', 'AMEX_ELAVON'),
    ('amex_global_total', 'AMEX_GLOBAL'),
    ('visa_total', 'VISA'),
    ('mastercard_total', 'MC'),
    ('debit_total', 'DEBIT'),
    ('discover_total', 'DISCOVER'),
]

# Typical merchant discount rates (from quasimodo_reconciliation memory)
DISCOUNT_RATES = {
    'AMEX_ELAVON': 0.0265,
    'AMEX_GLOBAL': 0.0265,
    'VISA': 0.017,
    'MC': 0.014,
    'DEBIT': 0.0,
    'DISCOVER': 0.028,
}


def main():
    with app.app_context():
        existing_recon = {r.date for r in DailyCashRecon.query.with_entities(DailyCashRecon.date).all()}
        existing_card = {(r.date, r.card_type) for r in DailyCardMetrics.query.with_entities(DailyCardMetrics.date, DailyCardMetrics.card_type).all()}

        jm_rows = DailyJourMetrics.query.order_by(DailyJourMetrics.date).all()
        print(f'JourMetrics rows: {len(jm_rows)}')
        print(f'Existing CashRecon dates: {len(existing_recon)}')
        print(f'Existing CardMetrics rows: {len(existing_card)}')

        new_recon = 0
        new_card = 0

        for jm in jm_rows:
            # Cash Recon backfill
            if jm.date not in existing_recon:
                rec = DailyCashRecon(
                    date=jm.date,
                    year=jm.year,
                    month=jm.month,
                    cash_ls_lecture=0,
                    cash_ls_correction=0,
                    cash_pos_lecture=0,
                    cash_pos_correction=0,
                    cheque_ar=0,
                    cheque_dr=0,
                    remb_gratuite=0,
                    remb_client=0,
                    dueback_total=0,
                    surplus_deficit=0,
                    deposit_cdn=0,
                    deposit_usd=0,
                    diff_caisse=jm.cash_difference or 0,
                    quasimodo_variance=0,
                    auditor_name='Auto-import',
                    source='jour_backfill',
                )
                db.session.add(rec)
                new_recon += 1

            # Card Metrics backfill — one row per card type
            for attr, card_type in CARD_TYPES:
                if (jm.date, card_type) in existing_card:
                    continue
                pos = float(getattr(jm, attr, 0) or 0)
                if pos == 0:
                    continue
                rate = DISCOUNT_RATES[card_type]
                discount = round(pos * rate, 2)
                net = round(pos - discount, 2)
                card = DailyCardMetrics(
                    date=jm.date,
                    year=jm.year,
                    month=jm.month,
                    card_type=card_type,
                    pos_total=pos,
                    bank_total=pos,
                    discount_rate=rate,
                    discount_amount=discount,
                    net_amount=net,
                    transaction_count=0,
                    source='jour_backfill',
                )
                db.session.add(card)
                new_card += 1

            if (new_recon + new_card) % 500 == 0 and (new_recon or new_card):
                db.session.commit()

        db.session.commit()
        print(f'\nBackfilled {new_recon} CashRecon rows, {new_card} CardMetrics rows.')

        # Verify
        from sqlalchemy import func
        mx = db.session.query(func.max(DailyCashRecon.date)).scalar()
        mxc = db.session.query(func.max(DailyCardMetrics.date)).scalar()
        print(f'CashRecon max date now: {mx}')
        print(f'CardMetrics max date now: {mxc}')


if __name__ == '__main__':
    main()
