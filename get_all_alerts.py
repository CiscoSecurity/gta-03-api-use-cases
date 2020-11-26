import requests

CUSTOMER_ID = "YOUR_CUSTOMER_ID"
ACCESS_TOKEN = "YOUR_VALID_ACCESS_TOKEN"

API_HOST_NAME = "https://api.cta.eu.amp.cisco.com"
FETCH_ALERTS_URL = "/alert-management/customer/" + CUSTOMER_ID + "/alerts"


def get_all_alerts():
    alerts = []
    fetch_url = FETCH_ALERTS_URL

    while True:
        # request for page of item
        response = requests.get(API_HOST_NAME + fetch_url,
                                headers={
                                    "Authorization": "Bearer " + ACCESS_TOKEN,
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
