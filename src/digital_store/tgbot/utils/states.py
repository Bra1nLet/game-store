from aiogram.fsm.state import StatesGroup, State


class PSState(StatesGroup):
    search_game = State()
    buy = State()
    log_and_pass = State()
    tfa = State()
    search_donation_game = State()
    refill = State()
    email = State()


class XBOXState(StatesGroup):
    search_game = State()
    buy = State()
    log_and_pass = State()
    tfa = State()
    search_donation_game = State()
    refill = State()
    email = State()


class EGState(StatesGroup):
    search_game = State()
    buy = State()
    log_and_pass = State()
    tfa = State()
    search_donation_game = State()


class BNState(StatesGroup):
    log_and_pass = State()
    tfa = State()
    refill = State()
    buy = State()


class MainState(StatesGroup):
    chat_w_admin = State()
    admin_w_user = State()

    cart_buy = State()


class AdminState(StatesGroup):
    spam = State()

    change_game_name = State()
    change_game_category = State()

    change_donation_price = State()
    change_donation_discount = State()
    change_donation_description = State()
    change_donation_margin = State()

    add_donation_name = State()

    change_edition_price = State()
    change_edition_discount = State()
    change_edition_name = State()
    change_edition_description = State()
    change_edition_margin = State()

    change_subscription_price = State()
    change_subscription_discount = State()
    change_subscription_description = State()
    change_subscription_margin = State()

    change_margin = State()

    change_category = State()
