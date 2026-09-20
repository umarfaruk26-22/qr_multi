import os
import re
import secrets
import math
from pathlib import Path
from werkzeug.utils import secure_filename
from config import Config
from database.connection import query_db, get_db_cursor
from services.slug_service import generate_unique_slug
from services.qr_service import generate_qr_code
from services.settings_service import get_company_settings

# Platform Metadata Definition for Social & Channel Links
PLATFORM_METADATA = {
    'twitter': {
        'default_title': 'Twitter / X',
        'placeholder': 'https://x.com/username',
        'brand_color': '#0f1419',
        'badge_class': 'badge-twitter',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'
    },
    'telegram': {
        'default_title': 'Telegram',
        'placeholder': 'https://t.me/username',
        'brand_color': '#229ED9',
        'badge_class': 'badge-telegram',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>'
    },
    'messenger': {
        'default_title': 'Messenger',
        'placeholder': 'https://m.me/username',
        'brand_color': '#0084FF',
        'badge_class': 'badge-messenger',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0C5.373 0 0 4.974 0 11.111c0 3.498 1.744 6.614 4.469 8.654V24l4.088-2.242c1.077.299 2.222.463 3.443.463 6.627 0 12-4.975 12-11.11S18.627 0 12 0zm1.191 14.963l-3.055-3.26-5.964 3.26 6.559-6.963 3.13 3.259 5.889-3.259-6.559 6.963z"/></svg>'
    },
    'github': {
        'default_title': 'GitHub',
        'placeholder': 'https://github.com/username',
        'brand_color': '#24292e',
        'badge_class': 'badge-github',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>'
    },
    'discord': {
        'default_title': 'Discord',
        'placeholder': 'https://discord.gg/invite',
        'brand_color': '#5865F2',
        'badge_class': 'badge-discord',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>'
    },
    'calendly': {
        'default_title': 'Schedule Meeting',
        'placeholder': 'https://calendly.com/your-calendar',
        'brand_color': '#006BFF',
        'badge_class': 'badge-calendly',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
    },
    'behance': {
        'default_title': 'Behance Portfolio',
        'placeholder': 'https://behance.net/username',
        'brand_color': '#1769ff',
        'badge_class': 'badge-behance',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff"><path d="M22 7h-7v-2h7v2zm1.726 10c-.442 1.297-2.029 3-4.726 3-3.341 0-5.834-2.261-5.834-5.908 0-3.486 2.368-6.092 5.76-6.092 3.398 0 5.405 2.463 5.405 5.922 0 .428-.046.856-.091 1.078h-8.232c.105 1.579 1.364 2.825 3.064 2.825 1.352 0 2.213-.647 2.684-1.325h1.97zm-5.011-4.225c-.092-1.282-1.066-2.162-2.387-2.162-1.35 0-2.316.91-2.484 2.162h4.871zm-13.715-7.775h5.482c2.094 0 3.518.91 3.518 2.646 0 1.157-.614 2.067-1.636 2.417 1.356.37 2.136 1.492 2.136 2.879 0 2.083-1.652 3.058-3.87 3.058h-5.63v-11zm2.741 4.542h2.247c.854 0 1.411-.424 1.411-1.127 0-.756-.566-1.156-1.411-1.156h-2.247v2.283zm0 4.195h2.464c.949 0 1.554-.484 1.554-1.289 0-.847-.645-1.267-1.639-1.267h-2.379v2.556z"/></svg>'
    },
    'spotify': {
        'default_title': 'Spotify / Music',
        'placeholder': 'https://open.spotify.com/user/username',
        'brand_color': '#1DB954',
        'badge_class': 'badge-spotify',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.49 17.307a.755.755 0 0 1-1.04.249c-2.85-1.741-6.438-2.135-10.665-1.169a.755.755 0 0 1-.336-1.472c4.629-1.057 8.59-.611 11.792 1.352.36.221.472.688.249 1.04zm1.464-3.256a.945.945 0 0 1-1.301.311c-3.263-2.006-8.238-2.587-12.098-1.415a.946.946 0 0 1-.557-1.808c4.412-1.339 9.897-.692 13.645 1.611a.946.946 0 0 1 .311 1.301zm.126-3.393c-3.914-2.324-10.364-2.538-14.095-1.405a1.133 1.133 0 1 1-.659-2.171c4.288-1.302 11.41-1.05 15.918 1.626a1.134 1.134 0 0 1-1.164 1.95z"/></svg>'
    },
    'pinterest': {
        'default_title': 'Pinterest',
        'placeholder': 'https://pinterest.com/username',
        'brand_color': '#E60023',
        'badge_class': 'badge-pinterest',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff"><path d="M12 0a12 12 0 0 0-4.37 23.18c-.03-.97-.05-2.47.1-3.53l1.1-4.68s-.28-.56-.28-1.38c0-1.29.75-2.26 1.68-2.26.79 0 1.17.6 1.17 1.31 0 .8-.51 1.99-.77 3.1-.22.93.47 1.68 1.38 1.68 1.66 0 2.94-1.75 2.94-4.27 0-2.23-1.6-3.79-3.9-3.79-2.66 0-4.22 2-4.22 4.06 0 .8.31 1.67.7 2.14.08.1.09.18.07.28l-.26 1.07c-.04.18-.14.22-.32.13-1.2-.56-1.95-2.31-1.95-3.72 0-3.03 2.2-5.81 6.35-5.81 3.33 0 5.92 2.38 5.92 5.55 0 3.31-2.09 5.98-4.99 5.98-.97 0-1.89-.51-2.2-.1.11l-.6 2.28c-.22.84-.81 1.89-1.21 2.53A12 12 0 1 0 12 0z"/></svg>'
    },
    'custom': {
        'default_title': 'Custom Link',
        'placeholder': 'https://your-custom-link.com',
        'brand_color': '#6366f1',
        'badge_class': 'badge-custom',
        'svg_icon': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1 4-10z"></path></svg>'
    }
}

