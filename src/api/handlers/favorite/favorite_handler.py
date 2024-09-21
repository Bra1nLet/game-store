from http import HTTPStatus
from bson import ObjectId
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from pydantic import BaseModel, Field
from src.db.db import users_favorite_list
from src.api.models.favorite_list import UsersFavoriteList, UsersFavoriteGame


info = Info(title='Wishlist api', version='1.0.0')
favorite_list_tag = Tag(name="wishlist", description="Wishlist endpoints")
favorite_list_api = APIBlueprint('Wishlist', __name__)


class RequestTgPath(BaseModel):
    tg_user_id: int = Field(...)


class RequestWishlist(BaseModel):
    tg_user_id: int = Field(...)
    favorite_game_bid: str = Field(...)


@favorite_list_api.get(
    "/user/wishlist/<int:tg_user_id>",
    summary="get all users wishlist",
    tags=[favorite_list_tag]
)
def get_users_wishlist(path: RequestTgPath):
    users_favorite_games = users_favorite_list.find(
        {"tg_user_id": path.tg_user_id})
    if users_favorite_games:
        return UsersFavoriteList(games=list(users_favorite_games)).model_dump(), HTTPStatus.OK
    return {"message": "User not found"}, HTTPStatus.NOT_FOUND


@favorite_list_api.post(
    "/user/wishlist",
    summary="add game to wishlist",
    tags=[favorite_list_tag]
)
def add_game_to_wishlist(body: UsersFavoriteGame):
    user_subscribe = users_favorite_list.insert_one(body.model_dump())
    new_game = users_favorite_list.find_one({"_id": user_subscribe.inserted_id})
    if new_game:
        return UsersFavoriteGame.model_validate(new_game).model_dump(), HTTPStatus.OK
    # return {"message": "Game already added"}, HTTPStatus.NOT_FOUND


@favorite_list_api.delete(
    "/user/wishlist",
    summary="delete game from wishlist",
    tags=[favorite_list_tag]
)
def remove_game_from_wishlist(body: RequestWishlist):
    wishlist = users_favorite_list.delete_one({"_id": ObjectId(body.favorite_game_bid),
                                                        "tg_user_id": body.tg_user_id})
    if wishlist.deleted_count:
        return {"message": "Game deleted from wishlist"}, HTTPStatus.OK
    return {"message": "Not found game to delete"}, HTTPStatus.NOT_FOUND
