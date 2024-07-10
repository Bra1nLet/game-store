from src.api.handlers.games.game_handlers import game_api
from flask_openapi3 import OpenAPI


app = OpenAPI(__name__)
app.register_api(game_api)


if __name__ == "__main__":
    app.run(debug=True)
