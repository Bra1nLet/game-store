from typing import List, Optional, Dict, Annotated
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict

PyObjectId = Annotated[str, BeforeValidator(str)]


class EditionModel(BaseModel):
    name: str = Field(...)
    price_rub: float = Field(...)
    picture: str = Field(...)
    price_without_discount: Optional[float] = Field(default=None)
    platforms: Optional[str] = Field(default=None)
    details: Optional[List[str]] = Field(default=None)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "AeonX",
                'price_rub': 3112,
                'price_without_discount': 4251,
                "picture": "./pictures/AeonX_AeonX_0.png",
                "platform": "PS5",
                "details": None,
            }
        }
    )


class GameModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    currency: str = Field(...)
    price_rub: float = Field(...)
    discount: Optional[Dict] = Field(default=None)
    image_url: str = Field(...)
    age_limit: Optional[str] = Field(default=None)
    details: Optional[Dict[str, str]] = Field(default=None)
    editions: Optional[List[EditionModel]] = Field(default=None)
    rating: Optional[str] = Field(default=None)
    trailer: Optional[str] = None
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "6692a7302bc5e59a9cb87ca0",
                "name": "Ace Attorney Investigations Collection",
                "currency": "UAH",
                "price_rub": 3112,
                "discount": {
                    "discount_percentage": "25%",
                    "price_without_discount": 4251,
                },
                "image_url": "https://image.api.playstation.com/vulcan/ap/rnd/202405/1405/5d900f2e0ca38f4eb5f1e7a267c63e03e46412d23aa64a4d.png?w=180",
                "age_limit": "ESRB Teen",
                "details": {
                    'Platform': 'PS4',
                    'Release': '9/6/2024',
                    'Publisher': 'Capcom U.S.A., Inc.',
                    'Genres': 'Adventure'
                },
                "editions": None,
                "rating": "3.41",
                "trailer": None
            }
        },
    )


class GameCollection(BaseModel):
    """
    A container holding a list of `GameModel` instances.

    This exists because providing a top-level array in a JSON response can be a [vulnerability]
    """
    games: List[GameModel]
