from src.parser.request.game_browse_parser import GameBrowseParser
from src.parser.currency_handler.currency_handler import get_rates
from mpi4py import MPI
from src.config import PROXY_LIST


comm = MPI.COMM_WORLD
TOTAL_THREADS = comm.Get_size()
THREAD = comm.Get_rank()
uah_rate = None
try_rate = None
total_pages = None

if THREAD == 0:
    uah_rate, try_rate = get_rates()
    gbp = GameBrowseParser(0)
    total_pages = gbp.get_total_pages()
    if TOTAL_THREADS > 1:
        for i in range(1, TOTAL_THREADS):
            comm.isend(uah_rate, dest=i, tag=10 + i)
            comm.isend(try_rate, dest=i, tag=20 + i)
            comm.isend(total_pages, dest=i, tag=30 + i)
else:
    uah_rate, try_rate = comm.recv(source=0, tag=10 + THREAD), comm.recv(source=0, tag=20 + THREAD)
    total_pages = comm.recv(source=0, tag=30 + THREAD)

RATES = {
    "UAH": uah_rate,
    "TRY": try_rate,
}

PROXYS = {}

for i in range(len(PROXY_LIST)):
    PROXYS[i] = {
        'http': PROXY_LIST[i],
        'https': PROXY_LIST[i]
    }

quota = total_pages // TOTAL_THREADS
start_page = quota * THREAD + 1


if THREAD + 1 != TOTAL_THREADS:
    end_page = quota * THREAD + quota
else:
    end_page = total_pages

gbp = GameBrowseParser(start_page, RATES, proxy=PROXYS[THREAD])
for i in range(start_page, end_page + 1):
    gbp.goto_page(i)
    gbp.parse_games()
