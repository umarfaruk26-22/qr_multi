from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, Response
from services.auth_service import login_required, generate_csrf_token, validate_csrf
from services.employee_service import (
    get_employees, get_employee_by_id, create_employee, update_employee,
    toggle_employee_status, soft_delete_employee, get_employee_counts
)
from services.analytics_service import (
    get_global_analytics_summary, get_employee_analytics, get_recent_activity_logs
)
from services.lead_service import (
    get_leads, get_lead_summary, get_recent_leads, delete_lead as remove_lead, export_leads_csv
)
from services.settings_service import get_company_settings, update_company_settings
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def before_admin_request():
    """Ensure user is logged in for all admin routes."""
    pass


@admin_bp.route('/dashboard')
def dashboard():
    """Admin Dashboard view."""
    counts = get_employee_counts()
    summary = get_global_analytics_summary()
    lead_summary = get_lead_summary()
    recent_logs = get_recent_activity_logs(limit=10)
    recent_leads = get_recent_leads(limit=6)
    settings = get_company_settings()
    
    # Recent 5 employees
    recent_employees_res = get_employees(page=1, per_page=5)
    
    return render_template(
        'admin/dashboard.html',
        counts=counts,
        summary=summary,
        lead_summary=lead_summary,
        recent_logs=recent_logs,
        recent_leads=recent_leads,
        recent_employees=recent_employees_res['employees'],
        settings=settings,
        active_page='dashboard',
        csrf_token=generate_csrf_token()
    )



@admin_bp.route('/employees')
def employees_list():
    """Employee management list with search, filter, and pagination."""
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'all').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    data = get_employees(search=search, status=status, page=page, per_page=per_page)
    counts = get_employee_counts()
    settings = get_company_settings()
    
    return render_template(
        'admin/employees.html',
        employees=data['employees'],
        total=data['total'],
        page=data['page'],
        pages=data['pages'],
        per_page=data['per_page'],
        search=search,
        status=status,
        counts=counts,
        settings=settings,
        active_page='employees',
        csrf_token=generate_csrf_token()
    )


@admin_bp.route('/employees/create', methods=['GET', 'POST'])
def add_employee():
    """Create a new employee profile."""
    settings = get_company_settings()
    
    if request.method == 'POST':
        if not validate_csrf():
            flash('Security token invalid. Please try again.', 'danger')
            return redirect(url_for('admin.add_employee'))
            
        try:
            profile_file = request.files.get('profile_image')
            logo_file = request.files.get('company_logo')
            
            emp_id, slug = create_employee(
                form_data=request.form,
                profile_file=profile_file,
                logo_file=logo_file
            )
            flash(f'Employee profile created successfully! Public URL: /{slug}', 'success')
            return redirect(url_for('admin.employee_details', id=emp_id))
        except Exception as e:
            flash(f'Failed to create employee: {str(e)}', 'danger')
            return render_template(
                'admin/add_employee.html',
                form=request.form,
                settings=settings,
                active_page='add_employee',
                csrf_token=generate_csrf_token()
            )
            
    return render_template(
        'admin/add_employee.html',
        form={},
        settings=settings,
        active_page='add_employee',
        csrf_token=generate_csrf_token()
    )


@admin_bp.route('/employees/<int:id>')
def employee_details(id):
    """View single employee details, QR downloads, and individual analytics."""
    emp = get_employee_by_id(id)
    if not emp:
        flash('Employee profile not found.', 'warning')
        return redirect(url_for('admin.employees_list'))
        
    analytics = get_employee_analytics(id)
    settings = get_company_settings()
    
    return render_template(
        'admin/employee_details.html',
        employee=emp,
        analytics=analytics,
        settings=settings,
        base_url=Config.BASE_URL,
        active_page='employees',
        csrf_token=generate_csrf_token()
    )


@admin_bp.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
def edit_employee(id):
    """Edit existing employee profile."""
    emp = get_employee_by_id(id)
    if not emp:
        flash('Employee profile not found.', 'warning')
        return redirect(url_for('admin.employees_list'))
        
    settings = get_company_settings()
    
    if request.method == 'POST':
        if not validate_csrf():
            flash('Security token invalid. Please try again.', 'danger')
            return redirect(url_for('admin.edit_employee', id=id))
            
        try:
            profile_file = request.files.get('profile_image')
            logo_file = request.files.get('company_logo')
            
            emp_id, slug = update_employee(
                employee_id=id,
                form_data=request.form,
                profile_file=profile_file,
                logo_file=logo_file
            )
            flash('Employee profile updated successfully!', 'success')
            return redirect(url_for('admin.employee_details', id=id))
        except Exception as e:
            flash(f'Failed to update employee: {str(e)}', 'danger')
            
    return render_template(
        'admin/edit_employee.html',
        employee=emp,
        settings=settings,
        active_page='employees',
        csrf_token=generate_csrf_token()
    )


@admin_bp.route('/employees/<int:id>/toggle-status', methods=['POST'])
def toggle_status(id):
    """Toggle active/inactive status."""
    if not validate_csrf():
        return jsonify({'success': False, 'message': 'Invalid CSRF token'}), 400
        
    new_status = toggle_employee_status(id)
    if new_status is None:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
    status_label = 'Activated' if new_status == 1 else 'Deactivated'
    return jsonify({
        'success': True,
        'is_active': new_status,
        'message': f'Employee status changed to {status_label}'
    })


