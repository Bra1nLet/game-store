from typing import Type

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.formatting import Text
from aiogram.filters import Command
from sqlalchemy.orm import Session

from tgbot.data import loader
from tgbot.data.config import admin_ids
from tgbot.data.loader import bot, storage
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.context import FSMContext

from tgbot.keyboards.admin_keyboards import *
from tgbot.services.database import User, AdminChat, PSGame, XBOXGame, PSGameEdition, XBOXGameEdition, \
    ConsoleSubscription, ConsoleDonation, Settings
from tgbot.keyboards.ps_keyboards import *
from tgbot.utils.other import format_user, send_admin_invites, admin_format_game, admin_format_donation, \
    admin_format_edition, admin_format_subscription, admin_margins_text
from tgbot.utils.states import MainState, AdminState

router = Router()


@router.message(MainState.admin_w_user)
async def admin_w_user_handler(message: Message, state: FSMContext, db_session: Session):
    chat: Type[AdminChat] | None = db_session.query(AdminChat).filter(
        AdminChat.admin_id == message.from_user.id).first()

    if message.text == '✅ Завершить чат':
        db_session.delete(chat)
        db_session.commit()
        await message.answer(f'Чат с пользователем {format_user(chat.user_id, db_session)} завершен.',
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()

        key = StorageKey(bot.id, chat.user_id, chat.user_id)
        user_state = FSMContext(storage, key)
        await user_state.clear()
        media = FSInputFile(f'tgbot/utils/media/{chat.platform}_finished.png')

        await bot.send_photo(chat.user_id, media,
                             caption='Заказ завершен✅\n\nОставь пожалуйста отзыв о работе и получите 5% скидку на '
                                     'следующий заказ: https://t.me/+c6--F8QT9MVlYmQ6\n\nИскренне надеемся, что тебе '
                                     'все понравилось😇 Хорошего тебе времени за любимой игрой')

    elif message.text == '❌ Передать чат другому администратору':
        chat.admin_id = 0
        db_session.commit()
        await message.answer(f'Вы вышли из чата с пользователем {format_user(chat.user_id, db_session)}',
                             reply_markup=ReplyKeyboardRemove())

        for admin in admin_ids:
            if admin == message.from_user.id:
                continue

            await bot.send_message(admin, f'Администратор {message.from_user.full_name} вышел из чата с пользователем'
                                          f'{format_user(chat.user_id, db_session)}',
                                   reply_markup=admin_enter_chat(chat.user_id))
        await state.clear()
        await bot.send_photo(chat.user_id, FSInputFile('tgbot/utils/media/ps_support.png'),
                             caption='Администратор вышел из чата с вами. Ожидайте подклюения другого '
                                     'администратора.')
    else:
        await bot.send_message(chat.user_id, message.text)


@router.callback_query(F.data.startswith('admin_enter_chat'))
async def admin_enter_chat_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    user_id = int(call.data.split(':')[1])
    chat: Type[AdminChat] | None = db_session.query(AdminChat).filter(AdminChat.user_id == user_id).first()
    if not chat:
        await call.answer("Чат с этип пользователем завершен.")
        return

    if chat.admin_id:
        await call.answer('Другой администратор уже подключился к чату с этим пользователем.')
        return

    chat.admin_id = call.from_user.id
    db_session.commit()

    user = db_session.query(User).filter(User.id == user_id).one()

    await state.set_state(MainState.admin_w_user)

    await bot.send_message(user_id, 'Оператор подключился к чату 💬')

    await call.message.answer(f"Вы вошли в чат с пользователем <b>@{user.username}</b> |"
                              f" <a href='tg://user?id={user.id}'>{user.full_name}</a>",
                              reply_markup=admin_exit_chat_kb())
    await call.answer()


@router.callback_query(F.data == 'admin_menu')
@router.message(F.text == '/admin')
async def admin_menu_handler(update: Message | CallbackQuery, state: FSMContext):
    if isinstance(update, Message):
        await update.answer('Выберите пункт меню', reply_markup=admin_menu_kb())
    elif isinstance(update, CallbackQuery):
        await update.message.edit_text('Выберите пункт меню', reply_markup=admin_menu_kb())


@router.callback_query(F.data == 'admin_sent')
async def admin_spam_handler(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Пришлите сообщение для рассылки (не более одного вложения)')
    await state.set_state(AdminState.spam)


@router.message(AdminState.spam, F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO]))
async def spam_start_y_n(message: Message, state: FSMContext):
    await message.copy_to(message.from_user.id, reply_markup=start_spam_kb())


