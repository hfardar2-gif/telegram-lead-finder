from __future__ import annotations
import logging
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel, Chat
from ..database.models import GroupRecord

log=logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self,client,repo): self.client=client; self.repo=repo
    async def search(self,keyword:str,limit:int=100):
        keyword=keyword.strip()[:100]
        if not keyword: raise ValueError("Keyword cannot be empty")
        result=await self.client(SearchRequest(q=keyword,limit=min(limit,100)))
        found=new=existing=0
        for entity in result.chats:
            if not isinstance(entity,(Channel,Chat)): continue
            is_broadcast=bool(getattr(entity,"broadcast",False)); is_group=bool(getattr(entity,"megagroup",False)) or isinstance(entity,Chat)
            group_type="broadcast_channel" if is_broadcast and not is_group else "supergroup" if getattr(entity,"megagroup",False) else "group"
            username=getattr(entity,"username",None); desc=None; members=getattr(entity,"participants_count",None)
            try:
                if isinstance(entity,Channel):
                    full=await self.client(GetFullChannelRequest(entity)); desc=getattr(full.full_chat,"about",None); members=getattr(full.full_chat,"participants_count",members)
            except Exception as exc: log.info("Optional group details unavailable: %s",type(exc).__name__)
            _,created=self.repo.upsert_group(GroupRecord(entity.id,getattr(entity,"title","Untitled"),username,f"https://t.me/{username}" if username else None,desc,members,keyword,group_type))
            found+=1; new+=int(created); existing+=int(not created)
        self.repo.record_search(keyword,found)
        return {"keyword":keyword,"found":found,"new":new,"existing":existing}
