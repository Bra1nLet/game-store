from src.db.games import GameCollection
from typing import Optional
from pydantic import BaseModel


class BasketModel(BaseModel):
    user_id: Optional[str]
    gameList: Optional[GameCollection]
