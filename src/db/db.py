from pymongo import MongoClient
from src.api.models.game import GameModel



db = MongoClient('mongodb://root:example@localhost:27017/')
games_collection = db['games'].get_collection("games_")
games_collection_tr = db['games'].get_collection("games_tr")
editions_collection = db['games'].get_collection("editions")
editions_collection_tr = db['games'].get_collection("editions_tr")

game_collection_converted = db['games'].get_collection("games_converted")
game_collection_converted_ua = db['games'].get_collection("games_converted_uah")
game_collection_converted_tr = db['games'].get_collection("games_converted_tr")
subscribes_collection = db['games'].get_collection("subscribes")
subscribe_categories_collection = db['games'].get_collection("subscribes_categories")
games_categories_collection = db['games'].get_collection("games_categories")

users_favorite_list = db['games'].get_collection("users_favorite_list")

main_page_game_section = db['games'].get_collection("game_main_section")
main_page_games = db['games'].get_collection("game_main_section")
main_page_banners = db['games'].get_collection("main_page_banners")

users_collection = db['users'].get_collection("users")
users_subscribes_collection = db['users'].get_collection("users_subscribes")
basket_collection = db['users'].get_collection("basket")
purchase_collection = db['users'].get_collection("users_purchases")


# prod_collection = db_prod["games"].get_collection("games_converted_uah")
# # data =  list(game_collection_converted_ua.find({}))
# print(list(prod_collection.find({})))