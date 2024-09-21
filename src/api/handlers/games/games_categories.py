from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from src.api.models.game_categories import GameCategoriesList
from src.db.db import games_categories_collection


info = Info(title='Games categories API', version='1.0.0')
game_category_tag = Tag(name="games categories", description="Games categories endpoints")
game_categories_api = APIBlueprint('games categories', __name__)


@game_categories_api.get("/game-categories", summary="get game categories", tags=[game_category_tag])
def get_subscribe_categories():
    """
    get subscribe categories
    """
    return  GameCategoriesList(categories=games_categories_collection.find({})).model_dump()
