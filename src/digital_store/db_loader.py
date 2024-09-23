import traceback

from tgbot.services.database import PSGame, PSGameEdition, XBOXGame, XBOXGameEdition, ConsoleSubscription
from tgbot.data.loader import Session

import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet


def load_xbox():
    with Session() as db_session:
        all_games = db_session.query(XBOXGame).all()
        games = [(i._name, i.category) for i in all_games]
        cats_dict = {i[0]: i[1] for i in set((j.category, j.emoji) for j in all_games)}

        wb: Workbook = openpyxl.load_workbook('XBOX.xlsx')
        sheet: Worksheet = wb.active

        for line in sheet.values:
            if not line[1]:
                continue
            if not line[2]:
                break

            try:
                game_name = line[0].strip()
                category = line[1].strip()
                if (game_name, category) in games:
                    continue

                game = XBOXGame(name=game_name, category=category, emoji=cats_dict.get('category', ''))
                db_session.add(game)
                db_session.commit()

                for edition_str in line[2:]:
                    if not edition_str:
                        break

                    # print(edition_str.split('|'))
                    if edition_str.split('|')[0].strip() not in ['X/S'] or edition_str.split('|')[0].strip() == 'xbox':
                        platforms = ['all']
                        if edition_str[0:4] == 'xbox':
                            edition_str = edition_str[5:]
                        edition_name, description, pic, prices = edition_str.split('|')
                    else:
                        platform, edition_name, description, pic, prices = edition_str.split('|')
                        platforms = [platform]
                    price = int(prices.split(',')[1]) if ',' in prices else int(prices)
                    region = 'tr'

                    for platform in platforms:
                        edition = XBOXGameEdition(name=edition_name.strip(), platform=platform.strip(), pic=pic.strip(),
                                                  region=region,
                                                  game_id=game.id,
                                                  price=price, description=description.replace('\\n', '\n').strip())
                        db_session.add(edition)
                db_session.commit()
            except Exception as e:
                db_session.rollback()
                db_session.delete(game)
                db_session.commit()
                print(f'Игра {line} не добавлена из-за ошибки {e}')


def load_ps():
    with Session() as db_session:
        all_games = db_session.query(PSGame).all()
        games = [(i._name, i.category) for i in all_games]
        cats_dict = {i[0]: i[1] for i in set((j.category, j.emoji) for j in all_games)}

        wb: Workbook = openpyxl.load_workbook('PS.xlsx')

        sheet: Worksheet = wb.active

        for line in sheet.values:
            if not line[1]:
                continue
            if not line[2]:
                break
            try:
                game_name = line[0].strip()
                category = line[1].strip()
                print(game_name, category, (game_name, category) in games)
                if (game_name, category) in games:
                    continue

                game = PSGame(name=game_name, category=category, emoji=cats_dict.get('category', ''))
                db_session.add(game)
                db_session.commit()
                for edition_str in line[2:]:
                    if not edition_str:
                        break

                    # print(edition_str.split('|'))
                    if edition_str.split('|')[0].strip() not in ['ps4', 'ps5'] or edition_str.split('|')[
                        0].strip() == 'ps':
                        platforms = ['ps4', 'ps5']
                        if edition_str[0:2] == 'ps':
                            edition_str = edition_str[3:]
                        edition_name, description, pic, prices = edition_str.split('|')
                    else:
                        platform, edition_name, description, pic, prices = edition_str.split('|')
                        platforms = [platform]
                    prices = [int(i) for i in prices.split(',')]
                    regions = ['ua', 'tr']

                    for platform in platforms:
                        for i in [0, 1]:
                            if not prices[i]:
                                continue

                            edition = PSGameEdition(name=edition_name, platform=platform, pic=pic, region=regions[i],
                                                    game_id=game.id,
                                                    price=prices[i],
                                                    description=description.replace('\\n', '\n').replace('/n',
                                                                                                         '\n').strip())
                            db_session.add(edition)
                db_session.commit()
            except:
                db_session.rollback()
                db_session.delete(game)
                db_session.commit()
                traceback.print_exc()
                print(f'Игра {line} не добавлена из-за ошибки')


