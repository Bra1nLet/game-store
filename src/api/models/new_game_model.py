from typing import List, Optional, Dict, Annotated
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict

PyObjectId = Annotated[str, BeforeValidator(str)]

class Game(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    image_url: str = Field(...)
    name: str = Field(...)
    currency: str = Field(...)
    price: float = Field(...)

    discount_available: bool = Field(default=False)
    discount_price: Optional[float] = Field(default=None)
    discount_percentage: Optional[int] = Field(default=None)
    discount_ends: Optional[str] = Field(default=None)

    details: Optional[Dict[str, str]] = Field(default=None)
    rating: Optional[float] = Field(default=None)

    trailer: Optional[str] = Field(default=None)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "6692a7302bc5e59a9cb87ca0",
                "name": "Ace Attorney Investigations Collection",
                "currency": "UAH",
                "price_rub": 3112.12,
                "discount_percentage": "25%",
                "price_without_discount": 4251.5,
                "image_url": "https://image.api.playstation.com/vulcan/ap/rnd/202405/1405/5d900f2e0ca38f4eb5f1e7a267c63e03e46412d23aa64a4d.png?w=180",
                "details": {
                    'Platform': 'PS4',
                    'Release': '9/6/2024',
                    'Publisher': 'Capcom U.S.A., Inc.',
                    'Genres': 'Adventure'
                },
                "rating": "3.41",
            }
        },
    )


class GamesList(BaseModel):
    games: List[Optional[Game]] = Field(default=[])

class UpdateGame(BaseModel):
    price_rub: Optional[float] = Field(default=None)
    price_without_discount: Optional[float] = Field(default=None)
    discount_percentage: Optional[str] = Field(default=None)
    discount_ends: Optional[str] = Field(default=None)

class EditionModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    game_id: str = Field(...)
    name: str = Field(...)
    currency: str = Field(...)
    price: float = Field(...)
    discount_available: bool = Field(default=False)
    discount_price: Optional[float] = Field(default=None)
    discount_percentage: Optional[int] = Field(default=None)
    discount_ends: Optional[str] = Field(default=None)
    details: List[Optional[str]] = Field(default=[])
    picture_url: str = Field(default=None)
    platforms: Optional[List[Optional[str]]] = Field(...)

class EditionsList(BaseModel):
    editions: List[Optional[EditionModel]] = Field(default=[])
