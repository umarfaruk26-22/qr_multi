from flask import Blueprint, request, jsonify
from services.analytics_service import record_event, get_employee_analytics, ALLOWED_EVENTS
from services.auth_service import login_required

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

def detect_device_type(user_agent_str):
    ua = (user_agent_str or '').lower()
    if any(m in ua for m in ['mobile', 'android', 'iphone', 'ipod']):
        return 'mobile'
    elif 'ipad' in ua or 'tablet' in ua:
        return 'tablet'
    return 'desktop'


@analytics_bp.route('/event', methods=['POST'])
def log_event():
    """
    Public REST API endpoint to log client-side engagement events
    (e.g., WhatsApp click, Google Review click, Social links clicks).
    """
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({'success': False, 'message': 'Missing event payload'}), 400
        
    employee_id = data.get('employee_id')
    event_type = data.get('event_type')
    
    if not employee_id or not event_type:
        return jsonify({'success': False, 'message': 'employee_id and event_type are required'}), 400
        
    if event_type not in ALLOWED_EVENTS:
        return jsonify({'success': False, 'message': 'Invalid event_type'}), 400
        
    ua = request.headers.get('User-Agent', '')
    device_type = data.get('device_type') or detect_device_type(ua)
    referrer = data.get('referrer') or request.referrer or ''
    ip_addr = request.remote_addr or ''
    
    success = record_event(
        employee_id=int(employee_id),
        event_type=event_type,
        device_type=device_type,
        referrer=referrer,
        ip_address=ip_addr,
        user_agent=ua
    )
    
    return jsonify({'success': success})


@analytics_bp.route('/employee/<int:employee_id>', methods=['GET'])
@login_required
def get_single_employee_analytics(employee_id):
    """
    Protected API to fetch analytics metrics for an employee.
    """
    metrics = get_employee_analytics(employee_id)
    return jsonify({'success': True, 'data': metrics})
