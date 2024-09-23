import os.path
import time
from typing import Type

from aiogram import Router, F, types
from yoomoney import Quickpay, Client

from tgbot.data import loader
from tgbot.data.config import receiver, p2p_token
from tgbot.data.loader import bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile, URLInputFile, InputMediaPhoto, \
    MessageEntity
from aiogram.fsm.context import FSMContext

from tgbot.keyboards.base_keyboards import *
from tgbot.services.database import User, PSGame, ConsoleSubscription, Settings, AdminChat, CartItems
from tgbot.keyboards.ps_keyboards import *
from sqlalchemy.orm.session import Session

from tgbot.utils.curs import get_course
from tgbot.utils.other import get_refill_prices, get_refill_block, format_subscription, get_round_price, \
    get_donation_price, format_game, get_game_price, send_admin_invites, get_currency, get_photo
from tgbot.utils.states import *

router = Router()


@router.callback_query(F.data == 'platform:PS')
async def platform_handler(call: CallbackQuery, db_session: Session):
    media_path = 'tgbot/utils/media/ps_menu.png'
    media = get_photo(media_path, db_session)

    message = await call.message.edit_media(
        InputMediaPhoto(media=media, caption='В каком регионе PS Store ты хочешь оформить покупку?'),
        reply_markup=ps_region())

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('ps_country:'))
async def ps_country_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    await state.clear()
    has_account = db_session.query(User).filter(User.id == call.from_user.id).one()
    has_account = has_account.ps_account

    region = call.data.split(':')[1]
    await state.update_data(region=region)

    media_path = 'tgbot/utils/media/ps_menu.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(
        media=media,
        caption='Прекрасный выбор🔥\nТеперь ты можешь выбрать то, зачем заглянул в наш магазин!'
    ),
        reply_markup=ps_menu(has_account))

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data == 'ps:info')
async def ps_help_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    text = f"""Текст для информации:

💛Основной канал JoyStick Store - https://t.me/storejoystick

🎮Новостной канал - https://t.me/newsjoystick

🗣️Отзывы - https://t.me/+c6--F8QT9MVlYmQ6

📞Чат поддержки - @joysticksupport

Особо важная информация для пользователя - https://t.me/storejoystick/127"""
    media_path = 'tgbot/utils/media/ps_info.png'
    media = get_photo(media_path, db_session)

    message = await call.message.edit_media(InputMediaPhoto(media=media, caption=text),
                                            reply_markup=back_ps_menu(data['region']))
    return media_path, message.photo[-1].file_id


@router.callback_query(F.data == 'ps:refill')
async def ps_refill_account_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    settings = db_session.query(Settings).first()

    if data['region'] == 'ua':
        currency = 'UAH'
        base_margin = settings.ps_base_refill_margin_ua
        additional_margin = settings.ps_additional_refill_margin_ua
    else:
        currency = 'TRY'
        base_margin = settings.ps_base_refill_margin_tr
        additional_margin = settings.ps_additional_refill_margin_tr

    rates, text = get_refill_prices(currency, additional_margin, base_margin)

    await state.update_data(rates=rates, currency=currency)

    media_path = 'tgbot/utils/media/ps_refill.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media, caption=text),
                                            reply_markup=back_ps_menu(data['region']))
    await state.set_state(PSState.refill)

    return media_path, message.photo[-1].file_id


@router.message(PSState.refill)
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
        price = get_round_price(currency, amount * rates[block], convert=False)
        await state.update_data(amount=amount, price=price)

        label = f'{int(time.time())}{message.from_user.id}'

        quickpay = Quickpay(
            receiver=receiver,
            quickpay_form='shop',
            targets=f'Пополнение аккаунта PS на {amount} {currency}',
            paymentType='SB',
            sum=price,
            label=label
        )

        media_path = 'tgbot/utils/media/ps_refill.png'
        media = get_photo(media_path, db_session)
        await message.answer_photo(photo=media,
                                   caption=f'Пополнение аккаунта PS на {amount} {currency}\n💸 Цена: '
                                           f'{price}₽ 💸',
                                   reply_markup=confirm_buy_kb(label, quickpay.redirected_url,
                                                               f'ps_country:{data["region"]}'))
        await state.set_state(PSState.buy)

    except ValueError:
        await message.answer(f'Введите целое число', reply_markup=back_ps_menu(data['region']))


