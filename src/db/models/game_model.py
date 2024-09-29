from typing import List, Optional
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from typing import Annotated, Dict


class EditionModel(BaseModel):
    name: str = Field(...)
    price: Dict[str, float] = Field(...)
    edition_picture: str = Field(...)
    price_without_discount: Optional[Dict[str, float]] = Field(default=None)
    edition_platforms: Optional[str] = Field(default=None)
    edition_details: Optional[List[str]] = Field(default=None)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "AeonX",
                'price': {'UAH': 270, 'TL': 240},
                'price_without_discount': {'UAH': 270, 'TL': 240},
                "edition_picture": "./pictures/AeonX_AeonX_0.png",
                "edition_platforms": "PS5",
                "edition_details": None,
            }
        }
    )


class GamePrice(BaseModel):
    price: Dict[str, float] = Field(...)
    discount: Optional[Dict] = Field(default={})


class GameModel(BaseModel):
    name: str = Field(...)
    price: Dict[str, float] = Field(...)
    discount_price: Optional[Dict] = Field(default=None)
    discount_available: bool = Field(default=False)
    image_url: str = Field(...)
    details: Optional[Dict[str, str]] = Field(default=None)
    editions: Optional[List[EditionModel]] = Field(default=None)
    rating: Optional[str] = Field(default=None)
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "Ace Attorney Investigations Collection",
                "price": {'UAH': 270.0, 'TL': 240.0, 'RUB': 810.0},
                "discount": {
                    "discount_percentage": "25%",
                    "price_without_discount": {"UAH": 400, "TL": 410, "RUB": 1300},
                },
                "game_url": "https://store.playstation.com/en-us/product/UP0102-CUSA45441_00-AAIM12FULLGAME00",
                "image_url": "https://image.api.playstation.com/vulcan/ap/rnd/202405/1405/5d900f2e0ca38f4eb5f1e7a267c63e03e46412d23aa64a4d.png?w=180",
                "age_limit": "ESRB Teen",
                "details": {
                    'Platform:': 'PS4',
                    'Release:': '9/6/2024',
                    'Publisher:': 'Capcom U.S.A., Inc.',
                    'Genres:': 'Adventure'
                },
                "editions": None,
                "rating": "3.41",
            }
        },
    )
