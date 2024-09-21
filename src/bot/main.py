import asyncio
import logging
import sys
from aiogram.types import (
    InlineKeyboardButton,
    WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, MenuButtonWebApp
)
from aiogram import Bot, Dispatcher, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


TOKEN = '7242408826:AAEf8hv5gaj_zIaau5VuwfG8CX_asgjfSyI'
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.bot.set_chat_menu_button(message.chat.id, MenuButtonWebApp(text='webapp', web_app=WebAppInfo(url="https://362d-95-54-184-55.ngrok-free.app/")))
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message(Command(commands='openApp'))
async def send_welcome(message: Message):
    web_app_url = "https://362d-95-54-184-55.ngrok-free.app/"
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Open Web App", web_app=WebAppInfo(url=web_app_url))]])
    await message.answer("Click the button to open the Web App:", reply_markup=inline_kb)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
