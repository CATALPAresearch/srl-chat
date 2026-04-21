import logging
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

logger = logging.getLogger("InterviewAgent")

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Load from project root first (canonical .env), fall back to backend/.env
rootdir = os.path.abspath(os.path.join(basedir, '..'))
load_dotenv(os.path.join(rootdir, '.env'))
load_dotenv(os.path.join(basedir, '.env'), override=False)  # legacy fallback


def _build_database_uri() -> str:
    """Build the SQLAlchemy database URI from environment variables."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    host = os.environ.get("PG_HOST")
    port = os.environ.get("PG_PORT")
    user = os.environ.get("PG_USER")
    password = os.environ.get("PG_PASSWORD")
    db = os.environ.get("PG_DB")

    missing = [name for name, val in (
        ("PG_HOST", host), ("PG_PORT", port),
        ("PG_USER", user), ("PG_PASSWORD", password), ("PG_DB", db)
    ) if not val]
    if missing:
        raise EnvironmentError(
            f"Database not configured. Set DATABASE_URL or the following variables: "
            f"{', '.join(missing)}"
        )

    return f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{db}"


class Config:
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Which interview protocol file to use (filename without .json)
    # Must correspond to a file in config/interview/<name>.json
    INTERVIEW_PROTOCOL = os.environ.get("INTERVIEW_PROTOCOL", "interview_default")


def get_interview_config_path() -> str:
    """Return the resolved path to the active interview protocol JSON file."""
    return os.path.join("config", "interview", f"{Config.INTERVIEW_PROTOCOL}.json")


logger.info("[DB] Using database: %s", Config.SQLALCHEMY_DATABASE_URI)
logger.info("[Interview] Using protocol: %s", Config.INTERVIEW_PROTOCOL)