"""Турция

890 - Essential 1m
1390 - Extra 1m
1590 - Deluxe 1m

2260 - essential 3m
3590 - extra 3m
4090 - Deluxe 3m

6290 - essential 12m
10490 - extra 12m
11990 - deluxe 12m

Украина

930 - Essential 1m
1390 - Extra 1m
1590 - Deluxe 1m

2190 - essential 3m
3490 - extra 3m
3090 - Deluxe 3m

5490 - essential 12m
8590 - extra 12m
9590 - deluxe 12m"""

"""
На Essential

• Доступ к онлайну
• 3 случайные игры каждый месяц

Extra

• Доступ к онлайну
• Каталог из 400 бесплатных игр

Ознакомиться с подробным каталогом игр вы можете в интернете или в самой консоли в разделе «Ps Plus»

Deluxe 

• Доступ к онлайну
• Каталог из 700 бесплатных игр
• Возможность играть в новинки ограниченное количество времени

Ознакомиться с подробным каталогом игр вы можете в интернете или в самой консоли в разделе «Ps Plus»

Ea Play

•Доступ к списку игр EA Play совершенно бесплатно. Ознакомиться со списком можно в интернете

Gamepass Ultimate

Самый выгодный по соотношению цена/качество тариф в Microsoft Store

Вы получаете:
• Каталог игр EA Play совершенно бесплатно
• Доступ к сотни невероятных игр от Gamepass
• Доступ в онлайн
• Экономию по сравнению с приобретением других подписок той же самой Microsoft"""


def load_subscriptions():
    descriptions = {'⚪️ Essential': '• Доступ к онлайну\n• 3 случайные игры каждый месяц',
                    '🟡 Extra': '• Доступ к онлайну\n• Каталог из 400 бесплатных игр',
                    '⚫️ Deluxe': '• Доступ к онлайну\n• Каталог из 700 бесплатных игр\n• Возможность играть в новинки ограниченное количество времени',
                    '🔴 Ea Play': '•Доступ к списку игр EA Play совершенно бесплатно. Ознакомиться со списком можно в интернете',
                    'Gamepass Ultimate': 'Самый выгодный по соотношению цена/качество тариф в Microsoft Store\n\nВы получаете:\n• Каталог игр EA Play совершенно бесплатно\n• Доступ к сотни невероятных игр от Gamepass\n• Доступ в онлайн\n• Экономию по сравнению с приобретением других подписок той же самой Microsoft'
                    }

    with Session() as db_session:
        platform = 'ps'
        names = ['⚪️ Essential', '🟡 Extra', '⚫️ Deluxe', '🔴 Ea Play']
        durations = [1, 3, 12]
        prices = {'tr': [(890, 1390, 1590, 320), (2260, 3590, 4090), (6290, 10490, 11990, 1500)],
                  'ua': [(930, 1390, 1590, 600), (2190, 3490, 3090), (5490, 8590, 9590, 2800)]}

        for i, name in enumerate(names):
            for j, duration in enumerate(durations):
                for region in ['tr', 'ua']:
                    if i == 3:
                        if j == 1:
                            continue
                    price = prices[region][j][i]
                    subscription = ConsoleSubscription(name=name, platform=platform, region=region, duration=duration,
                                                       price=price, description=descriptions[name])
                    db_session.add(subscription)
        """13 месяцев - 3590₽
9 месяцев - 2790₽ 
5 месяцев - 1990₽
1 месяц - 790₽"""
        platform = 'xbox'
        name = 'Gamepass Ultimate'
        durations = [1, 3, 9, 13]
        prices = [790, 1990, 2790, 3590]
        for i, duration in enumerate(durations):
            subscription = ConsoleSubscription(name=name, platform=platform, duration=duration,
                                               price=prices[i], description=descriptions[name])
            db_session.add(subscription)
        db_session.commit()


load_ps()
load_xbox()
