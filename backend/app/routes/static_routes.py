"""Static file serving routes."""
from flask import Blueprint, send_from_directory

from ._paths import FRONTEND_DIR, LTI_STATIC_DIR, STATIC_DIR

static_bp = Blueprint('static_files', __name__)


@static_bp.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@static_bp.route('/frontend/<path:filename>')
def serve_frontend_assets(filename):
    """Serve frontend assets (core stubs, etc.)."""
    return send_from_directory(FRONTEND_DIR, filename)


@static_bp.route('/static/lti/<path:filename>')
def serve_lti_static(filename):
    """Serve LTI static assets (AMD bundle + core stubs for Moodle LTI mode)."""
    return send_from_directory(LTI_STATIC_DIR, filename)


@static_bp.route('/static/favicon.ico')
def serve_favicon():
    return send_from_directory(STATIC_DIR, 'favicon.ico')
