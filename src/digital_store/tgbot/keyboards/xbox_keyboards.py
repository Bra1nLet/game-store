from typing import Optional
from typing import List

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session

from tgbot.services.database import PSGameEdition, XBOXGameEdition
from tgbot.utils.other import ps_format_edition, xbox_format_edition


def _state(value):
    if value == 0:
        return '❌'
    return '✅'


def xbox_menu(has_account):
    builder = InlineKeyboardBuilder()

    builder.button(text='🔎 Поиск игр', callback_data='xbox:search')
    builder.button(text='📁 Подборки игр', callback_data='xbox:games')
    builder.button(text='⭐️ Gamepass ULTIMATE', callback_data='xbox:plus')
    builder.button(text='💰 Донат', callback_data='xbox:donate')
    builder.button(text='Пополнение баланса', callback_data='xbox:refill')

    builder.adjust(2)

    builder.row(InlineKeyboardButton(text='🛒 Корзина', callback_data='show_cart:xbox'))

    if not has_account:
        builder.row(InlineKeyboardButton(text='❌ У меня нет аккаунта', callback_data=f'xbox_has_account:1'))
    else:
        builder.row(InlineKeyboardButton(text='✅ У меня есть аккаунт', callback_data=f'xbox_has_account:0'))

    builder.row(
        InlineKeyboardButton(text='🆘 Помощь', url='https://t.me/joysticksupport'),
        InlineKeyboardButton(text='ℹ️ Информация', callback_data='xbox:info'))

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'main_menu'))

    return builder.as_markup()


def back_xbox_menu():
    builder = InlineKeyboardBuilder()

    builder.button(text='🔙 Назад', callback_data=f'platform:XBOX')

    return builder.adjust(1).as_markup()


def xbox_categories_kb(categories: list[tuple[str, str]]):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=f'{i[0]} {i[1]}', callback_data=f'xbox_category:{i[0]}') for i in categories]
    builder.add(*kb)
    builder.button(text='🔙 Назад', callback_data=f'platform:XBOX')

    return builder.adjust(1).as_markup()


def xbox_games_kb(games: list[tuple[int, str, str]], page: int, donate: bool | None = False):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=f'{i[1]} {i[2]}', callback_data=f'xbox_game:{i[0]}') for i in
          games[page * 20:page * 20 + 20]]
    builder.add(*kb).adjust(2)

    navigation = []
    if page > 0.:
        navigation.append(InlineKeyboardButton(text='⬅️', callback_data=f'xbox_page:{page - 1}'))
    if len(games) / 20 > page + 1:
        navigation.append(InlineKeyboardButton(text='➡️️', callback_data=f'xbox_page:{page + 1}'))

    builder.row(*navigation)
    builder.row(
        InlineKeyboardButton(text='🔙 Назад', callback_data=f'xbox:games' if not donate else f'platform:XBOX'))

    return builder.as_markup()


def xbox_choose_edition(editions: list[XBOXGameEdition], page: int, db_session: Session):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=xbox_format_edition(i, db_session), callback_data=f'xbox_edition:{i.id}') for i in
          editions]

    builder.add(*kb)
    builder.button(text='🔙 Назад', callback_data=f'xbox_page:{page}')

    return builder.adjust(1).as_markup()


def xbox_buy_game_kb(edition_id, page):
    builder = InlineKeyboardBuilder()

    builder.button(text='🛒 Купить', callback_data=f'xbox_buy:{edition_id}')
    builder.button(text='🔙 Назад', callback_data=f'xbox_page:{page}')

    return builder.adjust(1).as_markup()


def xbox_choose_subscription_type():
    builder = InlineKeyboardBuilder()

    subscriptions = ['Gamepass Ultimate']
    kb = [InlineKeyboardButton(text=i, callback_data=f'sub_type:xbox:{i}') for i in subscriptions]
    builder.row(*kb, width=2)
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'platform:XBOX'))

    return builder.as_markup()


def xbox_go_to_manager():
    builder = InlineKeyboardBuilder()

    builder.button(text='Перейти в чат ', callback_data='xbox_go_manager')
    return builder.as_markup()


def xbox_choose_platform(page: int):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="X/S", callback_data=f'xbox_platform:X/S'))
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'xbox_page:{page}'))

    return builder.as_markup()
