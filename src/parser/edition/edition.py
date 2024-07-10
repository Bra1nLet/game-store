from pyppeteer.element_handle import ElementHandle
from src.parser.selectors.game_page.selector import game_page_selectors
from src.db.models.game_model import EditionModel


async def get_element_property(prop: str, selector=None, element=None):
    if element and selector:
        element = await element.querySelector(selector)
    if element:
        data = await (await element.getProperty(prop)).jsonValue()
        return data


class Edition:
    def __init__(self, edition_element: ElementHandle, game_name: str, _id: int):
        self.edition = edition_element
        self.game_name = game_name
        self._id = _id

    async def get_edition(self) -> EditionModel:
        edition_name = await get_element_property('innerText', game_page_selectors.edition_name, self.edition)
        return EditionModel(
            name=edition_name,
            price=await get_element_property('innerText', game_page_selectors.edition_price, self.edition),
            edition_details=await self.get_details(),
            edition_picture=await self.get_edition_picture(edition_name, self._id),
            edition_platforms=await get_element_property('innerText',
                                                         game_page_selectors.edition_platforms,
                                                         self.edition)
        )

    async def get_edition_picture(self, edition_name: str, _id: int):
        selector = game_page_selectors.edition_picture
        element = await self.edition.querySelector(selector)
        path = f"./pictures/{self.game_name}_{edition_name}_{_id}.png"
        await element.screenshot({'path': path})
        if _id == 0:
            await element.screenshot({'path': path})
        return path

    async def get_details(self) -> list:
        result = []
        details = await self.edition.querySelectorAll(game_page_selectors.edition_detail)
        if details:
            for detail in details:
                result.append(await get_element_property('innerText', element=detail))
        return result
