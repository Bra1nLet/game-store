# - *- coding: utf- 8 - *-
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tgbot.data.config import token, database_path

bot = Bot(token=token, parse_mode=ParseMode.HTML)
storage = MemoryStorage()

engine = create_engine(database_path, isolation_level='AUTOCOMMIT')
engine.connect()
Session = sessionmaker(engine)
Session.configure(bind=engine)
