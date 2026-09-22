from __future__ import annotations
import asyncio
import logging
from datetime import datetime,timezone
from aiogram import Bot,Dispatcher,F,Router
from aiogram.filters import Command,CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State,StatesGroup
from aiogram.types import CallbackQuery,FSInputFile,Message
from .keyboards import dashboard_keyboard,export_keyboard,groups_keyboard,settings_keyboard,leads_keyboard,delete_keyboard,resume_keyboard
from ..services.export_service import ExportService
from ..services.backup_service import BackupService
from ..telegram_client.scanner import ScanPaused

log=logging.getLogger(__name__)
class Flow(StatesGroup): keyword=State()

def authorized(event,admin_id:int): return bool(event.from_user and event.from_user.id==admin_id)

def build_router(settings,repo,discovery,scanner):
    r=Router(); exports=ExportService(repo,settings.database_path.parent/"exports"); backups=BackupService(settings.database_path,settings.database_path.parent/"backups")
    async def deny(e):
        if isinstance(e,CallbackQuery): await e.answer("Unauthorized",show_alert=True)
        else: await e.answer("This admin bot is private.")
    async def home(m):
        d=repo.dashboard(); last=d["last_scan"][0] if d["last_scan"] else "Never"; await m.answer(f"Telegram Lead Finder\n\nGroups: {d['groups']}\nUsers: {d['users']}\nActive Leads: {d['active']}\nLast Scan: {last}",reply_markup=dashboard_keyboard())
    @r.message(CommandStart())
    async def start(m:Message):
        if not authorized(m,settings.admin_telegram_id): return await deny(m)
        await home(m)
    @r.message(Command("myid"))
    async def myid(m:Message): await m.answer(f"Your Telegram User ID: {m.from_user.id}")
    @r.callback_query(F.data=="home")
    async def cb_home(q:CallbackQuery):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await q.answer(); await home(q.message)
    @r.callback_query(F.data=="search")
    async def search(q:CallbackQuery,state:FSMContext):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await state.set_state(Flow.keyword); await q.message.answer("Send one public-group keyword (maximum 100 characters)."); await q.answer()
    @r.message(Flow.keyword)
    async def keyword(m:Message,state:FSMContext):
        if not authorized(m,settings.admin_telegram_id): return await deny(m)
        await state.clear(); msg=await m.answer("Discovery started…")
        try:
            x=await discovery.search(m.text or ""); await msg.edit_text(f"Keyword: {x['keyword']}\nGroups Found: {x['found']}\nNew Groups: {x['new']}\nExisting Groups: {x['existing']}")
        except Exception as exc: log.exception("Discovery failed"); await msg.edit_text(f"Discovery failed: {type(exc).__name__}")
    async def show_groups(q,page=0):
        rows=repo.list_groups(5,page*5); text="Groups\n\n"+"\n".join(f"{r['title']} | Members: {r['member_count'] or '?'} | Leads: {r['leads']} | High: {r['active_leads'] or 0} | {r['scan_status']}" for r in rows) if rows else "No groups found yet."
        await q.message.answer(text,reply_markup=groups_keyboard(rows,page)); await q.answer()
    @r.callback_query(F.data=="groups")
    async def groups(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await show_groups(q)
    @r.callback_query(F.data.startswith("groups_page:"))
    async def page(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await show_groups(q,int(q.data.split(":")[1]))
    @r.callback_query(F.data.startswith("details:"))
    async def details(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        g=repo.group_by_id(int(q.data.split(":")[1])); await q.message.answer(f"{g['title']}\nType: {g['group_type']}\nLink: {g['link'] or 'N/A'}\nMembers: {g['member_count'] or 'Unknown'}\nKeyword: {g['keyword'] or 'N/A'}\nLast scan: {g['last_scanned_at'] or 'Never'}\nStatus: {g['scan_status']}\n\n{g['description'] or ''}"); await q.answer()
    async def show_leads(q,page=0):
        rows=repo.list_leads(8,page*8); text="Active Leads\n\n"+"\n\n".join(f"@{x['username'] or 'no_username'} | {x['telegram_user_id']}\n{x['display_name']} | {x['activity_level']} ({x['activity_score']}) | Messages: {x['message_count']}\nSources: {x['source_groups']}\nLast: {x['last_seen']}" for x in rows) if rows else "No active leads found."
        await q.message.answer(text,reply_markup=leads_keyboard(page)); await q.answer()
    @r.callback_query(F.data=="leads")
    async def leads(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await show_leads(q)
    @r.callback_query(F.data.startswith("leads_page:"))
    async def leads_page(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await show_leads(q,int(q.data.split(":")[1]))
    @r.callback_query(F.data.startswith("delete_confirm:"))
    async def delete_confirm(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        gid=int(q.data.split(":")[1]); g=repo.group_by_id(gid); await q.message.answer(f"Delete group record and its activity data?\n{g['title']}",reply_markup=delete_keyboard(gid)); await q.answer()
    @r.callback_query(F.data.startswith("delete_group:"))
    async def delete_group(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        repo.delete_group(int(q.data.split(":")[1])); await q.message.answer("Group and related activity deleted."); await q.answer()
    @r.callback_query(F.data.startswith("export_group:"))
    async def export_group(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        gid=int(q.data.split(":")[1]); path=exports.xlsx(False,gid); await q.message.answer_document(FSInputFile(path),caption="Group leads export"); await q.answer()
    async def run_scan(q,gid:int):
        message_limit=int(repo.get_setting("scan_message_limit","500")); days=int(repo.get_setting("scan_days","30")); await q.answer("Scan started"); note=await q.message.answer(f"Scanning last {message_limit} messages / {days} days…")
        try:
            x=await scanner.scan(gid,message_limit,days); await note.edit_text(f"Scan complete. Messages: {x['messages']} | Users: {x['users']} | New: {x['new_users']}")
        except ScanPaused as exc: await note.edit_text(f"Telegram requested a FloodWait of {exc.seconds} seconds. Job paused; no bypass attempted. Resume after the wait.",reply_markup=resume_keyboard(gid))
        except Exception as exc: log.exception("Scan failed"); await note.edit_text(f"Scan failed safely: {type(exc).__name__}")
    @r.callback_query(F.data.startswith("scan:"))
    async def scan(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await run_scan(q,int(q.data.split(":")[1]))
    @r.callback_query(F.data.startswith("resume_scan:"))
    async def resume_scan(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        gid=int(q.data.split(":")[1]); paused=repo.paused_job_for_group(gid)
        if not paused: return await q.answer("No paused scan exists.",show_alert=True)
        if paused["resume_after"] and datetime.fromisoformat(paused["resume_after"])>datetime.now(timezone.utc):
            return await q.answer(f"Wait until {paused['resume_after']}",show_alert=True)
        await run_scan(q,gid)
    @r.callback_query(F.data=="stats")
    async def stats(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        s=repo.statistics(); await q.message.answer("Statistics\n"+"\n".join(f"{k.replace('_',' ').title()}: {v}" for k,v in s.items())); await q.answer()
    @r.callback_query(F.data.in_({"export_menu","export_active"}))
    async def export_menu(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await q.message.answer("Choose export:",reply_markup=export_keyboard()); await q.answer()
    @r.callback_query(F.data.startswith("export_") & ~F.data.in_({"export_menu","export_active"}))
    async def export(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        active="active" in q.data; path=exports.xlsx(active) if q.data.endswith("xlsx") else exports.csv(active); await q.message.answer_document(FSInputFile(path)); await q.answer()
    @r.callback_query(F.data=="backup")
    async def backup(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        path=backups.create(); await q.message.answer_document(FSInputFile(path),caption="SQLite backup"); await q.answer()
    @r.callback_query(F.data=="settings")
    async def settings_cb(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        await q.message.answer(f"Scan settings\nMessages: {repo.get_setting('scan_message_limit','500')}\nDays: {repo.get_setting('scan_days','30')}",reply_markup=settings_keyboard()); await q.answer()
    @r.callback_query(F.data.startswith("set_messages:"))
    async def set_messages(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        value=int(q.data.split(":")[1]); repo.set_setting("scan_message_limit",value); await q.answer(f"Message limit set to {value}",show_alert=True)
    @r.callback_query(F.data.startswith("set_days:"))
    async def set_days(q):
        if not authorized(q,settings.admin_telegram_id): return await deny(q)
        value=int(q.data.split(":")[1]); repo.set_setting("scan_days",value); await q.answer(f"Day limit set to {value}",show_alert=True)
    return r

async def run_bot(settings,repo,discovery,scanner):
    bot=Bot(settings.bot_token); dp=Dispatcher(); dp.include_router(build_router(settings,repo,discovery,scanner)); await dp.start_polling(bot)
