# Multi-User Authentication System Setup Guide

## Overview

This document explains the new multi-user authentication system that replaces the single PIN-based authentication.

## Files Created

### 1. Database Models (`database/models.py`)
- **User Model**: Stores user accounts with password hashing
  - Fields: username, email, password_hash, role, full_name_fr, is_active, must_change_password, last_login
  - Methods: set_password(), check_password(), has_role(), to_dict()

- **AuditSession Model**: Track audit sessions per user
  - Fields: date, auditor_id (FK to User), started_at, completed_at, notes, rj_file_path

### 2. Authentication Routes (`routes/auth_v2.py`)
New Blueprint with the following endpoints:

- `GET/POST /auth/login` - User login with username and password
- `GET /auth/logout` - Clear session and logout
- `GET /auth/profile` - View and manage user profile
- `POST /auth/change-password` - Change user password
- `GET /auth/admin/users` - Admin panel for user management
- `POST /api/admin/users` - Create new user (admin only)
- `POST /api/admin/users/<id>/toggle` - Activate/deactivate user (admin only)

### 3. Authorization Decorators (`utils/auth_decorators.py`)
- `@login_required` - Require authentication
- `@role_required(*roles)` - Restrict by role
- `get_current_user()` - Get current user from session
- Role configuration constants

### 4. Templates

#### Authentication Pages
- `templates/auth/login.html` - Modern login form with username/password
- `templates/auth/profile.html` - User profile and password change
- `templates/auth/change_password.html` - Forced password change on first login

#### Admin Pages
- `templates/admin/users.html` - User management interface with create/deactivate features

### 5. Migration Script (`migrate_to_multiuser.py`)
Initializes the system with default users and tables.

## Installation & Setup

### Step 1: Install Dependencies
```bash
pip install flask-sqlalchemy werkzeug
```

### Step 2: Run Migration
```bash
python migrate_to_multiuser.py
```

This will:
- Create User and AuditSession tables
- Create default admin user (admin / ChangeMe123!)
- Create default auditor user (auditor / Sheraton858!)
- Print credentials to console

### Step 3: Start Application
```bash
python main.py
```

### Step 4: First Login
1. Navigate to `http://localhost:5000/auth/login`
2. Log in with admin credentials
3. You'll be prompted to change your password
4. After password change, access the admin panel at `/auth/admin/users`
5. Create additional users as needed

## User Roles

The system includes the following roles:

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | System administrator | Full access, user management |
| `night_auditor` | Night audit staff | Full audit tools access |
| `front_desk_supervisor` | Front desk supervisor | Limited access, reports, documentation |
| `gm` | General Manager | Reports, CRM, documentation |
| `gsm` | General Service Manager | Reports, CRM, documentation |
| `accounting` | Accounting department | Reports, balances, documentation |

## Session Variables

When a user logs in, these session variables are set:

```python
session['authenticated'] = True           # Boolean: user is logged in
session['user_id'] = user.id             # Integer: user's database ID
session['user_role_type'] = user.role    # String: user's role
session['user_role'] = 'back'|'front'    # String: interface type (legacy)
session['user_name'] = user.full_name_fr # String: user's display name
```

## Using Decorators

### Require Login
```python
from utils.auth_decorators import login_required

@app.route('/protected')
@login_required
def protected_route():
    return 'This requires login'
```

### Require Specific Roles
```python
from utils.auth_decorators import role_required

@app.route('/admin-only')
@role_required('admin')
def admin_only():
    return 'Admins only'

# Multiple roles allowed
@app.route('/reports')
@role_required('admin', 'gm', 'gsm', 'accounting')
def reports():
    return 'Reports for managers'
```

### Get Current User
```python
from utils.auth_decorators import get_current_user

@app.route('/user-info')
def user_info():
    user = get_current_user()
    return f'Hello {user.full_name_fr}'
```

## Security Features

1. **Password Hashing**: Uses werkzeug.security with bcrypt-like hashing
2. **Mandatory Password Change**: New users must change password on first login
3. **Session Management**: Secure session tokens via Flask
4. **Role-Based Access Control (RBAC)**: Fine-grained permission control
5. **Login Tracking**: Last login timestamp recorded per user

## Database Schema

### users table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'night_auditor',
    full_name_fr VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    must_change_password BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### audit_sessions table
```sql
CREATE TABLE audit_sessions (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    auditor_id INTEGER NOT NULL REFERENCES users(id),
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    notes TEXT,
    rj_file_path VARCHAR(500)
);
```

## Creating Users via Admin Panel

1. Log in as admin
2. Navigate to `/auth/admin/users`
3. Fill in the user creation form:
   - Username (required, must be unique)
   - Full Name (French)
   - Email (optional)
   - Role (required)
   - Initial Password (minimum 8 characters)
4. Click "Create User"
5. New user must change password on first login

## Creating Users Programmatically

```python
from database import db
from database.models import User

# Create new user
user = User(
    username='jdupont',
    full_name_fr='Jean Dupont',
    email='jean@example.com',
    role='night_auditor',
    is_active=True,
    must_change_password=True
)
user.set_password('InitialPassword123!')
db.session.add(user)
db.session.commit()
```

## Backward Compatibility

The old `auth.py` blueprint is still registered but the root `/` now redirects to the new login page:
- Old PIN-based login: `/login` (deprecated)
- New multi-user login: `/auth/login` (active)

To use the new system exclusively, users should navigate to `/auth/login`.

## Troubleshooting

### Database Already Exists
If you get "tables already exist" error, the migration script handles this gracefully by skipping existing tables and users.

### Password Requirements
- Minimum 8 characters
- No complexity requirements
- Can be changed anytime in profile

### User Not Found
- Check username is exact (case-sensitive)
- Verify user exists in admin panel
- Ensure user account is active (not deactivated)

### Decorators Not Working
- Ensure `from utils.auth_decorators import ...` is at the top
- Check session['authenticated'] is set (debug with print)
- Verify user has required role

## Testing

```bash
# Test imports
python -c "from routes.auth_v2 import auth_v2; print('✓ auth_v2 imported')"

# Test decorators
python -c "from utils.auth_decorators import login_required; print('✓ decorators imported')"

# Run migration
python migrate_to_multiuser.py

# Start app
python main.py
```

## Default Credentials

| User | Username | Password | Role |
|------|----------|----------|------|
| Admin | `admin` | `ChangeMe123!` | Administrator |
| Auditor | `auditor` | `Sheraton858!` | Night Auditor |

**Important**: Change these passwords immediately after first login!

## Next Steps

1. Create additional user accounts for your team
2. Update the basehtml sidebar to show user information
3. Apply role-based decorators to protected routes
4. Customize role permissions as needed
5. Monitor login activity via `user.last_login`

