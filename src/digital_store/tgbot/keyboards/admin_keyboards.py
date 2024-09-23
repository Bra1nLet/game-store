from typing import Type

from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from tgbot.services.database import PSGameEdition, XBOXGameEdition, ConsoleDonation, ConsoleSubscription


def admin_enter_chat(user_id):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"✅ Присоединиться к чату", callback_data=f"admin_enter_chat:{user_id}")

    return builder.as_markup()


def admin_exit_chat_kb():
    keyboard = ReplyKeyboardBuilder()

    kb = [KeyboardButton(text=f'✅ Завершить чат'), KeyboardButton(text=f'❌ Передать чат другому администратору')]
    return keyboard.add(*kb).adjust(1).as_markup(resize_keyboard=True)


def admin_menu_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text='Рассылка', callback_data='admin_sent')
    builder.button(text='Настройки', callback_data='admin_settings')

    return builder.as_markup()


def start_spam_kb():
    markup = InlineKeyboardBuilder()
    kb = [InlineKeyboardButton(text='✅ Начать рассылку', callback_data='spam_start'),
          InlineKeyboardButton(text='❌ Отмена', callback_data='admin_menu')]

    return markup.add(*kb).adjust(1).as_markup()


def admin_settings_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text='PS', callback_data='settings:ps')
    builder.button(text='XBOX', callback_data='settings:xbox')
    builder.button(text='BattleNet', callback_data='settings:bn')
    builder.adjust(2)

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='admin_menu'))

    return builder.as_markup()


def console_settings_kb():
    builder = InlineKeyboardBuilder()

    builder.button(text='Игры', callback_data=f'admin:games')
    builder.button(text='Подписки', callback_data=f'admin:subscriptions')
    # builder.button(text='Пополнение баланса', callback_data=f'admin:refill')
    builder.button(text='Наценки', callback_data=f'admin:margins')
    builder.adjust(2)

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'admin_settings'))
    return builder.as_markup()


def admin_ps_region():
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇦 Украина", callback_data='adm_ps_country:ua')
    builder.button(text='🇹🇷 Турция', callback_data='adm_ps_country:tr')
    builder.button(text='🔙 Назад', callback_data=f'settings:ps')

    return builder.adjust(2).as_markup()


def adm_categories_kb(categories: list[tuple[str, str]], region: str | None = None):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=f'{i[0]} {i[1]}', callback_data=f'adm_category:{i[0]}') for i in categories]
    builder.add(*kb)
    builder.button(text='🔙 Назад', callback_data=f'adm_ps_country:{region}' if region else 'settings:xbox')

    return builder.adjust(1).as_markup()


def adm_games_kb(games: list[tuple[int, str, str]], page: int, category: str | None = None):
    builder = InlineKeyboardBuilder()

    kb = [InlineKeyboardButton(text=f'{i[1]} {i[2]}', callback_data=f'adm_game:{i[0]}') for i in
          games[page * 20:page * 20 + 20]]
    builder.add(*kb).adjust(2)

    navigation = []
    if page > 0:
        navigation.append(InlineKeyboardButton(text='⬅️', callback_data=f'adm_page:{page - 1}'))
    if len(games) / 20 > page + 1:
        navigation.append(InlineKeyboardButton(text='➡️️', callback_data=f'adm_page:{page + 1}'))

    builder.row(*navigation)
    builder.row(InlineKeyboardButton(text='Изменить эмоджи', callback_data=f'change_category:{category}'))
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'admin:games'))

    return builder.as_markup()


def adm_choose_platform(page: int, platforms: list[str], platform):
    builder = InlineKeyboardBuilder()

    builder.add(
        *[InlineKeyboardButton(text=i.upper(), callback_data=f'adm_{platform}_platform:{i}') for i in platforms])
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'adm_page:{page}'))

    return builder.as_markup()


def adm_game_kb(editions: list[Type[PSGameEdition | XBOXGameEdition]], page: int):
    builder = InlineKeyboardBuilder()

    builder.button(text='Изменить категорию', callback_data='change_game:category')
    builder.button(text='Изменить название', callback_data='change_game:name')
    builder.adjust(2)

    builder.row(InlineKeyboardButton(text='Донат', callback_data='change_game:donate'))

    for edition in editions:
        builder.row(InlineKeyboardButton(text=edition._name, callback_data=f'adm_edition:{edition.id}'))

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'adm_page:{page}'))

    return builder.as_markup()


def adm_donations_kb(donations: list[Type[ConsoleDonation]], game_id: int):
    builder = InlineKeyboardBuilder()

    for donation in donations:
        builder.row(InlineKeyboardButton(text=donation.description, callback_data=f'adm_donation:{donation.id}'))

    builder.row(InlineKeyboardButton(text='Добавить', callback_data=f'add_donation:{game_id}'))
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'adm_game:{game_id}'))

    return builder.as_markup()


