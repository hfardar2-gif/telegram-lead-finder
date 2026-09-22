from __future__ import annotations

import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from .config import ENV_PATH


async def main() -> None:
    load_dotenv(ENV_PATH)
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing BOT_TOKEN. Add it to the local .env file first.")
    bot = Bot(token)
    dispatcher = Dispatcher()
    finished = asyncio.Event()

    @dispatcher.message(CommandStart())
    async def show_id(message: Message) -> None:
        if not message.from_user:
            return
        user_id = message.from_user.id
        print(f"ADMIN_TELEGRAM_ID={user_id}")
        await message.answer(f"Your Telegram User ID is: {user_id}\nConfirm it locally, save it as ADMIN_TELEGRAM_ID, then stop this helper.")
        finished.set()

    polling = asyncio.create_task(dispatcher.start_polling(bot))
    await finished.wait()
    await dispatcher.stop_polling()
    await polling
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
