from src.mparser.selectors.main_page_selectors import main_page_selectors
from playwright.sync_api._generated import Page, BrowserContext
from src.mparser.parser.initial_game_parser import InitialGamePageParser

class MainPageParser:
    def __init__(self, context: BrowserContext, page: Page, currency, currency_multiplier):
        self.currency = currency
        self._context = context
        self.page = page
        self.currency_multiplier = currency_multiplier
        self.initial_url = self._get_url()
        self.market_url = None

    def collect_all_games_info(self):
        elements = self.page.query_selector_all(main_page_selectors.all_games)
        for i in range(len(elements)):
            parser = InitialGamePageParser(self._context, i, elements[i], self.currency, self.currency_multiplier)
            if self.currency == "UAH":
                parser.collect_initial_data()
            elif self.currency == "TRY":
                parser.collect_tr_data()

    def get_total_pages(self):
        data = self.page.query_selector_all(main_page_selectors.total_pages)
        if data:
            return int(data[-1].inner_text())

    def next_page(self, page):
        self.page.goto(self.initial_url+f"/{page}")

    def _get_url(self):
        if self.currency == "UAH":
            return "https://store.playstation.com/ru-ua/pages/browse"
        elif self.currency == "TRY":
            return "https://store.playstation.com/en-tr/pages/browse"