@router.callback_query(F.data == 'ps:donate')
async def ps_enter_donate_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    games = [(i.id, i.name, i.emoji) for i in db_session.query(PSGame).filter(PSGame.has_donate == 1).all()]
    await state.update_data(games=games)

    media_path = 'tgbot/utils/media/ps_donate.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media),
                                            reply_markup=ps_games_kb(games, 0, data['region']))
    await state.set_state(PSState.search_donation_game)

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data == 'ps:plus')
async def ps_subscriptions_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    media_path = 'tgbot/utils/media/ps_sub_type.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media),
                                            reply_markup=ps_choose_subscription_type(data['region']))

    return media_path, message.photo[-1].file_id
    # await call.message.edit_caption(caption='Выберите подписку')


@router.callback_query(F.data.startswith('sub_type:ps:'))
async def ps_choose_subscription_type_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    name = str(call.data.split(':')[2])

    subscriptions = [i.duration for i in
                     db_session.query(ConsoleSubscription).filter(ConsoleSubscription.platform == 'ps',
                                                                  ConsoleSubscription.region == str(data['region']),
                                                                  ConsoleSubscription._name == name).all()]

    sub = db_session.query(ConsoleSubscription).filter(ConsoleSubscription.platform == 'ps',
                                                       ConsoleSubscription._name == name).first()

    media_path = 'tgbot/utils/media/ps_sub_duration.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media, caption=format_subscription(sub)),
                                            reply_markup=choose_subscription_duration(name, subscriptions, 'ps',
                                                                                      data['region']))

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('subscription:ps'))
async def ps_process_subscription(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    region = str(data['region'])
    name, duration = call.data.split(':')[2:]
    duration = int(duration)
    name = str(name)

    subscription: Type[ConsoleSubscription] = db_session.query(ConsoleSubscription).filter(
        ConsoleSubscription.duration == duration, ConsoleSubscription.region == region,
        ConsoleSubscription._name == name).one()

    if subscription.discount:
        price_text = f'💸 Цена: {f"<s>{subscription.price}</s> {subscription.discount}₽"}'
        price = subscription.discount
    else:
        price_text = f'💸 Цена: {subscription.price}₽ 💸'
        price = subscription.price

    await state.update_data(subscription_id=subscription.id)

    if name == '⚪️ Essential':
        media_path = 'tgbot/utils/media/essential.png'
    elif name == '🟡 Extra':
        media_path = 'tgbot/utils/media/extra.png'
    elif name == '⚫️ Deluxe':
        media_path = 'tgbot/utils/media/deluxe.png'
    elif name == '🔴 Ea Play':
        media_path = 'tgbot/utils/media/eaplay.png'
    else:
        media_path = 'tgbot/utils/media/ps_go_pay.png'

    in_cart = db_session.query(db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                                                  CartItems.obj_id == int(subscription.id),
                                                                  CartItems.platform == 'ps').exists()).scalar()

    media = get_photo(media_path, db_session)
    markup = item_kb(subscription.id, 'ps', 'subscription', f'ps:plus', in_cart)

    message = await call.message.edit_media(InputMediaPhoto(
        media=media, caption=f'PS Plus {subscription._name} {subscription.duration} мес.\n\n{price_text}'
    ),
        reply_markup=markup)

    await state.update_data(price=price, back='ps:plus')

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('ps:search'))
async def ps_search_game(call: CallbackQuery, state: FSMContext, db_session: Session):
    region = (await state.get_data())['region']

    await state.set_state(PSState.search_game)

    media_path = 'tgbot/utils/media/ps_search_games.png'
    media = get_photo(media_path, db_session)
    await call.message.edit_media(InputMediaPhoto(
        media=media, caption='Введи название игры, которую хочешь найти\n\n<i>🔍Примечание: желательно,'
                             'чтобы игра называлась так же, как и в официальном магазине PS Store</i>'
    ),
        reply_markup=back_ps_menu(region))

    return media_path, call.message.photo[-1].file_id


@router.callback_query(F.data.startswith('ps:games'))
async def ps_show_categories(call: CallbackQuery, db_session: Session, state: FSMContext):
    region = (await state.get_data())['region']

    categories = list(set((i.category, i.emoji) for i in db_session.query(PSGame).all()))

    media_path = 'tgbot/utils/media/ps_cats.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(
        InputMediaPhoto(
            media=media, caption='Если вы не нашли игру, которую искали, то приобрести ее можно через раздел'
                                 ' в боте «Пополнение кошелька» в главном меню',

        ),
        reply_markup=ps_categories_kb(categories, region)
    )

    return media_path, message.photo[-1].file_id


