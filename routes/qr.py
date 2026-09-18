from flask import Blueprint, redirect, url_for, abort, send_file, request
from services.employee_service import get_employee_by_slug, get_employee_by_id
from services.analytics_service import record_event
from services.qr_service import generate_qr_code
from config import Config
from pathlib import Path

qr_bp = Blueprint('qr', __name__)

def detect_device_type(user_agent_str):
    ua = (user_agent_str or '').lower()
    if any(m in ua for m in ['mobile', 'android', 'iphone', 'ipod']):
        return 'mobile'
    elif 'ipad' in ua or 'tablet' in ua:
        return 'tablet'
    return 'desktop'


@qr_bp.route('/q/<slug>')
def qr_scan_redirect(slug):
    """
    Dedicated entry point for QR code scans.
    1. Records `qr_scan` event into analytics table.
    2. Seamlessly redirects to the employee public profile /<slug>.
    """
    slug = slug.strip().lower()
    emp = get_employee_by_slug(slug)
    
    if emp:
        ua = request.headers.get('User-Agent', '')
        device_type = detect_device_type(ua)
        referrer = request.referrer or 'qr_scan'
        ip_addr = request.remote_addr or ''
        
        record_event(
            employee_id=emp['id'],
            event_type='qr_scan',
            device_type=device_type,
            referrer=referrer,
            ip_address=ip_addr,
            user_agent=ua
        )
        
    return redirect(url_for('employee.public_profile', slug=slug))


@qr_bp.route('/admin/qr/download/<int:employee_id>/<file_format>')
def download_qr(employee_id, file_format):
    """
    Download QR code asset in PNG, SVG, or Branded PNG format.
    """
    emp = get_employee_by_id(employee_id)
    if not emp:
        abort(404)
        
    slug = emp['slug']
    file_format = file_format.lower()
    
    if file_format == 'png':
        filename = f"{slug}.png"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/png'
        download_name = f"{slug}_qr.png"
    elif file_format == 'svg':
        filename = f"{slug}.svg"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/svg+xml'
        download_name = f"{slug}_qr.svg"
    elif file_format in ('branded', 'branded_png'):
        filename = f"{slug}_branded.png"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/png'
        download_name = f"{slug}_branded_qr.png"
    else:
        abort(400)
        
    # Regenerate on-the-fly if file was deleted or missing
    if not filepath.exists():
        generate_qr_code(
            slug=slug,
            employee_id=emp['id'],
            employee_name=f"{emp['first_name']} {emp['last_name']}".strip(),
            designation=emp['designation']
        )
        
    if not filepath.exists():
        abort(404)
        
    return send_file(
        str(filepath),
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_name
    )
