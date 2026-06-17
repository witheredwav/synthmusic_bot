import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.db.session import async_session_factory

from app.bot.routers import setup_routers
from app.bot.middlewares.user_context import UserContextMiddleware

from app.services.users import ensure_initial_admins

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=settings.BOT_TOKEN)

    dp = Dispatcher(storage=MemoryStorage())

    # роутеры
    setup_routers(dp)

    # middleware БЕЗ аргументов (ВАЖНО)
    dp.update.middleware(UserContextMiddleware())

    # стартовые админы (если функция есть)
    async with async_session_factory() as session:
        await ensure_initial_admins(session, settings.admin_ids)

    # запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
