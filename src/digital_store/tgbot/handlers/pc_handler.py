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
from tgbot.services.database import User, PSGame, ConsoleSubscription, Settings, AdminChat
from tgbot.keyboards.pc_keyboards import *
from sqlalchemy.orm.session import Session

from tgbot.utils.other import get_refill_prices, format_subscription, get_refill_block, get_round_price, draw_editions, \
    get_donation_price, format_game, get_currency, get_game_price, send_admin_invites, get_photo
from tgbot.utils.states import *

router = Router()


@router.callback_query(F.data == 'platform:PC')
async def platform_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    await state.clear()

    await call.message.answer('Выберите платформу для продолжения:', reply_markup=choose_pc_platform())


# @router.callback_query(F.data == 'pc:epicgames')
# async def epicgames_menu_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
#     user = db_session.query(User).filter(User.id == call.from_user.id).one()
#
#     await call.message.edit_text('Добро пожаловать. Выберите, что вы хотите:',
#                                  reply_markup=epicgames_menu(user.epicgames_account, user.epicgames_try_acc))
#
#
# @router.callback_query(F.data == 'eg:donate')
# async def eg_enter_donate_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
#     games = [(i.id, i.name) for i in db_session.query(EGGame).filter(EGGame.has_donate == 1).all()]
#     await state.update_data(games=games)
#
#     await call.message.edit_text('Выберите игру:', reply_markup=eg_games_kb(games, 0, True))
#     await state.set_state(EGGame.search_donation_game)
#
#
# @router.callback_query(F.data.startswith('eg:search'))
# async def eg_search_game(call: CallbackQuery, state: FSMContext):
#     await state.set_state(EGState.search_game)
#     await call.message.edit_text('Введите название игры, которую хотите найти', reply_markup=back_eg_menu())
#
#
# @router.callback_query(F.data.startswith('eg:games'))
# async def eg_show_categories(call: CallbackQuery, db_session: Session, state: FSMContext):
#     categories = list(set(i.category for i in db_session.query(EGGame).all()))
#
#     await call.message.edit_text('Выберите нужную подборку игр:', reply_markup=eg_categories_kb(categories))
#
#
# @router.callback_query(F.data.startswith('eg_page:'))
# @router.callback_query(F.data.startswith('eg_category'))
# async def eg_show_games_in_category(call: CallbackQuery, state: FSMContext, db_session: Session):
#     data = await state.get_data()
#
#     if call.data.startswith('eg_page'):
#         page = int(call.data.split(':')[1])
#         games = data['games']
#     else:
#         page = data.get('page', 0)
#         category = call.data.split(':')[1]
#         games = [(i.id, i.name) for i in db_session.query(EGGame).filter(EGGame.category == category).all()]
#         await state.update_data(games=games)
#     await state.update_data(page=page)
#
#     await call.message.edit_text('Выберите игру:',
#                                  reply_markup=eg_games_kb(games, page,
#                                                           await state.get_state() == EGState.search_donation_game))
#
#
# @router.callback_query(F.data.startswith('eg_has_account'))
# async def eg_has_account_handler(call: CallbackQuery, db_session: Session):
#     user = db_session.query(User).filter(User.id == call.from_user.id).one()
#     user.epicgames_account = int(call.data.split(':')[1])
#     db_session.commit()
#     print(user.epicgames_account, user.epicgames_try_acc)
#
#     await call.message.edit_text('Добро пожаловать. Выберите, что вы хотите:',
#                                  reply_markup=epicgames_menu(user.epicgames_account, user.epicgames_try_acc))
#
#
# @router.callback_query(F.data.startswith('eg_try:'))
# async def eg_has_account_handler(call: CallbackQuery, db_session: Session):
#     user = db_session.query(User).filter(User.id == call.from_user.id).one()
#     user.epicgames_try_acc = int(call.data.split(':')[1])
#     db_session.commit()
#     print(user.epicgames_account, user.epicgames_try_acc)
#
#     await call.message.edit_text('Добро пожаловать. Выберите, что вы хотите:',
#                                  reply_markup=epicgames_menu(user.epicgames_account, user.epicgames_try_acc))
#
#
# @router.message(EGState.search_game)
# @router.callback_query(F.data.startswith('eg_game:'))
# async def eg_choose_game_handler(update: Message | CallbackQuery, state: FSMContext, db_session: Session):
#     data = await state.get_data()
#
#     if isinstance(update, Message):
#         game = db_session.query(EGGame).filter(EGGame.name == update.text).first()
#         if not game:
#             await update.answer('Ничего не было найдено, попробуйте заново', reply_markup=back_eg_menu())
#             return
#         game = game.id
#         func = update.answer
#     else:
#         game = int(update.data.split(':')[1])
#         func = update.message.edit_text
#
#     await state.update_data(game=game)
#     if await state.get_state() == EGState.search_donation_game.state:
#         donation_options = db_session.query(ConsoleDonation).filter(ConsoleDonation.game_id == game).all()
#         await func('Выберите нужную опцию', reply_markup=console_choose_donation_kb(donation_options, 'eg'))
#         return
#
#     game: Type[EGGame] = db_session.query(EGGame).filter(EGGame.id == game).one()
#     editions = [i for i in game.editions]
#
#     await update.message.delete()
#     draw_editions(editions)
#     await update.message.answer_photo(FSInputFile('shit.png'),
#                                       caption=game.name,
#                                       reply_markup=eg_choose_edition(editions, data['page']))
#
#
# @router.callback_query(EGState.search_donation_game, F.data.startswith('donation:'))
# async def eg_process_buy_donation(call: CallbackQuery, state: FSMContext, db_session: Session):
#     data = await state.get_data()
#     donation_id = int(call.data.split(':')[1])
#
#     donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()
#     game = db_session.query(EGGame).filter(EGGame.id == int(donation.game_id)).one()
#     currency = 'TRY'
#
#     if donation.margin:
#         total_margin = donation.margin
#         price = get_round_price(currency, donation.price * total_margin, convert=False)
#     else:
#         price = get_round_price(currency, get_donation_price(donation.price, currency, 'epicgames', db_session),
#                                 convert=False)
#
#     await state.update_data(donation_id=donation_id)
#     await call.message.answer(f'{game.name}\n{donation.description}\n\n💸 Цена: {price} ₽💸\n'
#                               f'Перейдите по ссылке для проведения оплаты',
#                               reply_markup=confirm_buy_kb('order_id', 'link.com', f'ps_game:{data["game"]}'))
#
#
# @router.callback_query(F.data.startswith('eg_edition'))
# async def ps_choose_edition_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
#     data = await state.get_data()
#
#     edition: Type[EGGameEdition] = db_session.query(EGGameEdition).filter(
#         EGGameEdition.id == int(call.data.split(':')[1])).first()
#
#     await state.update_data(edition_id=edition.id)
#
#     await call.message.edit_media(InputMediaPhoto(media=URLInputFile(edition.pic)))
#     await call.message.edit_caption(caption=format_game(edition, 'epicgames', db_session),
#                                     reply_markup=eg_buy_game_kb(edition.id, data['page']))
#
#
# @router.callback_query(F.data.startswith('eg_buy'))
# async def ps_process_buy_game(call: CallbackQuery, state: FSMContext, db_session: Session):
#     data = await state.get_data()
#     await call.answer()
#
#     order_id, link = ('0123', 't.me/maxlearmingbot')
#     edition: Type[EGGameEdition] = db_session.query(EGGameEdition).filter(
#         EGGameEdition.id == int(call.data.split(':')[1])).one()
#     currency = get_currency(edition.region)
#
#     price = get_game_price(edition.price if not edition.discount else edition.discount, currency, 'epicgames',
#                            db_session)
#
#     await call.message.answer('Перейдите по ссылке для проведения оплаты',
#                               reply_markup=confirm_buy_kb(order_id, link, f'eg_edition:{data["edition_id"]}'))
#     await state.set_state(EGState.buy)
#
#
# @router.callback_query(EGState.search_donation_game, F.data.startswith('check:'))
# @router.callback_query(EGState.buy, F.data.startswith('check:'))
# async def eg_check_payment(call: CallbackQuery, state: FSMContext, db_session: Session):
#     data = await state.get_data()
#
#     order_id = call.data.split(':')[1]
#
#     if True:
#         user = db_session.query(User).filter(User.id == call.from_user.id).one()
#         if not user.epicgames_account:
#             if 'edition_id' in data:
#                 edition = db_session.query(EGGameEdition).filter(
#                     EGGameEdition.id == int(data['edition_id'])).first()
#                 game: EGGame = edition.game
#                 tov = game.name + ' ' + edition.name + ' Edition'
#             elif 'donation_id' in data:
#                 donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(
#                     ConsoleDonation.id == int(data['donation_id'])).one()
#                 game: Type[EGGame] = db_session.query(EGGame).filter(EGGame.id == int(donation.game_id)).one()
#                 tov = f'{game.name}\n{donation.description}'
#             elif 'amount' in data:
#                 currency = data['currency']
#                 amount = data['amount']
#                 tov = f'Пополение аккаунта EG на {amount} {currency}'
#             await state.set_state(MainState.chat_w_admin)
#
#             await call.message.edit_text(f'Вы приобрели {tov}.\nОжидайте подключения оператора.')
#             await send_admin_invites(tov, call.from_user, no_account=True, platform='Epic Games',
#                                      has_try=user.epicgames_try_acc)
#             db_session.add(AdminChat(user_id=call.from_user.id, object=tov))
#             db_session.commit()
#             return
#
#         await call.message.edit_text('Введите логин и пароль от аккаунта в формате log:pass')
#         await state.set_state(EGState.log_and_pass)
#     else:
#         await call.answer('❌ Оплата не прошла')
#
#
# @router.message(EGState.log_and_pass, F.text)
# async def eg_receive_creds(message: Message, state: FSMContext):
#     login, password = message.text.split(':')
#     await state.update_data(login=login, password=password)
#
#     await message.answer(f'Проверьте правильность введенных данных: \nЛогин: {login}\nПароль: {password}\n\n'
#                          f'<i>Если вы нашли ошибку, введите логин и пароль заново</i>',
#                          reply_markup=confirm_credentials())
#
#
# @router.callback_query(EGState.log_and_pass, F.data == 'credentials_confirmed')
# async def eg_ask_for_2fa(call: CallbackQuery, state: FSMContext):
#     await call.message.edit_text('Введите резервный код двухфакторной аутентификации, если он есть, или выберите опцию'
#                                  'с клавиатуры', reply_markup=tfa_kb())
#
#     await state.set_state(EGState.tfa)
#
#
# @router.callback_query(EGState.tfa, F.data.startswith('2fa'))
# @router.message(EGState.tfa, F.text)
# async def eg_process_2fa(update: Message | CallbackQuery, db_session: Session, state: FSMContext):
#     data = await state.get_data()
#     await state.set_state(MainState.chat_w_admin)
#     user = db_session.query(User).filter(User.id == update.from_user.id).first()
#
#     if 'edition_id' in data:
#         edition = db_session.query(EGGameEdition).filter(EGGameEdition.id == int(data['edition_id'])).first()
#         game: EGGame = edition.game
#         tov = game.name + ' ' + edition.name + ' Edition'
#     elif 'donation_id' in data:
#         donation: Type[ConsoleDonation] = db_session.query(ConsoleDonation).filter(
#             ConsoleDonation.id == int(data['donation_id'])).one()
#         game: Type[EGGame] = db_session.query(EGGame).filter(EGGame.id == int(donation.game_id)).one()
#         tov = f'{game.name}\n{donation.description}'
#
#     await state.set_state(MainState.chat_w_admin)
#
#     tfa = ''
#     if isinstance(update, CallbackQuery):
#         if update.data == '2fa:no_code':
#             tfa = 'Нет'
#         else:
#             tfa = 'Без кода'
#         await update.message.edit_text(f'Вы приобрели {tov}.\nОжидайте подключения оператора.')
#
#     elif isinstance(update, Message):
#         tfa = update.text
#         await update.answer(f'Вы приобрели {tov}.\nОжидайте подключения оператора.')
#
#     db_session.add(AdminChat(user_id=update.from_user.id, object=tov))
#     db_session.commit()
#     await send_admin_invites(tov, update.from_user, data['login'], data['password'], tfa, platform='Epic Games',
#                              has_try=user.epicgames_try_acc)


