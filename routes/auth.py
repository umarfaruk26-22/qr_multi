from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services.auth_service import verify_admin, update_admin_password, generate_csrf_token, validate_csrf, login_required
from services.settings_service import get_company_settings

auth_bp = Blueprint('auth', __name__, url_prefix='/admin')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
        
    settings = get_company_settings()
    
    if request.method == 'POST':
        if not validate_csrf():
            flash('Security token invalid or expired. Please try again.', 'danger')
            return render_template('admin/login.html', settings=settings, csrf_token=generate_csrf_token())
            
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        admin = verify_admin(username, password)
        if admin:
            session.clear()
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session['admin_name'] = admin['name']
            
            flash(f"Welcome back, {admin['name']}!", 'success')
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/admin'):
                return redirect(next_url)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            
    return render_template('admin/login.html', settings=settings, csrf_token=generate_csrf_token())


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    if not validate_csrf():
        flash('Invalid CSRF token.', 'danger')
        return redirect(url_for('admin.settings_view'))
        
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('admin.settings_view'))
        
    success, msg = update_admin_password(session['admin_id'], current_password, new_password)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('admin.settings_view'))
