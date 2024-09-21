from bson import ObjectId
from src.db.db import game_collection, db, subscribes_collection, game_collection_converted_ua, game_collection_converted_tr
# subscribes_collection.drop()
#
# save = db['save_games'].get_collection("games")
# save_full_ua = db['save_games'].get_collection("full_ua_games")
#
# game_collection_ua_tr = db['games'].get_collection("ua_tr")
#
#
# def save_to_db():
#     for game in game_collection.find({}):
#         save_full_ua.insert_one(game)
#
#
# games_list = list(game_collection.find({"price.TL": {"$exists": True}, "price.UAH": {"$exists": True}}))
# # save_to_db()
#
# for game in game_collection_ua_tr.find({}):
#     print(game)
# #
# game_collection_converted_ua.drop()
# game_collection_converted_tr.drop()
for i in game_collection_converted_tr.find({}):
    print(i)
print(len(list(game_collection_converted_ua.find({}))))