from flask_openapi3 import APIBlueprint
from flask_openapi3.models import Info
from src.api.handlers.subscribes.subscribes import subscribe_tag
from src.api.models.subscribe import SubscribeCategoryList
from src.db.db import subscribe_categories_collection


info = Info(title='Subscribes categories API', version='1.0.0')
subscribe_categories_api = APIBlueprint('subscribe categories', __name__)


@subscribe_categories_api.get("/subscribe-categories", tags=[subscribe_tag])
def get_subscribe_categories():
    """
    get subscribe categories
    """
    return  SubscribeCategoryList(categories=list(subscribe_categories_collection.find({}))).model_dump()
