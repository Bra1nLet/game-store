import asyncio
from pyppeteer import launch
from src.parser.parsers.main_page_parser import MainPageParser


async def main():
    browser = await launch()
    page = await browser.newPage()
    mp = MainPageParser(page)
    await mp.goto_games()
    await mp.parse_games()
    await browser.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
