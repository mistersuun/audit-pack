"""Reset all seeded users' passwords back to the defaults declared in seed_db.DEFAULT_USERS.

Safe to run any time — only touches the `password_hash` column for the seeded usernames.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from main import create_app
from database import db, User
from seed_db import DEFAULT_USERS


def main():
    app = create_app()
    with app.app_context():
        updated, missing = [], []
        for u in DEFAULT_USERS:
            user = User.query.filter_by(username=u['username']).first()
            if not user:
                missing.append(u['username'])
                continue
            user.set_password(u['password'])
            user.must_change_password = u.get('must_change_password', False)
            user.is_active = True
            updated.append((u['username'], u['password']))
        db.session.commit()

    print('Passwords reset:')
    for username, pwd in updated:
        print(f'  {username:15} -> {pwd}')
    if missing:
        print(f'\n[warn] users not in DB (skipped): {missing}')


if __name__ == '__main__':
    main()
