from __future__ import annotations
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from telethon.errors import FloodWaitError, ChannelPrivateError, ChatAdminRequiredError, RPCError
from telethon.tl.types import User
from ..database.models import UserRecord
from ..services.scoring_service import activity_score,activity_level

log=logging.getLogger(__name__)

class ScanPaused(Exception):
    def __init__(self,seconds): self.seconds=seconds; super().__init__(f"Flood wait {seconds}s")

class ScanningService:
    def __init__(self,client,repo): self.client=client; self.repo=repo
    async def scan(self,group_id:int,message_limit:int=500,days:int|None=30):
        row=self.repo.group_by_id(group_id)
        if not row: raise ValueError("Group not found")
        job=self.repo.start_job(group_id); cutoff=datetime.now(timezone.utc)-timedelta(days=days) if days else None; activity=defaultdict(list); scanned=0; new_users=0
        try:
            entity=await self.client.get_entity(row["username"] or row["telegram_group_id"])
            async for msg in self.client.iter_messages(entity,limit=max(1,min(message_limit,5000))):
                if cutoff and msg.date < cutoff: break
                scanned+=1
                if not msg.sender_id: continue
                sender=await msg.get_sender()
                if not isinstance(sender,User): continue
                seen=msg.date.astimezone(timezone.utc).isoformat(); uid,created=self.repo.upsert_user(UserRecord(sender.id,sender.username,sender.first_name,sender.last_name," ".join(filter(None,[sender.first_name,sender.last_name])) or sender.username or str(sender.id),bool(sender.bot),bool(sender.deleted)),seen)
                new_users+=int(created); activity[uid].append(seen)
            for uid,times in activity.items():
                count=len(times); last=max(times); previous=self.repo.activity_for(uid,group_id); total=count+(previous["message_count"] if previous else 0)
                self.repo.add_activity(uid,group_id,count,min(times),last,activity_score(total,last),activity_level(total))
            self.repo.set_group_status(group_id,"COMPLETED"); self.repo.finish_job(job,"COMPLETED",scanned,len(activity),new_users)
            return {"messages":scanned,"users":len(activity),"new_users":new_users}
        except FloodWaitError as exc:
            resume=(datetime.now(timezone.utc)+timedelta(seconds=exc.seconds)).isoformat(); self.repo.set_group_status(group_id,"FLOOD_WAIT"); self.repo.finish_job(job,"PAUSED",scanned,len(activity),new_users,"FloodWait",resume); raise ScanPaused(exc.seconds)
        except ChannelPrivateError as exc: self.repo.set_group_status(group_id,"PRIVATE"); self.repo.finish_job(job,"PRIVATE",scanned,error=type(exc).__name__); raise
        except ChatAdminRequiredError as exc: self.repo.set_group_status(group_id,"ADMIN_REQUIRED"); self.repo.finish_job(job,"ADMIN_REQUIRED",scanned,error=type(exc).__name__); raise
        except RPCError as exc: self.repo.set_group_status(group_id,"FAILED"); self.repo.finish_job(job,"FAILED",scanned,error=type(exc).__name__); raise
        except Exception as exc: self.repo.set_group_status(group_id,"FAILED"); self.repo.finish_job(job,"FAILED",scanned,error=type(exc).__name__); raise
