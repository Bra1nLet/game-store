import requests

API_TOKEN = "6162a3f473df334a7728c606"

def get_rates():
    r = requests.request(method='GET', url=f"https://v6.exchangerate-api.com/v6/{API_TOKEN}/latest/RUB")
    data = r.json()
    uah = 1 / data['conversion_rates']['UAH']
    tl = 1 / data['conversion_rates']['TRY']
    return uah, tl