@router.callback_query(AdminState.spam, F.data == 'spam_start')
async def start_spam(call: CallbackQuery, state: FSMContext, db_session: Session):
    active_users = db_session.query(User).all()
    c = 0
    for user in active_users:
        try:
            await call.message.copy_to(user.id)
            c += 1
        except Exception:
            continue

    await call.message.answer(f'Рассылка по {c} пользователям проведена')


@router.callback_query(F.data == 'admin_settings')
async def admin_settings_menu_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()

    await call.message.edit_text('Выберите, что хотите сделать/изменить:', reply_markup=admin_settings_kb())


@router.callback_query(F.data == 'settings:ps')
async def admin_choose_platform_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Выберите регион, в котором будете что-то менять', reply_markup=admin_ps_region())


@router.callback_query(F.data.startswith('adm_ps_country'))
@router.callback_query(F.data == 'settings:xbox')
async def admin_show_platform_handler(call: CallbackQuery, state: FSMContext):
    if call.data.startswith('settings'):
        platform = 'xbox'
        await state.update_data(region='tr')
    else:
        platform = 'ps'
        await state.update_data(region=call.data.split(':')[1])

    await state.update_data(platform=platform)
    await call.message.edit_text('Выберите, где вы хотите внести изменения', reply_markup=console_settings_kb())


@router.callback_query(F.data == 'admin:games')
async def admin_show_categories_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = data['platform']
    region = data.get('region', 'tr')

    categories = list(
        set((i.category, i.emoji) for i in db_session.query(PSGame if platform == 'ps' else XBOXGame).all()))

    await call.message.edit_text('Выберите категорию', reply_markup=adm_categories_kb(categories, region))


