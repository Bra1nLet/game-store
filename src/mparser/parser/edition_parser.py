from playwright.sync_api._generated import ElementHandle
from src.mparser.selectors.game_page_selectors import game_page_selectors
from src.api.models.new_game_model import EditionModel
from src.db.db import editions_collection, editions_collection_tr

class EditionParser:
    def __init__(self, edition: ElementHandle, currency, currency_multiplier, game_name, game_id, collection):
        self._edition = edition
        self._collection = collection
        self._currency = currency
        self._currency_multiplier = currency_multiplier
        self._game_name = game_name
        self._game_id = game_id
        self.name = None
        self._price = None
        self._price_without_discount = None
        self._discount_percentage = None
        self._discount_ends = None
        self.picture_path = None
        self.details = None
        self.platforms = None


    def insert_editions(self, _id):
        self._collect_price()
        if self._price:
            self._collect_name()
            self._collect_price_without_discount()

            self._collect_discount_percentage()
            self._collect_picture(_id)
            self._collect_details()
            self._collect_platforms()
            self._print_edition()

            edition = EditionModel(
                game_id=str(self._game_id),
                name=self.name,
                currency=self._currency,
                price_rub=self._price,
                price_without_discount=self._price_without_discount,
                discount_percentage=self._discount_percentage,
                discount_ends=self._discount_ends,
                picture_path=self.picture_path,
                details=self.details,
                platforms=self.platforms,
            )
            self._collection.insert_one(edition.model_dump())

    def _print_edition(self):
        print(
            "--------Edition--------" + "\n",
            self.name, "\n",
            self._price, "\n",
            self._price_without_discount, "\n",
            self._discount_percentage, "\n",
            self.picture_path, "\n",
            self.details, "\n",
            self.platforms, "\n",
            "------------------------"
        )

    def _collect_name(self):
        self.name = self._edition.query_selector(game_page_selectors.editions_name).inner_text()

    def _collect_price(self):
        price = self._edition.query_selector(game_page_selectors.editions_price).inner_text()
        price = validate_price(price, self._currency)
        if price:
            self._price = price * self._currency_multiplier

    def _collect_picture(self, _id):
        picture_game_name_path = self._game_name.replace("/", "")
        picture_edition_name_path = self.name.replace("/", "")
        self.picture_path = f"./pictures/{picture_game_name_path}/{picture_edition_name_path}/{_id}.png"
        self._edition.query_selector(game_page_selectors.editions_picture).screenshot(path=self.picture_path)

    def _collect_discount_percentage(self):
        discount_percentage = self._edition.query_selector(game_page_selectors.editions_discount_percentage)
        if discount_percentage:
            self._discount_percentage = discount_percentage.inner_text()

    def _collect_price_without_discount(self):
        price_without_discount = self._edition.query_selector(game_page_selectors.price_without_discount)
        if price_without_discount:
            if price_without_discount := validate_price(price_without_discount.inner_text()):
                self._price_without_discount = price_without_discount * self._currency_multiplier

    def _collect_platforms(self):
        result = []
        platforms = self._edition.query_selector_all(game_page_selectors.editions_platforms)
        if platforms:
            for platform in platforms:
                result.append(platform.inner_text())
            self.platforms =  result

    def _collect_details(self):
        result = []
        details = self._edition.query_selector_all(game_page_selectors.editions_details)
        if details:
            for detail in details:
                result.append(detail.inner_text())
            self.details = result


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
        print(f"Edition___FAILED______price:{price}")
        return False