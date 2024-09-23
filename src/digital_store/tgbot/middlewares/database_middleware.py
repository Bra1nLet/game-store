from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from tgbot.data.config import admin_ids
from tgbot.data.loader import Session
from tgbot.services.database import User, Photo


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        db_session = Session()
        event_user = data['event_from_user']
        user = db_session.query(User).filter(User.id == event_user.id).first()
        # if user.id not in admin_ids:
        #     return

        if not user:
            user = User(id=event_user.id, full_name=event_user.full_name, username=event_user.username)
            db_session.add(user)
            db_session.commit()
        elif user.full_name != event_user.full_name or user.username != event_user.username:
            user.full_name = event_user.full_name
            user.username = event_user.username
            db_session.commit()

        data['db_session'] = db_session

        result = await handler(event, data)
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], str) and isinstance(result[1], str):
            file_name, file_id = result
            photo = db_session.query(Photo).filter(Photo.file_path == file_name).first()
            if not photo:
                photo = Photo(file_path=file_name, file_id=file_id)
                db_session.add(photo)
                db_session.commit()

        db_session.close()
        return
