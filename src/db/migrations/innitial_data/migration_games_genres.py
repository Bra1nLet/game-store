from src.db.db import games_categories_collection


games_categories_collection.drop()
with open("raw_data/all_games_generes", "r") as file:
    data = file.read()
    for line in data.split("\n"):
        games_categories_collection.insert_one({
            "name": line,
        })
print(list(games_categories_collection.find({})))


