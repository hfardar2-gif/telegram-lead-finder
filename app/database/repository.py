from __future__ import annotations
from datetime import datetime, timezone
from .db import Database
from .models import GroupRecord, UserRecord

def now(): return datetime.now(timezone.utc).isoformat()

class Repository:
    def __init__(self, db: Database): self.db = db
    def upsert_group(self, g: GroupRecord) -> tuple[int,bool]:
        with self.db.connect() as c:
            old=c.execute("SELECT id FROM groups WHERE telegram_group_id=?",(g.telegram_group_id,)).fetchone()
            c.execute("""INSERT INTO groups(telegram_group_id,title,username,link,description,member_count,keyword,group_type) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(telegram_group_id) DO UPDATE SET title=excluded.title,username=excluded.username,link=excluded.link,description=COALESCE(excluded.description,groups.description),member_count=COALESCE(excluded.member_count,groups.member_count),keyword=excluded.keyword,group_type=excluded.group_type""",(g.telegram_group_id,g.title,g.username,g.link,g.description,g.member_count,g.keyword,g.group_type))
            row=c.execute("SELECT id FROM groups WHERE telegram_group_id=?",(g.telegram_group_id,)).fetchone(); return row[0], old is None
    def upsert_user(self, u: UserRecord, seen_at: str | None=None) -> tuple[int,bool]:
        seen_at=seen_at or now()
        with self.db.connect() as c:
            old=c.execute("SELECT id FROM users WHERE telegram_user_id=?",(u.telegram_user_id,)).fetchone()
            c.execute("""INSERT INTO users(telegram_user_id,username,first_name,last_name,display_name,is_bot,is_deleted,first_seen,last_seen) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(telegram_user_id) DO UPDATE SET username=excluded.username,first_name=excluded.first_name,last_name=excluded.last_name,display_name=excluded.display_name,is_bot=excluded.is_bot,is_deleted=excluded.is_deleted,last_seen=MAX(users.last_seen,excluded.last_seen)""",(u.telegram_user_id,u.username,u.first_name,u.last_name,u.display_name,int(u.is_bot),int(u.is_deleted),seen_at,seen_at))
            row=c.execute("SELECT id FROM users WHERE telegram_user_id=?",(u.telegram_user_id,)).fetchone(); return row[0], old is None
    def add_activity(self,user_id:int,group_id:int,count:int,first_seen:str,last_seen:str,score:float,level:str):
        with self.db.connect() as c: c.execute("""INSERT INTO user_group_activity(user_id,group_id,message_count,first_seen,last_seen,activity_score,activity_level) VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id,group_id) DO UPDATE SET message_count=user_group_activity.message_count+excluded.message_count,first_seen=MIN(user_group_activity.first_seen,excluded.first_seen),last_seen=MAX(user_group_activity.last_seen,excluded.last_seen),activity_score=excluded.activity_score,activity_level=excluded.activity_level""",(user_id,group_id,count,first_seen,last_seen,score,level))
    def activity_for(self,user_id:int,group_id:int):
        with self.db.connect() as c: return c.execute("SELECT * FROM user_group_activity WHERE user_id=? AND group_id=?",(user_id,group_id)).fetchone()
    def record_search(self,keyword:str,result_count:int):
        with self.db.connect() as c: c.execute("""INSERT INTO search_keywords(keyword,last_searched_at,result_count) VALUES(?,?,?) ON CONFLICT(keyword) DO UPDATE SET last_searched_at=excluded.last_searched_at,result_count=excluded.result_count""",(keyword,now(),result_count))
    def paused_job_for_group(self,gid:int):
        with self.db.connect() as c: return c.execute("SELECT * FROM scan_jobs WHERE group_id=? AND status='PAUSED' ORDER BY job_id DESC LIMIT 1",(gid,)).fetchone()
    def list_groups(self,limit=10,offset=0):
        with self.db.connect() as c: return c.execute("""SELECT g.*,COUNT(DISTINCT CASE WHEN u.is_bot=0 AND u.is_deleted=0 THEN a.user_id END) leads,SUM(CASE WHEN a.activity_level='High' AND u.is_bot=0 AND u.is_deleted=0 THEN 1 ELSE 0 END) active_leads FROM groups g LEFT JOIN user_group_activity a ON a.group_id=g.id LEFT JOIN users u ON u.id=a.user_id GROUP BY g.id ORDER BY g.id DESC LIMIT ? OFFSET ?""",(limit,offset)).fetchall()
    def group_by_id(self,gid):
        with self.db.connect() as c: return c.execute("SELECT * FROM groups WHERE id=?",(gid,)).fetchone()
    def delete_group(self,gid):
        with self.db.connect() as c: c.execute("DELETE FROM groups WHERE id=?",(gid,))
    def dashboard(self):
        with self.db.connect() as c:
            q=lambda sql:c.execute(sql).fetchone()[0]
            return {"groups":q("SELECT COUNT(*) FROM groups"),"users":q("SELECT COUNT(*) FROM users"),"active":q("SELECT COUNT(DISTINCT a.user_id) FROM user_group_activity a JOIN users u ON u.id=a.user_id WHERE a.activity_level='High' AND u.is_bot=0 AND u.is_deleted=0"),"last_scan":c.execute("SELECT finished_at FROM scan_jobs WHERE status='COMPLETED' ORDER BY job_id DESC LIMIT 1").fetchone()}
    def statistics(self):
        with self.db.connect() as c:
            q=lambda sql:c.execute(sql).fetchone()[0]
            return {"groups":q("SELECT COUNT(*) FROM groups"),"users":q("SELECT COUNT(*) FROM users"),"usernames":q("SELECT COUNT(*) FROM users WHERE username IS NOT NULL AND username<>''"),"high":q("SELECT COUNT(DISTINCT user_id) FROM user_group_activity WHERE activity_level='High'"),"medium":q("SELECT COUNT(DISTINCT user_id) FROM user_group_activity WHERE activity_level='Medium'"),"low":q("SELECT COUNT(DISTINCT user_id) FROM user_group_activity WHERE activity_level='Low'"),"bots":q("SELECT COUNT(*) FROM users WHERE is_bot=1"),"deleted":q("SELECT COUNT(*) FROM users WHERE is_deleted=1"),"today_users":q("SELECT COUNT(*) FROM users WHERE date(first_seen)=date('now')"),"today_scans":q("SELECT COUNT(*) FROM scan_jobs WHERE date(started_at)=date('now')")}
    def list_leads(self,limit=10,offset=0,level=None,has_username=None):
        clauses=["u.is_bot=0","u.is_deleted=0"]; params=[]
        if level: clauses.append("a.activity_level=?"); params.append(level)
        if has_username is True: clauses.append("u.username IS NOT NULL AND u.username<>''")
        sql=f"""SELECT u.telegram_user_id,u.username,u.display_name,GROUP_CONCAT(DISTINCT g.title) source_groups,SUM(a.message_count) message_count,MAX(a.activity_score) activity_score,CASE WHEN MAX(a.message_count)>=6 THEN 'High' WHEN MAX(a.message_count)>=2 THEN 'Medium' ELSE 'Low' END activity_level,MAX(a.last_seen) last_seen FROM users u JOIN user_group_activity a ON a.user_id=u.id JOIN groups g ON g.id=a.group_id WHERE {' AND '.join(clauses)} GROUP BY u.id ORDER BY activity_score DESC LIMIT ? OFFSET ?"""
        params.extend([limit,offset])
        with self.db.connect() as c: return c.execute(sql,params).fetchall()
    def export_rows(self,active_only=False,group_id=None):
        where="WHERE u.is_bot=0 AND u.is_deleted=0" + (" AND a.activity_level IN ('Medium','High')" if active_only else "")
        params=[]
        if group_id is not None: where+=" AND g.id=?"; params.append(group_id)
        sql=f"""SELECT u.telegram_user_id,u.username,u.first_name,u.last_name,u.display_name,GROUP_CONCAT(DISTINCT g.title) source_groups,COUNT(DISTINCT g.id) number_of_sources,SUM(a.message_count) message_count,MAX(a.activity_score) activity_score,CASE WHEN MAX(a.message_count)>=6 THEN 'High' WHEN MAX(a.message_count)>=2 THEN 'Medium' ELSE 'Low' END activity_level,MIN(a.first_seen) first_seen,MAX(a.last_seen) last_seen FROM users u JOIN user_group_activity a ON a.user_id=u.id JOIN groups g ON g.id=a.group_id {where} GROUP BY u.id ORDER BY activity_score DESC"""
        with self.db.connect() as c: return [dict(r) for r in c.execute(sql,params).fetchall()]
    def set_group_status(self,gid,status):
        with self.db.connect() as c: c.execute("UPDATE groups SET scan_status=?,last_scanned_at=? WHERE id=?",(status,now(),gid))
    def start_job(self,gid):
        with self.db.connect() as c: cur=c.execute("INSERT INTO scan_jobs(group_id,status) VALUES(?,'RUNNING')",(gid,)); return cur.lastrowid
    def finish_job(self,jid,status,messages=0,users=0,new_users=0,error=None,resume_after=None):
        with self.db.connect() as c: c.execute("UPDATE scan_jobs SET finished_at=?,messages_scanned=?,users_found=?,new_users=?,status=?,error=?,resume_after=? WHERE job_id=?",(now(),messages,users,new_users,status,error,resume_after,jid))
    def get_setting(self,key,default=None):
        with self.db.connect() as c:
            row=c.execute("SELECT value FROM settings WHERE key=?",(key,)).fetchone(); return row[0] if row else default
    def set_setting(self,key,value):
        with self.db.connect() as c: c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP",(key,str(value)))
