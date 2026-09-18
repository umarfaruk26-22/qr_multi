import re
import unicodedata
from database.connection import query_db

def sanitize_slug(text):
    """
    Sanitize text into a clean URL-safe slug string.
    Example: 'Rahul Sharma!' -> 'rahul-sharma'
    """
    if not text:
        return 'employee'
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    # Lowercase and replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    return text if text else 'employee'


def generate_unique_slug(first_name, last_name='', current_employee_id=None):
    """
    Generate a unique URL slug for an employee.
    Priority:
    1. First name based (e.g., 'rahul')
    2. If collision, try with last name if available ('rahul-sharma')
    3. Incremental suffix ('rahul-2', 'rahul-3', etc.)
    """
    base_slug = sanitize_slug(first_name)
    
    # Check if base_slug is available
    if is_slug_available(base_slug, current_employee_id):
        return base_slug
        
    # If last name is provided, try combining first + last name
    if last_name:
        combined_slug = sanitize_slug(f"{first_name} {last_name}")
        if is_slug_available(combined_slug, current_employee_id):
            return combined_slug
            
    # Sequential counter fallback
    counter = 2
    while True:
        candidate_slug = f"{base_slug}-{counter}"
        if is_slug_available(candidate_slug, current_employee_id):
            return candidate_slug
        counter += 1


def is_slug_available(slug, current_employee_id=None):
    """
    Checks if a slug is available in the employees table.
    Excludes the current employee if updating.
    """
    # Reserved slugs that shouldn't conflict with system routes
    reserved_slugs = {
        'admin', 'login', 'logout', 'api', 'q', 'static', 'uploads',
        'dashboard', 'employees', 'settings', 'analytics', 'health', '404', '500'
    }
    if slug in reserved_slugs:
        return False
        
    if current_employee_id:
        result = query_db(
            "SELECT id FROM employees WHERE slug = %s AND id != %s AND is_deleted = 0",
            (slug, current_employee_id),
            one=True
        )
    else:
        result = query_db(
            "SELECT id FROM employees WHERE slug = %s AND is_deleted = 0",
            (slug,),
            one=True
        )
    return result is None
