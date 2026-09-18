import unittest
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import Config
from services.qr_service import generate_qr_code

class QRServiceTestCase(unittest.TestCase):
    def test_qr_file_generation(self):
        """Test generation of PNG, SVG, and Branded Card PNG files on disk."""
        test_slug = "test_employee"
        result = generate_qr_code(
            slug=test_slug,
            employee_name="Test Employee",
            designation="QA Engineer",
            company_name="Apex Innovations"
        )
        
        self.assertIn('qr_url', result)
        self.assertTrue(result['qr_url'].endswith(f"/q/{test_slug}"))
        
        # Check files exist on disk
        png_path = Config.QR_PATH / f"{test_slug}.png"
        svg_path = Config.QR_PATH / f"{test_slug}.svg"
        branded_path = Config.QR_PATH / f"{test_slug}_branded.png"
        
        self.assertTrue(png_path.exists(), "PNG QR code should exist")
        self.assertTrue(svg_path.exists(), "SVG QR code should exist")
        self.assertTrue(branded_path.exists(), "Branded QR code should exist")
        
        # Cleanup test artifacts
        try:
            if png_path.exists(): png_path.unlink()
            if svg_path.exists(): svg_path.unlink()
            if branded_path.exists(): branded_path.unlink()
        except Exception:
            pass

if __name__ == '__main__':
    unittest.main()
