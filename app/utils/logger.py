import logging
from pathlib import Path

def configure_logging(level: str = "INFO") -> None:
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(level=getattr(logging, level, logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s", handlers=[logging.FileHandler("logs/app.log", encoding="utf-8"), logging.StreamHandler()])
    for noisy in ("telethon.network", "aiogram.event"): logging.getLogger(noisy).setLevel(logging.WARNING)

