from datetime import datetime, timezone

def activity_level(message_count: int) -> str:
    return "High" if message_count >= 6 else "Medium" if message_count >= 2 else "Low"

def activity_score(message_count: int, last_seen: str | datetime) -> float:
    dt = datetime.fromisoformat(last_seen) if isinstance(last_seen, str) else last_seen
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    days=max(0,(datetime.now(timezone.utc)-dt).days)
    bonus=10 if days<=1 else 6 if days<=7 else 3 if days<=30 else 0
    return round(message_count*5+bonus,2)

