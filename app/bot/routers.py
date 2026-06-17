from aiogram import Dispatcher

from app.bot.handlers import admin, booking, client, engineer, start


def setup_routers(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(start.router)
    dispatcher.include_router(booking.router)
    dispatcher.include_router(client.router)
    dispatcher.include_router(engineer.router)
    dispatcher.include_router(admin.router)

