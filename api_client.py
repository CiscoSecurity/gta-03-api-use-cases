import requests
from datetime import datetime, timedelta

TOKEN_PATH = "/iroh/oauth2/token"
AUTH_ME_PATH = "/auth/api-clients/me"

API_HOST_NAME = "https://api.cta.eu.amp.cisco.com"
APP_HOST_NAME = "https://cta.eu.amp.cisco.com"

token_value = None
token_validity = None

customer_id = None


def get_authorization(securex_host_name, secuerx_client_id, securex_client_password):
    """
    Get HTTPs "Authorization" header value based on SecureX client credentials

    :return: "Authorization" header value in form "<type> <credentials>". Type is now fixed (="Bearer")
        because "token_type" in response is lower case (="bearer") and is not accepted in this form.
    """
    global token_value
    global token_validity

    if token_value is not None and token_validity is not None:
        if datetime.now() < token_validity:
            return token_value

    fetch_token_url = securex_host_name + TOKEN_PATH

    token_response = requests.post(fetch_token_url,
                                   data="grant_type=client_credentials",
                                   headers={
                                       "Accept": "application/json",
                                       "Content-Type": "application/x-www-form-urlencoded"
                                   },
                                   auth=(secuerx_client_id, securex_client_password))
    token_response_data = token_response.json()

    # keep validity shorter - usually is 5-10 minutes, reduce it by 30 seconds to prevent longer request being rejected
    token_validity = datetime.now() + timedelta(seconds=(token_response_data["expires_in"] - 30))
    # cannot use directly "token_type" because it's not accepted ("bearer" -> must be "Bearer")
    token_value = "Bearer " + token_response_data["access_token"]

    return token_value


def get_customer_id(securex_host_name, secuerx_client_id, securex_client_password):
    """
    Get global threat alerts customer ID associated with SecureX client

    :return: customer ID or None
    """
    global customer_id

    if customer_id is None:
        response = requests.get(APP_HOST_NAME + AUTH_ME_PATH,
                                headers={
                                    "Authorization": get_authorization(
                                        securex_host_name,
                                        secuerx_client_id,
                                        securex_client_password
                                    ),
                                    "Accept": "application/json"
                                })
        me_response = response.json()
        customer_id = me_response["identity"]["customerId"]

    return customer_id


class CollectionIterator:
    """
    Object designed to help with processing of paged collections based on iterator pattern.
    Both GET and POST collections are supported.
    Params:
    - collection_url_path (str) - URL path of collection we'd like to get items (without hostname and query parameters),
      e.g., "/alert-management/customer/customerId/alerts"
    - authorization_fn (str) - function able to generate "Authorization" header,
      use "get_authorization" wrapped with credentials
    - (optional) query_params (key: str - value: str) - query parameters in dictionary
      e.g., { "size": "100" }
    - (optional) cursor (str) - position of item (cursor) in collection where to continue iterating (usually cursor of last item from previous run)
      e.g., "123456"
    - (optional) request_body (dict) - do POST with this provided requestBody
    """
    def __init__(self, collection_url_path, authorization_fn, query_params=None, cursor=None, request_body=None):
        # keep immutable these constructor parameters
        self.collection_url_path = collection_url_path
        self.authorization_fn = authorization_fn
        self.query_params = query_params or {}
        self.request_body = request_body

        self.has_api_response = False
        self.has_next_page = None
        self.end_cursor = cursor
        self.next_page_url = self.__build_next_page_url_from_variables(cursor)
        self.current_page_items = []
        self.current_page_items_pointer = 0

    def has_next(self):
        if not self.has_api_response:
            self.__fetch_next_page()

        return self.__has_current_page_items() or self.has_next_page

    def next(self):
        if not self.has_api_response \
                or (not self.__has_current_page_items() and self.has_next_page):
            self.__fetch_next_page()

        if self.__has_current_page_items():
            item = self.current_page_items[self.current_page_items_pointer]
            self.current_page_items_pointer = self.current_page_items_pointer + 1
            return item
        else:
            return None

    def __fetch_next_page(self):
        headers = {
            "Authorization": self.authorization_fn(),
            "Accept": "application/json"
        }

        if self.request_body:
            response = requests.post(API_HOST_NAME + self.next_page_url, headers=headers, json=self.request_body)
        else:
            response = requests.get(API_HOST_NAME + self.next_page_url, headers=headers)

        data = response.json()

        self.current_page_items = data["items"]
        self.has_api_response = True
        self.current_page_items_pointer = 0

        if "endCursor" in data["pageInfo"]:
            self.end_cursor = data["pageInfo"]["endCursor"]

        self.has_next_page = data["pageInfo"]["hasNextPage"]
        self.next_page_url = data["pageInfo"]["next"]

        if self.has_next_page and self.next_page_url is None:
            self.next_page_url = self.__build_next_page_url_from_variables(self.end_cursor)

    def __has_current_page_items(self):
        return self.current_page_items_pointer < len(self.current_page_items)

    def __build_next_page_url_from_variables(self, end_cursor=None):
        query_params_copy = self.query_params.copy()
        if end_cursor:
            query_params_copy["after"] = end_cursor

        if not query_params_copy:
            return self.collection_url_path

        query_params_list = list(map(lambda kv: (kv[0] + "=" + str(kv[1] or "")), query_params_copy.items()))
        query_params = "?" + "&".join(query_params_list)
        return self.collection_url_path + query_params
