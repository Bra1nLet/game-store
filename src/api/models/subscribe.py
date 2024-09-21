from typing import Optional, List
from pydantic import BaseModel, Field
from src.api.models.game import PyObjectId


class SubscribeModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    category: Optional[PyObjectId] = Field(...)
    title: str = Field(...)
    price: int = Field(...)
    oldPrice: int = Field(...)
    image: str = Field(...)

class SubscribeCategoryModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)


class SubscribeCategoryList(BaseModel):
    categories: List[Optional[SubscribeCategoryModel]]


class SubscribesList(BaseModel):
    subscribes: List[Optional[SubscribeModel]]


class UpdateSubscribeModel(BaseModel):
    name: Optional[str] = Field(default=None)
    price: Optional[int] = Field(default=None)
    picture_path: Optional[str] = Field(default=None)
