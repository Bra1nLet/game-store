from typing import Optional, Type
from typing import List

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session

from tgbot.services.database import PSGameEdition, ConsoleSubscription
from tgbot.utils.other import ps_format_edition


def _state(value):
    if value == 0:
        return '❌'
    return '✅'


def ps_region():
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇦 Украина", callback_data='ps_country:ua')
    builder.button(text='🇹🇷 Турция', callback_data='ps_country:tr')
    builder.button(text='🔙 Назад', callback_data='main_menu')

    return builder.adjust(2).as_markup()


def ps_menu(has_account):
    builder = InlineKeyboardBuilder()

    builder.button(text='🔎 Поиск игр', callback_data='ps:search')
    builder.button(text='📁 Подборки игр', callback_data='ps:games')
    builder.button(text='⭐️ PS Plus', callback_data='ps:plus')
    builder.button(text='💰 Донат', callback_data='ps:donate')
    builder.button(text='Пополнение баланса', callback_data='ps:refill')

    builder.adjust(2)

    builder.row(InlineKeyboardButton(text='🛒 Корзина', callback_data='show_cart:ps'))

    if not has_account:
        builder.row(InlineKeyboardButton(text='❌ У меня нет аккаунта', callback_data=f'ps_has_account:1'))
    else:
        builder.row(InlineKeyboardButton(text='✅ У меня есть аккаунт', callback_data=f'ps_has_account:0'))

    builder.row(
        InlineKeyboardButton(text='🆘 Помощь', url='https://t.me/joysticksupport'),
        InlineKeyboardButton(text='ℹ️ Информация', callback_data='ps:info'))

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'platform:PS'))

    return builder.as_markup()


def back_ps_menu(region):
    builder = InlineKeyboardBuilder()

    builder.button(text='🔙 Назад', callback_data=f'ps_country:{region}')

    return builder.adjust(1).as_markup()


def ps_categories_kb(categories: list[tuple[str, str]], region: str):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=f'{i[0]} {i[1]}', callback_data=f'ps_category:{i[0]}') for i in categories]
    builder.add(*kb)
    builder.button(text='🔙 Назад', callback_data=f'ps_country:{region}')

    return builder.adjust(1).as_markup()


def ps_games_kb(games: list[tuple[int, str, str]], page: int, region: str | None = ''):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=f'{i[1]} {i[2]}', callback_data=f'ps_game:{i[0]}') for i in
          games[page * 20:page * 20 + 20]]
    builder.add(*kb).adjust(2)

    navigation = []
    if page > 0:
        navigation.append(InlineKeyboardButton(text='⬅️', callback_data=f'ps_page:{page - 1}'))
    if len(games) / 20 > page + 1:
        navigation.append(InlineKeyboardButton(text='➡️️', callback_data=f'ps_page:{page + 1}'))

    builder.row(*navigation)
    builder.row(
        InlineKeyboardButton(text='🔙 Назад', callback_data=f'ps:games' if not region else f'ps_country:{region}'))

    return builder.as_markup()


def ps_choose_platform(page: int, platforms: list[str]):
    builder = InlineKeyboardBuilder()

    builder.add(*[InlineKeyboardButton(text=i.upper(), callback_data=f'ps_platform:{i}') for i in platforms])
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'ps_page:{page}'))

    return builder.as_markup()


def ps_choose_edition(editions: list[PSGameEdition], game: int, db_session: Session):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=ps_format_edition(i, db_session), callback_data=f'ps_edition:{i.id}') for i in
          editions]

    builder.add(*kb)
    builder.button(text='🔙 Назад', callback_data=f'ps_game:{game}')

    return builder.adjust(1).as_markup()


def ps_buy_game_kb(edition_id, platform):
    builder = InlineKeyboardBuilder()

    builder.button(text='🛒 Купить', callback_data=f'ps_buy:{edition_id}')
    builder.button(text='🛒 В корзину', callback_data=f'cart:ps:game:{edition_id}')
    builder.button(text='🔙 Назад', callback_data=f'ps_platform:{platform}')

    return builder.adjust(1).as_markup()


def ps_choose_subscription_type(region):
    builder = InlineKeyboardBuilder()

    subscriptions = ['⚪️ Essential', '🟡 Extra', '⚫️ Deluxe', '🔴 Ea Play']
    kb = [InlineKeyboardButton(text=i, callback_data=f'sub_type:ps:{i}') for i in subscriptions]
    builder.row(*kb, width=1)
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'ps_country:{region}'))

    return builder.as_markup()


def ps_go_to_manager():
    builder = InlineKeyboardBuilder()

    builder.button(text='Перейти в чат ', callback_data='ps_go_manager')
    return builder.as_markup()
