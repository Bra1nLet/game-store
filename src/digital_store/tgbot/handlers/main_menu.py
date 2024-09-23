from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.utils.formatting import Text
from aiogram.filters import Command
from sqlalchemy.orm import Session

from tgbot.data import loader
from tgbot.data.loader import bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from tgbot.keyboards.base_keyboards import main_menu, start_menu
from tgbot.services.database import User, AdminChat
from tgbot.keyboards.ps_keyboards import *
from tgbot.utils.other import get_photo
from tgbot.utils.states import MainState

router = Router()


@router.callback_query(MainState.chat_w_admin)
async def handle_missed_cq(call: CallbackQuery):
    await call.answer('Вы находитесь в чате с админом. Управление ботом вернется к вам по завершении чата.')


@router.message(MainState.chat_w_admin, F.content_type.in_([ContentType.TEXT, ContentType.PHOTO]))
async def chat_w_admin_handler(message: Message, state: FSMContext, db_session: Session):
    admin = db_session.query(AdminChat).filter(AdminChat.user_id == message.from_user.id).first()
    if admin:
        await message.copy_to(admin.admin_id)
    else:
        await message.answer('Администратор еще не подключился к чату с вами, ожидайте.')


@router.callback_query(F.data == 'main_menu')
@router.message(Command('start'))
async def common_handler(update: Message | CallbackQuery, state: FSMContext, db_session: Session, is_new=False):
    await state.clear()
    media = get_photo('tgbot/utils/media/main.png', db_session)
    if isinstance(update, Message):
        if is_new:
            text = 'text'
            media = get_photo('tgbot/utils/media/vid.mp4', db_session)
            message = await update.answer_video(media, caption=text, reply_markup=start_menu())
            return 'tgbot/utils/media/vid.mp4', message.video.file_id

        message = await update.answer_photo(media,
                                            caption='Привет👋\n\nЧтобы продолжить, выбери платформу🙂',
                                            reply_markup=main_menu())
        return 'tgbot/utils/media/main.png', message.photo[-1].file_id

    elif isinstance(update, CallbackQuery):
        await update.message.edit_media(media=InputMediaPhoto(
            media=FSInputFile('tgbot/utils/media/main.png'),
            caption='Привет👋\n\nЧтобы продолжить, выбери платформу🙂'
        ),
            reply_markup=main_menu())


@router.message(Command('info'))
async def show_info(message: Message):
    await message.answer("""💛Основной канал JoyStick Store - https://t.me/storejoystick

🎮Новостной канал - https://t.me/newsjoystick

🗣️Отзывы - https://t.me/+c6--F8QT9MVlYmQ6

📞Чат поддержки - @joysticksupport

Особо важная информация для пользователя - https://t.me/storejoystick/127""")
