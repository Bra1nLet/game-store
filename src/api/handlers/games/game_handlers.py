from http import HTTPStatus
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from src.db.db import games_collection, games_collection_tr
from src.api.models.new_game_model import GamesList, Game
from flask import abort

info = Info(title='Ps game store API', version='1.0.0')
game_tag = Tag(name="game", description="Game endpoints")
game_api = APIBlueprint('games', __name__)


class RequestPath(BaseModel):
    id: str = Field(max_length=24, min_length=24)
    currency: str = Field(default="UAH")

class RequestQuery(BaseModel):
    name: str = Field(default=None)
    page: int = Field(default=0)
    platform: Optional[str] = Field(default=None)
    genres: Optional[List[Optional[str]]] = Field(default=None)
    currency: str = Field(default="UAH")
    min_price: int = Field(default=None)
    max_price: int = Field(default=None)
    with_discount: bool = Field(default=None)

@game_api.get("/game", summary="get game by id", tags=[game_tag])
def get_game_by_id(query: RequestPath):
    """
    get single game by id
    """
    collection = games_collection
    print(query.currency)
    if query.currency == "TRY":
        collection = games_collection_tr
    game = list(collection.find({"_id": ObjectId(query.id)}))
    if game:
        model = Game.model_validate(game[0])
        return model.model_dump()
    return abort(404)


@game_api.post("/games", summary="get game sequence", tags=[game_tag])
def get_game_sequence(body: RequestQuery):
    """
    get game page
    """
    print("REQUEST")
    print(body)
    search = {}
    collection = games_collection
    if body.currency == "TRY":
        collection = games_collection_tr
    if body.name:
        search = {"name": {"$regex": body.name, "$options": "i"}}
    if body.min_price and body.max_price:
        search.update({"price_rub": {"$gte": body.min_price, "$lte": body.max_price}})
    elif body.min_price:
        search.update({"price_rub": {"$gte": body.min_price}})
    elif body.max_price:
        search.update({"price_rub": {"$lte": body.max_price}})
    if body.with_discount:
        search.update({"discount_percentage": {"$ne": None}})
    if body.platform:
        search.update({"details.Платформа": {"$regex": body.platform, "$options": "i"}})
    if body.genres:
        options = []
        for genre in body.genres:
            options.append({"details.Жанры:": {"$regex": genre, "$options": "i"}})
        for i in range(len(options)):
            options[i].update(search)
        search = {"$or": options}
    games = list(collection.find(search).skip(30 * body.page).limit(30))
    gc = GamesList(games=games)
    return gc.model_dump(), HTTPStatus.OK

@game_api.get("/games", summary="get game sequence", tags=[game_tag])
def games():
    games = list(games_collection.find({}).skip(0).limit(30))
    print(games)
    gc = GamesList(games=games)
    return gc.model_dump(), HTTPStatus.OK