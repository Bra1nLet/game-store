from typing import Optional, Type
from typing import List

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.services.database import ConsoleSubscription
from tgbot.utils.other import xbox_format_edition


def _state(value):
    if value == 0:
        return '❌'
    return '✅'


def choose_pc_platform():
    builder = InlineKeyboardBuilder()
    # builder.button(text='Epic Games', callback_data='pc:epicgames')
    builder.button(text='battle.net', callback_data='pc:battlenet')
    builder.button(text='🔙 Назад', callback_data='main_menu')

    return builder.adjust(2).as_markup()


def epicgames_menu(has_account, has_try):
    builder = InlineKeyboardBuilder()

    builder.button(text='🔎 Поиск игр', callback_data='eg:search')
    builder.button(text='📁 Подборки игр', callback_data='eg:games')
    builder.button(text='💰 Донат', callback_data='eg:donate')

    builder.adjust(2)

    if not has_account:
        builder.row(InlineKeyboardButton(text='❌ У меня нет аккаунта', callback_data=f'eg_has_account:1'))
    else:
        builder.row(InlineKeyboardButton(text='✅ У меня есть аккаунт', callback_data=f'eg_has_account:0'),
                    InlineKeyboardButton(text=f'{_state(has_try)} Туреций EpicId',
                                         callback_data=f'eg_try:{1 - has_try}'))

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'pc:epicgames'))

    return builder.as_markup()


def back_eg_menu():
    builder = InlineKeyboardBuilder()

    builder.button(text='🔙 Назад', callback_data=f'pc:epicgames')

    return builder.adjust(1).as_markup()


def eg_categories_kb(categories: list[str]):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=i, callback_data=f'eg_category:{i}') for i in categories]
    builder.add(*kb)
    builder.button(text='🔙 Назад', callback_data=f'pc:epicgames')

    return builder.adjust(1).as_markup()


def eg_games_kb(games: list[tuple[int, str]], page: int, donate=False):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=i[1], callback_data=f'eg_game:{i[0]}') for i in games[page * 20:page * 20 + 20]]
    builder.add(*kb).adjust(2)

    navigation = []
    if len(games) > 20:
        navigation.append(InlineKeyboardButton(text='⬅️', callback_data=f'eg_page:{page - 1}'))
    if len(games) / 20 > page + 1:
        navigation.append(InlineKeyboardButton(text='➡️️', callback_data=f'eg_page:{page + 1}'))

    builder.row(*navigation)
    builder.row(
        InlineKeyboardButton(text='🔙 Назад', callback_data=f'eg:games' if not donate else f'eg:donate'))

    return builder.as_markup()


# def eg_choose_edition(editions: list[EGGameEdition], page: int):
#     builder = InlineKeyboardBuilder()
#
#     kb = [InlineKeyboardButton(text=xbox_format_edition(i), callback_data=f'eg_edition:{i.id}') for i in editions]
#
#     builder.add(*kb)
#     builder.button(text='🔙 Назад', callback_data=f'eg_page:{page}')
#
#     return builder.adjust(1).as_markup()


def eg_buy_game_kb(edition_id, page):
    builder = InlineKeyboardBuilder()

    builder.button(text='🛒 Купить', callback_data=f'eg_buy:{edition_id}')
    builder.button(text='🔙 Назад', callback_data=f'eg_page:{page}')

    return builder.adjust(1).as_markup()


def back_pc():
    builder = InlineKeyboardBuilder()

    builder.button(text='🔙 Назад', callback_data='main_menu')
    return builder.as_markup()


def bn_go_to_manager():
    builder = InlineKeyboardBuilder()

    builder.button(text='Перейти в чат ', callback_data='bn_go_manager')
    return builder.as_markup()
