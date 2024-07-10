from pydantic import BaseModel
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from src.db.games import game_collection, GameModel, GameCollection
from flask import abort

info = Info(title='Ps game store API', version='1.0.0')
game_tag = Tag(name="game", description="Game endpoints")

game_api = APIBlueprint('games', __name__)


class RequestQuery(BaseModel):
    name: str


class RequestGamesQuery(BaseModel):
    start: int
    end: int


@game_api.get("/game", summary="get game", tags=[game_tag])
def get_game(query: RequestQuery):
    """
    to get single game
    """
    game = list(game_collection.find({"name": query.name}))
    print(game)
    if game:
        model = GameModel.model_validate(game[0])
        return model.model_dump()
    return abort(404)


@game_api.get("/games", summary="get all games", tags=[game_tag])
def get_games():
    """
    to get single game
    """
    games = list(game_collection.find({}))
    if not games:
        return abort(404)

    models = []
    for game in games:
        models.append(GameModel.model_validate(game))
    gc = GameCollection(games=models)
    return gc.model_dump()


@game_api.get("/game-sequence", summary="get game sequence", tags=[game_tag])
def get_game_sequence(query: RequestGamesQuery):
    """
    to get game sequence
    """
    games = list(game_collection.find({}))

    models = []
    for game in games:
        models.append(GameModel.model_validate(game))
    if query.start < len(games):
        gc = GameCollection(games=models[query.start:query.end])
        return gc.model_dump()
    elif query.start < len(games) < query.end:
        gc = GameCollection(games=models[query.start:])
        return gc.model_dump()

    return abort(404)
