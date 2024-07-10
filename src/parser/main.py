import asyncio
from pyppeteer import launch
from pyppeteer.page import Page
from src.parser.parsers.main_page_parser import MainPageParser
from src.db.games import game_collection
from src.parser.parsers.detail_parse_game import DetailGameParser


async def main():
    browser = await launch()
    page = await browser.newPage()
    # mp = MainPageParser(page)
    # await mp.goto_games()
    # await mp.parse_games()
    await collect_detail_information(page)
    await browser.close()


async def collect_detail_information(page: Page):
    games = list(game_collection.find({}))
    for game in games:
        await page.goto(game['game_url'])
        print(game['name'], type(game['name']))
        detail_game_parser = DetailGameParser(page, str(game['name']))
        await detail_game_parser.collect_data()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
