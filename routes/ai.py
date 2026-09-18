from flask import Blueprint, request, jsonify
from services.employee_service import get_employee_by_id, get_employee_categories
from services.settings_service import get_company_settings
from services.ai_review_service import generate_review_suggestions
from services.analytics_service import record_event

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/api/ai/suggest-reviews', methods=['POST'])
def suggest_reviews():
    """
    API Endpoint returning 3 dynamic AI-generated Google Review suggestions
    customized to the employee's role, company, tone, focus topic, star rating (1-5), and categories.
    """
    data = request.get_json(silent=True) or {}
    employee_id = data.get('employee_id')
    tone = data.get('tone', 'friendly')
    custom_topic = data.get('topic', '').strip()
    
    # Extract star rating
    raw_stars = data.get('star_rating') if 'star_rating' in data else data.get('stars', 5)
    try:
        star_rating = max(1, min(5, int(raw_stars)))
    except (TypeError, ValueError):
        star_rating = 5

    # Extract categories
    req_categories = data.get('categories')
    
    if not employee_id:
        return jsonify({'success': False, 'message': 'employee_id is required'}), 400
        
    employee = get_employee_by_id(employee_id)
    if not employee or not employee.get('is_active'):
        return jsonify({'success': False, 'message': 'Employee profile not found or inactive'}), 404
        
    settings = get_company_settings()
    company_name = settings.get('company_name', 'Enterprise')
    
    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
    designation = employee.get('designation', '')
    bio = employee.get('bio', '')
    gmb_url = employee.get('google_review_url', '')

    # Determine active categories
    if req_categories is not None:
        if isinstance(req_categories, list):
            active_categories = [str(c).strip() for c in req_categories if str(c).strip()]
        else:
            active_categories = [c.strip() for c in str(req_categories).split(',') if c.strip()]
    else:
        active_categories = get_employee_categories(employee)
    
    # Record event in analytics
    ua = request.headers.get('User-Agent', '')
    ip_addr = request.remote_addr or ''
    record_event(
        employee_id=employee['id'],
        event_type='ai_review_generated',
        device_type='web',
        referrer=request.referrer or '',
        ip_address=ip_addr,
        user_agent=ua
    )
    
    result = generate_review_suggestions(
        employee_name=employee_name,
        designation=designation,
        company_name=company_name,
        bio=bio,
        tone=tone,
        custom_topic=custom_topic,
        star_rating=star_rating,
        categories=active_categories
    )
    
    return jsonify({
        'success': True,
        'source': result.get('source', 'gemini_ai'),
        'model': result.get('model', 'gemini-3.7-flash'),
        'employee_name': employee_name,
        'designation': designation,
        'company_name': company_name,
        'gmb_url': gmb_url,
        'star_rating': star_rating,
        'categories': active_categories,
        'reviews': result.get('reviews', [])
    })
