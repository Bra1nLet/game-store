from src.api.handlers.basket.basket_handel import basket_api
from src.api.handlers.favorite.favorite_handler import favorite_list_api
from src.api.handlers.main_page.main_page import game_main_api
from src.api.handlers.games.game_handlers import game_api
from src.api.handlers.editions.editions_handlers import editions_api
from src.api.handlers.games.games_categories import game_categories_api
from src.api.handlers.subscribes.subscribe_categories import subscribe_categories_api
from src.api.handlers.subscribes.subscribes import subscribe_api
from src.api.handlers.user.purchase_handlers import purchase_api
from src.api.handlers.user.user_handlers import user_api
from flask_openapi3 import OpenAPI
from flask import request, jsonify, render_template
from flask_cors import CORS
from urllib.parse import urlparse, parse_qs
import hashlib
import hmac

from src.config import BOT_TOKEN

app = OpenAPI(__name__)
CORS_ALLOW_ORIGIN="*,*"
CORS_EXPOSE_HEADERS="*,*"
CORS_ALLOW_HEADERS="content-type,datacheckstring,DataCheckString,*"
cors = CORS(app, origins=CORS_ALLOW_ORIGIN.split(","), allow_headers=CORS_ALLOW_HEADERS.split(",") , expose_headers= CORS_EXPOSE_HEADERS.split(","),   supports_credentials = True)

@game_api.before_request
@game_categories_api.before_request
@favorite_list_api.before_request
@purchase_api.before_request
@user_api.before_request
@editions_api.before_request
@subscribe_api.before_request
@subscribe_categories_api.before_request
@basket_api.before_request
@game_main_api.before_request
def auth_middleware():
    """Middleware function to check authentication before each request."""
    if request.method == "OPTIONS":
        return {}, 200
    data_check_string = request.headers.get('DataCheckString')
    if not data_check_string:
        return jsonify({"error": "Some data is missing"}), 401

    data_check_string, _hash = string_to_data_check_string(data_check_string)
    if data_check_string and _hash:
        if not verify_telegram_data(data_check_string, _hash):
            return jsonify({"error": "Invalid or missing token"}), 403
    else:
        return {}, 403

app.register_api(game_api)
app.register_api(game_categories_api)
app.register_api(favorite_list_api)
app.register_api(purchase_api)
app.register_api(user_api)
app.register_api(editions_api)
app.register_api(subscribe_api)
app.register_api(subscribe_categories_api)
app.register_api(basket_api)
app.register_api(game_main_api)




def hmac_sha256(key, message):
    key = key.encode()
    message = message.encode()
    return hmac.new(
        key,
        message,
        hashlib.sha256
    ).hexdigest()


def string_to_data_check_string(init_data):
    parsed_url = urlparse('?' + init_data)
    query_params = parse_qs(parsed_url.query)

    keys = query_params.keys()
    sorted_keys = sorted(keys)

    _hash = query_params["hash"][0]
    sorted_keys.remove("hash")
    data = []
    for i in sorted_keys:
        data.append(i + "=" + query_params[i][0])
    return "\n".join(data), _hash

def verify_telegram_data(data_check_string, _hash):
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if calculated_hash == _hash:
        return True
    else:
        return False


def check_hash(data_check_string: str, _hash: str):
    secret_key = hmac_sha256(BOT_TOKEN, "WebAppData")
    if hmac_sha256(data_check_string, secret_key) == _hash:
        return True
    return False


@app.get('/')
def home():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(port=8881, debug=True)
