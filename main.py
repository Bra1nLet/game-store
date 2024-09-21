import time
from playwright.sync_api import sync_playwright, Playwright
from src.mparser.currency_handler.currency_handler import get_rates
from src.mparser.parser.main_page import MainPageParser
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
universe_size=comm.Get_attr(MPI.UNIVERSE_SIZE)

PROXYS = {
    0: {"server": "socks4://147.78.183.38:1085"},
    1: {"server": "socks4://217.145.227.217:1085"},
    2: {"server": "socks4://147.78.183.149:1085"} ,
    3: {"server": "socks4://217.145.227.191:1085"},
    4: {"server": "socks4://147.78.183.124:1085"} ,
    5: {"server": "socks4://147.78.183.230:1085"} ,
}

CHECK_PAGES = {
    "UAH": "",
    "TRY": ""
}

def run(pw: Playwright, total_pages):
    browser = pw.chromium.launch(headless=False, proxy=PROXYS[rank])
    ctx = browser.new_context()
    page = ctx.new_page()
    for currency in rates:
        start_page = rank * (total_pages[currency] // 6)
        end_page = rank * (total_pages[currency] // 6) + 1
        if rank == 6:
            end_page = total_pages[currency]

        mp = MainPageParser(ctx, page, currency, rates[currency])
        while start_page <= end_page:
            try:
                mp.next_page(start_page)
                time.sleep(3)
                mp.collect_all_games_info()
                start_page += 1
            except Exception as e:
                print("--------ERROR---------")
                print("On Page:", start_page)
                print(f"Thread #{rank}")
                print("Error:", e)
                print("----------------------")
    browser.close()


def get_total_pages(pw: Playwright):
    browser = pw.chromium.launch(headless=False, proxy=PROXYS[rank])
    ctx = browser.new_context()
    page = ctx.new_page()
    pages = []
    for currency in CHECK_PAGES:
        mp = MainPageParser(ctx, page, currency, CHECK_PAGES[currency])
        mp.next_page(0)
        pages.append(mp.get_total_pages())
    browser.close()
    return pages

if rank == 0:
    uah_rate, try_rate = get_rates()
    with sync_playwright() as playwright:
        data = get_total_pages(playwright)
    try_pages = data[1]
    uah_pages = data[0]

    for i in range(1, universe_size):
        comm.isend(uah_rate, dest=i, tag=10 + i)
        comm.isend(try_rate, dest=i, tag=20 + i)
        comm.isend(uah_pages, dest=i, tag=30 + i)
        comm.isend(try_pages, dest=i, tag=40 + i)

else:
    uah_rate, try_rate = comm.recv(source=0, tag=10 + rank), comm.recv(source=0, tag=20 + rank)
    uah_pages, try_pages = comm.recv(source=0, tag=30 + rank), comm.recv(source=0, tag=40 + rank)


rates = {
    "UAH": uah_rate,
    "TRY": try_rate,
}

total_pages = {
    "UAH": uah_pages,
    "TRY": try_pages,
}


with sync_playwright() as playwright:
    run(playwright, total_pages)
