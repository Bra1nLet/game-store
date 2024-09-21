from typing import List
from pydantic import BaseModel, Field
from typing_extensions import Optional
from src.api.models.game import PyObjectId


class GameMain(BaseModel):
    game_id: Optional[PyObjectId] = Field(...)
    picture_path: str

class GameSection(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    games: List[Optional[GameMain]] = Field(default=[])

class GameSectionList(BaseModel):
    sections: List[Optional[GameSection]] = Field(...)

class BannerModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    picture_path: str

class BannersList(BaseModel):
    banners: List[Optional[BannerModel]] = Field(...)