@router.callback_query(F.data.startswith('adm_page:'))
@router.callback_query(F.data.startswith('adm_category'))
async def admin_category_handler(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = data['platform']

    if call.data.startswith('adm_page'):
        page = int(call.data.split(':')[1])
        games = data['games']
    else:
        page = data.get('page', 0)
        category = call.data.split(':')[1]
        await state.update_data(category=category)
        if platform == 'ps':
            games = [(i.id, i.name, i.emoji or '') for i in
                     db_session.query(PSGame).filter(PSGame.category == category).all() if
                     any(j.region == data['region'] for j in i.editions)]
        else:
            games = [(i.id, i.name, i.emoji or '') for i in
                     db_session.query(XBOXGame).filter(XBOXGame.category == category).all()]

        await state.update_data(games=games)

    await state.update_data(page=page)

    await call.message.edit_text('Выберите игру',
                                 reply_markup=adm_games_kb(games, page, data.get('category')))


@router.callback_query(F.data.startswith('adm_ps_platform'))
@router.callback_query(F.data.startswith('adm_xbox_platform'))
@router.callback_query(F.data.startswith('adm_game'))
async def admin_show_game_menu(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = data['platform']

    GameClass = PSGame if platform == 'ps' else XBOXGame
    if call.data.startswith(f'adm_{platform}_platform'):
        console_platform = call.data.split(':')[1]
        await state.update_data(console_platform=console_platform)
        game_id = int(data['game_id'])
        game = db_session.query(GameClass).filter(GameClass.id == game_id).one()
    else:

        game_id = int(call.data.split(':')[1])
        game = db_session.query(GameClass).filter(GameClass.id == game_id).one()

        await state.update_data(game_id=game_id)

        console_platforms = list(set(i.platform for i in game.editions))

        await call.message.edit_text('Выберите платформу',
                                     reply_markup=adm_choose_platform(data['page'], console_platforms, platform))
        return

    editions = [i for i in game.editions if i.platform == console_platform and i.region == data['region']]

    await call.message.edit_text(admin_format_game(game), reply_markup=adm_game_kb(editions, data['page']))


@router.callback_query(F.data.startswith('change_game'))
async def admin_change_game(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    game_id = data['game_id']
    platform = data['platform']

    if call.data == 'change_game:category':
        await call.message.answer('Пришлите новую категорию для этой игры')
        await state.set_state(AdminState.change_game_category)
    elif call.data == 'change_game:name':
        await call.message.answer('Пришлите новое название игры')
        await state.set_state(AdminState.change_game_name)
    elif call.data == 'change_game:donate':
        donations = db_session.query(ConsoleDonation).filter(ConsoleDonation.game_id == int(game_id),
                                                             ConsoleDonation.platform == str(platform)).all()

        await call.message.edit_text('Выберите опцию', reply_markup=adm_donations_kb(donations, game_id))


@router.message(AdminState.change_game_category)
async def change_game_category_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    game_id = int(data['game_id'])
    platform = str(data['platform'])

    if platform == 'xbox':
        game = db_session.query(XBOXGame).filter(XBOXGame.id == game_id).one()
        editions = game.editions
    else:
        game = db_session.query(PSGame).filter(PSGame.id == game_id).one()
        editions = [i for i in game.editions if i.region == data['region'] and i.platform == data['console_platform']]

    category = message.text
    await state.update_data(category=message.text)
    if platform == 'ps':
        games = [(i.id, i.name, i.emoji or '') for i in
                 db_session.query(PSGame).filter(PSGame.category == category).all() if
                 any(j.region == data['region'] for j in i.editions)]
    else:
        games = [(i.id, i.name, i.emoji or '') for i in
                 db_session.query(XBOXGame).filter(XBOXGame.category == category).all()]

    await state.update_data(games=games)

    game.category = message.text
    db_session.commit()

    await message.answer(admin_format_game(game), reply_markup=adm_game_kb(editions, data['page']))

    await state.set_state(None)


@router.message(AdminState.change_game_name)
async def change_game_name_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    game_id = int(data['game_id'])
    platform = str(data['platform'])

    if platform == 'xbox':
        game = db_session.query(XBOXGame).filter(XBOXGame.id == game_id).one()
        editions = game.editions
    else:
        game = db_session.query(PSGame).filter(PSGame.id == game_id).one()
        editions = [i for i in game.editions if i.region == data['region'] and i.platform == data['console_platform']]

    game.name = message.text
    db_session.commit()

    category = str(game.category)
    if platform == 'ps':
        games = [(i.id, i.name, i.emoji or '') for i in
                 db_session.query(PSGame).filter(PSGame.category == category).all() if
                 any(j.region == data['region'] for j in i.editions)]
    else:
        games = [(i.id, i.name, i.emoji or '') for i in
                 db_session.query(XBOXGame).filter(XBOXGame.category == category).all()]

    await state.update_data(games=games)

    await message.answer(admin_format_game(game), reply_markup=adm_game_kb(editions, data['page']))

    await state.set_state(None)


@router.callback_query(F.data.startswith('adm_donation'))
async def admin_change_donation(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    donation_id = int(call.data.split(':')[1])

    donation = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()

    await call.message.edit_text(admin_format_donation(donation), reply_markup=admin_donation_kb(donation))


@router.callback_query(F.data.startswith('change_donation'))
async def admin_change_donation(call: CallbackQuery, state: FSMContext, db_session: Session):
    donation_id = int(call.data.split(':')[1])
    action = call.data.split(':')[2]

    if action == 'price':
        await call.message.answer('Пришлите новую цену')
        await state.set_state(AdminState.change_donation_price)
    elif action == 'description':
        await call.message.answer('Пришлите новое описание')
        await state.set_state(AdminState.change_donation_description)
    elif action == 'discount':
        if len(call.data.split(':')) == 4:
            donation = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()
            donation.discount = 0
            db_session.commit()
            await call.message.edit_text(admin_format_donation(donation), reply_markup=admin_donation_kb(donation))
            return

        await call.message.answer('Пришлите новую цену')
        await state.set_state(AdminState.change_donation_discount)
    elif action == 'margin':
        await call.message.answer('Пришлите новую наценку')
        await state.set_state(AdminState.change_donation_margin)

    await state.update_data(donation_id=donation_id)


@router.message(AdminState.change_donation_margin)
async def change_donation_margin_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    donation_id = int(data['donation_id'])

    donation = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()
    try:
        donation.margin = int(message.text)
    except ValueError:
        await message.answer('Пришлите новую наценку (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_donation(donation), reply_markup=admin_donation_kb(donation))

    await state.set_state(None)


@router.message(AdminState.change_donation_price)
async def change_donation_price_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    donation_id = int(data['donation_id'])

    donation = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()
    try:
        donation.price = int(message.text)
    except ValueError:
        await message.answer('Пришлите новую цену (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_donation(donation), reply_markup=admin_donation_kb(donation))

    await state.set_state(None)


@router.message(AdminState.change_donation_description)
async def change_donation_description_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    donation_id = int(data['donation_id'])

    donation = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()
    donation.description = message.text
    db_session.commit()

    await message.answer(admin_format_donation(donation), reply_markup=admin_donation_kb(donation))

    await state.set_state(None)


@router.message(AdminState.change_donation_discount)
async def change_donation_discount_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    donation_id = int(data['donation_id'])

    donation = db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).one()
    try:
        donation.discount = int(message.text)
    except ValueError:
        await message.answer('Пришлите новую цену (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_donation(donation), reply_markup=admin_donation_kb(donation))

    await state.set_state(None)


@router.callback_query(F.data.startswith('delete_donation:'))
async def delete_donation(call: CallbackQuery, state: FSMContext, db_session: Session):
    donation_id = int(call.data.split(':')[1])
    await call.message.edit_text('Вы уверены, что хотите удалить эту опцию?',
                                 reply_markup=delete_donation_confirm_kb(donation_id))


@router.callback_query(F.data.startswith('delete_donation_confirm'))
async def delete_donation_confirm(call: CallbackQuery, state: FSMContext, db_session: Session):
    donation_id = int(call.data.split(':')[1])

    db_session.query(ConsoleDonation).filter(ConsoleDonation.id == donation_id).delete()
    db_session.commit()

    await call.answer('Опция удалена')

    game_id = int((await state.get_data())['game_id'])
    donations = db_session.query(ConsoleDonation).filter(ConsoleDonation.game_id == game_id).all()
    if len(donations) == 0:
        GameClass = PSGame if (await state.get_data())['platform'] == 'ps' else XBOXGame
        db_session.query(GameClass).filter(GameClass.id == game_id).update({GameClass.has_donate: 0})
        db_session.commit()
    await call.message.edit_text('Выберите опцию', reply_markup=adm_donations_kb(donations, game_id))


@router.callback_query(F.data.startswith('add_donation'))
async def add_donation(call: CallbackQuery, state: FSMContext, db_session: Session):
    game_id = int(call.data.split(':')[1])
    await state.update_data(game_id=game_id)

    await call.message.answer('Пришлите описание опции')
    await state.set_state(AdminState.add_donation_name)


@router.message(AdminState.add_donation_name)
async def add_donation_name_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    game_id = int((await state.get_data())['game_id'])
    donation = ConsoleDonation(game_id=game_id, description=message.text, platform=data['platform'])
    if data['platform'] == 'ps':
        donation.region = data['region']

    db_session.add(donation)
    GameClass = PSGame if (await state.get_data())['platform'] == 'ps' else XBOXGame
    db_session.query(GameClass).filter(GameClass.id == game_id).update({GameClass.has_donate: 1})
    db_session.commit()

    await message.answer(admin_format_donation(donation), reply_markup=admin_donation_kb(donation))

    await state.set_state(None)


@router.callback_query(F.data.startswith('adm_edition'))
async def admin_show_edition_menu(call: CallbackQuery, state: FSMContext, db_session: Session):
    edition_id = int(call.data.split(':')[1])
    edition = db_session.query(PSGameEdition).filter(PSGameEdition.id == edition_id).one()

    await call.message.edit_text(admin_format_edition(edition), reply_markup=admin_edition_kb(edition))


@router.callback_query(F.data.startswith('change_edition'))
async def admin_change_edition(call: CallbackQuery, state: FSMContext, db_session: Session):
    edition_id = int(call.data.split(':')[1])
    action = call.data.split(':')[2]

    if action == 'price':
        await call.message.answer('Пришлите новую цену')
        await state.set_state(AdminState.change_edition_price)
    elif action == 'description':
        await call.message.answer('Пришлите новое описание')
        await state.set_state(AdminState.change_edition_description)
    elif action == 'name':
        await call.message.answer('Пришлите новое название')
        await state.set_state(AdminState.change_edition_name)
    elif action == 'discount':
        if len(call.data.split(':')) == 4:
            edition = db_session.query(PSGameEdition).filter(PSGameEdition.id == edition_id).one()
            edition.discount = 0
            db_session.commit()
            await call.message.edit_text(admin_format_edition(edition), reply_markup=admin_edition_kb(edition))
            return

        await call.message.answer('Пришлите цену со скидкой')
        await state.set_state(AdminState.change_edition_discount)
    elif action == 'margin':
        await call.message.answer('Пришлите новую наценку')
        await state.set_state(AdminState.change_edition_margin)

    await state.update_data(edition_id=edition_id)


@router.message(AdminState.change_edition_margin)
async def change_edition_margin_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    edition_id = int(data['edition_id'])

    edition = db_session.query(PSGameEdition).filter(PSGameEdition.id == edition_id).one()
    try:
        edition.margin = int(message.text)
    except ValueError:
        await message.answer('Пришлите новую наценку (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_edition(edition), reply_markup=admin_edition_kb(edition))

    await state.set_state(None)


@router.message(AdminState.change_edition_price)
async def change_edition_price_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    edition_id = int(data['edition_id'])

    edition = db_session.query(PSGameEdition).filter(PSGameEdition.id == edition_id).one()
    try:
        edition.price = int(message.text)
    except ValueError:
        await message.answer('Пришлите новую цену (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_edition(edition), reply_markup=admin_edition_kb(edition))

    await state.set_state(None)


@router.message(AdminState.change_edition_description)
async def change_edition_description_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    edition_id = int(data['edition_id'])

    edition = db_session.query(PSGameEdition).filter(PSGameEdition.id == edition_id).one()
    edition.description = message.text
    db_session.commit()

    await message.answer(admin_format_edition(edition), reply_markup=admin_edition_kb(edition))

    await state.set_state(None)


@router.message(AdminState.change_edition_name)
async def change_edition_name_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    edition_id = int(data['edition_id'])

    edition = db_session.query(PSGameEdition).filter(PSGameEdition.id == edition_id).one()
    edition.name = message.text
    db_session.commit()

    await message.answer(admin_format_edition(edition), reply_markup=admin_edition_kb(edition))

    await state.set_state(None)


@router.message(AdminState.change_edition_discount)
async def change_edition_discount_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    edition_id = int(data['edition_id'])

    edition = db_session.query(PSGameEdition).filter(PSGameEdition.id == edition_id).one()
    try:
        edition.discount = int(message.text)
    except ValueError:
        await message.answer('Пришлите цену со скидкой (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_edition(edition), reply_markup=admin_edition_kb(edition))

    await state.set_state(None)


@router.callback_query(F.data == 'admin:subscriptions')
async def admin_subscriptions(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = str(data['platform'])

    subscriptions = list(set(
        i.name for i in db_session.query(ConsoleSubscription).filter(ConsoleSubscription.platform == platform).all()))
    await call.message.edit_text('Выберите тип подписки', reply_markup=admin_subscriptions_kb(subscriptions, platform))


@router.callback_query(F.data.startswith('adm_subscription'))
async def admin_subscriptions(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    region = str(data['region'])
    subscription = call.data.split(':')[1]
    await state.update_data(subscription=subscription)

    platform = str(data['platform'])

    durations = [i.duration for i in
                 db_session.query(ConsoleSubscription).filter(ConsoleSubscription._name == subscription,
                                                              ConsoleSubscription.platform == platform,
                                                              ConsoleSubscription.region == region).all()]

    await call.message.edit_text('Выберите опцию', reply_markup=admin_subscription_kb(durations))


@router.callback_query(F.data.startswith('adm_sub_duration'))
async def admin_subscriptions(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    duration = int(call.data.split(':')[1])
    platform = str(data['platform'])
    subscription = str(data['subscription'])
    region = str(data['region'])

    subscription = db_session.query(ConsoleSubscription).filter(ConsoleSubscription._name == subscription,
                                                                ConsoleSubscription.duration == duration,
                                                                ConsoleSubscription.platform == platform,
                                                                ConsoleSubscription.region == region).one()

    await state.update_data(subscription_id=subscription.id)

    await call.message.edit_text(admin_format_subscription(subscription), reply_markup=admin_duration_kb(subscription))


@router.callback_query(F.data.startswith('change_subscription'))
async def admin_change_subscription(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    subscription = db_session.query(ConsoleSubscription).filter(
        ConsoleSubscription.id == int(data['subscription_id'])).one()

    action = call.data.split(':')[1]

    if action == 'price':
        await call.message.answer('Пришлите новую цену подписки')
        await state.set_state(AdminState.change_subscription_price)
    elif action == 'discount':
        if len(call.data.split(':')) == 3:
            subscription.discount = 0
            db_session.commit()
            await call.message.edit_text(admin_format_subscription(subscription),
                                         reply_markup=admin_duration_kb(subscription))
            return

        await call.message.answer('Пришлите новую цену')
        await state.set_state(AdminState.change_subscription_discount)
    elif action == 'margin':
        await call.message.answer('Пришлите новую наценку')
        await state.set_state(AdminState.change_subscription_margin)

    await state.update_data(subscription_id=subscription.id)


@router.message(AdminState.change_subscription_price)
async def change_subscription_price_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    subscription_id = int(data['subscription_id'])

    subscription = db_session.query(ConsoleSubscription).filter(ConsoleSubscription.id == subscription_id).one()
    try:
        subscription.price = int(message.text)
    except ValueError:
        await message.answer('Пришлите новую цену (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_subscription(subscription), reply_markup=admin_duration_kb(subscription))

    await state.set_state(None)


@router.message(AdminState.change_subscription_discount)
async def change_subscription_discount_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    subscription_id = int(data['subscription_id'])

    subscription = db_session.query(ConsoleSubscription).filter(ConsoleSubscription.id == subscription_id).one()
    try:
        subscription.discount = int(message.text)
    except ValueError:
        await message.answer('Пришлите новую цену (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_subscription(subscription), reply_markup=admin_duration_kb(subscription))

    await state.set_state(None)


@router.message(AdminState.change_subscription_margin)
async def change_subscription_margin_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    subscription_id = int(data['subscription_id'])

    subscription = db_session.query(ConsoleSubscription).filter(ConsoleSubscription.id == subscription_id).one()
    try:
        subscription.margin = int(message.text)
    except ValueError:
        await message.answer('Пришлите новую наценку (целое число)')
        return

    db_session.commit()

    await message.answer(admin_format_subscription(subscription), reply_markup=admin_duration_kb(subscription))

    await state.set_state(None)


# admin:margins
@router.callback_query(F.data == 'admin:margins')
async def admin_margins(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = str(data['platform'])

    await call.message.edit_text(admin_margins_text(db_session.query(Settings).one(), platform),
                                 reply_markup=admin_margins_kb(platform))


@router.callback_query(F.data.startswith('change_margin'))
async def admin_change_margin(call: CallbackQuery, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform, category, type = call.data.split(':')[1:4]

    await state.update_data(platform=platform, category=category, type=type)
    if platform == 'ps' and category == 'refill':
        await state.update_data(region=call.data.split(':')[4])

    await call.message.answer('Пришлите новое значение')
    await state.set_state(AdminState.change_margin)


@router.message(AdminState.change_margin)
async def change_margin_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    platform = data['platform']
    category = data['category']
    type = data['type']

    settings = db_session.query(Settings).one()
    if platform == 'ps':
        if category == 'games':
            if type == 'base':
                settings.ps_base_game_margin = int(message.text)
            else:
                settings.ps_additional_game_margin = float(message.text)
        elif category == 'donate':
            if type == 'base':
                settings.ps_base_donate_margin = int(message.text)
            else:
                settings.ps_additional_donate_margin = float(message.text)
        elif category == 'refill':
            if data['region'] == 'ua':
                if type == 'base':
                    settings.ps_base_refill_margin_ua = int(message.text)
                else:
                    settings.ps_additional_refill_margin_ua = float(message.text)
            else:
                if type == 'base':
                    settings.ps_base_refill_margin_tr = int(message.text)
                else:
                    settings.ps_additional_refill_margin_tr = float(message.text)
    elif platform == 'xbox':
        if category == 'games':
            if type == 'base':
                settings.xbox_base_game_margin = int(message.text)
            else:
                settings.xbox_additional_game_margin = float(message.text)
        elif category == 'donate':
            if type == 'base':
                settings.xbox_base_donate_margin = int(message.text)
            else:
                settings.xbox_additional_donate_margin = float(message.text)
        elif category == 'refill':
            if type == 'base':
                settings.xbox_base_refill_margin = int(message.text)
            else:
                settings.xbox_additional_refill_margin = float(message.text)
    else:
        if category == 'refill':
            if type == 'base':
                settings.bn_base_refill_margin = int(message.text)
            else:
                settings.bn_additional_refill_margin = float(message.text)

    db_session.commit()

    await message.answer(admin_margins_text(db_session.query(Settings).one(), platform),
                         reply_markup=admin_margins_kb(platform))
    await state.set_state(None)


@router.callback_query(F.data.startswith('change_category'))
async def admin_change_category(call: CallbackQuery, state: FSMContext, db_session: Session):
    category = (await state.get_data())['category']

    await call.message.edit_text(f'Пришлите новый эмоджи для категории {category}')
    await state.set_state(AdminState.change_category)


@router.message(AdminState.change_category)
async def change_category_handler(message: Message, state: FSMContext, db_session: Session):
    data = await state.get_data()
    category = str(data['category'])
    platform = data['platform']

    if platform == 'ps':
        db_session.query(PSGame).filter(PSGame.category == category).update(
            {PSGame.emoji: message.text.replace('.', '')})
        db_session.commit()
    else:
        db_session.query(XBOXGame).filter(XBOXGame.category == category).update(
            {XBOXGame.emoji: message.text.replace('.', '')})
        db_session.commit()

    categories = list(
        set((i.category, i.emoji) for i in db_session.query(PSGame if platform == 'ps' else XBOXGame).all()))

    await message.answer('Выберите категорию',
                         reply_markup=adm_categories_kb(categories, region=data.get('region', None)))

    await state.set_state(None)
