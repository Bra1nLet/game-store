from aiogram.types import Message
from aiogram.filters import BaseFilter
from tgbot.data.config import admin_ids


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        return user_id in admin_ids