@admin_bp.route('/employees/<int:id>/delete', methods=['POST'])
def delete_employee(id):
    """Soft-delete an employee."""
    if not validate_csrf():
        flash('Invalid CSRF token.', 'danger')
        return redirect(url_for('admin.employees_list'))
        
    soft_delete_employee(id)
    flash('Employee profile deleted successfully.', 'success')
    return redirect(url_for('admin.employees_list'))


@admin_bp.route('/analytics')
def analytics_view():
    """Global Analytics and engagement metrics breakdown."""
    summary = get_global_analytics_summary()
    recent_logs = get_recent_activity_logs(limit=50)
    settings = get_company_settings()
    
    # Top active employees
    employees_res = get_employees(page=1, per_page=50)
    employee_stats = []
    for emp in employees_res['employees']:
        metrics = get_employee_analytics(emp['id'])
        employee_stats.append({
            'employee': emp,
            'metrics': metrics
        })
    # Sort by total profile views descending
    employee_stats.sort(key=lambda x: x['metrics']['profile_views'] + x['metrics']['qr_scans'], reverse=True)
    
    return render_template(
        'admin/analytics.html',
        summary=summary,
        recent_logs=recent_logs,
        employee_stats=employee_stats,
        settings=settings,
        active_page='analytics',
        csrf_token=generate_csrf_token()
    )


@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings_view():
    """Company settings and branding configuration."""
    if request.method == 'POST':
        if not validate_csrf():
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('admin.settings_view'))
            
        logo_file = request.files.get('company_logo')
        updated = update_company_settings(request.form, logo_file)
        flash('Company settings and branding saved successfully!', 'success')
        return render_template(
            'admin/settings.html',
            settings=updated,
            active_page='settings',
            csrf_token=generate_csrf_token()
        )
        
    settings = get_company_settings()
    return render_template(
        'admin/settings.html',
        settings=settings,
        active_page='settings',
        csrf_token=generate_csrf_token()
    )


@admin_bp.route('/leads')
def leads_view():
    """Visitor leads management page with search, employee filter, and summary breakdown."""
    search = request.args.get('search', '').strip()
    employee_id = request.args.get('employee_id', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    data = get_leads(
        search=search,
        employee_id=employee_id if employee_id else None,
        page=page,
        per_page=per_page
    )
    summary = get_lead_summary()
    employees_res = get_employees(page=1, per_page=100)
    settings = get_company_settings()

    return render_template(
        'admin/leads.html',
        leads=data['leads'],
        total=data['total'],
        page=data['page'],
        pages=data['pages'],
        per_page=data['per_page'],
        search=search,
        employee_id=employee_id,
        summary=summary,
        all_employees=employees_res['employees'],
        settings=settings,
        active_page='leads',
        csrf_token=generate_csrf_token()
    )


@admin_bp.route('/leads/export')
def export_leads():
    """Exports filtered visitor leads to CSV or Excel file."""
    search = request.args.get('search', '').strip()
    employee_id = request.args.get('employee_id', '').strip()
    export_format = request.args.get('format', 'csv').lower()

    csv_data = export_leads_csv(
        employee_id=employee_id if employee_id else None,
        search=search
    )

    from datetime import datetime
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M')

    if export_format in ('excel', 'xlsx', 'xls'):
        filename = f"visitor_leads_excel_{timestamp_str}.csv"
        mimetype = 'application/vnd.ms-excel; charset=utf-8'
    else:
        filename = f"visitor_leads_{timestamp_str}.csv"
        mimetype = 'text/csv; charset=utf-8'

    response = Response(csv_data, mimetype=mimetype)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response



@admin_bp.route('/leads/<int:id>/delete', methods=['POST'])
def delete_lead_route(id):
    """Delete a visitor lead record."""
    if not validate_csrf():
        flash('Invalid CSRF token.', 'danger')
        return redirect(url_for('admin.leads_view'))

    success = remove_lead(id)
    if success:
        flash('Visitor lead record deleted successfully.', 'success')
    else:
        flash('Failed to delete lead or lead not found.', 'warning')
    return redirect(url_for('admin.leads_view'))


# ==========================================
# REST API Endpoints (Admin Protected)
# ==========================================

api_bp = Blueprint('api_admin', __name__, url_prefix='/api')

@api_bp.route('/employees', methods=['GET'])
@login_required
def api_get_employees():
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    data = get_employees(search=search, status=status, page=page, per_page=per_page)
    return jsonify({'success': True, 'data': data})


@api_bp.route('/employees/<int:id>', methods=['GET'])
@login_required
def api_get_employee(id):
    emp = get_employee_by_id(id)
    if not emp:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    return jsonify({'success': True, 'data': emp})


@api_bp.route('/employees/<int:id>', methods=['DELETE'])
@login_required
def api_delete_employee(id):
    soft_delete_employee(id)
    return jsonify({'success': True, 'message': 'Employee deleted successfully'})
