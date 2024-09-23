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

from tgbot.keyboards.base_keyboards import *
from tgbot.services.database import User, PSGame, ConsoleSubscription, Settings, AdminChat, XBOXGame, XBOXGameEdition, \
    CartItems
from tgbot.keyboards.xbox_keyboards import *
from sqlalchemy.orm.session import Session

from tgbot.utils.other import get_refill_prices, format_subscription, get_refill_block, get_round_price, draw_editions, \
    get_donation_price, format_game, get_currency, get_game_price, send_admin_invites, get_photo
from tgbot.utils.states import *

router = Router()


@router.callback_query(F.data == 'platform:XBOX')
async def platform_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    await state.clear()

    user = db_session.query(User).filter(User.id == call.from_user.id).one()
    has_account = user.xbox_account

    media_path = 'tgbot/utils/media/xbox_menu.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(
        InputMediaPhoto(
            media=media,
            caption='Прекрасный выбор🔥\nТеперь ты можешь выбрать то, зачем заглянул в наш магазин!'),
        reply_markup=xbox_menu(has_account)
    )

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data == 'xbox:info')
async def ps_help_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    text = f"""Текст для информации:

💛Основной канал JoyStick Store - https://t.me/storejoystick

🎮Новостной канал - https://t.me/newsjoystick

🗣️Отзывы - https://t.me/+c6--F8QT9MVlYmQ6

📞Чат поддержки - @joysticksupport

Особо важная информация для пользователя - https://t.me/storejoystick/127"""
    media_path = 'tgbot/utils/media/xbox_info.png'
    media = get_photo(media_path, db_session)

    message = await call.message.edit_media(InputMediaPhoto(media=media, caption=text),
                                            reply_markup=back_xbox_menu())
    return media_path, message.photo[-1].file_id


@router.callback_query(F.data == 'xbox:refill')
async def xbox_refill_account_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    settings = db_session.query(Settings).first()

    currency = 'TRY'
    rates, text = get_refill_prices(currency, settings.xbox_additional_refill_margin, settings.xbox_base_refill_margin)

    await state.update_data(rates=rates, currency=currency)
    media_path = 'tgbot/utils/media/xbox_refill.png'
    media = get_photo(media_path, db_session)

    message = await call.message.edit_media(InputMediaPhoto(media=media, caption=text),
                                            reply_markup=back_xbox_menu())

    await state.set_state(XBOXState.refill)

    return media_path, message.photo[-1].file_id


