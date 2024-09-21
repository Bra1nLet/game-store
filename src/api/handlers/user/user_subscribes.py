import datetime
from http import HTTPStatus
from uuid import uuid1
from bson import ObjectId
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from src.api.models.basket_model import BasketModel
from src.api.models.usersmodel import UsersModel, UserSubscribe, UserSubscribes
from src.db.db import users_subscribes_collection, basket_collection

info = Info(title='Users subscribes api', version='1.0.0')
subscribes_tag = Tag(name="user subscribes", description="User subscribes endpoints")
subscribes_api = APIBlueprint('user subscribes', __name__)


class RequestTgPath(BaseModel):
    tg_user_id: int = Field(...)


class RequestDeleteSubscribe(BaseModel):
    tg_user_id: int = Field(...)
    subscribe_bid: str = Field(...)


@subscribes_api.get(
    "/user/subscribes/<int:tg_user_id>",
    summary="get all user subscribes purchase from basket",
    tags=[subscribes_tag]
)
def get_user_subscribes(path: RequestTgPath):
    user_subscribes = users_subscribes_collection.find(
        {"tg_user_id": path.tg_user_id})
    if user_subscribes:
        return UserSubscribes(subscribes=list(user_subscribes)).model_dump(), HTTPStatus.OK
    return {"message": "User not found"}, HTTPStatus.NOT_FOUND


@subscribes_api.post(
    "/user/subscribes",
    summary="add purchase to basket",
    tags=[subscribes_tag]
)
def add_user_subscribes(body: UserSubscribe):
    user_subscribe = users_subscribes_collection.insert_one(body.model_dump())
    new_subscribe = users_subscribes_collection.find_one({"_id": user_subscribe.inserted_id})
    if new_subscribe:
        return UserSubscribe.model_validate(new_subscribe).model_dump(), HTTPStatus.OK
    return {"message": "User already exists"}, HTTPStatus.NOT_FOUND


@subscribes_api.delete(
    "/user/subscribes",
    summary="delete purchase from basket",
    tags=[subscribes_tag]
)
def delete_user_subscribes(body: RequestDeleteSubscribe):
    subscribe = users_subscribes_collection.delete_one({"_id": ObjectId(body.subscribe_bid),
                                                        "tg_user_id": body.tg_user_id})
    if subscribe.deleted_count:
        return {"message": "Subscribe deleted"}, HTTPStatus.OK
    return {"message": "Not found"}, HTTPStatus.NOT_FOUND