@router.callback_query(F.data.startswith('ps_page:'))
@router.callback_query(F.data.startswith('ps_category'))
async def ps_show_games_in_category(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    if call.data.startswith('ps_page'):
        page = int(call.data.split(':')[1])
        games = data.get('games', [])
        if not games:
            await call.message.edit_media(InputMediaPhoto(media=get_photo('tgbot/utils/media/ps_menu.png', db_session)),
                                          reply_markup=ps_menu(db_session.query(User).filter(
                                              User.id == call.from_user.id).one().ps_account))
            return
    else:
        page = data.get('page', 0)
        category = call.data.split(':')[1]
        games = [(i.id, i.name, i.emoji) for i in
                 db_session.query(PSGame).filter(PSGame.category == category).all() if
                 any(j.region == data['region'] for j in i.editions)]
        await state.update_data(games=games)

    media_path = 'tgbot/utils/media/ps_games.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media), reply_markup=ps_games_kb(games, page, data[
        'region'] if await state.get_state() == PSState.search_donation_game else ''))

    await state.update_data(page=page)

    return media_path, message.photo[-1].file_id

    # await call.message.edit_caption(caption='Выберите игру:',
    #                                 reply_markup=ps_games_kb(games, page, data[
    #                                     'region'] if await state.get_state() == PSState.search_donation_game else ''))


@router.callback_query(F.data.startswith('ps_has_account'))
async def ps_has_account_handler(call: CallbackQuery, db_session: Session):
    user = db_session.query(User).filter(User.id == call.from_user.id).one()
    user.ps_account = int(call.data.split(':')[1])
    db_session.commit()

    await call.message.edit_caption(
        caption='Прекрасный выбор🔥\nТеперь ты можешь выбрать то, зачем заглянул в наш магазин!',
        reply_markup=ps_menu(user.ps_account))


@router.message(PSState.search_game)
@router.callback_query(F.data.startswith('ps_game:'))
async def ps_choose_game_handler(update: Message | CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    if isinstance(update, Message):
        game = db_session.query(PSGame).filter(PSGame._name == update.text).first()
        if not game:
            media_path = 'tgbot/utils/media/ps_game_not_found.png'
            media = get_photo(media_path, db_session)

            message = await update.answer_photo(
                media,
                caption='Игра не была найдена☹️\n\n<i>Проверь правильность написания игры.\n'
                        'И помни, что игра должна записываться так же, как и в '
                        'официальном магазине🛒</i>',
                reply_markup=back_ps_menu(data['region'])
            )
            return media_path, message.photo[-1].file_id
        if not any(i.region == data['region'] for i in game.editions):
            media_path = 'tgbot/utils/media/ps_game_not_found.png'
            media = get_photo(media_path, db_session)

            message = await update.answer_photo(media,
                                                caption='Этой игры нет в выбранном регионе',
                                                reply_markup=back_ps_menu(data['region']))
            return media_path, message.photo[-1].file_id
        game = game.id

    else:
        game = int(update.data.split(':')[1])

    await state.update_data(game=game)
    if await state.get_state() == PSState.search_donation_game.state:
        donation_options = db_session.query(ConsoleDonation).filter(ConsoleDonation.game_id == game).all()
        await update.message.edit_caption(caption='Выберите нужную опцию',
                                          reply_markup=console_choose_donation_kb(donation_options, 'ps',
                                                                                  data.get('region', 'tr'), db_session))
        return

    game = db_session.query(PSGame).filter(PSGame.id == game).one()
    platforms = list(set(i.platform for i in game.editions))

    media_path = 'tgbot/utils/media/ps_choose_platform.png'
    media = get_photo(media_path, db_session)
    if isinstance(update, Message):
        message = await update.answer_photo(media,
                                            reply_markup=ps_choose_platform(0, platforms))
    else:
        message = await update.message.edit_media(InputMediaPhoto(media=media),
                                                  reply_markup=ps_choose_platform(data.get('page', 0), platforms))

    return media_path, message.photo[-1].file_id


@router.callback_query(PSState.search_donation_game, F.data.startswith('donation:'))
async def ps_process_buy_donation(call: CallbackQuery, state: FSMContext, db_session: Session):
    donation_id = int(call.data.split(':')[1])

    donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()
    currency = 'UAH' if donation.region == 'ua' else 'TRY'
    game = db_session.query(PSGame).filter(PSGame.id == int(donation.game_id)).one()

    price = get_donation_price(donation.price if not donation.discount else donation.discount, currency, 'ps',
                               db_session, donation.margin)

    await state.update_data(price=price, game_id=game.id, donation_id=donation_id, back=f'ps_game:{game.id}')

    in_cart = db_session.query(db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                                                  CartItems.obj_id == int(donation.id),
                                                                  CartItems.platform == 'ps').exists()).scalar()

    await call.message.edit_caption(caption=f'{game.name}\n{donation.description}\n\n💸 Цена: {price} ₽💸\n',
                                    reply_markup=item_kb(donation_id, 'ps', 'donation', f'ps_game:{game.id}',
                                                         in_cart))


