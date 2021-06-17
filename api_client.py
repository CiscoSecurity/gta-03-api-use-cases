import requests
from requests.auth import AuthBase
from datetime import datetime, timedelta

TOKEN_PATH = "/iroh/oauth2/token"
AUTH_ME_PATH = "/auth/api-clients/me"

API_HOST_NAME = "https://api.cta.eu.amp.cisco.com"
APP_HOST_NAME = "https://cta.eu.amp.cisco.com"


class GtaAuth(AuthBase):
    """
    Class providing authorization mechanism to global threat alerts API.
    """
    def __init__(self, securex_host_name, secuerx_client_id, securex_client_password):
        self._securex_host_name = securex_host_name
        self._secuerx_client_id = secuerx_client_id
        self._securex_client_password = securex_client_password

        self._token_value = None
        self._token_validity = None

    def __call__(self, request):
        if (self._token_value is None or self._token_validity is None) \
                or (self._token_validity is not None and datetime.now() >= self._token_validity):
            fetch_token_url = self._securex_host_name + TOKEN_PATH

            token_response = requests.post(fetch_token_url,
                                           data="grant_type=client_credentials",
                                           headers={
                                               "Accept": "application/json",
                                               "Content-Type": "application/x-www-form-urlencoded"
                                           },
                                           auth=(self._secuerx_client_id, self._securex_client_password))
            token_response_data = token_response.json()

            # keep validity shorter - usually is 5-10 minutes, reduce it by 30 seconds to prevent request being rejected
            self._token_validity = datetime.now() + timedelta(seconds=(token_response_data["expires_in"] - 30))
            # cannot use directly "token_type" because it's not accepted ("bearer" -> must be "Bearer")
            self._token_value = "Bearer " + token_response_data["access_token"]

        request.headers["Authorization"] = self._token_value
        return request


class ApiClient:
    """
    Global threat alerts API client containing session instance (when instantiated) which is supposed to be used when accessing the API
    including authorization.
    """
    def __init__(self, securex_host_name, secuerx_client_id, securex_client_password, api_host_name=API_HOST_NAME, app_host_name=APP_HOST_NAME):
        self._api_host_name = api_host_name
        self._app_host_name = app_host_name
        self._customer_id = None
        self._api_session = requests.Session()

        self._api_session.auth = GtaAuth(securex_host_name, secuerx_client_id, securex_client_password)
        self._api_session.headers.update({
            "Accept": "application/json"
        })

    def get_customer_id(self):
        """
        Get global threat alerts customer ID associated with SecureX client

        :return: customer ID
        """
        if self._customer_id is None:
            response = self._api_session.get(self._app_host_name + AUTH_ME_PATH)
            me_response = response.json()
            self._customer_id = me_response["identity"]["customerId"]

        return self._customer_id

    def create_collection_iterator(self, collection_url_path, query_params=None, cursor=None, request_body=None):
        """
        Creates new instance of CollectionIterator with current ApiClient reference

        :return: CollectionIterator instance
        """
        return ApiClient.CollectionIterator(
            api_client=self,
            collection_url_path=collection_url_path,
            query_params=query_params,
            cursor=cursor,
            request_body=request_body)

    def api_session(self):
        """
        Returns current Session instance in ApiClient with authorization ("auth") set.

        :return: Session instance
        """
        return self._api_session

    def api_host_name(self):
        """
        Returns current instance API host name.

        :return: API host name string
        """
        return self._api_host_name

    class CollectionIterator:
        """
        Object designed to help with processing of paged collections based on iterator pattern.
        Both GET and POST collections are supported.
        Params:
        - api_client (ApiClient) - initialized instance of ApiClient
        - collection_url_path (str) - URL path of collection we'd like to get items (without hostname and query parameters),
          e.g., "/alert-management/customer/customerId/alerts"
        - (optional) query_params (key: str - value: str) - query parameters in dictionary
          e.g., { "size": "100" }
        - (optional) cursor (str) - position of item (cursor) in collection where to continue iterating (usually cursor of last item from previous run)
          e.g., "123456"
        - (optional) request_body (dict) - do POST with this provided requestBody
        """

        def __init__(self, api_client, collection_url_path, query_params=None, cursor=None, request_body=None):
            # keep immutable these constructor parameters
            self._api_client = api_client
            self._collection_url_path = collection_url_path
            self._query_params = query_params or {}
            self._request_body = request_body

            self._has_api_response = False
            self._has_next_page = None
            self._end_cursor = cursor
            self._next_page_url = self.__build_next_page_url_from_variables(cursor)
            self._current_page_items = []
            self._current_page_items_pointer = 0

        def __iter__(self):
            return self

        def __next__(self):
            if not self._has_api_response \
                    or (not self.__has_current_page_items() and self._has_next_page):
                self.__fetch_next_page()

            if self.__has_current_page_items():
                item = self._current_page_items[self._current_page_items_pointer]
                self._current_page_items_pointer = self._current_page_items_pointer + 1
                return item
            else:
                raise StopIteration

        next = __next__  # Python 2 support

        def __fetch_next_page(self):
            if self._request_body:
                response = self._api_client.api_session().post(self._api_client.api_host_name() + self._next_page_url, json=self._request_body)
            else:
                response = self._api_client.api_session().get(self._api_client.api_host_name() + self._next_page_url)

            data = response.json()

            self._current_page_items = data["items"]
            self._has_api_response = True
            self._current_page_items_pointer = 0

            if "endCursor" in data["pageInfo"]:
                self._end_cursor = data["pageInfo"]["endCursor"]

            self._has_next_page = data["pageInfo"]["hasNextPage"]
            self._next_page_url = data["pageInfo"]["next"]

            if self._has_next_page and self._next_page_url is None:
                self._next_page_url = self.__build_next_page_url_from_variables(self._end_cursor)

        def __has_current_page_items(self):
            return self._current_page_items_pointer < len(self._current_page_items)

        def __build_next_page_url_from_variables(self, end_cursor=None):
            query_params_copy = self._query_params.copy()
            if end_cursor:
                query_params_copy["after"] = end_cursor

            if not query_params_copy:
                return self._collection_url_path

            query_params_list = list(map(lambda kv: (kv[0] + "=" + str(kv[1] or "")), query_params_copy.items()))
            query_params = "?" + "&".join(query_params_list)
            return self._collection_url_path + query_params

        def end_cursor(self):
            return self._end_cursor
