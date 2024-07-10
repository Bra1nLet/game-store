from pydantic import BaseModel, Field


class AccountModel(BaseModel):
    user_id: str = Field(...)
    balance_joy: float = Field(default=0)
    balance_joy_plus: float = Field(default=0)
