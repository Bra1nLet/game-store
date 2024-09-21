from pymongo import MongoClient
from sympy.physics.units import percents

from src.db.db import subscribe_categories_collection, subscribes_collection
from src.api.models.subscribe import SubscribeModel, SubscribeCategoryList

# client_prod = MongoClient(
#     'mongodb+srv://arhipov744:Joy.Fp.10!@serverlessinstance0.rjo7kf1.mongodb.net/?retryWrites=true&w=majority&appName=ServerlessInstance0',
# )

# subscribes_collection.drop()
with open("/src/migrations/innitial_data/subscribe-categories", "r") as file:
    data = file.read()
    for line in data.split("\n"):
        line = line.split("|")
        subscribes_collection.insert_one({
            "category": line[0],
            "title": line[1],
            "price": line[2],
            "oldPrice": line[3],
            "image": line[4]
        })
print(list(subscribes_collection.find({})))

# print(SubscribeCategoryList(categories=subscribe_categories_collection.find({})).model_dump())

