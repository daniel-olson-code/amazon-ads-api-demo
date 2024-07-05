"""Amazon Ads API Client.

This module provides functionality to interact with the Amazon Ads API,
including authentication, token management, and profile retrieval.

Typical usage example:

  tokens = receive_code(AmazonAdsApiRegions.NA, "authorization_code", "redirect_url")
  save_tokens(tokens)
  profiles = fetch_profiles(tokens)
"""

import time
import json
import requests
import enum
import os
import class_json_util
import amazon_ads_api_util
import dotenv

dotenv.load_dotenv()

client_id = os.environ['AMAZON_ADS_CLIENT_ID']
client_secret = os.environ['AMAZON_ADS_CLIENT_SECRET']


class AmazonAdsApiRegions(enum.Enum):
    """Enumeration of Amazon Ads API regions."""
    NA = 'North America (NA)'
    EU = 'Europe (EU)'
    FE = 'Far East (FE)'


class Tokens(class_json_util.JsonObject):
    """Represents authentication tokens for Amazon Ads API.

    Attributes:
        region: A string representing the API region.
        url: A string URL for token refresh.
        refresh_token: A string refresh token.
        access_token: A string access token.
        token_type: A string indicating the token type.
        expires_in: A float representing token expiration time in seconds.
        time: A float representing the timestamp of token creation.
    """

    region: str | None = None
    url: str | None = None
    refresh_token: str | None = None
    access_token: str = None
    token_type: str | None = None
    expires_in: float | None = None
    time: float = 0

    def refresh(self):
        """Refreshes the access token using the refresh token.

        Returns:
            A requests.Response object containing the API response.
        """
        data = {'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token',
                'client_id': client_id,
                'client_secret': client_secret}
        r = requests.post(self.url, data=data)
        self.absorb(r.json())
        self.time = time.time()
        return r

    def expired(self):
        """Checks if the token has expired.

        Returns:
            A boolean indicating whether the token has expired.
        """
        return self._expired(60.)

    def _expired(self, padding=0.):
        """Internal method to check token expiration with padding.

        Args:
            padding: A float representing additional time in seconds to consider
                for expiration.

        Returns:
            A boolean indicating whether the token has expired.
        """
        return self.expires_in - padding < time.time() - self.time

    def refresh_if_expired(self):
        """Refreshes the token if it has expired."""
        if self.expired():
            self.refresh()


def save_tokens(tokens: Tokens, path: str = 'tokens.json'):
    """Saves tokens to a JSON file.

    Args:
        tokens: A Tokens object to be saved.
        path: A string path where the tokens will be saved.
    """
    with open(path, 'w') as f:
        f.write(json.dumps(tokens.json, indent=4))


def load_tokens(path: str = 'tokens.json') -> Tokens | None:
    """Loads tokens from a JSON file.

    Args:
        path: A string path from where to load the tokens.

    Returns:
        A Tokens object if the file exists, None otherwise.
    """
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return Tokens.create(json.loads(f.read()))


def create_consent_url(
        region: AmazonAdsApiRegions,
        redirect_uri: str
) -> str:
    """Creates a consent URL for Amazon Ads API authorization.

    Args:
        region: An AmazonAdsApiRegions enum value.
        redirect_uri: A string redirect URI for the OAuth flow.

    Returns:
        A string URL for user consent.
    """
    consent_url_base = {
        'North America (NA)': 'https://www.amazon.com/ap/oa',
        'Europe (EU)': 'https://eu.account.amazon.com/ap/oa',
        'Far East (FE)': 'https://apac.account.amazon.com/ap/oa',
    }[region.value]
    return (f'{consent_url_base}'
            f'?client_id={client_id}'
            f'&scope=advertising::campaign_management'
            f'&response_type=code'
            f'&redirect_uri={redirect_uri}')


def get_api_url(region: AmazonAdsApiRegions | str):
    """Gets the API URL for a given region.

    Args:
        region: An AmazonAdsApiRegions enum value or string.

    Returns:
        A string URL for the specified region's API.
    """
    key = region if isinstance(region, str) else region.value

    return {
        AmazonAdsApiRegions.NA.value: 'https://advertising-api.amazon.com',
        AmazonAdsApiRegions.EU.value: 'https://advertising-api-eu.amazon.com',
        AmazonAdsApiRegions.FE.value: 'https://advertising-api-fe.amazon.com'
    }[key]


def receive_code(
        region: AmazonAdsApiRegions,
        code: str,
        redirect_url: str
) -> Tokens:
    """Exchanges an authorization code for access tokens.

    Args:
        region: An AmazonAdsApiRegions enum value.
        code: A string authorization code.
        redirect_url: A string redirect URL used in the OAuth flow.

    Returns:
        A Tokens object containing the received tokens.
    """
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_url,
        'client_id': client_id,
        'client_secret': client_secret,
    }

    access_token_url = {
        "North America (NA)": "https://api.amazon.com/auth/o2/token",
        "Europe (EU)": "https://api.amazon.co.uk/auth/o2/token",
        "Far East (FE)": "https://api.amazon.co.jp/auth/o2/token"
    }[region.value]

    print('requesting', data, '@', access_token_url)

    r = requests.post(
        access_token_url,
        data='&'.join([f'{k}={v}' for k, v in data.items()]),
        headers={'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
    )

    response_json = r.json()
    print(f'j', response_json)

    tokens = Tokens.create({
        'region': region.value,
        'url': access_token_url,
        'refresh_token': response_json['refresh_token'],
        'access_token': response_json['access_token'],
        'token_type': response_json['token_type'],
        'expires_in': response_json['expires_in'],
        'time': time.time()
    })

    return tokens


def get_authorization_headers(
        profile_id: str | int | None,
        tokens: Tokens,
        check_to_refresh: bool = True,
) -> dict[str, str]:
    """Generates authorization headers for API requests.

    Args:
        profile_id: A string or integer profile ID, or None.
        tokens: A Tokens object containing the access token.
        check_to_refresh: A boolean indicating whether to check and refresh
            the token if expired.

    Returns:
        A dictionary of headers for API authorization.
    """
    if check_to_refresh:
        tokens.refresh_if_expired()
    headers = {
        'Amazon-Advertising-API-ClientID': client_id,
        'Authorization': f'Bearer {tokens.access_token}',
    }
    if profile_id:
        headers['Amazon-Advertising-API-Scope'] = f'{profile_id}'
    return headers


def fetch_profiles(tokens: Tokens) -> list[dict]:
    """Fetches advertising profiles from the Amazon Ads API.

    Args:
        tokens: A Tokens object for API authorization.

    Returns:
        A list of dictionaries containing profile information.
    """
    headers = get_authorization_headers(None, tokens)
    r = requests.get('https://advertising-api.amazon.com/v2/profiles', headers=headers)

    if amazon_ads_api_util.rate_limit(r):
        return fetch_profiles(tokens)

    return r.json()

