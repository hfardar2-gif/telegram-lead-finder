from datetime import datetime,timezone
from pathlib import Path
import os
import pytest
from app.database.db import Database
from app.database.repository import Repository
from app.database.models import GroupRecord,UserRecord
from app.services.scoring_service import activity_level,activity_score
from app.services.export_service import ExportService
from app.services.backup_service import BackupService
from app.bot.admin_bot import authorized

@pytest.fixture
def repo(tmp_path):
    db=Database(tmp_path/"test.db"); db.initialize(); return Repository(db)

def test_schema_and_dedup(repo):
    gid,new=repo.upsert_group(GroupRecord(123,"Test","test")); assert new
    gid2,new=repo.upsert_group(GroupRecord(123,"Changed","test")); assert gid==gid2 and not new
    uid,new=repo.upsert_user(UserRecord(456,"alice","Alice",None,"Alice")); assert new
    uid2,new=repo.upsert_user(UserRecord(456,"alice","Alice",None,"Alice")); assert uid==uid2 and not new
    now=datetime.now(timezone.utc).isoformat(); repo.add_activity(uid,gid,2,now,now,20,"Medium"); repo.add_activity(uid,gid,1,now,now,15,"Low")
    assert repo.export_rows()[0]["message_count"]==3

def test_batch_inserts(repo):
    gid,_=repo.upsert_group(GroupRecord(1,"G")); now=datetime.now(timezone.utc).isoformat()
    for n in range(50):
        uid,_=repo.upsert_user(UserRecord(1000+n,f"u{n}","U",str(n),f"U {n}"),now); repo.add_activity(uid,gid,1,now,now,15,"Low")
    assert len(repo.export_rows())==50

def test_scoring():
    assert [activity_level(n) for n in (1,2,5,6)]==["Low","Medium","Medium","High"]
    assert activity_score(6,datetime.now(timezone.utc))>activity_score(1,datetime.now(timezone.utc))

def test_exports_and_backup(repo,tmp_path):
    gid,_=repo.upsert_group(GroupRecord(1,"G")); uid,_=repo.upsert_user(UserRecord(2,"u","F","L","F L")); now=datetime.now(timezone.utc).isoformat(); repo.add_activity(uid,gid,6,now,now,40,"High")
    svc=ExportService(repo,tmp_path/"exports"); csv=svc.csv(); xlsx=svc.xlsx(True)
    assert csv.exists() and "Telegram User ID" in csv.read_text(encoding="utf-8-sig")
    assert xlsx.exists() and xlsx.stat().st_size>0
    backup=BackupService(repo.db.path,tmp_path/"backups").create(); assert backup.exists()

class User: 
    def __init__(self,id): self.id=id
class Event:
    def __init__(self,id): self.from_user=User(id)
def test_admin_auth():
    assert authorized(Event(10),10); assert not authorized(Event(11),10)

