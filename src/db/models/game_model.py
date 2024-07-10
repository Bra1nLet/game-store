from typing import List, Optional
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from typing import Annotated, Dict

PyObjectId = Annotated[str, BeforeValidator(str)]


# Have to provide changes in parsing price !
class EditionModel(BaseModel):
    name: str = Field(...)
    price: List[str] = Field(...)
    edition_picture: str = Field(...)
    edition_platforms: Optional[str] = Field(default=None)
    edition_details: Optional[List[str]] = Field(default=None)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "name": "AeonX",
            'price': "$6.99",
            "edition_picture": "./pictures/AeonX_AeonX_0.png",
            "edition_platforms": "PS5",
            "edition_details": None,
        }
    )


class GameModel(BaseModel):
    name: str = Field(...)
    price: List[str] = Field(...)
    game_url: str = Field(...)
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
                "name": "Ace Attorney Investigations Collection",
                "price": "$5.99",
                "game_url": "https://store.playstation.com/en-us/product/UP0102-CUSA45441_00-AAIM12FULLGAME00",
                "image_url": "https://image.api.playstation.com/vulcan/ap/rnd/202405/1405/5d900f2e0ca38f4eb5f1e7a267c63e03e46412d23aa64a4d.png?w=180",
                "age_limit": "ESRB Teen",
                "details": {
                    'Platform:': 'PS4',
                    'Release:': '9/6/2024',
                    'Publisher:': 'Capcom U.S.A., Inc.',
                    'Genres:': 'Adventure'
                }
            }
        },
    )
