from bson import ObjectId
from src.config import BOT_TOKEN
from pydantic import BaseModel, Field
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from src.api.models.basket_model import PurchaseModel
from src.api.models.new_game_model import Game
from src.api.models.subscribe import SubscribeModel
from src.db.db import subscribes_collection, games_collection, games_collection_tr, purchase_collection
import requests

info = Info(title='Purchase API', version='1.0.0')
purchase_tag = Tag(name="Purchase handler", description="Purchase endpoints")
purchase_api = APIBlueprint('purchase', __name__)


class RequestBuy(BaseModel):
    tg_user_id: int = Field(...)
    currency: str = Field(...)

@purchase_api.post('/create-invoice', methods=['POST'], tags=[purchase_tag])
def create_invoice_for_basket_purchases(body: RequestBuy):
    purchases = list(purchase_collection.find({"tg_user_id": body.tg_user_id}))
    model = games_collection
    total_price = 0
    if  body.currency == "TRY":
        model = games_collection_tr
    for item in purchases:
        print(item)
        purchase = PurchaseModel.model_validate(item)
        purchase_id = purchase.purchase_id
        price = 0
        if purchase.purchase_type == "games":
            single_item = Game.model_validate(model.find_one({"_id": ObjectId(purchase_id)}))
            price = single_item.price_rub
        elif purchase.purchase_type == "subscriptions":
            single_item = SubscribeModel.model_validate(subscribes_collection.find_one({"_id": ObjectId(purchase_id)}))
            price = single_item.price
        total_price += price
    create_invoice(total_price, body.tg_user_id)
    return {"answer": f"price: {total_price}"}, 200

def create_invoice(price, chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice"
    response = requests.post(
        url=url,
        json={
            "chat_id": chat_id,
            "title": "Purchse",
            "description": "desc",
            "payload": "payload",
            "currency": "XTR",
            "provider_token": "",
            "prices": [{"label": "price", "amount": int(price)}],
        }
    )
