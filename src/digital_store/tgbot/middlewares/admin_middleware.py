from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

import tgbot.data.config as config
from tgbot.data.loader import Session
from tgbot.services.database import User


class AdminMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        event_user = data['event_from_user']

        if event_user.id not in config.admin_ids:
            return

        db_session = Session()
        data['db_session'] = db_session

        result = await handler(event, data)

        db_session.close()
        return result
