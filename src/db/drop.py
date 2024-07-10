from games import game_collection
# db.drop_database('games')
games = game_collection.find({})

for game in games:
    print(game)
