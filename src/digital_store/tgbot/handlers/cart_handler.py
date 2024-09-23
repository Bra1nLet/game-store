import os.path
import time
from typing import Type

from aiogram import Router, F, types
from yoomoney import Client, Quickpay

from tgbot.data import loader
from tgbot.data.config import p2p_token, receiver
from tgbot.data.loader import bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile, URLInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from tgbot.handlers.ps_handler import ps_country_handler
from tgbot.handlers.xbox_handler import platform_handler
from tgbot.keyboards.base_keyboards import *
from tgbot.keyboards.ps_keyboards import ps_go_to_manager
from tgbot.services.database import User, PSGame, ConsoleSubscription, Settings, AdminChat, XBOXGame, XBOXGameEdition, \
    CartItems
from tgbot.keyboards.xbox_keyboards import *
from sqlalchemy.orm.session import Session

from tgbot.utils.other import get_refill_prices, format_subscription, get_refill_block, get_round_price, draw_editions, \
    get_donation_price, format_game, get_currency, get_game_price, send_admin_invites, get_photo, get_total_price, \
    get_sub_media, admin_format_cart
from tgbot.utils.states import *

router = Router()


@router.callback_query(F.data.startswith('cart:'))
async def add_to_cart_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    platform, item_type, item_id, in_cart = call.data.split(':')[1:]
    item_id, in_cart = int(item_id), int(in_cart)
    platform, item_type = str(platform), str(item_type)

    if in_cart:
        db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id, CartItems.obj_id == item_id,
                                           CartItems.platform == platform, CartItems.obj_type == item_type).delete()
    else:
        db_session.add(CartItems(user_id=call.from_user.id, obj_id=item_id, platform=platform, obj_type=item_type))
    db_session.commit()

    await call.message.edit_reply_markup(reply_markup=item_kb(item_id, platform, item_type, data['back'], 1 - in_cart))


@router.callback_query(F.data.startswith('show_cart:'))
async def show_cart_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    platform = call.data.split(':')[1]

    items = db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                               CartItems.platform == platform).all()

    if not items:
        await call.answer('Корзина пуста')
        return

    if platform == 'ps':
        GameClass = PSGameEdition
    else:
        GameClass = XBOXGameEdition

    editions = db_session.query(GameClass).filter(
        GameClass.id.in_([i.obj_id for i in items if i.obj_type == 'game'])).all()
    subs = db_session.query(ConsoleSubscription).filter(
        ConsoleSubscription.id.in_([i.obj_id for i in items if i.obj_type == 'subscription'])).all()
    donations = db_session.query(ConsoleDonation).filter(
        ConsoleDonation.id.in_([i.obj_id for i in items if i.obj_type == 'donation'])).all()

    cart_text = admin_format_cart(db_session, platform, editions, subs, donations)

    media_path = f'tgbot/utils/media/{platform}_cart.png'
    media = get_photo(media_path, db_session)

    message = await call.message.edit_media(InputMediaPhoto(media=media, caption='⏳ Подождите, корзина загружается'))

    total_price = get_total_price(db_session, platform, editions, subs, donations)

    await call.message.edit_caption(caption=f'Итого: {total_price}₽',
                                    reply_markup=cart_kb(platform, db_session, editions, subs, donations,
                                                         data.get('region', 'tr')))

    await state.update_data(price=total_price, platform=platform, cart_text=cart_text)

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('cart_show_item:'))
async def show_cart_item_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = str(data['platform'])

    obj_type, item_id = call.data.split(':')[1:]
    item_id = int(item_id)

    EditionClass = PSGameEdition if platform == 'ps' else XBOXGameEdition
    GameClass = PSGame if platform == 'ps' else XBOXGame

    if obj_type == 'game':
        edition = db_session.query(EditionClass).filter(EditionClass.id == item_id).first()
        game = db_session.query(GameClass).get(edition.game_id)

        text = f'{get_flag(edition.region)} {game.name} {edition.name} {edition.platform}\n' \
               f'💸 Цена: {get_game_price(edition.price if not edition.discount else edition.discount, get_currency(edition.region), platform, db_session, edition.margin)}₽ 💸'

        media = InputMediaPhoto(media=edition.pic, caption=text)
    elif obj_type == 'subscription':
        sub = db_session.query(ConsoleSubscription).get(item_id)
        text = f'{get_flag(sub.region)}\n{format_subscription(sub, True)}'
        media = InputMediaPhoto(media=get_photo(get_sub_media(sub.name), db_session), caption=text)
    else:
        donation = db_session.query(ConsoleDonation).get(item_id)
        game = db_session.query(GameClass).get(donation.game_id)
        price = get_donation_price(donation.price if not donation.discount else donation.discount,
                                   get_currency(donation.region), platform, db_session, donation.margin)
        text = f'{get_flag(donation.region)} {game.name} {donation.description}\n💸 Цена: {price}₽ 💸'
        media = None

    if media:
        await call.message.edit_media(media, reply_markup=cart_item_kb(obj_type, item_id, platform))
    else:
        await call.message.edit_caption(caption=text, reply_markup=cart_item_kb(obj_type, item_id, platform))


