from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    bot_token: str
    admin_telegram_id: int
    database_path: Path
    session_path: Path
    log_level: str = "INFO"
    auto_backup_hours: int = 24

class ConfigurationError(RuntimeError):
    pass

def _resolve(value: str, default: str) -> Path:
    path = Path(value or default)
    return path if path.is_absolute() else ROOT / path

def missing_settings() -> list[str]:
    load_dotenv(ENV_PATH)
    required = ["API_ID", "API_HASH", "BOT_TOKEN", "ADMIN_TELEGRAM_ID"]
    return [key for key in required if not os.getenv(key, "").strip()]

def load_settings() -> Settings:
    load_dotenv(ENV_PATH)
    missing = missing_settings()
    if missing:
        raise ConfigurationError("Missing " + ", ".join(missing) + ". Telegram API setup required. Run: python -m app.setup_wizard")
    try:
        api_id = int(os.environ["API_ID"])
        admin_id = int(os.environ["ADMIN_TELEGRAM_ID"])
    except ValueError as exc:
        raise ConfigurationError("API_ID and ADMIN_TELEGRAM_ID must be integers.") from exc
    return Settings(
        api_id=api_id, api_hash=os.environ["API_HASH"].strip(),
        bot_token=os.environ["BOT_TOKEN"].strip(), admin_telegram_id=admin_id,
        database_path=_resolve(os.getenv("DATABASE_PATH", ""), "data/telegram_lead_finder.db"),
        session_path=_resolve(os.getenv("SESSION_PATH", ""), "data/sessions/telegram_user"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        auto_backup_hours=max(0, int(os.getenv("AUTO_BACKUP_HOURS", "24"))),
    )

