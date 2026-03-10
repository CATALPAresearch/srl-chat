import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # Allow full override via DATABASE_URL (recommended)
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Fallback to PostgreSQL environment variables
        PG_HOST = os.environ.get("PG_HOST")
        PG_PORT = os.environ.get("PG_PORT")
        PG_USER = os.environ.get("PG_USER")
        PG_PASSWORD = os.environ.get("PG_PASSWORD")
        PG_DB = os.environ.get("PG_DB")

        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


print(f"[DB] Using database: {Config.SQLALCHEMY_DATABASE_URI}")
