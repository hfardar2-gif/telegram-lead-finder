from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def dashboard_keyboard():
    b=InlineKeyboardBuilder()
    for text,data in [("Search Groups","search"),("Groups","groups"),("Active Leads","leads"),("Statistics","stats"),("Export","export_menu"),("Settings","settings"),("Backup","backup")]: b.button(text=text,callback_data=data)
    b.adjust(2,2,2,1); return b.as_markup()

def export_keyboard():
    b=InlineKeyboardBuilder()
    for text,data in [("All CSV","export_all_csv"),("All XLSX","export_all_xlsx"),("Active CSV","export_active_csv"),("Active XLSX","export_active_xlsx"),("Back","home")]: b.button(text=text,callback_data=data)
    b.adjust(2,2,1); return b.as_markup()

def groups_keyboard(rows,page):
    b=InlineKeyboardBuilder()
    for r in rows:
        b.row(InlineKeyboardButton(text=f"{r['title'][:24]} | Scan",callback_data=f"scan:{r['id']}"),InlineKeyboardButton(text="Details",callback_data=f"details:{r['id']}"))
        b.row(InlineKeyboardButton(text="Export",callback_data=f"export_group:{r['id']}"),InlineKeyboardButton(text="Delete",callback_data=f"delete_confirm:{r['id']}"))
    if page>0: b.button(text="Previous",callback_data=f"groups_page:{page-1}")
    if len(rows)==5: b.button(text="Next",callback_data=f"groups_page:{page+1}")
    b.button(text="Back",callback_data="home"); b.adjust(2); return b.as_markup()

def settings_keyboard():
    b=InlineKeyboardBuilder()
    for n in (100,500,1000,5000): b.button(text=f"{n} messages",callback_data=f"set_messages:{n}")
    for n in (7,30,90): b.button(text=f"{n} days",callback_data=f"set_days:{n}")
    b.button(text="Back",callback_data="home"); b.adjust(2,2,3,1); return b.as_markup()

def leads_keyboard(page):
    b=InlineKeyboardBuilder()
    if page>0: b.button(text="Previous",callback_data=f"leads_page:{page-1}")
    b.button(text="Next",callback_data=f"leads_page:{page+1}"); b.button(text="Back",callback_data="home"); b.adjust(2,1); return b.as_markup()

def delete_keyboard(gid):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Confirm delete",callback_data=f"delete_group:{gid}"),InlineKeyboardButton(text="Cancel",callback_data="groups")]])
