from requests import request
from bs4 import BeautifulSoup
from src.parser.request.game_paser import GameParser

class GameBrowseParser:
    def __init__(self, page, rates=None, proxy=None):
        self.url = f'https://store.playstation.com/ru-ua/pages/browse/'
        self.proxy = proxy
        self.rates = rates
        self.soup = BeautifulSoup()
        self.game = BeautifulSoup()
        self.page = page
        self.goto_page(page)

    def parse_games(self):
        games = self.soup.select('div[class="psw-l-w-1/1"] li[class]')
        for game in games:
            self.game = game
            gp = GameParser(self._get_game_url(), self._get_name(), self._get_image_url(), self.rates, self.proxy)
            game = gp.get_game()
            if game:
                gp.insert_game_to_db()
                gp.parse_editions()
                gp.parse_tr_game()

    def goto_page(self, page):
        self.page = page
        r = request("get", self.url + str(page))
        self.soup = BeautifulSoup(r.text, "html.parser")

    def _get_name(self):
        return self.game.select_one('span.psw-t-body.psw-c-t-1.psw-t-truncate-2.psw-m-b-2').text

    def _get_image_url(self):
        return self.game.select_one('img:not([aria-hidden])').get('src')

    def _get_game_url(self):
        return self.game.select_one('a[href]').get('href')

    def get_total_pages(self):
        return int(self.soup.select('div[class="psw-l-w-1/1"] li')[-1].text)
