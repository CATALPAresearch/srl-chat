from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import MetaData
from logging.config import dictConfig
import os
from dotenv import load_dotenv

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "fileRotate": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "api.log"),
                "maxBytes": 1000000,
                "backupCount": 5,
                "formatter": "default",
            },
        },
        "root": {"level": "INFO", "handlers": ["console", "fileRotate"]},
        "StudyBot": {"level": "DEBUG", "handlers": ["console", "fileRotate"]},
    }
)


load_dotenv()
app = Flask('StudyBot')
app.config.from_object(Config)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key")
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

app.logger.warn(Config)
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db, render_as_batch=True)

from app import routes, models
from app.lti import lti_bp
app.register_blueprint(lti_bp)

# Seed RAG strategy embeddings on startup (when enabled)
from app.rag import USE_RAG_STRATEGY, seed_strategy_embeddings
if USE_RAG_STRATEGY:
    with app.app_context():
        db.create_all()  # ensure strategy_embedding table exists
        seed_strategy_embeddings()


