import unittest
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from config import Config
from services.auth_service import verify_admin

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_password_hashing(self):
        """Test Werkzeug password hashing and verification."""
        pw = "Admin@12345"
        hashed = generate_password_hash(pw)
        self.assertTrue(check_password_hash(hashed, pw))
        self.assertFalse(check_password_hash(hashed, "WrongPassword"))

    def test_unauthorized_admin_redirect(self):
        """Test that unauthenticated access to admin dashboard redirects to login."""
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.headers['Location'])

    def test_login_page_renders(self):
        """Test that the login page renders successfully."""
        response = self.client.get('/admin/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Portal', response.data)

if __name__ == '__main__':
    unittest.main()