def get_platform_metadata(platform_key: str):
    """Retrieve brand styling and icon for a given platform."""
    key = (platform_key or 'custom').strip().lower()
    return PLATFORM_METADATA.get(key, PLATFORM_METADATA['custom'])

def get_custom_links_for_employee(employee_id: int):
    """Fetch custom social/channel links for an employee."""
    rows = query_db(
        "SELECT * FROM custom_social_links WHERE employee_id = %s ORDER BY sort_order ASC, id ASC",
        (employee_id,)
    )
    if not rows:
        return []
    enriched = []
    for r in rows:
        meta = get_platform_metadata(r.get('platform', 'custom'))
        enriched.append({
            'id': r['id'],
            'employee_id': r['employee_id'],
            'platform': r.get('platform', 'custom'),
            'title': r.get('title') or meta['default_title'],
            'url': r.get('url', ''),
            'sort_order': r.get('sort_order', 0),
            'brand_color': meta['brand_color'],
            'badge_class': meta['badge_class'],
            'svg_icon': meta['svg_icon'],
            'placeholder': meta['placeholder']
        })
    return enriched

def _extract_custom_links(form_data):
    """Extract list of custom links from submitted form data."""
    if hasattr(form_data, 'getlist'):
        platforms = form_data.getlist('custom_platform[]') or form_data.getlist('custom_platform')
        titles = form_data.getlist('custom_title[]') or form_data.getlist('custom_title')
        urls = form_data.getlist('custom_url[]') or form_data.getlist('custom_url')
    elif isinstance(form_data, dict):
        platforms = form_data.get('custom_platform[]') or form_data.get('custom_platform') or []
        titles = form_data.get('custom_title[]') or form_data.get('custom_title') or []
        urls = form_data.get('custom_url[]') or form_data.get('custom_url') or []
        if isinstance(platforms, str): platforms = [platforms]
        if isinstance(titles, str): titles = [titles]
        if isinstance(urls, str): urls = [urls]
    else:
        return []

    custom_links = []
    count = max(len(platforms), len(titles), len(urls))
    for i in range(count):
        plat = platforms[i].strip().lower() if i < len(platforms) else 'custom'
        title = titles[i].strip() if i < len(titles) else ''
        url = urls[i].strip() if i < len(urls) else ''
        if url:
            if not title:
                meta = get_platform_metadata(plat)
                title = meta['default_title']
            custom_links.append({
                'platform': plat or 'custom',
                'title': title,
                'url': url,
                'sort_order': i
            })
    return custom_links

