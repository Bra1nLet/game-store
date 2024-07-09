from pymongo import MongoClient
# Sample of collection "game"
'''
game = {
    "game_url": "",
    "name": "",
    "image_url": "",    
    "rating": "4.3",
    "age_limit": "13+",
    "editions": [
        {"edition_name": "", "edition_picture":"./", edition_platforms: "", edition_details: [], "price": ""},
        {"edition_name": "", "edition_picture":"./", edition_platforms: "", edition_details: [], "price": ""},
        {"edition_name": "", "edition_picture":"./", edition_platforms: "", edition_details: [], "price": ""},
    ],
    "details": {
        "publisher": "",
        "release": "4.10.2017",    
    },
    "genres": ["Боевики", "Приключения"],
    "trailer_url": [None | str],
}
'''
db = MongoClient('mongodb://root:example@localhost:27017/')


class GamesCollection:
    def __init__(self):
        self.collection = db['games'].get_collection('games')

    def find_by_name(self, game_name):
        return self.collection.find_one({'name': game_name})

    def update_game(self, game, data):
        self.collection.update_one(game, {'$set': data})


games_collection = GamesCollection()
