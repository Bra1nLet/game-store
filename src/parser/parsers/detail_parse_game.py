import asyncio

from pyppeteer.page import Page
from src.db.games import games_collection
from src.parser.selectors.game_page.selector import game_page_selectors
from src.parser.edition.edition import Edition


class DetailGameParser:
    def __init__(self, page: Page, game_name: str):
        self.game = games_collection.find_by_name(game_name)
        self.game_name = game_name
        self.page = page

    async def collect_data(self):
        print("collecting information about:", self.game_name)
        print(self.game)
        btn_text = await self.get_element_property('innerHTML', selector=game_page_selectors.buy_btn)
        if btn_text in ["Pre-Order", 'Предварительный заказ']:
            data = {
                "age_limit": await self.get_element_property('alt', selector=game_page_selectors.age_limit),
                "details": await self.get_details()
            }
        else:
            data = {
                "editions": await self.get_editions(),
                "age_limit": await self.get_element_property('alt', selector=game_page_selectors.age_limit),
                "rating": await self.get_element_property('innerText', selector=game_page_selectors.rating),
                "details": await self.get_details()
            }
        print(data)
        print("----------------")
        if data != {}:
            games_collection.update_game(self.game, data)

    async def get_editions(self) -> list:
        await asyncio.sleep(5)
        editions_elements = await self.page.querySelectorAll(game_page_selectors.editions)
        editions = []
        if editions_elements:
            for i in range(len(editions_elements)):
                edition = Edition(editions_elements[i], self.game_name, i)
                editions.append(await edition.get_edition())
        return editions

    async def get_details(self) -> dict:
        details = {}
        details_labels = await self.page.querySelectorAll(game_page_selectors.game_details_labels)
        details_data = await self.page.querySelectorAll(game_page_selectors.game_details_information)
        print("details and labels:")
        print(details_labels)
        print(details_data)
        for i in range(0, len(details_labels)):
            detail_label = await self.get_element_property('innerText', element=details_labels[i])
            detail_data = await self.get_element_property('innerText', element=details_data[i])
            print("detail_label and detail data:")
            print(detail_label, detail_data)
            details[detail_label] = detail_data
        return details

    async def get_element_property(self, prop: str, selector=None, element=None):
        if element and selector:
            element = await element.querySelector(selector)
        elif selector:
            element = await self.page.querySelector(selector)
        if element:
            data = await (await element.getProperty(prop)).jsonValue()
            return data
