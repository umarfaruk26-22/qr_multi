import sys
import os

# Subdomain path on Hostinger
APP_DIR = os.path.dirname(__file__)
VENV_PYTHON = os.path.join(APP_DIR, 'venv', 'bin', 'python3')
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = os.path.join(APP_DIR, 'venv', 'bin', 'python')

# Add virtualenv site-packages to sys.path
venv_lib = os.path.join(APP_DIR, 'venv', 'lib')
if os.path.exists(venv_lib):
    for entry in os.listdir(venv_lib):
        sp = os.path.join(venv_lib, entry, 'site-packages')
        if os.path.exists(sp) and sp not in sys.path:
            sys.path.insert(0, sp)

# Force passenger to use virtualenv python interpreter if available
if os.path.exists(VENV_PYTHON) and sys.executable != VENV_PYTHON:
    try:
        os.execl(VENV_PYTHON, VENV_PYTHON, *sys.argv)
    except Exception:
        pass

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app as application
