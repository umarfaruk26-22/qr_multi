import sys
import os

# Subdomain path on Hostinger
APP_DIR = os.path.dirname(__file__)
VENV_PYTHON = os.path.join(APP_DIR, 'venv', 'bin', 'python3')

# Force passenger to use virtualenv python interpreter if it exists
if os.path.exists(VENV_PYTHON) and sys.executable != VENV_PYTHON:
    os.execl(VENV_PYTHON, VENV_PYTHON, *sys.argv)

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app as application
