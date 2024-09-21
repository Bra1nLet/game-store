from playwright.sync_api._generated import BrowserContext, ElementHandle
from src.mparser.selectors.main_page_selectors import main_page_selectors
from src.mparser.parser.game_parser import GamePageParser
from src.db.db import games_collection, games_collection_tr


class InitialGamePageParser:
    def __init__(self, context: BrowserContext, _id, element: ElementHandle, currency, currency_multiplier):
        self._context = context
        self._element = element
        self._currency = currency
        self._currency_multiplier = currency_multiplier
        self._id = _id
        self._name = None
        self._game_url = None
        self._image_url = None

    def _collect_name(self):
        self._name = str(self._element.query_selector(main_page_selectors.name.replace("%", str(self._id))).inner_text())

    def _collect_image_url(self):
        self._image_url = str(self._element.query_selector(main_page_selectors.img_url).get_property("src"))

    def _get_game_link(self):
        self._game_url = str(self._element.query_selector(main_page_selectors.link_to_game).get_property("href"))

    def collect_initial_data(self):
        self._collect_image_url()
        self._collect_name()
        self._get_game_link()
        game = self._find_game_by_img_url(games_collection)
        if game:
            self._update_data(game["_id"], games_collection)
        else:
            self._collect_rest_data()

    def collect_tr_data(self):
        self._collect_image_url()
        self._get_game_link()
        game = self._find_game_by_img_url(games_collection_tr)
        if game:
            self._update_data(game["_id"], games_collection_tr)
            print("EXISTED TR GAME UPDATED")
        else:
            game = self._find_game_by_img_url(games_collection)
            if game:
                game["currency"] = self._currency
                inserted_game = games_collection_tr.insert_one(game)
                print("TR GAME INSERTED")
                self._update_data(inserted_game.inserted_id, games_collection_tr)
                print("TR GAME UPDATED")
            else:
                print("DIDNT FOUND TR GAMES AT ALL")

    def _collect_rest_data(self):
        page = self._context.new_page()
        page.goto(self._game_url)
        game_parser = GamePageParser(page, self._currency, self._currency_multiplier, self._name, self._image_url, games_collection)
        game_parser.insert_game()
        page.close()

    def _update_data(self, game_id, collection):
        page = self._context.new_page()
        page.goto(self._game_url)
        game_parser = GamePageParser(page, self._currency, self._currency_multiplier, self._name, self._image_url, collection)
        game_parser.update_discount_and_prices(game_id)
        page.close()

    def _find_game_by_img_url(self, collection):
        return collection.find_one({"image_url": self._image_url})

