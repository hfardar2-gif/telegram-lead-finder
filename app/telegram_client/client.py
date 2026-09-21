from telethon import TelegramClient

def create_client(settings):
    settings.session_path.parent.mkdir(parents=True,exist_ok=True)
    return TelegramClient(str(settings.session_path),settings.api_id,settings.api_hash)