@router.callback_query(F.data.startswith('ps_platform:'))
async def ps_choose_platform_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    game_id: int = data['game']
    platform = call.data.split(':')[1]
    await state.update_data(platform=platform)

    game: Type[PSGame] = db_session.query(PSGame).filter(PSGame.id == game_id).one()
    editions = [i for i in game.editions if i.region == data['region'] and i.platform == platform]

    # draw_editions(editions)
    media_path = 'tgbot/utils/media/ps_choose_edition.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media),
                                            reply_markup=ps_choose_edition(editions, game.id, db_session))

    return media_path, message.photo[-1].file_id
    # await call.message.edit_caption(caption=game.name,
    #                                 reply_markup=ps_choose_edition(editions, game.id, db_session))


@router.callback_query(F.data.startswith('ps_edition'))
async def ps_choose_edition_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    edition: Type[PSGameEdition] = db_session.query(PSGameEdition).filter(
        PSGameEdition.id == int(call.data.split(':')[1])).first()

    currency = get_currency(edition.region)
    price = get_game_price(edition.price if not edition.discount else edition.discount, currency, 'ps', db_session,
                           edition.margin)

    await state.update_data(edition_id=edition.id, price=price, back=f'ps_platform:{edition.platform}')

    in_cart = db_session.query(db_session.query(CartItems).filter(CartItems.user_id == call.from_user.id,
                                                                  CartItems.obj_id == int(edition.id),
                                                                  CartItems.platform == 'ps').exists()).scalar()

    await call.message.edit_media(
        InputMediaPhoto(
            media=URLInputFile(edition.pic),
            caption=format_game(edition, 'ps', db_session)
        ),
        reply_markup=item_kb(edition.id, 'ps', 'game', f'ps_platform:{edition.platform}', in_cart)
    )


@router.callback_query(F.data.startswith('buy:ps:'))
async def ps_buy_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    item_type, item_id = call.data.split(':')[2:]
    item_id = int(item_id)
    data = await state.get_data()
    price = int(data['price'])

    media_path = 'tgbot/utils/media/ps_go_pay.png'
    media = get_photo(media_path, db_session)

    message = await call.message.edit_media(InputMediaPhoto(media=media))
    label = f'{int(time.time())}{call.from_user.id}'

    if item_type == 'subscription':
        subscription: Type[ConsoleSubscription] = db_session.query(ConsoleSubscription).filter(
            ConsoleSubscription.id == item_id).one()

        target = f'Покупка PS Plus{subscription._name} {subscription.duration} мес.'
        back = f'subscription:ps:{subscription._name}:{subscription.duration}'
        await state.set_state(PSState.buy)
    elif item_type == 'donation':
        donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(
            ConsoleDonation.id == item_id).one()
        game: Type[PSGame] = db_session.query(PSGame).filter(PSGame.id == int(donation.game_id)).one()

        target = f'Покупка {game._name}\n{donation.description}'
        back = f'donation:{donation.id}'
    elif item_type == 'game':
        edition: Type[PSGameEdition] = db_session.query(PSGameEdition).filter(
            PSGameEdition.id == item_id).one()

        target = f'Покупка {edition.game._name} {edition._name} Edition'
        back = f'ps_edition:{item_id}'
        await state.set_state(PSState.buy)

    quickpay = Quickpay(
        receiver=receiver,
        quickpay_form='shop',
        targets=target,
        paymentType='SB',
        sum=price,  # price
        label=label
    )

    # entities = [
    #     MessageEntity(
    #         type=call.message.caption_entities[0].type,
    #         offset=call.message.caption_entities[0].offset,
    #         length=call.message.caption_entities[0].length
    #     )
    # ] if call.message.caption_entities else None
    await call.message.edit_caption(
        caption=call.message.html_text + '\n\n<i>Осталось совсем чуть-чуть🤏</i>',
        reply_markup=confirm_buy_kb(label, quickpay.redirected_url, back),
    )

    return media_path, message.photo[-1].file_id


