import os
import secrets
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from config import Config
from database.connection import query_db

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    'id': 1,
    'company_name': 'Apex Innovations',
    'company_logo': '',
    'company_phone': '+91 98765 43210',
    'company_email': 'contact@apexinnovations.com',
    'company_website': 'https://apexinnovations.com',
    'primary_color': '#4f46e5',
    'secondary_color': '#06b6d4',
    'default_whatsapp_message': 'Hello, I visited your digital profile and would like to connect.'
}

def get_company_settings():
    """Retrieve company branding settings from database with fallback."""
    try:
        settings = query_db("SELECT * FROM settings WHERE id = 1", one=True)
        if not settings:
            return DEFAULT_SETTINGS.copy()
        return settings
    except Exception as e:
        logger.warning(f"Unable to retrieve settings from DB: {e}. Using defaults.")
        return DEFAULT_SETTINGS.copy()


def update_company_settings(data, logo_file=None):
    """Update company settings and handle logo upload."""
    settings = get_company_settings()
    
    company_name = data.get('company_name', settings['company_name']).strip() or settings['company_name']
    company_phone = data.get('company_phone', '').strip()
    company_email = data.get('company_email', '').strip()
    company_website = data.get('company_website', '').strip()
    primary_color = data.get('primary_color', settings['primary_color']).strip() or '#4f46e5'
    secondary_color = data.get('secondary_color', settings['secondary_color']).strip() or '#06b6d4'
    default_whatsapp_message = data.get('default_whatsapp_message', '').strip() or DEFAULT_SETTINGS['default_whatsapp_message']
    
    logo_path = settings.get('company_logo', '')
    
    if logo_file and logo_file.filename:
        # Save new company logo
        ext = logo_file.filename.rsplit('.', 1)[-1].lower()
        if ext in Config.ALLOWED_EXTENSIONS:
            Config.LOGOS_PATH.mkdir(parents=True, exist_ok=True)
            safe_name = f"company_logo_{secrets.token_hex(4)}.{ext}"
            full_path = Config.LOGOS_PATH / safe_name
            logo_file.save(str(full_path))
            logo_path = f"uploads/logos/{safe_name}"

    query_db(
        """
        INSERT INTO settings (id, company_name, company_logo, company_phone, company_email, company_website, primary_color, secondary_color, default_whatsapp_message)
        VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            company_name = VALUES(company_name),
            company_logo = VALUES(company_logo),
            company_phone = VALUES(company_phone),
            company_email = VALUES(company_email),
            company_website = VALUES(company_website),
            primary_color = VALUES(primary_color),
            secondary_color = VALUES(secondary_color),
            default_whatsapp_message = VALUES(default_whatsapp_message),
            updated_at = CURRENT_TIMESTAMP
        """,
        (company_name, logo_path, company_phone, company_email, company_website, primary_color, secondary_color, default_whatsapp_message),
        commit=True
    )
    
    return get_company_settings()
