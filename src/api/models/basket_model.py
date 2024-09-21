from src.api.models.game import PyObjectId, GameModel
from src.api.models.subscribe import SubscribeModel
from typing import Optional, List
from pydantic import BaseModel, Field


class PurchaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    tg_user_id: int
    purchase_id: Optional[PyObjectId] = Field()
    purchase_name: Optional[str] = Field()
    purchase_type: str = Field()


class BasketModel(BaseModel):
    purchases_list: Optional[List[PurchaseModel]] = Field(default=[])
