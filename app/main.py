import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.middlewares.user_context import UserContextMiddleware
from app.bot.routers import setup_routers
from app.config import get_settings
from app.db.session import async_session_factory, dispose_engine
from app.logging_config import configure_logging
from app.services.notifications import setup_scheduler
from app.services.users import ensure_initial_admins

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()

    # Middleware (ВАЖНО: и для сообщений, и для кнопок)
    middleware = UserContextMiddleware(async_session_factory)

    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)

    # Роутеры
    setup_routers(dp)

    # Создание админов
    async with async_session_factory() as session:
        await ensure_initial_admins(session, settings.admin_ids)

    # Планировщик
    scheduler = setup_scheduler(bot)
    scheduler.start()

    try:
        logger.info("Starting bot polling")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