@router.message(XBOXState.refill)
async def ps_enter_refill_amount(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    rates = data['rates']
    currency = data['currency']

    try:
        amount = int(message.text)
        if amount <= 0:
            await message.answer('Введите целое положительное число')
            return

        block = get_refill_block(amount)
        await state.update_data(amount=amount, price=int(amount * rates[block]))

        label = f'{int(time.time())}{message.from_user.id}'

        quickpay = Quickpay(
            receiver=receiver,
            quickpay_form='shop',
            targets=f'Пополнение аккаунта XBOX на {amount} {currency}',
            paymentType='SB',
            sum=int(amount * rates[block]),  # price
            label=label
        )

        media_path = 'tgbot/utils/media/xbox_go_pay.png'
        media = get_photo(media_path, db_session)

        message = await message.answer_photo(media,
                                             f'Пополнение аккаунта XBOX на {amount} {currency}\n💸 Цена: '
                                             f'{int(amount * rates[block])}₽ 💸',
                                             reply_markup=confirm_buy_kb(label, quickpay.redirected_url,
                                                                         f'platform:XBOX'))
        await state.set_state(XBOXState.buy)

        return media_path, message.photo[-1].file_id
    except ValueError:
        await message.answer(f'Введите целое число')


@router.callback_query(F.data == 'xbox:donate')
async def xbox_enter_donate_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    games = [(i.id, i.name, i.emoji or '') for i in db_session.query(XBOXGame).filter(XBOXGame.has_donate == 1).all()]
    await state.update_data(games=games)

    media_path = 'tgbot/utils/media/xbox_donate.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media),
                                            reply_markup=xbox_games_kb(games, 0, True))

    await state.set_state(XBOXState.search_donation_game)

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data == 'xbox:plus')
async def xbox_subscriptions_handler(call: CallbackQuery, db_session: Session):
    subscriptions = db_session.query(ConsoleSubscription).filter(ConsoleSubscription.platform == 'xbox').all()

    media_path = 'tgbot/utils/media/xbox_sub_duration.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(
        InputMediaPhoto(media=media),
        reply_markup=choose_subscription_duration(subscriptions[0].name,
                                                  [i.duration for i in
                                                   subscriptions], 'xbox')
    )

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('subscription:xbox'))
async def xbox_process_subscription(call: CallbackQuery, state: FSMContext, db_session: Session):
    subscription: Type[ConsoleSubscription] = db_session.query(ConsoleSubscription).filter(
        ConsoleSubscription.duration == int(call.data.split(':')[3]), ConsoleSubscription.platform == 'xbox').one()

    if subscription.discount:
        price_text = f'💸 Цена: {f"<s>{subscription.price}</s> {subscription.discount}₽"}'
        price = subscription.discount
    else:
        price_text = f'💸 Цена: {subscription.price}₽ 💸'
        price = subscription.price

    await state.update_data(subscription_id=subscription.id)

    if subscription._name == 'Gamepass Ultimate':
        media_path = 'tgbot/utils/media/ultimate.png'
    else:
        media_path = 'tgbot/utils/media/xbox_go_pay.png'

    in_cart = db_session.query(db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                                                  CartItems.obj_id == int(subscription.id),
                                                                  CartItems.platform == 'xbox').exists()).scalar()

    media = get_photo(media_path, db_session)
    markup = item_kb(subscription.id, 'xbox', 'subscription', f'xbox:plus', in_cart)

    message = await call.message.edit_media(
        InputMediaPhoto(
            media=media,
            caption=f'XBOX {subscription._name} {subscription.duration} мес.\n\n{price_text}'
        ),
        reply_markup=markup
    )

    await state.update_data(price=price, back='xbox:plus')

    # media = get_photo(media_path, db_session)
    # message = await call.message.edit_media(InputMediaPhoto(media=media),
    #                                         reply_markup=confirm_buy_kb(label, quickpay.redirected_url,
    #                                                                     f'sub_type:xbox:{subscription.name}'))
    # await call.message.edit_caption(caption=f'XBOX {subscription.name} {subscription.duration} мес.\n\n{price_text}',
    #                                 reply_markup=confirm_buy_kb(label, quickpay.redirected_url,
    #                                                             f'sub_type:xbox:{subscription.name}'))
    # await state.set_state(XBOXState.buy)

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('xbox:search'))
async def xbox_search_game(call: CallbackQuery, state: FSMContext, db_session: Session):
    await state.set_state(XBOXState.search_game)

    media_path = 'tgbot/utils/media/xbox_search_games.png'
    media = get_photo(media_path, db_session)

    message = await call.message.edit_media(
        InputMediaPhoto(
            media=media,
            caption='Введи название игры, которую хочешь найти\n\n<i>🔍Примечание: желательно,'
                    'чтобы игра называлась так же, как и в официальном магазине XBOX Store</i>'
        ),
        reply_markup=back_xbox_menu()
    )

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('xbox:games'))
async def xbox_show_categories(call: CallbackQuery, db_session: Session, state: FSMContext):
    categories = list(set((i.category, i.emoji) for i in db_session.query(XBOXGame).all()))

    media_path = 'tgbot/utils/media/xbox_cats.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(
        InputMediaPhoto(
            media=media,
            caption='Если вы не нашли игру, которую искали, то приобрести ее можно через раздел'
                    ' в боте «Пополнение кошелька» в главном меню'
        ),
        reply_markup=xbox_categories_kb(categories)
    )

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('xbox_page:'))
@router.callback_query(F.data.startswith('xbox_category'))
async def xbox_show_games_in_category(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    if call.data.startswith('xbox_page'):
        page = int(call.data.split(':')[1])
        games = data.get('games', [])
        if not games:
            media_path = 'tgbot/utils/media/xbox_menu.png'
            media = get_photo(media_path, db_session)
            await call.message.edit_media(InputMediaPhoto(media=media),
                                          reply_markup=xbox_menu(db_session.query(User).filter(
                                              User.id == call.from_user.id).one().xbox_account))
            return
    else:
        page = data.get('page', 0)
        category = call.data.split(':')[1]
        games = [(i.id, i.name, i.emoji or '') for i in
                 db_session.query(XBOXGame).filter(XBOXGame.category == category).all()]
        await state.update_data(games=games)

    await state.update_data(page=page)

    media_path = 'tgbot/utils/media/xbox_games.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(
        InputMediaPhoto(media=media),
        reply_markup=xbox_games_kb(games, page, await state.get_state() == XBOXState.search_donation_game)
    )

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('xbox_has_account'))
async def xbox_has_account_handler(call: CallbackQuery, db_session: Session):
    user = db_session.query(User).filter(User.id == call.from_user.id).one()
    user.xbox_account = int(call.data.split(':')[1])
    db_session.commit()

    await call.message.edit_caption(
        caption='Прекрасный выбор🔥\nТеперь ты можешь выбрать то, зачем заглянул в наш магазин!',
        reply_markup=xbox_menu(user.xbox_account))


