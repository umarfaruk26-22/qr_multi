"""
Utility script to regenerate high-definition branded QR cards and assets for all active employees.
"""
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import query_db
from services.settings_service import get_company_settings
from services.qr_service import generate_qr_code
from config import Config

def main():
    try:
        employees = query_db("SELECT * FROM employees WHERE is_deleted = 0") or []
        company_settings = get_company_settings() or {}
        company_name = company_settings.get('company_name', 'Nexalogic Techno')
        
        count = 0
        for emp in employees:
            slug = emp.get('slug')
            if not slug:
                continue
                
            emp_id = emp.get('id')
            full_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            desig = emp.get('designation', '')
            
            logo_path = None
            if emp.get('company_logo') and (Config.BASE_DIR / emp['company_logo']).exists():
                logo_path = str(Config.BASE_DIR / emp['company_logo'])
            elif company_settings.get('company_logo') and (Config.BASE_DIR / company_settings['company_logo']).exists():
                logo_path = str(Config.BASE_DIR / company_settings['company_logo'])
                
            generate_qr_code(
                slug=slug,
                employee_id=emp_id,
                employee_name=full_name,
                designation=desig,
                company_name=company_name,
                company_logo_path=logo_path
            )
            count += 1
            print(f"Successfully generated QR cards for: {slug} ({full_name})")
            
        print(f"Total {count} employee QR cards refreshed successfully.")
    except Exception as e:
        print(f"Error during QR regeneration: {e}")

if __name__ == '__main__':
    main()
