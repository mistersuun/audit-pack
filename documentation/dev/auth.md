# Authentication System

Sources: `routes/auth_v2.py`, `routes/auth.py`, `database/models.py`, `utils/auth_decorators.py`

---

## Overview

The application uses a multi-user authentication system with role-based access control (RBAC).
This replaced an earlier single-PIN system. The legacy `routes/auth.py` redirects all
requests to `routes/auth_v2.py`.

---

## Authentication Method

- **Type**: Username + password, server-side sessions (Flask `session`)
- **Password hashing**: `werkzeug.security.generate_password_hash` / `check_password_hash`
- **Minimum password length**: 8 characters
- **Forced password change**: New users have `must_change_password=True` and are redirected to `/auth/change-password` on first login

---

## User Roles

Six roles defined in the `User.role` column:

| Role | Category | Default Redirect |
|------|----------|-----------------|
| `night_auditor` | Auditor | `/checklist` |
| `front_desk_supervisor` | Auditor | `/checklist` |
| `admin` | Manager | `/direction` |
| `gm` (General Manager) | Manager | `/direction` |
| `gsm` (Guest Services Manager) | Manager | `/direction` |
| `accounting` | Manager | `/direction` |

### Role Type Validation

The login form sends a `role_type` field (`'auditor'` or `'manager'`). The backend validates
that the user's actual role matches the requested type:
- Auditor roles: `night_auditor`, `front_desk_supervisor`
- Manager roles: `admin`, `gm`, `gsm`, `accounting`

---

## Session Management

Session keys set on login:

| Key | Value |
|-----|-------|
| `authenticated` | `True` |
| `user_id` | User primary key |
| `user_role_type` | The user's `role` value |
| `user_role` | `'back'` for night_auditor, `'front'` for front_desk_supervisor, else `None` |
| `user_name` | `full_name_fr` or `username` |
| `login_role_type` | `'auditor'` or `'manager'` (from form) |

Logout clears the entire session via `session.clear()`.

### Protection Decorators

- `@login_required` -- Checks `session['authenticated']`, redirects to login if missing
- `@role_required('admin')` -- Checks that the logged-in user has the specified role
- `get_current_user()` -- Returns the `User` object for the current session

---

## API Endpoints

### Public

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/auth/login` | Login form and handler |
| GET | `/auth/logout` | Clear session, redirect to login |

### Authenticated

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/profile` | User profile page |
| GET/POST | `/auth/change-password` | Change password form |

### Admin Only

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/admin/users` | User management page |
| POST | `/auth/api/admin/users` | Create user (JSON) |
| POST | `/auth/api/admin/users/<id>/toggle` | Activate/deactivate user |

---

## Setup / Configuration

### Initial Setup

1. Ensure `werkzeug` is installed
2. Run the migration script: `python migrate_to_multiuser.py`
3. Default credentials created:
   - Admin: `admin` / `ChangeMe123!`
   - Auditor: `auditor` / `Sheraton858!`
4. Change passwords on first login

### Database

The `User` model is in `database/models.py`. The `users` table is created automatically
by SQLAlchemy on application startup. See `database.md` for schema details.

### Adding Users

Via the admin panel at `/auth/admin/users`, or via API:

```bash
curl -X POST /auth/api/admin/users \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "TempPass123!", "role": "night_auditor", "full_name_fr": "Jean Dupont"}'
```

New users are created with `must_change_password=True`.
