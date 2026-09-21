from datetime import datetime, timezone
from pathlib import Path
import sqlite3

class BackupService:
    def __init__(self,db_path:Path|str,directory:Path|str="data/backups"): self.db_path=Path(db_path); self.directory=Path(directory)
    def create(self):
        self.directory.mkdir(parents=True,exist_ok=True); target=self.directory/f"telegram-lead-finder-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.db"
        source=sqlite3.connect(self.db_path); dest=sqlite3.connect(target)
        try: source.backup(dest)
        finally: source.close(); dest.close()
        return target

