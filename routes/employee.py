import urllib.parse
from flask import Blueprint, render_template, request, abort, redirect, url_for, Response
from services.employee_service import get_employee_by_slug, get_employee_categories
from services.analytics_service import record_event
from services.settings_service import get_company_settings
from config import Config

employee_bp = Blueprint('employee', __name__)

def detect_device_type(user_agent_str):
    """Simple user-agent helper to detect device category."""
    ua = (user_agent_str or '').lower()
    if any(m in ua for m in ['mobile', 'android', 'iphone', 'ipod']):
        return 'mobile'
    elif 'ipad' in ua or 'tablet' in ua:
        return 'tablet'
    return 'desktop'


@employee_bp.route('/<slug>')
def public_profile(slug):
    """
    Dynamic public route for employee profiles.
    Renders single dynamic template populated from MySQL.
    """
    slug = slug.strip().lower()
    
    # Exclude static/system endpoints from dynamic slug matcher
    if slug in ('admin', 'api', 'q', 'static', 'uploads', 'favicon.ico', 'vcard'):
        abort(404)
        
    emp = get_employee_by_slug(slug)
    settings = get_company_settings()
    
    if not emp:
        return render_template('public/404.html', slug=slug, settings=settings), 404
        
    # If employee is deactivated by admin
    if not emp.get('is_active'):
        return render_template(
            'public/employee.html',
            employee=emp,
            settings=settings,
            is_unavailable=True,
            base_url=Config.BASE_URL
        ), 200

    # Record profile view event
    ua = request.headers.get('User-Agent', '')
    device_type = detect_device_type(ua)
    referrer = request.referrer or ''
    ip_addr = request.remote_addr or ''
    
    record_event(
        employee_id=emp['id'],
        event_type='profile_view',
        device_type=device_type,
        referrer=referrer,
        ip_address=ip_addr,
        user_agent=ua
    )

    # Format WhatsApp URL
    whatsapp_number = (emp.get('whatsapp') or emp.get('phone') or '').replace('+', '').replace(' ', '').replace('-', '')
    default_msg = settings.get('default_whatsapp_message', 'Hello, I visited your digital profile and would like to connect.')
    encoded_msg = urllib.parse.quote(default_msg)
    
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_msg}" if whatsapp_number else None
    review_categories = get_employee_categories(emp)

    return render_template(
        'public/employee.html',
        employee=emp,
        settings=settings,
        whatsapp_url=whatsapp_url,
        review_categories=review_categories,
        is_unavailable=False,
        base_url=Config.BASE_URL
    )



@employee_bp.route('/vcard/<slug>')
def download_vcard(slug):
    """
    Generates standard RFC 6350 vCard 3.0 file for 1-click contact import on mobile/desktop.
    """
    slug = slug.strip().lower()
    emp = get_employee_by_slug(slug)
    if not emp or not emp.get('is_active'):
        abort(404)
        
    settings = get_company_settings()
    company_name = settings.get('company_name', 'Company')
    
    # Record vcard download event in analytics
    ua = request.headers.get('User-Agent', '')
    device_type = detect_device_type(ua)
    record_event(
        employee_id=emp['id'],
        event_type='vcard_download',
        device_type=device_type,
        referrer=request.referrer or '',
        ip_address=request.remote_addr or '',
        user_agent=ua
    )
    
    first_name = emp.get('first_name', '')
    last_name = emp.get('last_name', '')
    full_name = f"{first_name} {last_name}".strip()
    title = emp.get('designation', '')
    phone = emp.get('phone', '')
    email = emp.get('email', '')
    website = emp.get('website_url') or settings.get('company_website', '')
    bio = emp.get('bio', '')
    profile_url = f"{Config.BASE_URL}/{slug}"
    
    vcard_lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{last_name};{first_name};;;",
        f"FN:{full_name}",
        f"ORG:{company_name};",
    ]
    if title:
        vcard_lines.append(f"TITLE:{title}")
    if phone:
        vcard_lines.append(f"TEL;TYPE=CELL,VOICE:{phone}")
    if email:
        vcard_lines.append(f"EMAIL;TYPE=PREF,INTERNET:{email}")
    if website:
        vcard_lines.append(f"URL;TYPE=WORK:{website}")
    vcard_lines.append(f"URL;TYPE=PROFILE:{profile_url}")
    if bio:
        cleaned_bio = bio.replace('\n', ' ').replace('\r', '')
        vcard_lines.append(f"NOTE:{cleaned_bio}")
    vcard_lines.append("END:VCARD")
    
    vcard_content = "\r\n".join(vcard_lines) + "\r\n"
    
    response = Response(vcard_content, mimetype='text/vcard; charset=utf-8')
    filename = f"{slug}-contact.vcf"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