@router.message(XBOXState.search_game)
@router.callback_query(F.data.startswith('xbox_game:'))
async def xbox_choose_game_handler(update: Message | CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    if isinstance(update, Message):
        game = db_session.query(XBOXGame).filter(XBOXGame._name == update.text).first()
        if not game:
            media_path = 'tgbot/utils/media/xbox_game_not_found.png'
            media = get_photo(media_path, db_session)
            message = await update.answer_photo(
                media,
                caption='Игра не была найдена☹️\n\n<i>Проверь правильность написания игры.\n'
                        'И помни, что игра должна записываться так же, как и в '
                        'официальном магазине🛒</i>',
                reply_markup=back_xbox_menu()
            )
            return media_path, message.photo[-1].file_id

        game = game.id
        func = update.answer
    else:
        game = int(update.data.split(':')[1])
        func = update.message.edit_caption

    await state.update_data(game=game)
    if await state.get_state() == XBOXState.search_donation_game.state:
        donation_options = db_session.query(ConsoleDonation).filter(ConsoleDonation.game_id == game).all()

        await func('Выберите нужную опцию',
                   reply_markup=console_choose_donation_kb(donation_options, 'xbox', 'tr', db_session))
        return

    game: Type[XBOXGame] = db_session.query(XBOXGame).filter(XBOXGame.id == game).one()
    platform = list(set(i.platform for i in game.editions))[0]

    reply_markup, media_path = (xbox_choose_platform(data.get('page', 0)),
                                'tgbot/utils/media/ps_choose_platform.png') if platform == 'X/S' else (
        xbox_choose_edition(
            game.editions,
            data.get('page', 0),
            db_session), 'tgbot/utils/media/xbox_choose_edition.png')

    media = get_photo(media_path, db_session)
    if isinstance(update, Message):
        message = await update.answer_photo(media,
                                            reply_markup=reply_markup)
    else:
        message = await update.message.edit_media(InputMediaPhoto(media=media),
                                                  reply_markup=reply_markup)

    return media_path, message.photo[-1].file_id


@router.callback_query(XBOXState.search_donation_game, F.data.startswith('donation:'))
async def xbox_process_buy_donation(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    donation_id = int(call.data.split(':')[1])

    donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()
    game = db_session.query(XBOXGame).filter(XBOXGame.id == int(donation.game_id)).one()
    currency = 'TRY'

    price = get_donation_price(donation.price if not donation.discount else donation.discount, currency, 'xbox',
                               db_session, donation.margin)

    await state.update_data(price=price, game_id=game.id, donation_id=donation_id, back=f'xbox_game:{data["game"]}')

    in_cart = db_session.query(db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                                                  CartItems.obj_id == int(donation.id),
                                                                  CartItems.platform == 'xbox').exists()).scalar()

    await call.message.edit_caption(caption=f'{game.name}\n{donation.description}\n\n💸 Цена: {price} ₽💸\n',
                                    reply_markup=item_kb(donation_id, 'xbox', 'donation', f'xbox_game:{game.id}',
                                                         in_cart))


@router.callback_query(F.data.startswith('xbox_platform:'))
async def xbox_choose_platform_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    game_id: int = data['game']
    platform = call.data.split(':')[1]
    await state.update_data(platform=platform)

    game: Type[XBOXGame] = db_session.query(XBOXGame).filter(XBOXGame.id == game_id).one()

    reply_markup, media_path = (xbox_choose_edition(
        game.editions,
        data.get('page', 0),
        db_session), 'tgbot/utils/media/xbox_choose_edition.png')

    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media),
                                            reply_markup=reply_markup)

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('xbox_edition'))
async def ps_choose_edition_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    edition: Type[XBOXGameEdition] = db_session.query(XBOXGameEdition).filter(
        XBOXGameEdition.id == int(call.data.split(':')[1])).first()

    price = get_game_price(edition.price if not edition.discount else edition.discount, 'TRY', 'xbox', db_session,
                           edition.margin)

    await state.update_data(edition_id=edition.id, price=price, back=f'xbox_platform:{edition.platform}')

    in_cart = db_session.query(db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                                                  CartItems.obj_id == int(edition.id),
                                                                  CartItems.platform == 'xbox').exists()).scalar()

    await call.message.edit_media(
        InputMediaPhoto(
            media=URLInputFile(edition.pic),
            caption=format_game(edition, 'xbox', db_session)
        ),
        reply_markup=item_kb(edition.id, 'xbox', 'game',
                             f'xbox_platform:{edition.platform}', in_cart)
    )


