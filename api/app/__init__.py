from flask import Flask
from app_config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import MetaData
from logging.config import dictConfig

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
                "filename": "logs/api.log",
                "maxBytes": 1000000,
                "backupCount": 5,
                "formatter": "default",
            },
        },
        "root": {"level": "INFO", "handlers": ["console", "fileRotate"]},
        "StudyBot": {"level": "INFO", "handlers": ["console", "fileRotate"]},
    }
)


app = Flask('StudyBot')
app.config.from_object(Config)
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db, render_as_batch=True)

from app import routes, models
