import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_default_secret_key_123456789')
    BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'employee_qr_system')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # File uploads configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    UPLOAD_PATH = BASE_DIR / UPLOAD_FOLDER
    PROFILES_PATH = UPLOAD_PATH / 'profiles'
    LOGOS_PATH = UPLOAD_PATH / 'logos'
    QR_PATH = UPLOAD_PATH / 'qr'
    
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))  # 5MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/webp'}

    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    # Google Gemini AI configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.7-flash')

    @classmethod
    def init_app(cls, app):
        """Ensure upload directories exist."""
        cls.PROFILES_PATH.mkdir(parents=True, exist_ok=True)
        cls.LOGOS_PATH.mkdir(parents=True, exist_ok=True)
        cls.QR_PATH.mkdir(parents=True, exist_ok=True)