@router.callback_query(F.data.startswith('buy:ps:'))
async def ps_buy_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    item_type, item_id = call.data.split(':')[2:]
    item_id = int(item_id)
    data = await state.get_data()
    price = int(data['price'])

    media_path = 'tgbot/utils/media/xbox_go_pay.png'
    media = get_photo(media_path, db_session)

    await call.message.edit_media(InputMediaPhoto(media=media))
    label = f'{int(time.time())}{call.from_user.id}'

    if item_type == 'subscription':
        subscription: Type[ConsoleSubscription] = db_session.query(ConsoleSubscription).filter(
            ConsoleSubscription.id == item_id).one()

        target = f'Покупка XBOX {subscription._name} {subscription.duration} мес.'
        back = f'subscription:xbox:{subscription._name}:{subscription.duration}'
        await state.set_state(XBOXState.buy)
    elif item_type == 'donation':
        donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(
            ConsoleDonation.id == item_id).one()
        game: Type[XBOXGame] = db_session.query(XBOXGame).filter(XBOXGame.id == int(donation.game_id)).one()

        target = f'Покупка {game._name}\n{donation.description}'
        back = f'donation:{donation.id}'
    elif item_type == 'game':
        edition: Type[XBOXGameEdition] = db_session.query(XBOXGameEdition).filter(
            XBOXGameEdition.id == item_id).one()

        target = f'Покупка {edition.game._name} {edition._name} Edition'
        back = f'xbox_edition:{item_id}'
        await state.set_state(XBOXState.buy)

    quickpay = Quickpay(
        receiver=receiver,
        quickpay_form='shop',
        targets=target,
        paymentType='SB',
        sum=price,  # price
        label=label
    )

    await call.message.edit_caption(
        caption=call.message.html_text + '\n\n<i>Осталось совсем чуть-чуть🤏</i>',
        reply_markup=confirm_buy_kb(label, quickpay.redirected_url, back)
    )


