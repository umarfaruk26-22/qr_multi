from flask import Blueprint, redirect, url_for, abort, send_file, request
from services.employee_service import get_employee_by_slug, get_employee_by_id, get_company_settings
from services.analytics_service import record_event
from services.qr_service import generate_qr_code
from config import Config
from pathlib import Path
import os

qr_bp = Blueprint('qr', __name__)

def detect_device_type(user_agent_str):
    ua = (user_agent_str or '').lower()
    if any(m in ua for m in ['mobile', 'android', 'iphone', 'ipod']):
        return 'mobile'
    elif 'ipad' in ua or 'tablet' in ua:
        return 'tablet'
    return 'desktop'


def _regenerate_employee_qr(emp):
    """Helper to regenerate all QR asset formats for an employee with current branding."""
    company_settings = get_company_settings()
    company_name = company_settings.get('company_name', 'Nexalogic Techno')
    logo_full_path = None
    if emp.get('company_logo') and (Config.BASE_DIR / emp['company_logo']).exists():
        logo_full_path = str(Config.BASE_DIR / emp['company_logo'])
    elif company_settings.get('company_logo') and (Config.BASE_DIR / company_settings['company_logo']).exists():
        logo_full_path = str(Config.BASE_DIR / company_settings['company_logo'])

    return generate_qr_code(
        slug=emp['slug'],
        employee_id=emp['id'],
        employee_name=f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
        designation=emp.get('designation', ''),
        company_name=company_name,
        company_logo_path=logo_full_path
    )


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
    Download QR code asset in JPEG Card, PNG Card, Raw PNG, or SVG format.
    """
    emp = get_employee_by_id(employee_id)
    if not emp:
        abort(404)
        
    slug = emp['slug']
    file_format = (file_format or 'jpg').lower()
    
    if file_format in ('jpg', 'jpeg', 'card', 'card_jpg'):
        filename = f"{slug}_card.jpg"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/jpeg'
        download_name = f"{slug}_digital_card.jpg"
    elif file_format in ('branded', 'branded_png', 'card_png'):
        filename = f"{slug}_branded.png"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/png'
        download_name = f"{slug}_digital_card.png"
    elif file_format in ('png', 'raw', 'raw_qr', 'plain'):
        filename = f"{slug}.png"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/png'
        download_name = f"{slug}_qr.png"
    elif file_format == 'svg':
        filename = f"{slug}.svg"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/svg+xml'
        download_name = f"{slug}_qr.svg"
    else:
        abort(400)
        
    # Regenerate on-the-fly if file was deleted or missing
    if not filepath.exists():
        _regenerate_employee_qr(emp)
        
    if not filepath.exists():
        abort(404)
        
    return send_file(
        str(filepath),
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_name
    )


@qr_bp.route('/qr/download/<slug>')
@qr_bp.route('/qr/download/<slug>/<file_format>')
def public_download_qr(slug, file_format='jpg'):
    """
    Publicly accessible endpoint to download high-res branded JPEG/PNG card, raw QR code, or vector SVG.
    Allows employees or customers to export high quality cards with name, role, and details.
    """
    slug = slug.strip().lower()
    emp = get_employee_by_slug(slug)
    if not emp:
        abort(404)
        
    file_format = (file_format or 'jpg').lower()
    
    if file_format in ('jpg', 'jpeg', 'card', 'card_jpg'):
        filename = f"{slug}_card.jpg"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/jpeg'
        download_name = f"{slug}_digital_card.jpg"
    elif file_format in ('branded', 'branded_png', 'card_png'):
        filename = f"{slug}_branded.png"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/png'
        download_name = f"{slug}_digital_card.png"
    elif file_format in ('raw', 'raw_qr', 'png', 'plain'):
        filename = f"{slug}.png"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/png'
        download_name = f"{slug}_qr.png"
    elif file_format == 'svg':
        filename = f"{slug}.svg"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/svg+xml'
        download_name = f"{slug}_qr.svg"
    else:
        filename = f"{slug}_card.jpg"
        filepath = Config.QR_PATH / filename
        mimetype = 'image/jpeg'
        download_name = f"{slug}_digital_card.jpg"
        
    # Regenerate on-the-fly if file is missing
    if not filepath.exists():
        _regenerate_employee_qr(emp)
        
    if not filepath.exists():
        abort(404)
        
    return send_file(
        str(filepath),
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_name
    )


