from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from pydantic import BaseModel
from src.api.models.game_main import GameSectionList, BannersList
from src.db.db import main_page_game_section, main_page_banners

info = Info(title='Games on main page API', version='1.0.0')
game_main_tag = Tag(name="main page games ", description="Games main page endpoints")
game_main_api = APIBlueprint('games on main page', __name__)


class GetGamesMainQuery(BaseModel):
    section_id: str

@game_main_api.get("/main-page/games", summary="get games sections", tags=[game_main_tag])
def get_main_page_games():
    """
    get games section list
    """
    return  GameSectionList(sections=main_page_game_section.find({})).model_dump()


@game_main_api.get("/main-page/banners", summary="get banners", tags=[game_main_tag])
def get_main_page_banners():
    """
    get banners
    """
    return  BannersList(banners=main_page_banners.find({})).model_dump()

