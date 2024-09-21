from http import HTTPStatus
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from src.api.models.basket_model import BasketModel, PurchaseModel
from src.api.models.new_game_model import PyObjectId, Game
from src.api.models.subscribe import SubscribeModel
from src.db.db import basket_collection, subscribes_collection, games_collection, games_collection_tr, \
    purchase_collection

info = Info(title='Basket API', version='1.0.0')
basket_tag = Tag(name="basket", description="Basket endpoints")
basket_api = APIBlueprint('basket', __name__)


class PurchaseRequest(BaseModel):
    purchase_id: Optional[PyObjectId] = Field(alias="_id", default=None)
    purchase_name: Optional[str] = Field(...)
    purchase_type: str = Field(...)


class PurchaseBIdRequest(BaseModel):
    purchase_bid: str = Field(min_length=24, max_length=24)
    tg_user_id: int = Field(...)
    currency: str = Field(default="UAH")

class DeletePurchaseBIdRequest(BaseModel):
    purchase_bid: str = Field(min_length=24, max_length=24)
    tg_user_id: int = Field(...)


class RequestTgPath(BaseModel):
    tg_user_id: int = Field(...)


class PurchaseRequestPath(BaseModel):
    purchase_type: str = Field(...)


@basket_api.get('/basket/<int:tg_user_id>',  summary="get basket", tags=[basket_tag])
def get_basket(path: RequestTgPath):
    """
    get single basket by tg user id
    """
    purchases = list(purchase_collection.find({"tg_user_id": path.tg_user_id}))
    model = BasketModel(purchases_list=purchases)
    return model.model_dump(), 200


@basket_api.post(
    '/basket/games',
    summary="add game to basket",
    tags=[basket_tag]
)
def add_purchase_to_basket(body: PurchaseBIdRequest):
    """
    add game to basket
    """
    collection = games_collection
    model = None
    if body.currency == "TRY":
        collection = games_collection_tr
    data = collection.find_one({"_id": ObjectId(body.purchase_bid)})
    if data:
        model = Game.model_validate(data)
    return purchase_handler(model, body.purchase_bid, body.tg_user_id, "games")

@basket_api.post(
    '/basket/subscriptions',
    summary="add subscription to basket",
    tags=[basket_tag]
)
def add_subscription_to_basket(body: PurchaseBIdRequest):
    """
    add subscription to basket
    :param body:
    """
    data = subscribes_collection.find_one({"_id": ObjectId(body.purchase_bid)})
    model = None
    if data:
        model = SubscribeModel.model_validate(data)
    return purchase_handler(model, body.purchase_bid, body.tg_user_id, "subscriptions")


def purchase_handler(model, purchase_bid, tg_user_id, purchase_type):
    if model:
        purchase = None
        if purchase_type == "subscriptions":
            purchase = PurchaseModel(
                tg_user_id=tg_user_id,
                purchase_id=ObjectId(purchase_bid),
                purchase_name=model.title,
                purchase_type=purchase_type
            )
        elif purchase_type == "games":
            purchase = PurchaseModel(
                tg_user_id=tg_user_id,
                purchase_id=ObjectId(purchase_bid),
                purchase_name=model.name,
                purchase_type=purchase_type
            )
        if purchase:
            if not purchase_collection.find_one({"tg_user_id": tg_user_id, "purchase_id": purchase.purchase_id}):
                purchase = purchase_collection.insert_one(purchase.model_dump())
                if purchase:
                    basket = BasketModel(purchases_list=list(purchase_collection.find({"tg_user_id": tg_user_id})))
                    return basket.model_dump(), 200
            return {"message": "This game already has been added"}, 412
    return {"message": "not found"}, HTTPStatus.NOT_FOUND


@basket_api.delete(
    '/basket/purchase',
    summary="delete purchase from basket",
    tags=[basket_tag]
)
def delete_purchase_from_basket(body: DeletePurchaseBIdRequest):
    """
    delete purchase from basket
    :param body:
    """
    status = purchase_collection.delete_one({"_id": ObjectId(body.purchase_bid)})
    if status.deleted_count:
        return BasketModel(purchases_list=basket_collection.find_one({"tg_user_id": body.tg_user_id})).model_dump(), 200
    return {"message", "not found"}, 404
