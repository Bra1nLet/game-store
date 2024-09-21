from typing import Optional, List
from pydantic import BaseModel, Field
from src.api.models.game import PyObjectId


class UserSubscribe(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    tg_user_id: int = Field(...)
    name: str = Field(...)
    starts: str = Field(...)
    ends: str = Field(...)


class UserSubscribes(BaseModel):
    subscribes: List[Optional[UserSubscribe]] = Field(...)


class UsersModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    tg_user_id: int
    email: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    reserve_code: Optional[str] = Field(default='')
    country: str = Field(default='')
    platform: str = Field(default="PS4")
    joys: int = Field(default=0)
    joy_plus: int = Field(default=0)


class UsersListModel(BaseModel):
    users: Optional[List[Optional[UsersModel]]] = Field(default=[])


class UpdateUserModel(BaseModel):
    reserve_code: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)
    platform: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
