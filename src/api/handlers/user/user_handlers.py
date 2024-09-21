from http import HTTPStatus
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from src.api.models.usersmodel import UsersModel, UsersListModel, UserSubscribes, UpdateUserModel
from src.db.db import users_collection, users_subscribes_collection
from src.api.handlers.user.user_subscribes import subscribes_api

info = Info(title='User api', version='1.0.0')
user_tag = Tag(name="user", description="User endpoints")
user_api = APIBlueprint('user', __name__)
user_api.register_api(subscribes_api)


class TgUserIdRequest(BaseModel):
    tg_user_id: int = Field()


@user_api.get("/users", summary="Get user list", tags=[user_tag])
def get_users():
    return UsersListModel.model_validate({"users": list(users_collection.find({}))}).model_dump()


@user_api.get("/user/<int:tg_user_id>", summary="Get user by tg id", tags=[user_tag])
def get_user(path: TgUserIdRequest):
    data = users_collection.find_one({"tg_user_id": path.tg_user_id}, {})
    if data:
        return UsersModel.model_validate(data).model_dump()
    return {"message": "Not found"}, 404


@user_api.post("/user", summary="Create user", tags=[user_tag])
def create_user(body: TgUserIdRequest):
    user = UsersModel(tg_user_id=body.tg_user_id)
    tg_user = users_collection.find_one({"tg_user_id": body.tg_user_id})
    subscribes = users_subscribes_collection.find_one({"tg_user_id": body.tg_user_id})
    if not (tg_user and subscribes):
        users_collection.insert_one(user.model_dump())
        return {"message": "User created"}, HTTPStatus.OK
    return {"message": "User already exists"}, HTTPStatus.CONFLICT


@user_api.put("/user/<int:tg_user_id>", summary="Update user", tags=[user_tag])
def update_user(path: TgUserIdRequest, body: UpdateUserModel):
    user = {
        k: v for k, v in body.model_dump(by_alias=True).items() if v is not None
    }
    if len(user) >= 1:
        update_result = users_collection.find_one_and_update(
            {"tg_user_id": path.tg_user_id},
            {"$set": user},
            return_document=ReturnDocument.AFTER,
        )
        if update_result:
            return UsersModel.model_validate(update_result).model_dump(), HTTPStatus.OK
        else:
            return {"message": "not found"}, HTTPStatus.NOT_FOUND
    if (existing_user := users_collection.find_one({"tg_user_id": path.tg_user_id})) is not None:
        return existing_user
    return {"message": "not found"}, HTTPStatus.NOT_FOUND


@user_api.delete("/user", summary="Delete user", tags=[user_tag])
def delete_user(body: TgUserIdRequest):
    result = users_collection.delete_one({"tg_user_id": body.tg_user_id})
    users_subscribes_collection.delete_many({"tg_user_id": body.tg_user_id})
    if result.deleted_count:
        return {"message": "User deleted"}, HTTPStatus.OK
    return {"message": "User doesn't exist"}, HTTPStatus.NOT_FOUND