def admin_donation_kb(donation: Type[ConsoleDonation] | ConsoleDonation):
    builder = InlineKeyboardBuilder()

    builder.button(text='Изменить описание', callback_data=f'change_donation:{donation.id}:description')
    builder.button(text='Изменить цену', callback_data=f'change_donation:{donation.id}:price')
    if not donation.discount:
        builder.button(text='Добавить скидку', callback_data=f'change_donation:{donation.id}:discount')
    else:
        builder.button(text='Изменить скидку', callback_data=f'change_donation:{donation.id}:discount')
        builder.button(text='Убрать скидку', callback_data=f'change_donation:{donation.id}:discount:remove')
    builder.adjust(2)

    builder.row(InlineKeyboardButton(text='Изменить наценку', callback_data=f'change_donation:{donation.id}:margin'))

    builder.row(InlineKeyboardButton(text='🗑 Удалить', callback_data=f'delete_donation:{donation.id}'))

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'change_game:donate'))

    return builder.as_markup()


def delete_donation_confirm_kb(donation_id: int):
    builder = InlineKeyboardBuilder()

    builder.button(text='✅ Удалить', callback_data=f'delete_donation_confirm:{donation_id}')
    builder.button(text='❌ Отмена', callback_data=f'adm_donation:{donation_id}')

    return builder.as_markup()


def admin_edition_kb(edition: Type[PSGameEdition | XBOXGameEdition]):
    builder = InlineKeyboardBuilder()

    builder.button(text='Изменить название', callback_data=f'change_edition:{edition.id}:name')
    builder.button(text='Изменить описание', callback_data=f'change_edition:{edition.id}:description')

    builder.button(text='Изменить цену', callback_data=f'change_edition:{edition.id}:price')
    if not edition.discount:
        builder.button(text='Добавить скидку', callback_data=f'change_edition:{edition.id}:discount')
    else:
        builder.button(text='Изменить скидку', callback_data=f'change_edition:{edition.id}:discount')
        builder.button(text='Убрать скидку', callback_data=f'change_edition:{edition.id}:discount:remove')
    builder.adjust(2)

    builder.row(InlineKeyboardButton(text='Изменить наценку', callback_data=f'change_edition:{edition.id}:margin'))

    # builder.row(InlineKeyboardButton(text='🗑 Удалить', callback_data=f'delete_edition:{edition.id}'))

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'adm_game:{edition.game_id}'))

    return builder.as_markup()


def admin_subscriptions_kb(subscriptions: list[str], platform: str):
    builder = InlineKeyboardBuilder()

    for subscription in subscriptions:
        builder.row(InlineKeyboardButton(text=subscription, callback_data=f'adm_subscription:{subscription}'))
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'settings:{platform}'))

    return builder.as_markup()


def admin_subscription_kb(durations: list[str]):
    builder = InlineKeyboardBuilder()

    for duration in durations:
        builder.row(InlineKeyboardButton(text=f'{duration} мес.', callback_data=f'adm_sub_duration:{duration}'))
    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'admin:subscriptions'))

    return builder.as_markup()


def admin_duration_kb(subscription: Type[ConsoleSubscription]):
    builder = InlineKeyboardBuilder()

    builder.button(text='Изменить описание', callback_data=f'change_subscription:description')
    builder.button(text='Изменить цену', callback_data=f'change_subscription:price')
    builder.adjust(1)

    if not subscription.discount:
        builder.button(text='Добавить скидку', callback_data=f'change_subscription:discount')
    else:
        builder.row(InlineKeyboardButton(text='Изменить скидку',
                                         callback_data=f'change_subscription:discount'),
                    InlineKeyboardButton(text='Убрать скидку', callback_data=f'change_subscription:discount:remove'))

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'adm_subscription:{subscription._name}'))

    return builder.as_markup()


def admin_margins_kb(platform: str):
    builder = InlineKeyboardBuilder()

    if platform != 'bn':
        builder.button(text='Игры: стандартная', callback_data=f'change_margin:{platform}:games:base')
        builder.button(text='Игры: дополнительная', callback_data=f'change_margin:{platform}:games:additional')
        builder.button(text='Донат: стандартная', callback_data=f'change_margin:{platform}:donate:base')
        builder.button(text='Донат: дополнительная', callback_data=f'change_margin:{platform}:donate:additional')
    if platform == 'ps':
        builder.button(text='Гривна: стандартная', callback_data=f'change_margin:{platform}:refill:base:ua')
        builder.button(text='Гривна: дополнительная', callback_data=f'change_margin:{platform}:refill:additional:ua')
        builder.button(text='Лира: стандартная', callback_data=f'change_margin:{platform}:refill:base:tr')
        builder.button(text='Лира: дополнительная', callback_data=f'change_margin:{platform}:refill:additional:tr')
    else:
        builder.button(text='Пополнение: стандартная', callback_data=f'change_margin:{platform}:refill:base')
        builder.button(text='Пополнение: дополнительная', callback_data=f'change_margin:{platform}:refill:additional')

    builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=f'settings:{platform}'))

    return builder.adjust(2).as_markup()