def _save_custom_links(cursor, employee_id, form_data, is_update=False):
    """Save custom links for employee."""
    if is_update:
        cursor.execute("DELETE FROM custom_social_links WHERE employee_id = %s", (employee_id,))
    
    custom_links = _extract_custom_links(form_data)
    for link in custom_links:
        cursor.execute(
            """
            INSERT INTO custom_social_links (employee_id, platform, title, url, sort_order)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (employee_id, link['platform'], link['title'], link['url'], link['sort_order'])
        )

def optimize_google_review_url(url: str) -> str:
    """
    Optimizes a Google Review URL so it directly triggers the 5-star Write Review popup dialog.
    In Google Search URLs, #lrd=<id>,1 opens reviews list, whereas #lrd=<id>,3 opens the
    direct write-review composer dialog modal.
    """
    if not url:
        return ""
    url = url.strip()
    if "lrd=" in url:
        # Convert ,1 to ,3 in #lrd=0x...:0x...,1
        url = re.sub(r'(lrd=[a-zA-Z0-9_xX:]+),1', r'\1,3', url)
    return url

def get_employee_counts():
    """Retrieve counts for total, active, and inactive employees."""
    row = query_db(
        """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive
        FROM employees 
        WHERE is_deleted = 0
        """,
        one=True
    )
    return {
        'total': row['total'] or 0,
        'active': row['active'] or 0,
        'inactive': row['inactive'] or 0
    }


def get_employees(search=None, status=None, page=1, per_page=20):
    """
    Get paginated employees list with optional search and status filters.
    """
    page = max(1, int(page))
    per_page = max(1, min(100, int(per_page)))
    offset = (page - 1) * per_page
    
    where_clauses = ["e.is_deleted = 0"]
    params = []
    
    if search:
        search_term = f"%{search.strip()}%"
        where_clauses.append("(e.first_name LIKE %s OR e.last_name LIKE %s OR e.slug LIKE %s OR e.designation LIKE %s)")
        params.extend([search_term, search_term, search_term, search_term])
        
    if status == 'active':
        where_clauses.append("e.is_active = 1")
    elif status == 'inactive':
        where_clauses.append("e.is_active = 0")
        
    where_sql = " AND ".join(where_clauses)
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM employees e WHERE {where_sql}"
    total_row = query_db(count_query, tuple(params), one=True)
    total = total_row['total'] if total_row else 0
    pages = math.ceil(total / per_page) if total > 0 else 1
    
    # Get page rows
    select_query = f"""
        SELECT e.*, q.qr_url, q.png_path, q.svg_path, q.branded_png_path
        FROM employees e
        LEFT JOIN qr_codes q ON e.id = q.employee_id
        WHERE {where_sql}
        ORDER BY e.id DESC
        LIMIT %s OFFSET %s
    """
    query_params = list(params) + [per_page, offset]
    employees = query_db(select_query, tuple(query_params))
    if employees:
        employees = [_ensure_employee_qr(e) for e in employees]
    
    return {
        'employees': employees or [],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages
    }


def _ensure_employee_qr(emp):
    """Ensure that the employee has valid QR code files and database records."""
    if not emp:
        return emp
        
    png_path = emp.get('png_path')
    needs_generation = False
    
    if not png_path:
        needs_generation = True
    else:
        full_path = Config.BASE_DIR / png_path
        if not full_path.exists():
            needs_generation = True
            
    if needs_generation:
        try:
            company_settings = get_company_settings()
            company_name = company_settings.get('company_name', 'Nexalogic Techno')
            logo_full_path = None
            if emp.get('company_logo') and (Config.BASE_DIR / emp['company_logo']).exists():
                logo_full_path = str(Config.BASE_DIR / emp['company_logo'])
            elif company_settings.get('company_logo') and (Config.BASE_DIR / company_settings['company_logo']).exists():
                logo_full_path = str(Config.BASE_DIR / company_settings['company_logo'])
                
            qr_data = generate_qr_code(
                slug=emp['slug'],
                employee_id=emp['id'],
                employee_name=f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
                designation=emp.get('designation', ''),
                company_name=company_name,
                company_logo_path=logo_full_path
            )
            emp['qr_url'] = qr_data['qr_url']
            emp['png_path'] = qr_data['png_path']
            emp['svg_path'] = qr_data['svg_path']
            emp['branded_png_path'] = qr_data['branded_png_path']
        except Exception as e:
            pass
        
    return emp


def get_employee_by_id(employee_id, include_deleted=False):
    """
    Get an employee by ID including social links, custom links, and QR records.
    """
    where_deleted = "" if include_deleted else "AND e.is_deleted = 0"
    emp = query_db(
        f"""
        SELECT e.*, 
               s.instagram_url, s.facebook_url, s.linkedin_url, 
               s.youtube_url, s.website_url, s.google_review_url,
               q.qr_url, q.png_path, q.svg_path, q.branded_png_path
        FROM employees e
        LEFT JOIN social_links s ON e.id = s.employee_id
        LEFT JOIN qr_codes q ON e.id = q.employee_id
        WHERE e.id = %s {where_deleted}
        """,
        (employee_id,),
        one=True
    )
    if emp:
        if emp.get('google_review_url'):
            emp['google_review_url'] = optimize_google_review_url(emp['google_review_url'])
        emp['custom_links'] = get_custom_links_for_employee(emp['id'])
        emp = _ensure_employee_qr(emp)
    return emp


def get_employee_by_slug(slug):
    """
    Get employee profile data by slug for the public route.
    """
    emp = query_db(
        """
        SELECT e.*, 
               s.instagram_url, s.facebook_url, s.linkedin_url, 
               s.youtube_url, s.website_url, s.google_review_url,
               q.qr_url, q.png_path, q.svg_path, q.branded_png_path
        FROM employees e
        LEFT JOIN social_links s ON e.id = s.employee_id
        LEFT JOIN qr_codes q ON e.id = q.employee_id
        WHERE e.slug = %s AND e.is_deleted = 0
        """,
        (slug.strip().lower(),),
        one=True
    )
    if emp:
        if emp.get('google_review_url'):
            emp['google_review_url'] = optimize_google_review_url(emp['google_review_url'])
        emp['custom_links'] = get_custom_links_for_employee(emp['id'])
        emp = _ensure_employee_qr(emp)
    return emp


def _save_upload_file(file_obj, upload_dir, prefix='img'):
    """Helper to safely save uploaded images with unique names."""
    if not file_obj or not file_obj.filename:
        return ''
    ext = file_obj.filename.rsplit('.', 1)[-1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        return ''
    
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}_{secrets.token_hex(6)}.{ext}"
    target_path = upload_dir / filename
    file_obj.save(str(target_path))
    
    rel_folder = upload_dir.name
    return f"uploads/{rel_folder}/{filename}"


def create_employee(form_data, profile_file=None, logo_file=None):
    """
    Create a new employee, save social links, generate slug and QR codes.
    """
    first_name = form_data.get('first_name', '').strip()
    last_name = form_data.get('last_name', '').strip()
    
    if not first_name:
        raise ValueError("First Name is required.")
        
    designation = form_data.get('designation', '').strip()
    phone = form_data.get('phone', '').strip()
    whatsapp = form_data.get('whatsapp', '').strip() or phone.replace('+', '').replace(' ', '')
    email = form_data.get('email', '').strip()
    bio = form_data.get('bio', '').strip()
    review_categories = form_data.get('review_categories', '').strip()
    is_active = 1 if form_data.get('is_active') in (True, '1', 'on', 'true') else 0
    
    # Generate unique slug
    custom_slug = form_data.get('slug', '').strip()
    if custom_slug:
        slug = generate_unique_slug(custom_slug)
    else:
        slug = generate_unique_slug(first_name, last_name)

    # Save images if provided
    profile_image = _save_upload_file(profile_file, Config.PROFILES_PATH, prefix=slug)
    company_logo = _save_upload_file(logo_file, Config.LOGOS_PATH, prefix=f"{slug}_logo")
    
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO employees (first_name, last_name, slug, designation, phone, whatsapp, email, profile_image, company_logo, bio, review_categories, is_active, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (first_name, last_name, slug, designation, phone, whatsapp, email, profile_image, company_logo, bio, review_categories, is_active)
        )
        employee_id = cursor.lastrowid
        
        # Social links
        cursor.execute(
            """
            INSERT INTO social_links (employee_id, instagram_url, facebook_url, linkedin_url, youtube_url, website_url, google_review_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                employee_id,
                form_data.get('instagram_url', '').strip(),
                form_data.get('facebook_url', '').strip(),
                form_data.get('linkedin_url', '').strip(),
                form_data.get('youtube_url', '').strip(),
                form_data.get('website_url', '').strip(),
                optimize_google_review_url(form_data.get('google_review_url', ''))
            )
        )

        # Custom Channel & Social links
        _save_custom_links(cursor, employee_id, form_data, is_update=False)

    # Generate QR codes
    company_settings = get_company_settings()
    company_name = company_settings.get('company_name', 'Apex Innovations')
    logo_full_path = None
    if company_logo and (Config.BASE_DIR / company_logo).exists():
        logo_full_path = str(Config.BASE_DIR / company_logo)
    elif company_settings.get('company_logo') and (Config.BASE_DIR / company_settings['company_logo']).exists():
        logo_full_path = str(Config.BASE_DIR / company_settings['company_logo'])
        
    generate_qr_code(
        slug=slug,
        employee_id=employee_id,
        employee_name=f"{first_name} {last_name}".strip(),
        designation=designation,
        company_name=company_name,
        company_logo_path=logo_full_path
    )
    
    return employee_id, slug


