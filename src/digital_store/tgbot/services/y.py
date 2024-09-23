import requests
from yoomoney import Authorize

Authorize(
    client_id="",
    redirect_uri="https://t.me/",
    scope=["account-info",
           "operation-history",
           "operation-details",
           "incoming-transfers",
           "payment-p2p",
           "payment-shop",
           ]
)