@router.callback_query(XBOXState.search_donation_game, F.data.startswith('check:'))
@router.callback_query(XBOXState.buy, F.data.startswith('check:'))
async def xbox_check_payment(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    label = call.data.split(':')[1]

    client = Client(p2p_token)

    history = client.operation_history(label=label)

    try:
        operation = history.operations[-1]
        if operation.status == 'success':
            user = db_session.query(User).filter(User.id == call.from_user.id).one()
            if not user.xbox_account:
                if 'edition_id' in data:
                    edition = db_session.query(XBOXGameEdition).filter(
                        XBOXGameEdition.id == int(data['edition_id'])).first()
                    game: XBOXGame = edition.game
                    tov = game._name + ' ' + edition.name + ' Edition' + ' ' + edition.platform
                elif 'subscription_id' in data:
                    subscription = db_session.query(ConsoleSubscription).filter(
                        ConsoleSubscription.id == int(data['subscription_id'])).one()
                    tov = f'Gamepass ULTIMATE {subscription.duration} мес.'
                elif 'donation_id' in data:
                    donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(
                        ConsoleDonation.id == int(data['donation_id'])).one()
                    game: Type[XBOXGame] = db_session.query(XBOXGame).filter(XBOXGame.id == int(donation.game_id)).one()
                    tov = f'{game._name}\n{donation.description}'
                elif 'amount' in data:
                    currency = data['currency']
                    amount = data['amount']
                    tov = f'Пополение аккаунта XBOX на {amount} {currency}'
                await state.set_state(MainState.chat_w_admin)

                media_path = 'tgbot/utils/media/xbox_buy_success.png'
                media = get_photo(media_path, db_session)
                message = await call.message.edit_media(
                    InputMediaPhoto(
                        media=media,
                        caption=f"""Оплата прошла успешно🔥\n\nНапиши почту для создания аккаунта.
<i>
Примечание: 
    1.	Почта должна быть обязательно с доменом .com (gmail, outlook например), на русские почты аккаунты не создаются
    2.	Почта должна быть той, что не привязана ни к одному аккаунту Microsoft
</i>
Если у тебя есть вопросы по этому пункту - нажми кнопку «Перейти в чат»
Там менеджер тебя проконсультирует!:)
"""
                    ),
                    reply_markup=xbox_go_to_manager()
                )

                await state.set_state(XBOXState.email)
                await state.update_data(tov=tov)
                return media_path, message.photo[-1].file_id

            media_path = 'tgbot/utils/media/xbox_data.png'
            media = get_photo(media_path, db_session)
            message = await call.message.edit_media(
                InputMediaPhoto(
                    media=media,
                    caption='Введи почту и пароль от аккаунта в формате: email:pass\n\n'
                            '<i>Пример: heroes21@gmail.com:Hetp33asd</i>'
                )
            )
            await state.set_state(XBOXState.log_and_pass)

            return media_path, message.photo[-1].file_id
        else:
            await call.answer('❌ Оплата не прошла')
    except:
        await call.answer(f'Платеж не найден или не прошел. Пожалуйста, проверьте еще раз.')


@router.message(XBOXState.email)
@router.callback_query(XBOXState.email, F.data == 'xbox_go_manager')
async def ps_no_acc_handler(update: CallbackQuery | Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    if isinstance(update, Message):
        email = update.text
        await update.answer('Оператор уже бежит в диалог😉')

        if tov := data.get('tov', ''):
            await send_admin_invites(tov, update.from_user, email, no_account=True, platform='XBOX')
        elif cart := data.get('cart_text', ''):
            await send_admin_invites('', update.from_user, email, no_account=True, platform='XBOX', cart=cart)

    else:
        await update.message.edit_caption(caption='Оператор уже бежит в диалог😉')

        if tov := data.get('tov', ''):
            await send_admin_invites(tov, update.from_user, no_account=True, platform='XBOX')
        elif cart := data.get('cart_text', ''):
            await send_admin_invites('', update.from_user, no_account=True, platform='XBOX', cart=cart)

    await state.set_state(MainState.chat_w_admin)
    db_session.add(AdminChat(user_id=update.from_user.id, platform='xbox'))
    db_session.commit()


@router.message(XBOXState.log_and_pass, F.text)
async def xbox_receive_creds(message: Message, state: FSMContext, db_session: Session):
    login, password = message.text.split(':')
    await state.update_data(login=login, password=password)

    media_path = 'tgbot/utils/media/xbox_confirmation.png'
    media = get_photo(media_path, db_session)
    message = await message.answer_photo(
        media,
        caption=f'Проверьте правильность введенных данных: \n<b>Почта:</b> {login}\n<b>Пароль:'
                f'</b> {password}\n\n<i>Если ты нашел ошибку, введи логин и пароль заново😇</i>',
        reply_markup=confirm_credentials()
    )
    return media_path, message.photo[-1].file_id


@router.callback_query(XBOXState.log_and_pass, F.data == 'credentials_confirmed')
async def xbox_process_2fa(update: CallbackQuery, db_session: Session, state: FSMContext):
    data = await state.get_data()
    await state.set_state(MainState.chat_w_admin)

    await state.set_state(MainState.chat_w_admin)

    media_path = 'tgbot/utils/media/xbox_buy_success.png'
    media = get_photo(media_path, db_session)
    message = await update.message.edit_media(
        InputMediaPhoto(
            media=media,
            caption=f'Оплата прошла успешно🔥\n\nОператор уже бежит в диалог😉')
    )

    db_session.add(AdminChat(user_id=update.from_user.id, platform='xbox'))
    db_session.commit()

    if tov := data.get('tov', ''):
        await send_admin_invites(tov, update.from_user, data['login'], data['password'], platform='XBOX')
    elif cart := data.get('cart_text', ''):
        await send_admin_invites('', update.from_user, data['login'], data['password'], platform='XBOX', cart=cart)

    return media_path, message.photo[-1].file_id
