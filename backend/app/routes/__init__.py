"""
Route registration.

Imports all Blueprint modules and registers them with the Flask app.
The actual route handlers live in routes/*_routes.py:

    routes/static_routes.py    /  /frontend  /static
    routes/chat_routes.py      /startConversation  /reply  /resetConversation
    routes/user_routes.py      /user_language/  /user_role/
    routes/survey_routes.py    /survey  /student/results
    routes/dashboard_routes.py /dashboard
    routes/log_routes.py       /log/tab_event  /log/mouse_traces
    routes/protocol_routes.py  /protocols
"""
import json

from flask_cors import CORS

from app import app, db
from .static_routes import static_bp
from .chat_routes import chat_bp
from .user_routes import user_bp
from .survey_routes import survey_bp
from .dashboard_routes import dashboard_bp
from .log_routes import logs_bp
from .protocol_routes import protocols_bp

CORS(app)


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(error)
    db.session.rollback()
    with open("config/translations.json", "r", encoding="utf-8") as file:
        translations = json.load(file)
    return translations["translations"]["en"]["create_error"], 500


@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
        app.logger.error("Caught error: %s - rolling back", exception)
    else:
        db.session.commit()
    db.session.remove()


for _bp in [static_bp, chat_bp, user_bp, survey_bp, dashboard_bp, logs_bp, protocols_bp]:
    app.register_blueprint(_bp)
