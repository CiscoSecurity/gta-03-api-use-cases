import requests
from datetime import datetime, timedelta

TOKEN_PATH = "/iroh/oauth2/token"

token_value = None
token_validity = None


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
