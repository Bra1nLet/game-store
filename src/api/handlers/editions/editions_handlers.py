from bson import ObjectId
from pydantic import BaseModel, Field
from flask_openapi3 import Tag, APIBlueprint
from flask_openapi3.models import Info
from src.db.db import editions_collection
from src.api.models.new_game_model import EditionsList, EditionModel
from flask import abort

info = Info(title='Editions API', version='1.0.0')
edition_tag = Tag(name="edition", description="Editions endpoints")
editions_api = APIBlueprint('editions', __name__)

class RequestPath(BaseModel):
    id: str = Field(max_length=24, min_length=24)
    country: str = Field(default="UA")

@editions_api.get("/editions/<string:id>", summary="get editions by game id", tags=[edition_tag])
def get_game_by_id(path: RequestPath):
    """
    get games editions by game id
    """
    collection = editions_collection
    if path.country == "TR":
        collection = editions_collection
    editions = list(collection.find({"game_id": path.id}))
    if editions:
        model = EditionsList(editions=editions)
        return model.model_dump()
    return abort(404)


@editions_api.get("/edition/<string:id>", summary="get edition by id", tags=[edition_tag])
def get_game_sequence(path: RequestPath):
    """
    Get edition by id
    :param path:
    :return:
    """
    collection = editions_collection
    if path.country == "TR":
        collection = editions_collection
    edition = collection.find_one({"_id": ObjectId(path.id)})
    if edition:
        model = EditionModel.model_validate(edition)
        return model.model_dump()
    return abort(404)
