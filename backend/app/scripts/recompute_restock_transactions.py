"""Recompute and optionally fix restock BankTransaction amounts.

Usage:
  python scripts/recompute_restock_transactions.py [--apply]

If --apply is passed, the script will update transactions in the database.
Otherwise it prints a report (dry-run).

This parses descriptions created by restock_ingredients() which look like:
Restock: IngredientName x2: 10(+2.00)€ = 24.00

It recomputes totals as sum(quantity * (package_price + per_package_pfand)).
"""
import re
import sys
from chame_app.database_instance import Database

APPLY = '--apply' in sys.argv

def parse_restock_description(desc: str):
    lines = desc.splitlines()
    # skip the first 'Restock: ' line if present
    items = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith('restock'):
            # may be just header
            continue
        # Expect pattern: Name x{qty}: {price}(+{per_package_pfand})€ = {total}
        m = re.search(r"x(\d+):\s*([0-9.,]+)\s*\(\+([0-9.,]+)\)€", line)
        if m:
            qty = int(m.group(1))
            price = float(m.group(2).replace(',', '.'))
            per_package_pfand = float(m.group(3).replace(',', '.'))
            items.append((qty, price, per_package_pfand))
        else:
            # fallback: try simpler pattern 'Name x{qty}: {price}€'
            m2 = re.search(r"x(\d+):\s*([0-9.,]+)€", line)
            if m2:
                qty = int(m2.group(1))
                price = float(m2.group(2).replace(',', '.'))
                items.append((qty, price, 0.0))
    return items


def recompute_amount_from_description(desc: str) -> float:
    items = parse_restock_description(desc)
    total = 0.0
    for qty, package_price, per_package_pfand in items:
        total += qty * (package_price + per_package_pfand)
    return round(total, 2)


def main():
    print('Connecting to database...')
    db = create_database()


if __name__ == '__main__':
    # Lazy import to avoid side-effects when module loaded
    from services.admin_api import create_database
    db = create_database()
    session = db.get_session()
    try:
        from models.bank_table import BankTransaction
    except Exception as e:
        print('Failed to import BankTransaction model:', e)
        sys.exit(1)

    txs = session.query(BankTransaction).filter(BankTransaction.description.like('Restock:%')).all()
    if not txs:
        print('No restock transactions found.')
        sys.exit(0)

    changed = 0
    for tx in txs:
        desc = tx.description or ''
        recomputed = recompute_amount_from_description(desc)
        stored = round(float(tx.amount or 0.0), 2)
        if recomputed != stored:
            print(f'Transaction id={tx.transaction_id} stored={stored} recomputed={recomputed} description="{desc.splitlines()[0]}..."')
            if APPLY:
                print(f'  Updating transaction id={tx.transaction_id} amount {stored} -> {recomputed}')
                tx.amount = recomputed
                session.add(tx)
                changed += 1
        else:
            print(f'Transaction id={tx.transaction_id} ok: {stored}')

    if APPLY and changed > 0:
        session.commit()
        print(f'Applied {changed} updates.')
    else:
        print('Dry run complete.')
    session.close()
