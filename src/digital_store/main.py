import asyncio
import logging
import sys

from aiogram import Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tgbot.data.loader import Session, bot, storage
from tgbot.middlewares.admin_middleware import AdminMiddleware
from tgbot.middlewares.database_middleware import DatabaseMiddleware
import tgbot.handlers.main_menu as main_menu
import tgbot.handlers.admin_handler as admin_handler
import tgbot.handlers.ps_handler as ps_handler
import tgbot.handlers.pc_handler as pc_handler
import tgbot.handlers.xbox_handler as xbox_handler
import tgbot.handlers.cart_handler as cart_handler

import platform

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def on_startup(dp):
    scheduler = AsyncIOScheduler()
    scheduler.start()


dp = Dispatcher(storage=storage)


async def main():
    dp.include_router(main_menu.router)
    dp.include_router(admin_handler.router)
    dp.include_router(ps_handler.router)
    dp.include_router(pc_handler.router)
    dp.include_router(xbox_handler.router)
    dp.include_router(cart_handler.router)

    dp.update.middleware(DatabaseMiddleware())
    admin_handler.router.message.middleware(AdminMiddleware())
    admin_handler.router.callback_query.middleware(AdminMiddleware())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(main())
