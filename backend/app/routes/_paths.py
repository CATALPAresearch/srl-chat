"""Shared filesystem paths for route modules."""
import os

_APP_DIR = os.path.dirname(os.path.abspath(__file__))   # backend/app/
_BACKEND_DIR = os.path.dirname(_APP_DIR)                 # backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)            # workspace root

FRONTEND_DIR = os.path.join(_PROJECT_ROOT, 'frontend')
CONFIG_DIR = os.path.join(_BACKEND_DIR, 'config')
LTI_STATIC_DIR = os.path.join(_BACKEND_DIR, 'static', 'lti')
STATIC_DIR = os.path.join(_BACKEND_DIR, 'static')