@router.callback_query(PSState.search_donation_game, F.data.startswith('check:'))
@router.callback_query(PSState.buy, F.data.startswith('check:'))
async def ps_check_payment(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    label = call.data.split(':')[1]

    client = Client(p2p_token)

    history = client.operation_history(label=label)

    try:
        operation = history.operations[-1]
        if operation.status == 'success':
            user = db_session.query(User).filter(User.id == call.from_user.id).one()
            if not user.ps_account:
                if 'edition_id' in data:
                    edition = db_session.query(PSGameEdition).filter(
                        PSGameEdition.id == int(data['edition_id'])).first()
                    game: PSGame = edition.game
                    tov = game._name + ' ' + edition.name + ' Edition' + ' ' + edition.platform
                elif 'subscription_id' in data:
                    subscription = db_session.query(ConsoleSubscription).filter(
                        ConsoleSubscription.id == int(data['subscription_id'])).one()
                    tov = f'{subscription.name} {subscription.duration} мес.'
                elif 'donation_id' in data:
                    donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(
                        ConsoleDonation.id == int(data['donation_id'])).one()
                    game: Type[PSGame] = db_session.query(PSGame).filter(PSGame.id == int(donation.game_id)).one()
                    tov = f'{game._name}\n{donation.description}'
                elif 'amount' in data:
                    currency = data['currency']
                    amount = data['amount']
                    tov = f'Пополение аккаунта PS на {amount} {currency}'

                media_path = 'tgbot/utils/media/ps_buy_success.png'
                media = get_photo(media_path, db_session)
                message = await call.message.edit_media(
                    InputMediaPhoto(
                        media=media,
                        caption=f"""Оплата прошла успешно🔥\n\nНапиши почту для создания аккаунта.
    <i>
Примечание: 
    1.	Почта должна быть обязательно с доменом .com (gmail, outlook например), на русские почты аккаунты не создаются
    2.	Почта должна быть той, что не привязана ни к одному аккаунту Sony
</i>
Если у тебя есть вопросы по этому пункту - нажми кнопку «Перейти в чат»
Там менеджер тебя проконсультирует!:)
"""),
                    reply_markup=ps_go_to_manager()
                )
                await state.set_state(PSState.email)
                await state.update_data(tov=tov)

                return media_path, message.photo[-1].file_id

            media_path = 'tgbot/utils/media/ps_data.png'
            media = get_photo(media_path, db_session)
            message = await call.message.edit_media(
                InputMediaPhoto(
                    media=media,
                    caption='Введи почту и пароль от аккаунта в формате: email:pass\n\n'
                            '<i>Пример: heroes21@gmail.com:Hetp33asd</i>')
            )
            await state.set_state(PSState.log_and_pass)

            return media_path, message.photo[-1].file_id
        else:
            await call.answer('❌ Оплата не прошла')
    except:
        await call.answer(f'Платеж не найден или не прошел. Пожалуйста, проверьте еще раз.')


@router.message(PSState.email)
@router.callback_query(PSState.email, F.data == 'ps_go_manager')
async def ps_no_acc_handler(update: CallbackQuery | Message, state: FSMContext, db_session: Session):
    data = await state.get_data()

    if isinstance(update, Message):
        email = update.text
        await update.answer('Оператор уже бежит в диалог😉')
        if tov := data.get('tov', ''):
            await send_admin_invites(tov, update.from_user, email, no_account=True, platform='PS')
        elif cart := data.get('cart_text', ''):
            await send_admin_invites('', update.from_user, email, no_account=True, platform='PS', cart=cart)
    else:
        await update.message.edit_caption(caption='Оператор уже бежит в диалог😉')
        if tov := data.get('tov', ''):
            await send_admin_invites(tov, update.from_user, no_account=True, platform='PS')
        elif cart := data.get('cart_text', ''):
            await send_admin_invites('', update.from_user, no_account=True, platform='PS', cart=cart)

    await state.set_state(MainState.chat_w_admin)
    db_session.add(AdminChat(user_id=update.from_user.id, platform='ps'))
    db_session.commit()


@router.message(PSState.log_and_pass, F.text)
async def ps_receive_creds(message: Message, state: FSMContext, db_session: Session):
    login, password = message.text.split(':')
    await state.update_data(login=login, password=password)

    media_path = 'tgbot/utils/media/ps_confirmation.png'
    media = get_photo(media_path, db_session)
    message = await message.answer_photo(
        media,
        caption=f'Проверьте правильность введенных данных: \n<b>Почта:</b> {login}\n<b>Пароль:'
                f'</b> {password}\n\n<i>Если ты нашел ошибку, введи логин и пароль заново😇</i>',
        reply_markup=confirm_credentials())

    return media_path, message.photo[-1].file_id


@router.callback_query(PSState.log_and_pass, F.data == 'credentials_confirmed')
async def ps_ask_for_2fa(call: CallbackQuery, state: FSMContext, db_session: Session):
    media_path = 'tgbot/utils/media/ps_tfa.png'
    media = get_photo(media_path, db_session)

    message = await call.message.edit_media(
        InputMediaPhoto(media=media,
                        caption='Напиши резервный код двухфакторной аутентификации сообщением, если он '
                                'есть😌\nЕсли его нет или по каким то причинам не хочешь его давать - '
                                'выбери опцию в кнопке ниже👇\n\n<b>Если у тебя нет двухфакторной '
                                'аутентификации, то наш менеджер может попросить ее поставить '
                                'во избежание ошибок входа</b>'),
        reply_markup=tfa_kb()
    )

    await state.set_state(PSState.tfa)

    return media_path, message.photo[-1].file_id


@router.callback_query(PSState.tfa, F.data.startswith('2fa'))
@router.message(PSState.tfa, F.text)
async def ps_process_2fa(update: Message | CallbackQuery, db_session: Session, state: FSMContext):
    data = await state.get_data()
    await state.set_state(MainState.chat_w_admin)

    # if 'edition_id' in data:
    #     edition = db_session.query(PSGameEdition).filter(PSGameEdition.id == int(data['edition_id'])).first()
    #     game: PSGame = edition.game
    #     tov = game.name + ' ' + edition.name + ' Edition'
    # elif 'subscription_id' in data:
    #     subscription = db_session.query(ConsoleSubscription).filter(
    #         ConsoleSubscription.id == int(data['subscription_id'])).one()
    #     tov = f'{subscription.name} {subscription.duration} мес.'
    # elif 'donation_id' in data:
    #     donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(
    #         ConsoleDonation.id == int(data['donation_id'])).one()
    #     game: Type[PSGame] = db_session.query(PSGame).filter(PSGame.id == int(donation.game_id)).one()
    #     tov = f'{game.name}\n{donation.description}'
    # elif 'amount' in data:
    #     currency = data['currency']
    #     amount = data['amount']
    #     tov = f'Пополение аккаунта PS на {amount} {currency}'

    await state.set_state(MainState.chat_w_admin)

    tfa = ''
    media_path = 'tgbot/utils/media/ps_buy_success.png'
    media = get_photo(media_path, db_session)
    if isinstance(update, CallbackQuery):
        if update.data == '2fa:no_code':
            tfa = 'Нет'
        else:
            tfa = 'Без кода'

        message = await update.message.edit_media(
            InputMediaPhoto(media=media, caption=f'Оплата прошла успешно🔥\n\nОператор уже бежит в диалог😉'))

    elif isinstance(update, Message):
        tfa = update.text
        message = await update.answer_photo(media,
                                            caption=f'Оплата прошла успешно🔥\n\nОператор уже бежит в диалог😉')

    db_session.add(AdminChat(user_id=update.from_user.id, platform='ps'))
    db_session.commit()

    if tov := data.get('tov', ''):
        await send_admin_invites(tov, update.from_user, data['login'], data['password'], tfa, platform='PS')
    elif cart := data.get('cart_text', ''):
        await send_admin_invites('', update.from_user, data['login'], data['password'], tfa, platform='PS', cart=cart)

    await send_admin_invites(tov, update.from_user, data['login'], data['password'], tfa, platform='ps')

    return media_path, message.photo[-1].file_id