@router.callback_query(F.data.startswith('cart_delete:'))
async def delete_cart_item_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    await call.answer("🗑 Удалено")

    data = await state.get_data()
    platform = str(data['platform'])
    obj_type, item_id = call.data.split(':')[1:]
    item_id = int(item_id)
    obj_type = str(obj_type)

    db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id, CartItems.obj_id == item_id,
                                       CartItems.obj_type == obj_type, CartItems.platform == platform).delete()
    db_session.commit()

    call = CallbackQuery(id=call.id, from_user=call.from_user, message=call.message, chat_instance=call.chat_instance,
                         data=f'show_cart:{platform}')

    items = db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                               CartItems.platform == platform).all()

    if not items:
        call_data = 'platform:XBOX' if platform == 'xbox' else f'ps_country:{data.get("region")}'
        call = CallbackQuery(id=call.id, from_user=call.from_user, message=call.message,
                             chat_instance=call.chat_instance,
                             data=call_data)
        if platform == 'ps':
            await ps_country_handler(call, state, db_session)
        else:
            await platform_handler(call, state, db_session)

        return

    await show_cart_handler(call, state, db_session)


@router.callback_query(F.data == 'cart_pay')
async def cart_pay_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = str(data['platform'])
    price = int(data['price'])

    items = db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                               CartItems.platform == platform).all()

    if not items:
        await call.answer('Корзина пуста')
        return

    label = f'{int(time.time())}{call.from_user.id}'

    quickpay = Quickpay(
        receiver=receiver,
        quickpay_form='shop',
        targets=f'Оплата корзины',
        paymentType='SB',
        sum=price,
        label=label
    )

    media = InputMediaPhoto(media=get_photo(f'tgbot/utils/media/{platform}_go_pay.png', db_session),
                            caption=f'Итого: {price}₽\n\n<i>Осталось совсем чуть-чуть🤏</i>')
    await call.message.edit_media(media,
                                  reply_markup=confirm_buy_kb(label, quickpay.redirected_url, f'show_cart:{platform}'))

    await state.set_state(MainState.cart_buy)


@router.callback_query(MainState.cart_buy, F.data.startswith('check:'))
async def check_cart_pay_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = str(data['platform'])
    label = call.data.split(':')[1]

    client = Client(p2p_token)

    history = client.operation_history(label=label)

    try:
        operation = history.operations[-1]
        if operation.status == 'success':
            user = db_session.query(User).filter(User.id == call.from_user.id).one()

            db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                               CartItems.platform == platform).delete()
            db_session.commit()

            if (not user.ps_account) if platform == 'ps' else (not user.xbox_account):
                media_path = 'tgbot/utils/media/ps_buy_success.png' if platform == 'ps' else 'tgbot/utils/media/xbox_' \
                                                                                             'buy_success.png'
                media = get_photo(media_path, db_session)
                message = await call.message.edit_media(
                    InputMediaPhoto(media=media,
                                    caption=f"""Оплата прошла успешно🔥\n\nНапиши почту для создания аккаунта.
<i>
Примечание: 
    1.	Почта должна быть обязательно с доменом .com (gmail, outlook например), на русские почты аккаунты не создаются
    2.	Почта должна быть той, что не привязана ни к одному аккаунту {'Sony' if platform == 'ps' else 'Microsoft'}
</i>
Если у тебя есть вопросы по этому пункту - нажми кнопку «Перейти в чат»
Там менеджер тебя проконсультирует!:)
        """),
                    reply_markup=ps_go_to_manager())
                await state.set_state(PSState.email if platform == 'ps' else XBOXState.email)

                return media_path, message.photo[-1].file_id

            media_path = 'tgbot/utils/media/ps_data.png' if platform == 'ps' else 'tgbot/utils/media/xbox_data.png'
            media = get_photo(media_path, db_session)
            message = await call.message.edit_media(InputMediaPhoto(media=media))
            await call.message.edit_caption(caption='Введи почту и пароль от аккаунта в формате: email:pass\n\n'
                                                    '<i>Пример: heroes21@gmail.com:Hetp33asd</i>')
            await state.set_state(PSState.log_and_pass if platform == 'ps' else XBOXState.log_and_pass)

            return media_path, message.photo[-1].file_id
        else:
            await call.answer('❌ Оплата не прошла')
    except:
        await call.answer(f'Платеж не найден или не прошел. Пожалуйста, проверьте еще раз.')
