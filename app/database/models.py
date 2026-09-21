from dataclasses import dataclass

@dataclass
class GroupRecord:
    telegram_group_id: int; title: str; username: str | None = None; link: str | None = None
    description: str | None = None; member_count: int | None = None; keyword: str | None = None; group_type: str = "group"

@dataclass
class UserRecord:
    telegram_user_id: int; username: str | None; first_name: str | None; last_name: str | None
    display_name: str; is_bot: bool = False; is_deleted: bool = False

