import json
from sre_constants import error
from wave import Error

from bs4 import Tag
from json import loads
from src.api.models.new_game_model import EditionModel
from src.db.db import editions_collection, editions_collection_tr
from pydantic import ValidationError

class EditionParser:
    def __init__(self, game_name, edition_element: Tag, game_id, currency, rates):
        self.game_name = game_name
        self.edition_element = edition_element
        self.rates = rates
        self.model = None


        self.game_id = str(game_id)
        self.name = None
        self.price = None
        self.currency = currency
        self.discount_available = False
        self.discount_price = None
        self.discount_percentage = None
        self.discount_ends = None
        self.details = None
        self.picture_url = None
        self.platforms = None

    def parse_edition(self):
        try:
            self._parse_price_name_discount()
            self._parse_details()
            self._parse_platforms()
            self._parse_image_url()
            is_valid = self.validate_model()
            if not is_valid:
                return False
            print(is_valid)
            return True
        except Exception as e:
            print("-------ОШИБКА ПРИ ДОБАВЛЕНИИ ИЗДАНИЯ-------")
            print(self.game_name)
            print(e)
            return False
    def _parse_discount_ends(self):
        self.discount_ends = self.edition_element.select_one('span[class="psw-c-t-2"]').text


    def _parse_price_name_discount(self):
        btn = self.edition_element.select_one("div.psw-l-line-left.psw-hidden button.psw-fill-x.dtm-track.psw-button.psw-b-0.psw-t-button.psw-l-line-center.psw-button-sizing.psw-button-sizing--medium.psw-purchase-button.psw-solid-button")
        product = btn.get("data-telemetry-meta")
        self._parse_price(product)


    def _parse_details(self):
        details = []
        for detail in  self.edition_element.select("ul li"):
            details.append(detail.text)
        self.details = details
        print(details)

    def _parse_platforms(self):
        platforms = []
        for platform in self.edition_element.select("span.psw-p-x-2.psw-p-y-1.psw-t-tag"):
            platforms.append(platform.text)
        self.platforms = platforms
        print(self.platforms)

    def _parse_image_url(self):
        try:
            self.picture_url = self.edition_element.select_one('img[class="psw-center psw-l-fit-contain"]').get("src")
            print(self.picture_url)
        except:
            print(self.edition_element.prettify())

    def validate_model(self):
        try:
            self.model = EditionModel(
                game_id=self.game_id,
                name=self.name,
                currency=self.currency,
                price=self.price,
                discount_available=self.discount_available,
                discount_price=self.discount_price,
                discount_percentage=self.discount_percentage,
                discount_ends=self.discount_ends,
                details=self.details,
                picture_url=self.picture_url,
                platforms=self.platforms,
            )
            return json.dumps(self.model.model_dump(), indent=4)
        except ValidationError:
            return False

    def _parse_price(self, data):
        data_product_json = loads(data)

        data_product_detail_json = data_product_json['productDetail'][0]
        name = data_product_detail_json['productName']

        self.name = name

        i = 0
        for product in data_product_detail_json['productPriceDetail']:
            if product['originalPriceValue'] != 0 and product['discountPriceValue'] != 0:
                self.currency = product["priceCurrencyCode"]
                self.price = (product['originalPriceValue'] / 100) * self.rates[self.currency]
                self.discount_price = (product['discountPriceValue'] / 100) * self.rates[self.currency]
                if self.discount_price != self.price:
                    self.discount_available = True
                    self.discount_percentage = int(((self.price - self.discount_price) / self.price) * 100)
                    self._parse_discount_ends()
                    break
            i += 1

    def insert_to_db(self):
        collection = editions_collection
        if self.currency == "TRY":
            collection = editions_collection_tr
        collection.insert_one(self.model.model_dump())

