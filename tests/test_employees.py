import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.slug_service import sanitize_slug

class EmployeeLogicTestCase(unittest.TestCase):
    def test_slug_sanitization(self):
        """Test slug sanitization logic."""
        self.assertEqual(sanitize_slug('Rahul'), 'rahul')
        self.assertEqual(sanitize_slug('Rahul Sharma'), 'rahul-sharma')
        self.assertEqual(sanitize_slug('Aamir Khan & Co.'), 'aamir-khan-co')
        self.assertEqual(sanitize_slug('Priya_Patel!@#'), 'priya-patel')
        self.assertEqual(sanitize_slug(''), 'employee')

if __name__ == '__main__':
    unittest.main()