def update_employee(employee_id, form_data, profile_file=None, logo_file=None):
    """
    Update an existing employee.
    """
    current = get_employee_by_id(employee_id)
    if not current:
        raise ValueError("Employee not found.")
        
    first_name = form_data.get('first_name', current['first_name']).strip()
    last_name = form_data.get('last_name', current['last_name']).strip()
    if not first_name:
        raise ValueError("First Name is required.")
        
    designation = form_data.get('designation', '').strip()
    phone = form_data.get('phone', '').strip()
    whatsapp = form_data.get('whatsapp', '').strip()
    email = form_data.get('email', '').strip()
    bio = form_data.get('bio', '').strip()
    review_categories = form_data.get('review_categories', '').strip()
    is_active = 1 if form_data.get('is_active') in (True, '1', 'on', 'true') else 0
    
    # Check if slug should be updated
    desired_slug = form_data.get('slug', '').strip()
    if desired_slug and desired_slug != current['slug']:
        slug = generate_unique_slug(desired_slug, current_employee_id=employee_id)
        slug_changed = True
    else:
        slug = current['slug']
        slug_changed = False

    profile_image = current['profile_image']
    if profile_file and profile_file.filename:
        new_prof = _save_upload_file(profile_file, Config.PROFILES_PATH, prefix=slug)
        if new_prof:
            profile_image = new_prof
            
    company_logo = current['company_logo']
    if logo_file and logo_file.filename:
        new_logo = _save_upload_file(logo_file, Config.LOGOS_PATH, prefix=f"{slug}_logo")
        if new_logo:
            company_logo = new_logo

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE employees
            SET first_name = %s, last_name = %s, slug = %s, designation = %s,
                phone = %s, whatsapp = %s, email = %s, profile_image = %s,
                company_logo = %s, bio = %s, review_categories = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (first_name, last_name, slug, designation, phone, whatsapp, email, profile_image, company_logo, bio, review_categories, is_active, employee_id)
        )
        
        # Upsert social links
        cursor.execute(
            """
            INSERT INTO social_links (employee_id, instagram_url, facebook_url, linkedin_url, youtube_url, website_url, google_review_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                instagram_url = VALUES(instagram_url),
                facebook_url = VALUES(facebook_url),
                linkedin_url = VALUES(linkedin_url),
                youtube_url = VALUES(youtube_url),
                website_url = VALUES(website_url),
                google_review_url = VALUES(google_review_url),
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                employee_id,
                form_data.get('instagram_url', '').strip(),
                form_data.get('facebook_url', '').strip(),
                form_data.get('linkedin_url', '').strip(),
                form_data.get('youtube_url', '').strip(),
                form_data.get('website_url', '').strip(),
                optimize_google_review_url(form_data.get('google_review_url', ''))
            )
        )

        # Custom Channel & Social links
        _save_custom_links(cursor, employee_id, form_data, is_update=True)

    # Regenerate QR if slug changed or files updated
    company_settings = get_company_settings()
    company_name = company_settings.get('company_name', 'Apex Innovations')
    logo_full_path = None
    if company_logo and (Config.BASE_DIR / company_logo).exists():
        logo_full_path = str(Config.BASE_DIR / company_logo)
    elif company_settings.get('company_logo') and (Config.BASE_DIR / company_settings['company_logo']).exists():
        logo_full_path = str(Config.BASE_DIR / company_settings['company_logo'])

    generate_qr_code(
        slug=slug,
        employee_id=employee_id,
        employee_name=f"{first_name} {last_name}".strip(),
        designation=designation,
        company_name=company_name,
        company_logo_path=logo_full_path
    )
    
    return employee_id, slug


def get_employee_categories(employee_dict):
    """
    Extracts custom review categories or provides domain-aware smart presets.
    Returns a list of clean category label strings.
    """
    if not employee_dict:
        return ["Customer Service", "Product Quality", "Professional Advice", "Prompt Delivery"]
        
    custom_cats = employee_dict.get('review_categories') or ''
    if custom_cats.strip():
        # Split by comma or newline
        cats = [c.strip() for c in re.split(r'[,;\n]+', custom_cats) if c.strip()]
        if cats:
            return cats

    # Smart fallback presets by designation / company context
    desig = (employee_dict.get('designation') or '').lower()
    bio = (employee_dict.get('bio') or '').lower()
    combined_ctx = f"{desig} {bio}"

    if any(k in combined_ctx for k in ['menswear', 'clothing', 'fashion', 'tailor', 'suit', 'apparel', 'textile', 'garment']):
        return ["👔 Menswear", "✂️ Custom Tailoring", "💍 Wedding Collection", "🧵 Fabric Quality", "⏱️ Fitting & Alterations"]
    elif any(k in combined_ctx for k in ['doctor', 'dr', 'clinic', 'hospital', 'dentist', 'physician', 'medical', 'nurse']):
        return ["🩺 Doctor Consultation", "💉 Treatment Care", "🏥 Clinic Hygiene", "🤝 Staff Hospitality", "📋 Diagnosis & Advice"]
    elif any(k in combined_ctx for k in ['real estate', 'property', 'realtor', 'housing', 'builder', 'broker']):
        return ["🏡 Property Buying", "📄 Legal Documentation", "🤝 Transparent Pricing", "📈 Market Advisory", "⚡ Fast Closing"]
    elif any(k in combined_ctx for k in ['sales', 'executive', 'business development', 'growth', 'consultant']):
        return ["💼 Sales Support", "⭐ Product Knowledge", "⚡ Quick Response", "🤝 Honest Advisory", "🚀 Seamless Onboarding"]
    elif any(k in combined_ctx for k in ['tech', 'developer', 'engineer', 'software', 'it', 'coder']):
        return ["💻 Project Delivery", "🛠️ Technical Expertise", "⚡ Fast Bug Resolution", "📞 Clear Communication", "💡 Innovation"]
    elif any(k in combined_ctx for k in ['hr', 'talent', 'people', 'recruiter', 'hiring']):
        return ["🎯 Hiring Process", "📋 Career Guidance", "🤝 Smooth Onboarding", "⚡ Prompt Interview Updates", "🌟 Employee Support"]
    elif any(k in combined_ctx for k in ['salon', 'spa', 'beauty', 'hair', 'makeup']):
        return ["💇 Hair Styling", "✨ Beauty Treatment", "🧼 Hygiene & Cleanliness", "☕ Great Hospitality", "🌟 Premium Products"]
    else:
        return ["⭐ Overall Experience", "💼 Professional Support", "⚡ Quick Service", "🤝 Trust & Reliability", "💯 Highly Recommended"]


def toggle_employee_status(employee_id):
    """Toggle is_active between 0 and 1."""
    emp = get_employee_by_id(employee_id)
    if not emp:
        return None
    new_status = 0 if emp['is_active'] == 1 else 1
    query_db(
        "UPDATE employees SET is_active = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (new_status, employee_id),
        commit=True
    )
    return new_status


def soft_delete_employee(employee_id):
    """Soft delete an employee."""
    query_db(
        "UPDATE employees SET is_deleted = 1, is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (employee_id,),
        commit=True
    )
    return True
