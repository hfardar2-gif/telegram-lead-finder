from __future__ import annotations
import asyncio
from .config import ConfigurationError,load_settings
from .database.db import Database
from .database.repository import Repository
from .telegram_client.client import create_client
from .telegram_client.discovery import DiscoveryService
from .telegram_client.scanner import ScanningService
from .bot.admin_bot import run_bot
from .utils.logger import configure_logging
from .services.backup_service import BackupService

async def auto_backup_loop(settings):
    if settings.auto_backup_hours <= 0: return
    service=BackupService(settings.database_path,settings.database_path.parent/"backups")
    while True:
        await asyncio.sleep(settings.auto_backup_hours*3600)
        await asyncio.to_thread(service.create)

async def async_main():
    settings=load_settings(); configure_logging(settings.log_level); db=Database(settings.database_path); db.initialize(); repo=Repository(db); client=create_client(settings)
    print("Connecting Telegram user account. Telegram may request phone, login code, and 2FA password in this console.")
    await client.start()
    backup_task=asyncio.create_task(auto_backup_loop(settings))
    try: await run_bot(settings,repo,DiscoveryService(client,repo),ScanningService(client,repo))
    finally: backup_task.cancel(); await client.disconnect()

def main():
    try: asyncio.run(async_main())
    except ConfigurationError as exc: print(f"Configuration error: {exc}"); raise SystemExit(2)
    except KeyboardInterrupt: print("Stopped.")

if __name__=="__main__": main()
