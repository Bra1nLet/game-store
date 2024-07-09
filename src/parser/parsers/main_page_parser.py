import asyncio
from pyppeteer.element_handle import ElementHandle
from pyppeteer.page import Page
from src.parser.selectors.main_page.selector import main_page_selector
from src.parser.selectors.main_page.tags import main_page_tags
from src.parser.game.game_element import GameElement
from src.db.games import games_collection


class MainPageParser:
    def __init__(self, page: Page):
        self.page = page

    async def goto_games(self):
        await self.page.goto('https://store.playstation.com/ru-ua/pages/latest')
        selector = main_page_selector.get_selector_by_tag(main_page_tags.store)
        await self.page.waitForSelector(selector)
        element = await self.page.querySelector(selector)
        if element:
            await self.page.click(selector)
            ps4_btn = main_page_selector.get_selector_by_tag(main_page_tags.ps4_btn)
            await self.page.waitForSelector(ps4_btn)
            go_btn = await self.page.querySelector(ps4_btn)
            link = await self.get_link(go_btn)
            await self.page.goto(link)
            await self.page.screenshot({'path': 'example2.png'})

    async def parse_games(self):
        current_url = self.page.url
        page_number = 1
        all_games_selector = main_page_selector.get_selector_by_tag(main_page_tags.games)
        total_pages_selector = main_page_selector.get_selector_by_tag(main_page_tags.page_number)
        total_pages_element = (await self.page.querySelectorAll(total_pages_selector))[-1]
        total_pages = int(await self.get_text(total_pages_element))
        while page_number <= total_pages:
            elements = await self.page.querySelectorAll(all_games_selector)
            for element in elements:
                collection_length = len(list(games_collection.collection.find({})))
                print(collection_length)
                if collection_length == 100:
                    print("finish", collection_length)
                    for i in list(games_collection.collection.find({})):
                        print(i)
                    return
                game_element = GameElement(element)
                data = await game_element.get_game_data()
                games_collection.collection.insert_one(data)
            page_number += 1
            await self.page.goto(current_url + f"/{page_number}")
            await asyncio.sleep(5)

    async def get_link(self, element: ElementHandle):
        return await (await element.getProperty('href')).jsonValue()

    async def get_text(self, element: ElementHandle) -> str:
        return str(await (await element.getProperty('innerText')).jsonValue())
