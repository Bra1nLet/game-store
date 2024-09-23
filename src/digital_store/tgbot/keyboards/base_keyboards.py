from typing import Type

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy.orm import Session

from tgbot.services.database import ConsoleDonation, PSGameEdition, XBOXGameEdition, ConsoleSubscription, PSGame, \
    XBOXGame
from tgbot.utils.other import get_donation_price, get_currency, ps_format_edition, xbox_format_edition, get_flag, \
    get_round_price


def start_menu():
    builder = InlineKeyboardBuilder()

    builder.button(text='Перейти к покупкам', callback_data='main_menu')
    builder.button(text='Почитать отзывы', url='https://t.me/+c6--F8QT9MVlYmQ6')
    builder.button(text='Задать вопрос', callback_data='https://t.me/joysticksupport')


def main_menu():
    builder = InlineKeyboardBuilder()

    builder.button(text='PlayStation', callback_data='platform:PS')
    builder.button(text='Xbox', callback_data='platform:XBOX')
    builder.button(text='BattleNet', callback_data='pc:battlenet')

    builder.adjust(2)

    return builder.as_markup()


def confirm_buy_kb(order_id, url, back):
    builder = InlineKeyboardBuilder()

    builder.button(text='Оплатить', url=url)
    builder.button(text='✅ Проверить оплату', callback_data=f'check:{order_id}')
    builder.button(text='🔙 Назад', callback_data=back)

    return builder.adjust(2).as_markup()


def confirm_credentials():
    builder = InlineKeyboardBuilder()

    builder.button(text='✅ Данные верны', callback_data='credentials_confirmed')

    return builder.as_markup()


def tfa_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text="У меня нет резервного кода", callback_data='2fa:no_code')
    builder.button(text="У меня нет 2fa", callback_data='2fa:disabled')

    return builder.adjust(1).as_markup()


def choose_subscription_duration(sub_name, durations, platform: str, region=None):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=f'{i} мес.', callback_data=f'subscription:{platform}:{sub_name}:{i}') for i in
          durations]
    builder.add(*kb).adjust(2)

    if region:
        builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'ps_country:{region}'))
    else:
        builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='platform:XBOX'))

    return builder.as_markup()


def console_choose_donation_kb(options: list[Type[ConsoleDonation]], platform, region, db_session):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=i.description + ' ' + str(
        get_donation_price(i.price if not i.discount else i.discount, get_currency(region), platform, db_session,
                           i.margin)) + '₽',
                               callback_data=f'donation:{i.id}') for i in
          options]
    builder.row(*kb, width=2)
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'{platform}:donate'))
    return builder.as_markup()


def item_kb(item, platform, item_type, back, in_cart=False):
    builder = InlineKeyboardBuilder()

    builder.button(text='🛒 Купить', callback_data=f'buy:{platform}:{item_type}:{item}')
    if not in_cart:
        builder.button(text='🛒 В корзину', callback_data=f'cart:{platform}:{item_type}:{item}:{int(in_cart)}')
    else:
        builder.button(text='🛒 Убрать из корзины', callback_data=f'cart:{platform}:{item_type}:{item}:{int(in_cart)}')

    builder.button(text='🔙 Назад', callback_data=back)

    return builder.adjust(1).as_markup()


def cart_kb(platform, db_session: Session,
            editions: list[Type[PSGameEdition | XBOXGameEdition]] | None = None,
            subscriptions: list[Type[ConsoleSubscription]] | None = None,
            donations: list[Type[ConsoleDonation]] | None = None, region=None):
    builder = InlineKeyboardBuilder()

    format_edition = ps_format_edition if platform == 'ps' else xbox_format_edition
    for edition in editions:
        builder.button(text=get_flag(edition.region) + format_edition(edition, db_session),
                       callback_data=f'cart_show_item:game:{edition.id}')
    for sub in subscriptions:
        if sub.platform == 'ps':
            builder.button(text=f'{get_flag(sub.region)} PS Plus {sub.duration} мес. '
                                f'{sub.price if not sub.discount else sub.discount}₽',
                           callback_data=f'cart_show_item:subscription:{sub.id}')
        else:
            builder.button(text=f'{get_flag(sub.region)} Gamepass Ultimate {sub.duration} мес. '
                                f'{sub.price if not sub.discount else sub.discount}₽',
                           callback_data=f'cart_show_item:subscription:{sub.id}')
    for donation in donations:
        GameClass = PSGame if platform == 'ps' else XBOXGame
        game = db_session.query(GameClass).filter(GameClass.id == int(donation.game_id)).first()
        currency = get_currency(donation.region)

        price = get_donation_price(donation.price if not donation.discount else donation.discount, currency, platform,
                                   db_session, donation.margin)
        builder.button(
            text=f'{get_flag(donation.region)} {game.name} {donation.description} {price}₽',
            callback_data=f'cart_show_item:donation:{donation.id}')

    builder.button(text='➡️ Перейти к оплате', callback_data='cart_pay')
    builder.button(text='🔙 Назад', callback_data='platform:XBOX' if platform == 'xbox' else f'ps_country:{region}')

    return builder.adjust(1).as_markup()


def cart_item_kb(item_type, item_id, platform):
    builder = InlineKeyboardBuilder()

    builder.button(text='🗑 Удалить', callback_data=f'cart_delete:{item_type}:{item_id}')
    builder.button(text='🔙 Назад', callback_data=f'show_cart:{platform}')

    return builder.adjust(1).as_markup()
