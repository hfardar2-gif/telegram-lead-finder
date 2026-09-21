from __future__ import annotations
import csv
from datetime import datetime, timezone
from pathlib import Path
from openpyxl import Workbook

HEADERS=["Telegram User ID","Username","First Name","Last Name","Display Name","Source Groups","Number of Sources","Message Count","Activity Score","Activity Level","First Seen","Last Seen","Export Date"]
KEYS=["telegram_user_id","username","first_name","last_name","display_name","source_groups","number_of_sources","message_count","activity_score","activity_level","first_seen","last_seen"]

class ExportService:
    def __init__(self, repo, directory: Path|str="data/exports"): self.repo=repo; self.directory=Path(directory)
    def _data(self,active,group_id=None):
        stamp=datetime.now(timezone.utc).isoformat(); return [[r.get(k) for k in KEYS]+[stamp] for r in self.repo.export_rows(active,group_id)]
    def csv(self,active=False,group_id=None):
        self.directory.mkdir(parents=True,exist_ok=True); p=self.directory/f"{'group_'+str(group_id) if group_id else 'active_leads' if active else 'all_leads'}.csv"
        with p.open("w",newline="",encoding="utf-8-sig") as f: w=csv.writer(f); w.writerow(HEADERS); w.writerows(self._data(active,group_id))
        return p
    def xlsx(self,active=False,group_id=None):
        self.directory.mkdir(parents=True,exist_ok=True); p=self.directory/f"{'group_'+str(group_id) if group_id else 'active_leads' if active else 'all_leads'}.xlsx"
        wb=Workbook(); ws=wb.active; ws.title="Leads"; ws.append(HEADERS)
        for row in self._data(active,group_id): ws.append(row)
        ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=min(45,max(12,max(len(str(x.value or "")) for x in col)+2))
        wb.save(p); return p
