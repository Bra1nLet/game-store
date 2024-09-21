import time
from bson import ObjectId
from playwright.sync_api._generated import Page
from src.db.db import editions_collection, editions_collection_tr
from src.mparser.parser.edition_parser import EditionParser
from src.mparser.selectors.game_page_selectors import game_page_selectors
from src.api.models.new_game_model import Game, UpdateGame


class GamePageParser:
    def __init__(self, page: Page, currency, currency_multiplier, name, image_url, collection):
        self._page = page
        self._collection = collection
        self._currency = currency
        self._currency_multiplier = currency_multiplier
        self._name = name
        self._price = None
        self._image_url = image_url
        self._price_without_discount = None
        self._discount_percentage = None
        self._discount_ends = None
        self._rating = None
        self._details = None

    def insert_game(self):
        time.sleep(1.5)
        self._collect_price()
        if self._price:
            self._collect_rating()
            self._collect_details()
            self._print_collected_data()
            model = self._make_model()
            inserted_game = self._collection.insert_one(model.model_dump())
            self._collect_editions(inserted_game.inserted_id)
        else:
            print(f"SKIP, INVALID PRICE {self._name}")

    def _make_model(self):
        return Game(
            name=self._name,
            price=self._price,
            image_url=self._image_url,
            currency=self._currency,
            price_rub=self._price,
            price_without_discount=self._price_without_discount,
            discount_percentage=self._discount_percentage,
            discount_ends=self._discount_ends,
            details=self._details,
            rating=self._rating
        )

    def _print_collected_data(self):
        print("------------Game collected--------------", "\n",
              self._name, "\n",
              self._image_url, "\n",
              self._currency, "\n",
              self._price, "\n",
              self._rating, "\n",
              self._details, "\n",
              self._price_without_discount, "\n",
              self._discount_percentage, "\n",
              self._discount_ends, "\n",
              "----------------------------------------"
              )

    def update_discount_and_prices(self, game_id):
        time.sleep(1.5)
        self._collect_price()
        if self._price:
            self._collect_editions(game_id)
            self._print_collected_data()
            data = UpdateGame(
                price_rub=self._price,
                price_without_discount=self._price_without_discount,
                discount_percentage=self._discount_percentage,
                discount_ends=self._discount_ends,
            ).model_dump()
            print("data that updated")
            print(data)
            updated_data = self._collection.update_one({"_id": ObjectId(game_id)}, {'$set': data})
            print(updated_data)

    def _collect_price(self):
        price_options = self._page.query_selector_all(game_page_selectors.price_containers)
        for option in price_options:
            price = option.query_selector(game_page_selectors.price).inner_text()
            price = validate_price(price, self._currency)
            if price:
                self._price = price * self._currency_multiplier
                self._collect_discount(option)
                break

    def _collect_discount(self, element):
        price_without_discount = element.query_selector(game_page_selectors.price_without_discount)
        if price_without_discount:
            price_without_discount = validate_price(price_without_discount.inner_text(), self._currency)
            if price_without_discount:
                self._price_without_discount = price_without_discount * self._currency_multiplier
                self._discount_percentage = element.query_selector(game_page_selectors.price_discount_percentage).inner_text()
                self._discount_ends = element.query_selector(game_page_selectors.discount_ends).inner_text()

    def _collect_editions(self, game_id):
        editions = self._page.query_selector_all(game_page_selectors.editions)
        if editions:
            for i in range(len(editions)):
                ep = None
                if self._currency == "UAH":
                    ep = EditionParser(editions[i], self._currency, self._currency_multiplier, self._name, game_id, editions_collection)
                elif self._currency == "TRY":
                    ep = EditionParser(editions[i], self._currency, self._currency_multiplier, self._name, game_id, editions_collection_tr)
                ep.insert_editions(i)

    def _collect_discount_end(self):
        element = self._page.query_selector(game_page_selectors.discount_ends)
        if element:
            element = element.inner_text()
        self._discount_ends = element

    def _collect_rating(self):
        element =  self._page.query_selector(game_page_selectors.rating)
        if element:
            element = element.inner_text()
            self._rating = element

    def _collect_details(self):
        result = {}
        indexes = self._page.query_selector_all(game_page_selectors.details_index)
        values = self._page.query_selector_all(game_page_selectors.details_value)
        for i in range(len(indexes)):
            result.update({str(indexes[i].inner_text()):str(values[i].inner_text())})
        self._details = result

def validate_price(price, currency):
    try:
        price = price.replace(",", ".").replace("\xa0", " ")
        if currency == "UAH":
            price =  int(float(price.split(" ", 1)[1].replace(" ", "")))
        elif currency == "TRY":
            price = int(float(price.split(" ", 1)[0].replace(" ", "")))
        if price != 0:
            return price
    except:
        return False