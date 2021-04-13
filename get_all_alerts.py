import requests
from api_client import get_authorization

CUSTOMER_ID = "YOUR_CUSTOMER_ID"

SECUREX_CLIENT_ID = "YOUR_SECUREX_CLIENT_ID"
SECUREX_CLIENT_PASSWORD = "YOUR_SECUREX_CLIENT_PASSWORD"
SECUREX_VISIBILITY_HOST_NAME = "YOUR_SECUREX_VISIBILITY_HOST_NAME"

API_HOST_NAME = "https://api.cta.eu.amp.cisco.com"
FETCH_ALERTS_URL = "/alert-management/customer/" + CUSTOMER_ID + "/alerts"


def get_all_alerts():
    fetch_url = FETCH_ALERTS_URL
    alerts = []

    while True:
        # request for page of item
        response = requests.get(API_HOST_NAME + fetch_url,
                                headers={
                                    "Authorization": get_authorization(
                                        SECUREX_VISIBILITY_HOST_NAME,
                                        SECUREX_CLIENT_ID,
                                        SECUREX_CLIENT_PASSWORD
                                    ),
                                    "Accept": "application/json"
                                })
        data = response.json()

        # collect all received items together, preserve order
        alerts = alerts + data["items"]

        # set fetchUrl to next page
        fetch_url = data["pageInfo"]["next"]

        # repeat loop when next page is available
        if not data["pageInfo"]["hasNextPage"]:
            break

    return alerts


print(get_all_alerts())
