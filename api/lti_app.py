import os
from flask import Flask
from lti import lti_bp

def create_lti_app():
    app = Flask(__name__)

    # REQUIRED for Flask sessions (LTI)
    app.secret_key = os.environ.get(
        "FLASK_SECRET_KEY",
        "dev-secret-key-change-me"
    )

    app.register_blueprint(lti_bp)
    return app

if __name__ == "__main__":
    app = create_lti_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
