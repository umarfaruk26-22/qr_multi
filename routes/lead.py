from flask import Blueprint, request, jsonify
from services.lead_service import create_lead
from services.analytics_service import record_event

lead_bp = Blueprint('lead', __name__)

def detect_device_type(user_agent_str):
    ua = (user_agent_str or '').lower()
    if any(m in ua for m in ['mobile', 'android', 'iphone', 'ipod']):
        return 'mobile'
    elif 'ipad' in ua or 'tablet' in ua:
        return 'tablet'
    return 'desktop'


@lead_bp.route('/api/leads/submit', methods=['POST'])
def submit_lead():
    """
    Public API endpoint to capture visitor details from profile modal.
    Accepts JSON or FormData.
    """
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict() or {}

    employee_id = data.get('employee_id')
    if not employee_id:
        return jsonify({'success': False, 'message': 'Employee ID is required.'}), 400

    ip_address = request.remote_addr or ''
    user_agent = request.headers.get('User-Agent', '')
    source = data.get('source') or ('qr_scan' if 'q/' in (request.referrer or '') else 'direct_web')

    try:
        lead = create_lead(
            employee_id=employee_id,
            data=data,
            ip_address=ip_address,
            user_agent=user_agent,
            source=source
        )

        # Log analytics event
        record_event(
            employee_id=int(employee_id),
            event_type='visitor_lead_submitted',
            device_type=detect_device_type(user_agent),
            referrer=request.referrer or source,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return jsonify({
            'success': True,
            'lead_id': lead['id'],
            'message': f"Thank you {lead['name']}, your details have been shared with {lead['employee_name']}!"
        }), 200

    except ValueError as val_err:
        return jsonify({'success': False, 'message': str(val_err)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to save your details. Please try again.'}), 500