@router.callback_query(F.data == 'pc:battlenet')
async def battlenet_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    await state.clear()

    settings = db_session.query(Settings).first()

    currency = 'TRY'
    rates, text = get_refill_prices(currency, settings.battlenet_additional_refill_margin,
                                    settings.battlenet_base_refill_margin)

    await state.update_data(rates=rates, currency=currency)

    media_path = 'tgbot/utils/media/bn_menu.png'
    media = get_photo(media_path, db_session)
    message = await call.message.edit_media(InputMediaPhoto(media=media, caption=text),
                                            reply_markup=back_pc())
    await state.set_state(BNState.refill)

    return media_path, message.photo[-1].file_id


@router.message(BNState.refill)
async def bn_enter_refill_amount(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    rates = data['rates']
    currency = data['currency']
    divisor = 10

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
            targets=f'Пополнение аккаунта Battle.net на {amount} {currency}',
            paymentType='SB',
            sum=int(amount * rates[block]),  # price
            label=label
        )

        media_path = 'tgbot/utils/media/bn_go_pay.png'
        media = get_photo(media_path, db_session)
        message = await message.answer_photo(media,
                                             f'Пополнение аккаунта Battle.net на {amount} {currency}\n💸 Цена: '
                                             f'{int(amount * rates[block])}₽ 💸',
                                             reply_markup=confirm_buy_kb(label, quickpay.redirected_url,
                                                                         f'pc:battlenet'))

        await state.set_state(BNState.buy)
        return media_path, message.photo[-1].file_id

    except ValueError:
        await message.answer(f'Введите целое число', reply_markup=back_pc())


@router.callback_query(BNState.buy, F.data.startswith('check:'))
async def bn_check_payment(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()

    label = call.data.split(':')[1]

    client = Client(p2p_token)

    history = client.operation_history(label=label)

    try:
        operation = history.operations[-1]
        if operation.status == 'success':
            currency = data['currency']
            amount = data['amount']
            tov = f'Пополение аккаунта Battle.net на {amount} {currency}'
            await state.set_state(MainState.chat_w_admin)

            media_path = 'tgbot/utils/media/bn_buy_success.png'
            media = get_photo(media_path, db_session)

            message = await call.message.edit_media(
                InputMediaPhoto(
                    media=media,
                    caption=f'Вы приобрели {tov}.\nОжидайте подключения оператора.'
                )
            )

            await send_admin_invites(tov, call.from_user, no_account=True, platform='BattleNet')
            db_session.add(AdminChat(user_id=call.from_user.id, platform='bn'))
            db_session.commit()
            return media_path, message.photo[-1].file_id

        else:
            await call.answer('❌ Оплата не прошла')
    except:
        await call.answer(f'Платеж не найден или не прошел. Пожалуйста, проверьте еще раз.')
