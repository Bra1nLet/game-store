from pymongo import MongoClient
from sympy.physics.units import percents

from src.db.db import main_page_game_section, main_page_games


# client_prod = MongoClient(
#     'mongodb+srv://arhipov744:Joy.Fp.10!@serverlessinstance0.rjo7kf1.mongodb.net/?retryWrites=true&w=majority&appName=ServerlessInstance0',
# )

main_page_game_section.drop()
with open("/src/migrations/innitial_data/game-categories", "r") as file:
    data = file.read()
    for line in data.split("\n"):
        main_page_game_section.insert_one({
            "name": line,
        })
print(list(main_page_game_section.find({})))

# print(SubscribeCategoryList(categories=subscribe_categories_collection.find({})).model_dump())

