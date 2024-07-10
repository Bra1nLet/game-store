from typing import List
from pydantic import BaseModel
from pymongo import MongoClient
from src.db.models.game_model import GameModel

db = MongoClient('mongodb://root:example@localhost:27017/')
game_collection = db['games'].get_collection("games")


class GameCollection(BaseModel):
    """
    A container holding a list of `GameModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability]
    """
    games: List[GameModel]


def insert_game(game: GameModel):
    """
    Insert a game record to db.
    :return:
    """
    game_collection.insert_one(
        game.model_dump(by_alias=True)
    )
