from __future__ import annotations

import getpass
from pathlib import Path
from .config import ENV_PATH

KEYS = ("API_ID", "API_HASH", "BOT_TOKEN", "ADMIN_TELEGRAM_ID")

def run() -> None:
    existing: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1); existing[key] = value
    print("Telegram Lead Finder setup. Values are saved only to local .env.")
    for key in KEYS:
        current = existing.get(key, "")
        prompt = f"{key} [{'*' * 8 if current else 'required'}]: "
        value = getpass.getpass(prompt) if key in {"API_HASH", "BOT_TOKEN"} else input(prompt)
        if value.strip(): existing[key] = value.strip()
    defaults = {"DATABASE_PATH":"data/telegram_lead_finder.db", "SESSION_PATH":"data/sessions/telegram_user", "LOG_LEVEL":"INFO", "AUTO_BACKUP_HOURS":"24"}
    existing.update({k: existing.get(k, v) for k, v in defaults.items()})
    ENV_PATH.write_text("\n".join(f"{k}={existing.get(k,'')}" for k in (*KEYS,*defaults)) + "\n", encoding="utf-8")
    print("Saved. Secret values were not displayed.")

if __name__ == "__main__": run()

