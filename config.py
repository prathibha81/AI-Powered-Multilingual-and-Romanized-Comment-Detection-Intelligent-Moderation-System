import os
from pathlib import Path

from dotenv import load_dotenv

# Always load the project's .env before reading environment variables.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


def _database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()

    # This project is intended to use SQLite locally. Resolve relative
    # SQLite URLs against the project directory so Windows cwd/OneDrive
    # does not change where SQLite tries to create the file.
    if not configured or configured.lower().startswith("sqlite:///"):
        return f"sqlite:///{DB_PATH.resolve().as_posix()}"

    return configured


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = (
        os.getenv("SECRET_KEY")
        or os.getenv("SESSION_SECRET")
        or "dev-only-change-me"
    )
    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "model"))
    DATABASE_URL = _database_url()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
    APIFY_ACTOR_ID = os.getenv(
        "APIFY_ACTOR_ID", "apify/instagram-comment-scraper"
    )
    MOCK_SCRAPER = _as_bool(os.getenv("MOCK_SCRAPER"), True)
    MAX_COMMENTS = max(1, _as_int(os.getenv("MAX_COMMENTS"), 1000))
    BATCH_SIZE = max(1, _as_int(os.getenv("BATCH_SIZE"), 16))
    MAX_LENGTH = max(16, _as_int(os.getenv("MAX_LENGTH"), 256))
