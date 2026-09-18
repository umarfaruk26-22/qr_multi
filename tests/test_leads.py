import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from services.lead_service import (
    validate_phone, validate_email, parse_date_safe,
    create_lead, get_leads, get_lead_summary, export_leads_csv, delete_lead
)
from services.employee_service import get_employees

class LeadServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_validation_helpers(self):
        """Test phone and email validator functions."""
        self.assertTrue(validate_phone('+91 98765 43210'))
        self.assertTrue(validate_phone('9876543210'))
        self.assertFalse(validate_phone('12345'))
        self.assertFalse(validate_phone(''))

        self.assertTrue(validate_email('test@example.com'))
        self.assertTrue(validate_email('user.name+tag@sub.domain.org'))
        self.assertFalse(validate_email('invalid-email'))
        self.assertFalse(validate_email('user@domain'))
        self.assertFalse(validate_email(''))

    def test_date_parser(self):
        """Test safe date parsing."""
        d1 = parse_date_safe('1995-08-15')
        self.assertIsNotNone(d1)
        self.assertEqual(d1.year, 1995)
        self.assertEqual(d1.month, 8)
        self.assertEqual(d1.day, 15)

        d2 = parse_date_safe('15-08-1995')
        self.assertIsNotNone(d2)
        self.assertEqual(d2.year, 1995)

        self.assertIsNone(parse_date_safe(''))
        self.assertIsNone(parse_date_safe(None))
        self.assertIsNone(parse_date_safe('invalid-date'))

    def test_create_lead_validation_errors(self):
        """Test that missing mandatory fields raise ValueError."""
        # Missing employee ID
        with self.assertRaises(ValueError):
            create_lead(None, {'name': 'John', 'phone': '9876543210', 'email': 'john@example.com'})

        # Missing name
        with self.assertRaises(ValueError):
            create_lead(1, {'name': '', 'phone': '9876543210', 'email': 'john@example.com'})

        # Missing phone
        with self.assertRaises(ValueError):
            create_lead(1, {'name': 'John', 'phone': '', 'email': 'john@example.com'})

        # Missing email
        with self.assertRaises(ValueError):
            create_lead(1, {'name': 'John', 'phone': '9876543210', 'email': ''})

    def test_lead_lifecycle_and_api(self):
        """Test lead creation via public API, querying, and deletion."""
        # Find an existing sample employee
        emps = get_employees(page=1, per_page=1)['employees']
        if not emps:
            self.skipTest("No employee available in DB for lead test.")
            
        emp_id = emps[0]['id']

        # 1. Test POST /api/leads/submit
        payload = {
            'employee_id': emp_id,
            'name': 'Aarav Mehta',
            'phone': '+91 9988776655',
            'email': 'aarav.mehta@example.com',
            'dob': '1992-05-20',
            'anniversary': '2018-12-10',
            'city': 'Mumbai'
        }
        res = self.client.post('/api/leads/submit', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        lead_id = data['lead_id']
        self.assertIsNotNone(lead_id)

        # 2. Query leads
        leads_res = get_leads(search='Aarav Mehta', employee_id=emp_id)
        self.assertGreaterEqual(leads_res['total'], 1)
        found = any(l['id'] == lead_id for l in leads_res['leads'])
        self.assertTrue(found)

        # 3. Check summary stats
        summary = get_lead_summary()
        self.assertGreaterEqual(summary['total_leads'], 1)
        self.assertIsInstance(summary['employee_breakdown'], list)

        # 4. Check CSV export
        csv_text = export_leads_csv(employee_id=emp_id, search='Aarav')
        self.assertIn('Aarav Mehta', csv_text)
        self.assertIn('Mumbai', csv_text)

        # 5. Clean up created test lead
        del_res = delete_lead(lead_id)
        self.assertTrue(del_res)

if __name__ == '__main__':
    unittest.main()
