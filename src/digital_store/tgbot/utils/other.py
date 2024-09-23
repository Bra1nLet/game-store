from io import BytesIO

import requests as requests
from PIL import Image
from aiogram.types import User, FSInputFile
from sqlalchemy.orm import Session

from tgbot.data import loader
from tgbot.data.config import admin_ids
from tgbot.data.loader import bot
from tgbot.keyboards.admin_keyboards import admin_enter_chat
from tgbot.services.database import PSGameEdition, PSGame, XBOXGameEdition, ConsoleSubscription, Settings, XBOXGame, \
    ConsoleDonation, Photo
from tgbot.services import database
from typing import Type

from tgbot.utils.curs import get_course


def draw_editions(editions: list[PSGameEdition]):
    images = []
    for edition in editions:
        edition_img = Image.open(BytesIO(requests.get(edition.pic).content))
        images.append(edition_img)

    image = Image.new('RGB', (sum([i.width for i in images]), max([i.height for i in images])))

    w = 0
    for i in images:
        image.paste(i, (w, 0))
        w += i.width

    # bytes_io = BytesIO()
    image = image.resize((image.width // 2, image.height // 2))
    image.save('shit.png', 'png')

    # image.save(bytes_io, 'PNG')
    # bytes_io.seek(0)
    #
    # return bytes_io


def ps_format_edition(edition: PSGameEdition, db_session: Session):
    text = f'{edition.game._name} {edition._name}'
    currency = get_currency(edition.region)
    default_price = get_game_price(edition.price, currency, "ps", db_session, edition.margin)
    if edition.discount:
        discount_price = get_game_price(edition.discount, currency, "ps", db_session, edition.margin)
        discount = int((default_price - discount_price) / default_price * 100)
        text += f' {discount_price}₽ ({discount}% скидка) '
    else:
        text += f' {default_price}₽'

    return text


def xbox_format_edition(edition: XBOXGameEdition, db_session: Session):
    text = edition.game._name + ' ' + edition._name
    currency = get_currency(edition.region)

    default_price = get_game_price(edition.price, currency, "xbox", db_session, edition.margin)
    if edition.discount:
        discount_price = get_game_price(edition.price, currency, "xbox", db_session, edition.margin)
        discount = int(discount_price / default_price * 100)
        text += f' {discount_price} ({discount}% скидка) '
    else:
        text += f' {default_price} '

    text += '₽'
    return text


def get_currency(region):
    currency = 'UAH' if region == 'ua' else 'TRY'
    return currency


def format_game(edition: Type[PSGameEdition] | Type[XBOXGameEdition], platform, db_session: Session):
    game: PSGame = edition.game
    currency = get_currency(edition.region)

    text = f'{game._name} {edition._name} Edition\n\n'
    text += f'{edition.description}\n\n'
    text += f'💸 Цена: {f"<s>{get_game_price(edition.price, currency, platform, db_session, edition.margin)}</s> {get_game_price(edition.discount, currency, platform, db_session, edition.margin)}₽" if edition.discount else f"{get_game_price(edition.price, currency, platform, db_session, edition.margin)}₽"} 💸'

    return text


async def send_admin_invites(item: str, user: User, login: str | None = None, password: str | None = None,
                             tfa: str | None = None, no_account: bool = False,
                             platform: str | None = None, cart: str | None = None):
    text = f"""💰 Новая покупка!
👤 Пользователь: <b>@{user.username}</b> | <a href='tg://user?id={user.id}'>{user.full_name}</a> | <code>{user.id}</code>
Платформа: {platform}
"""
    if cart:
        text += cart
    else:
        text += f'⚙️ Товар: <code>{item}</code>\n'
    if no_account:
        text += f"❌ Нет аккаунта, email:{login if login else 'Нет'}"
    else:
        text = f"""Логин: <code>{login}</code>
Пароль: <code>{password}</code>
2FA: <code>{tfa}</code>"""
    for admin in admin_ids:
        await bot.send_message(admin, text, reply_markup=admin_enter_chat(user.id))


def format_user(user_id: int, db_session: Session):
    user = db_session.query(database.UsersModel).filter(database.UsersModel.id == user_id).one()

    text = f'<b>@{user.username}</b> | <a href="tg://user?id={user.id}">{user.full_name}</a>'
    return text


def get_refill_prices(currency, additional_margin, floor_margin):
    base_rate = get_course(currency)
    rates = [round(base_rate * (1 + floor_margin / 100 + additional_margin / 100 * i), 2) for i in range(0, 6)]
    return rates, format_refill(currency, rates)


def format_refill(currency, rates):
    text = f'<i>Введите сумму для пополнения в {"лирах🇹🇷" if currency == "TRY" else "гривнах🇺🇦"}\n'
    text += f"""1. Сумма должна быть кратной {10 if currency == 'UAH' else 50} если пополнение кошелька
2. Сумма может быть любой, если нужно оплатить корзину или определенную игру</i>
"""
    return text


def get_refill_block(amount):
    if 0 < amount < 500:
        return 5
    if 500 <= amount < 1000:
        return 4
    if 1000 <= amount < 2000:
        return 3
    if 2000 <= amount < 3000:
        return 2
    if 3000 <= amount < 5000:
        return 1
    return 0


def get_game_block(amount):
    if 0 <= amount < 500:
        return 4
    if 500 <= amount < 1000:
        return 3
    if 1000 <= amount < 2000:
        return 2
    if 2000 <= amount < 3000:
        return 1
    if 3000 <= amount < 5000:
        return 0


def get_game_price(price, currency, platform, db_session: Session, specify_margin=0):
    settings = db_session.query(Settings).first()
    base_margin = 100
    additional_margin = 5
    base_rate = get_course(currency)

    if specify_margin:
        price *= base_rate * (1 + specify_margin / 100)
        price += 10 - price % 10
        return int(price)

    if platform == 'ps':
        base_margin = settings.ps_base_game_margin
        additional_margin = settings.ps_additional_game_margin
    elif platform == 'xbox':
        base_margin = settings.xbox_base_game_margin
        additional_margin = settings.xbox_additional_game_margin
    elif platform == 'epicgames':
        base_margin = settings.epicgames_base_game_margin
        additional_margin = settings.epicgames_additional_game_margin

    rates = [round(base_rate * (1 + base_margin / 100 + additional_margin / 100 * i), 2) for i in range(0, 5)]
    rate = rates[get_game_block(price or 0)]

    price *= rate
    price += 10 - price % 10

    return int(price)


def get_donation_margin(platform, price, db_session: Session):
    settings = db_session.query(Settings).first()
    base_margin = 30
    additional_margin = 5

    if platform == 'ps':
        base_margin = settings.ps_base_donate_margin
        additional_margin = settings.ps_additional_donate_margin
    elif platform == 'xbox':
        base_margin = settings.xbox_base_donate_margin
        additional_margin = settings.xbox_additional_donate_margin
    elif platform == 'epicgames':
        base_margin = settings.epicgames_base_donate_margin
        additional_margin = settings.epicgames_additional_donate_margin

    rates = [round((base_margin / 100 + additional_margin / 100 * i), 2) for i in range(0, 5)]
    rate = rates[get_game_block(price or 0)]

    return rate


def get_donation_price(price, currency, platform, db_session: Session, specify_margin=0):
    rate = (1 + (get_donation_margin(platform, price, db_session))) if not specify_margin else (
            1 + specify_margin / 100)

    price *= rate * get_course(currency)
    price += 10 - price % 10

    return get_round_price(currency, price, convert=False)


def format_subscription(subscription: Type[ConsoleSubscription], cart=False):
    text = f'Подписка {"PS Plus" if subscription.platform == "ps" else "XBOX"} {subscription._name}\n\n'
    text += f'Описание:\n{subscription.description}\n'
    if not cart:
        text += 'Выберите длительность подписки'
    else:
        text += f'💸 Цена: {subscription.price if not subscription.discount else subscription.discount}₽ 💸'
    return text


def get_round_price(currency, amount, convert=True):
    if convert:
        price = int(get_course(currency) * amount)
    else:
        price = amount
    price += 10 - price % 10
    return int(price)


def admin_format_game(game: Type[PSGame | XBOXGame]):
    text = f'Игра: {game._name}\n'
    text += f'Категория: {game.category}\n'
    return text


def admin_format_donation(donation: Type[ConsoleDonation] | ConsoleDonation):
    text = f'Описание: {donation.description}\n'
    text += f'Цена: {donation.price} {get_currency(donation.region)}\n'
    if donation.discount:
        text += f'Цена со скидкой: {donation.discount} {get_currency(donation.region)}\n'

    if donation.margin:
        text += f'Маржа: {donation.margin}%'
    else:
        db_session = loader.Session()
        margin = get_donation_margin(donation.platform, donation.price if not donation.discount else donation.discount,
                                     db_session)
        db_session.close()

        text += f'Маржа: {int(margin * 100)}%'

    return text


def admin_format_edition(edition: Type[PSGameEdition | XBOXGameEdition]):
    text = f'Издание: {edition._name}\n'
    text += f'Описание: {edition.description}\n'
    text += f'Цена: {edition.price} {get_currency(edition.region)}\n'
    if edition.discount:
        text += f'Цена со скидкой: {edition.discount} {get_currency(edition.region)}\n'

    if edition.margin:
        text += f'Маржа: {edition.margin}%'
    else:
        db_session = loader.Session()
        margin = get_donation_margin('ps' if isinstance(edition, PSGameEdition) else 'xbox',
                                     edition.price if not edition.discount else edition.discount, db_session)
        db_session.close()

        text += f'Маржа: {int(margin * 100)}%'

    return text


def admin_format_subscription(subscription: Type[ConsoleSubscription]):
    text = f'Платформа: {subscription.platform}\n'
    text += f'Подписка: {subscription._name}\n'
    text += f'Описание: {subscription.description}\n'
    text += f'Цена: {subscription.price} ₽\n'
    if subscription.discount:
        text += f'Цена со скидкой: {subscription.discount} {get_currency(subscription.region)}\n'

    return text


def admin_margins_text(settings: Type[Settings], platform: str):
    if platform == 'ps':
        base_game_margin = settings.ps_base_game_margin
        additional_game_margin = settings.ps_additional_game_margin
        base_donate_margin = settings.ps_base_donate_margin
        additional_donate_margin = settings.ps_additional_donate_margin
        base_refill_margin_ua = settings.ps_base_refill_margin_ua
        additional_refill_margin_ua = settings.ps_additional_refill_margin_ua
        base_refill_margin_tr = settings.ps_base_refill_margin_tr
        additional_refill_margin_tr = settings.ps_additional_refill_margin_tr
        text = '<code>Категория | Базовая наценка | Дополнительная наценка\n\n'
        text += f'Игры      |{base_game_margin:^17}| {additional_game_margin}\n'
        text += f'Донаты    |{base_donate_margin:^17}| {additional_donate_margin}\n'
        text += f'Гривна    |{base_refill_margin_ua:^17}| {additional_refill_margin_ua}\n'
        text += f'Лира      |{base_refill_margin_tr:^17}| {additional_refill_margin_tr}\n</code>'
    elif platform == 'xbox':
        base_game_margin = settings.xbox_base_game_margin
        additional_game_margin = settings.xbox_additional_game_margin
        base_donate_margin = settings.xbox_base_donate_margin
        additional_donate_margin = settings.xbox_additional_donate_margin
        base_refill_margin = settings.xbox_base_refill_margin
        additional_refill_margin = settings.xbox_additional_refill_margin
        text = '<code>Категория | Базовая наценка | Дополнительная наценка\n\n'
        text += f'Игры      |{base_game_margin:^17}| {additional_game_margin}\n'
        text += f'Донаты    |{base_donate_margin:^17}| {additional_donate_margin}\n'
        text += f'Пополнение|{base_refill_margin:^17}| {additional_refill_margin}\n</code>'
    else:
        base_refill_margin = settings.bn_base_refill_margin
        additional_refill_margin = settings.bn_additional_refill_margin
        text = '<code>Категория | Базовая наценка | Дополнительная наценка\n\n'
        text += f'Донаты    |{base_refill_margin:^17}| {additional_refill_margin}\n</code>'

    return text


def get_photo(file_name: str, db_session: Session):
    photo = db_session.query(Photo).filter(Photo.file_path == file_name).first()
    if photo:
        return photo.file_id
    else:
        return FSInputFile(file_name)


def get_total_price(db_session: Session, platform,
                    editions: list[Type[PSGameEdition | XBOXGameEdition]] | None = None,
                    subscriptions: list[Type[ConsoleSubscription]] | None = None,
                    donations: list[Type[ConsoleDonation]] | None = None):
    total_price = 0

    for edition in editions:
        currency = get_currency(edition.region)
        total_price += get_game_price(edition.price if not edition.discount else edition.discount, currency, platform,
                                      db_session,
                                      edition.margin)
    for sub in subscriptions:
        total_price += sub.price if not sub.discount else sub.discount
    for donation in donations:
        currency = get_currency(donation.region)

        total_price += get_donation_price(donation.price if not donation.discount else donation.discount, currency,
                                          platform,
                                          db_session, donation.margin)

    return total_price


def get_flag(region):
    if region == 'ua':
        return '🇺🇦 '
    if region == 'tr':
        return '🇹🇷 '


def get_sub_media(name):
    if name == '⚪️ Essential':
        media_path = 'tgbot/utils/media/essential.png'
    elif name == '🟡 Extra':
        media_path = 'tgbot/utils/media/extra.png'
    elif name == '⚫️ Deluxe':
        media_path = 'tgbot/utils/media/deluxe.png'
    elif name == '🔴 Ea Play':
        media_path = 'tgbot/utils/media/eaplay.png'
    elif name == 'Gamepass Ultimate':
        media_path = 'tgbot/utils/media/ultimate.png'

    return media_path


def admin_format_cart(db_session: Session, platform,
                      editions: list[Type[PSGameEdition | XBOXGameEdition]] | None = None,
                      subscriptions: list[Type[ConsoleSubscription]] | None = None,
                      donations: list[Type[ConsoleDonation]] | None = None):
    text = '🛒 Корзина:\n\n'
    for edition in editions:
        text += f'{get_flag(edition.region)} {edition.game._name} {edition._name} Edition {edition.platform}\n'
    for sub in subscriptions:
        text += f'{get_flag(sub.region)} {"PS Plus" if platform == "ps" else "XBOX"} {sub._name} {sub.duration}\n'
    for donation in donations:
        game = db_session.query(PSGame if platform == 'ps' else XBOXGame).get(donation.game_id)
        text += f'{get_flag(donation.region)} {game.name} {donation.description}\n'

    return text
