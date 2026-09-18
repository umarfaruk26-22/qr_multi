import secrets
from functools import wraps
from flask import session, redirect, url_for, request, abort, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database.connection import query_db

def verify_admin(username, password):
    """
    Verify admin credentials against database.
    Returns admin dict if valid and active, else None.
    """
    if not username or not password:
        return None
        
    admin = query_db(
        "SELECT id, username, password_hash, name, is_active FROM admins WHERE username = %s",
        (username.strip(),),
        one=True
    )
    
    if admin and admin.get('is_active') and check_password_hash(admin['password_hash'], password):
        return {
            'id': admin['id'],
            'username': admin['username'],
            'name': admin['name']
        }
    return None


def update_admin_password(admin_id, current_password, new_password):
    """
    Update password for an admin after verifying current password.
    """
    admin = query_db(
        "SELECT id, password_hash FROM admins WHERE id = %s",
        (admin_id,),
        one=True
    )
    if not admin:
        return False, "Admin account not found."
        
    if not check_password_hash(admin['password_hash'], current_password):
        return False, "Current password is incorrect."
        
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
        
    new_hash = generate_password_hash(new_password)
    query_db(
        "UPDATE admins SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (new_hash, admin_id),
        commit=True
    )
    return True, "Password updated successfully."


def login_required(f):
    """
    Decorator to protect admin routes.
    Redirects unauthenticated requests to /admin/login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            if request.path.startswith('/api/'):
                return {'success': False, 'message': 'Authentication required.'}, 401
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def generate_csrf_token():
    """Generate or retrieve a CSRF token for the current session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf():
    """Validate CSRF token from request headers or form data."""
    token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    session_token = session.get('_csrf_token')
    if not session_token or not token or token != session_token:
        return False
    return True
