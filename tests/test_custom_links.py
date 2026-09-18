import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.employee_service import (
    create_employee,
    get_employee_by_id,
    get_employee_by_slug,
    update_employee,
    get_platform_metadata
)
from database.connection import get_db_cursor

class CustomLinksTestCase(unittest.TestCase):
    def setUp(self):
        self.created_ids = []

    def tearDown(self):
        if self.created_ids:
            with get_db_cursor(commit=True) as cur:
                format_strings = ','.join(['%s'] * len(self.created_ids))
                cur.execute(f"DELETE FROM employees WHERE id IN ({format_strings})", tuple(self.created_ids))

    def test_platform_metadata(self):
        """Test metadata resolver for platforms."""
        tw = get_platform_metadata('twitter')
        self.assertEqual(tw['default_title'], 'Twitter / X')
        self.assertEqual(tw['brand_color'], '#0f1419')

        tg = get_platform_metadata('telegram')
        self.assertEqual(tg['default_title'], 'Telegram')
        self.assertEqual(tg['brand_color'], '#229ED9')

        custom = get_platform_metadata('unknown_platform')
        self.assertEqual(custom['default_title'], 'Custom Link')

    def test_create_and_retrieve_custom_links(self):
        """Test creating an employee with dynamic custom links."""
        form_data = {
            'first_name': 'TestCustom',
            'last_name': 'User',
            'designation': 'Senior Designer',
            'phone': '+91 99999 11111',
            'whatsapp': '919999911111',
            'email': 'testcustom@example.com',
            'custom_platform[]': ['twitter', 'telegram', 'messenger'],
            'custom_title[]': ['My Twitter', 'Telegram Channel', 'Messenger Chat'],
            'custom_url[]': ['https://x.com/testuser', 'https://t.me/testchannel', 'https://m.me/testuser']
        }

        emp_id, slug = create_employee(form_data)
        self.created_ids.append(emp_id)

        emp = get_employee_by_id(emp_id)
        self.assertIsNotNone(emp)
        self.assertIn('custom_links', emp)
        self.assertEqual(len(emp['custom_links']), 3)

        platforms = [cl['platform'] for cl in emp['custom_links']]
        self.assertEqual(platforms, ['twitter', 'telegram', 'messenger'])

        titles = [cl['title'] for cl in emp['custom_links']]
        self.assertEqual(titles, ['My Twitter', 'Telegram Channel', 'Messenger Chat'])

        # Verify get by slug
        slug_emp = get_employee_by_slug(slug)
        self.assertIsNotNone(slug_emp)
        self.assertEqual(len(slug_emp['custom_links']), 3)

    def test_update_custom_links(self):
        """Test updating/replacing custom links for an existing employee."""
        initial_data = {
            'first_name': 'UpdateCustom',
            'last_name': 'User',
            'designation': 'Developer',
            'custom_platform[]': ['github'],
            'custom_title[]': ['GitHub Repo'],
            'custom_url[]': ['https://github.com/testuser']
        }

        emp_id, slug = create_employee(initial_data)
        self.created_ids.append(emp_id)

        # Verify initial
        emp = get_employee_by_id(emp_id)
        self.assertEqual(len(emp['custom_links']), 1)
        self.assertEqual(emp['custom_links'][0]['platform'], 'github')

        # Update with Discord and Calendly
        updated_data = {
            'first_name': 'UpdateCustom',
            'last_name': 'User',
            'designation': 'Lead Developer',
            'custom_platform[]': ['discord', 'calendly'],
            'custom_title[]': ['Discord Community', 'Book a Call'],
            'custom_url[]': ['https://discord.gg/test', 'https://calendly.com/testuser']
        }

        update_employee(emp_id, updated_data)

        updated_emp = get_employee_by_id(emp_id)
        self.assertEqual(len(updated_emp['custom_links']), 2)
        self.assertEqual(updated_emp['custom_links'][0]['platform'], 'discord')
        self.assertEqual(updated_emp['custom_links'][1]['platform'], 'calendly')

if __name__ == '__main__':
    unittest.main()
