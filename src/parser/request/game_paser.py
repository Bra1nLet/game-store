import json
import traceback
from  requests.exceptions import ConnectionError
from pydantic import ValidationError
from requests import request
from bs4 import BeautifulSoup
from json import loads
from src.api.models.new_game_model import Game
from src.db.db import games_collection, games_collection_tr, editions_collection, editions_collection_tr
from src.parser.request.edition_parser import EditionParser
from bson import ObjectId

class GameParser:
    def __init__(self, game_url: str, name: str, image_url: str, rates: dict, proxy: str = None):
        self.original_url = "https://store.playstation.com/"
        self.game_url = game_url
        self.rates = rates
        self.model = None
        self.proxy = proxy
        self.game_id = None

        self.name = name
        self.price = None
        self.currency = None
        self.discount_available = False
        self.discount_price = None
        self.discount_percentage = None
        self.image_url = image_url
        self.discount_ends = None
        self._details = None
        self.rating = None
        while True:
            try:
                r = request("get", self.original_url + game_url, proxies=proxy)
                break
            except ConnectionError:
                print("CONNECTION ERROR !!")
                print("TRY AGAIN", self.name)

        self.soup = BeautifulSoup(r.text, "html.parser")
        if r.status_code == 200:
            try:
                self._parse_data_top()
                self._parse_details()
            except Exception as e:
                print(traceback.print_exception(e))
                print("---------------------------------------")
                print("ОШИБКА ПРИ ДОБАВЛЕНИИ ИГРЫ:", self.name)
                print(self.original_url + self.game_url)
                print("---------------------------------------")
        else:
            print("КОД ОШИБКИ:", r.status_code)

    def _parse_data_top(self):
        data_header = self.soup.select_one("div.pdp-cta")

        if not self.rating:
            rating = self.soup.select_one('.pdp-game-title div[data-qa="mfe-game-title#average-rating"]')
            if not rating:
                print("EXIT BECAUSE THERE IS NOT RATING")
                return
            self.rating = rating.text
        btn = data_header.select_one('button.psw-fill-x.dtm-track.psw-button.psw-b-0.psw-t-button.psw-l-line-center.psw-button-sizing.psw-button-sizing--medium.psw-purchase-button.psw-solid-button')
        data = loads(btn.get('data-telemetry-meta'))
        i = 0
        for product in data['productDetail'][0]['productPriceDetail']:
            if product['originalPriceValue'] != 0 and product['discountPriceValue'] != 0:
                self.currency = product["priceCurrencyCode"]
                self.price = (product['originalPriceValue'] / 100) * self.rates[self.currency]
                self.discount_price = (product['discountPriceValue'] / 100) * self.rates[self.currency]
                if self.discount_price != self.price:
                    self.discount_available = True
                    self.discount_percentage = int(((self.price - self.discount_price) / self.price) * 100)
                    self.discount_ends = data_header.select_one(f'span.psw-c-t-2[data-qa="mfeCtaMain#offer{str(i)}#discountDescriptor"]').text
                    break
            i += 1

    def _parse_details(self):
        indexes = self.soup.select("dl dt")
        values = self.soup.select("dl dd")
        result = {}
        for i in range(len(indexes)):
            result.update({str(indexes[i].text): str(values[i].text)})
        self._details = result

    def get_game(self):
        try:
            gm = Game(
                name=self.name,
                image_url=self.image_url,
                currency=self.currency,

                price=self.price,

                discount_available=self.discount_available,
                discount_price=self.discount_price,
                discount_percentage=self.discount_percentage,
                discount_ends=self.discount_ends,

                details=self._details,
                rating=self.rating
            )
            self.model = gm.model_dump()
            return json.dumps(gm.model_dump(), indent=4)
        except ValidationError as e:
            print(f"----------------------{self.name} НЕ ПРОШЕЛ ВАЛИДАЦИЮ----------------------")
            print(self.original_url + self.game_url)
            print(self.currency)
            print(self.price)
            print(f"---------------------------------------------------------------------------")
            return False

    def insert_game_to_db(self, collection=games_collection):
        update = collection.find_one_and_update({"image_url": self.image_url}, {"$set": self.model})
        if not update:
            inserted = collection.insert_one(self.model)
            self.game_id = inserted.inserted_id
            print("ДОБАВЛЕНА ИГРА")
        else:
            self.game_id = update.get("_id")
            print("ОБНОВЛЕНА ЗАПИСЬ ОБ ИГРЕ")

    def parse_editions(self):
        editions = self.soup.select('article[class]')
        if editions:
            self._clear_edition_records()
        for edition in editions:
            ep = EditionParser(self.name, edition, self.game_id, self.currency, self.rates)
            if ep.parse_edition():
                ep.insert_to_db()

    def parse_tr_game(self):
        print("ПАРСИНГ ТУРЕЦКОЙ ВЕРСИИ ИГРЫ")
        parse_url = self.original_url + self.game_url.replace("ru-ua", "en-tr")
        while True:
            try:
                r = request("get", parse_url, proxies=self.proxy)
                break
            except ConnectionError:
                print("CONNECTION ERROR !!")
                print("TRY AGAIN", self.name)

        if r.status_code == 200:
            try:
                self.soup = BeautifulSoup(r.text, "html.parser")
                if not self.soup.select_one("main.page-not-found.psw-fill-x"):
                    self._parse_data_top()
                    self.get_game()
                    self.insert_game_to_db(games_collection_tr)
                    self.parse_editions()
                else:
                    print(f"ТУРЕЦКАЯ ВЕРСИЯ ИГРЫ {self.name} НЕ НАЙДЕНА")
            except Exception as e:
                print("----------------------------------------------------")
                print(e)
                print("ОШИБКА ДОБАВЛЕНИЯ ТУРЕЦКОЙ ВЕРСИИ ИГРЫ:" + self.name)
                print(self.game_url)
                # self.soup = BeautifulSoup(r.text, "html.parser")
                # print(self.soup.prettify())
                print("----------------------------------------------------")
        else:
            print("КОД ЗАПРОСА НЕ ВЕРНЫЙ", r.status_code)


    def _clear_edition_records(self):
        collection = editions_collection
        if self.currency == "TRY":
            collection = editions_collection_tr
        collection.delete_many({"_id": ObjectId(self.game_id)})


# gp = GameParser("ru-ua/product/EP4108-CUSA24124_00-NINJAGAIDENMCDX1", "GOD of WAR", "image url", {"UAH": 2, "TRY": 2})
# print(gp.get_game())
# gp.parse_editions()