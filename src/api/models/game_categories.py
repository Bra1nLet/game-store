from typing import Optional, List
from pydantic import BaseModel, Field
from src.api.models.game import PyObjectId


class GamesCategoryModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)


class GameCategoriesList(BaseModel):
    categories: List[Optional[GamesCategoryModel]]
