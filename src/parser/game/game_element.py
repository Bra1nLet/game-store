from pyppeteer.element_handle import ElementHandle
from src.parser.selectors.main_page.selector import main_page_selector
from src.parser.selectors.main_page.tags import main_page_tags


class GameElement:
    def __init__(self, game: ElementHandle):
        self.game_element = game

    async def get_game_data(self):
        return {
            "name": await self.get_name(),
            "image_url": await self.get_img_url(),
            "price": await self.get_price()
        }

    async def get_img_url(self):
        return await self.get_property_text(main_page_tags.game_image_url, 'src')

    async def get_price(self):
        return await self.get_property_text(main_page_tags.game_price, 'innerText')

    async def get_name(self):
        return await self.get_property_text(main_page_tags.game_name, 'innerText')

    async def get_property_text(self, tag: str, prop: str):
        selector = main_page_selector.get_selector_by_tag(tag)
        element = await self.game_element.querySelector(selector)
        return await (await element.getProperty(prop)).jsonValue()
