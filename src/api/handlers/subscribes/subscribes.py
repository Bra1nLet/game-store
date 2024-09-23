from http import HTTPStatus
from bson import ObjectId
from pydantic import BaseModel, Field
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from src.api.models.subscribe import SubscribeModel, SubscribesList
from src.db.db import subscribes_collection

info = Info(title='Subscribes API', version='1.0.0')
subscribe_tag = Tag(name="subscribe", description="Subscribes endpoints")
subscribe_api = APIBlueprint('subscribe', __name__)


class SubscribeRequest(BaseModel):
    name: str = Field(...)
    price: int = Field(...)
    picture_path: str = Field(...)


class RequestQuery(BaseModel):
    bid: str = Field(max_length=24, min_length=24)


@subscribe_api.get('/subscribes',   summary="get subscribes", tags=[subscribe_tag])
def get_subscribes():
    """
    get subscribes list
    """
    return SubscribesList(subscribes=list(subscribes_collection.find({}))).model_dump()


@subscribe_api.get('/subscribes/<string:bid>',  summary="get subscribe", tags=[subscribe_tag])
def get_subscribe(path: RequestQuery):
    """
    get single subscribe
    """
    subscribe = subscribes_collection.find_one({"_id": ObjectId(path.bid)})
    if subscribe:
        model = SubscribeModel.model_validate(subscribe)
        return model.model_dump()
    return {"message": "not found"}, HTTPStatus.NOT_FOUND
