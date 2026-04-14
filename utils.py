import re
from functools import wraps

from flask import flash, redirect, session, url_for

from db import execute_read_one


# ─────────────────────────────────────────────
# Auth decorators
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'username' not in session:
                flash('Please log in first.', 'error')
                return redirect(url_for('auth.login'))
            if session.get('role') not in roles:
                flash('Access denied: insufficient permissions.', 'error')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
# Password validation
# ─────────────────────────────────────────────

def validate_password(password):
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter.')
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one digit.')
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append('Password must contain at least one special character (@, #, $, %, &, etc.).')
    return errors


# ─────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────

def get_manager_club(person_id):
    return execute_read_one(
        'SELECT club_id, club_name FROM Club WHERE manager_id = %s',
        (person_id,)
    )


def get_player_current_club(person_id):
    """Return club_name for player's current club (loan preferred over permanent)."""
    loan = execute_read_one(
        '''SELECT cl.club_name FROM Contract c
           JOIN Loan_Contract lc ON lc.contract_id = c.contract_id
           JOIN Club cl ON cl.club_id = c.club_id
           WHERE c.player_id = %s AND c.start_date <= CURDATE() AND c.end_date >= CURDATE()
           LIMIT 1''',
        (person_id,)
    )
    if loan:
        return loan['club_name']
    perm = execute_read_one(
        '''SELECT cl.club_name FROM Contract c
           JOIN Permanent_Contract pc ON pc.contract_id = c.contract_id
           JOIN Club cl ON cl.club_id = c.club_id
           WHERE c.player_id = %s AND c.start_date <= CURDATE() AND c.end_date >= CURDATE()
           LIMIT 1''',
        (person_id,)
    )
    return perm['club_name'] if perm else 'No Club'
