from typing import Optional, List
from pydantic import BaseModel, Field
from src.api.models.game import PyObjectId


class UsersFavoriteGame(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    game_id: str = Field(...)
    tg_user_id: int = Field(...)


class UsersFavoriteList(BaseModel):
    games: List[Optional[UsersFavoriteGame]] = Field(...)
