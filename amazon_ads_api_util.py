"""Utility module for API calls and data manipulation."""

import enum
import time
from typing import List, Dict, Tuple, Optional

import requests


class ExtendedEnum(enum.Enum):
    """Extends enum.Enum to allow listing of all values."""

    @classmethod
    def list(cls) -> List:
        """Returns a list of all enum values."""
        return [c.value for c in cls]


def fix_table(data: List[Dict]) -> List[Dict]:
    """
    Normalizes a list of dictionaries by adding missing keys with None values.

    Args:
        data: A list of dictionaries representing table rows.

    Returns:
        A list of dictionaries with consistent keys across all rows.
    """
    keys = set()

    # Get all unique keys from the data
    for row in data:
        keys.update(row.keys())

    # Normalize rows by adding missing keys with None values
    return [{k: row.get(k) for k in keys} for row in data]


def join_url(*args: str) -> str:
    """
    Joins URL components, handling slash conflicts.

    Args:
        *args: Variable number of URL components to join.

    Returns:
        A properly joined URL string.
    """
    if len(args) == 1:
        return args[0]

    if len(args) > 2:
        return_value = args[0]
        for arg in args[1:]:
            return_value = join_url(return_value, arg)
        return return_value

    first, second = args
    first_has_slash = first.endswith('/')
    second_has_slash = second.startswith('/')

    if not first_has_slash and not second_has_slash:
        return f'{first}/{second}'
    if first_has_slash and second_has_slash:
        return f'{first}{second[1:]}'
    return f'{first}{second}'


def rate_limit(r: requests.Response) -> bool:
    """
    Handles rate limiting for API calls.

    Args:
        r: The response object from a request.

    Returns:
        True if rate limited and waited, False otherwise.
    """
    if r.status_code == 429:
        time.sleep(int(r.headers.get('Retry-After', 10)))
        return True
    return False


def amazon_api_call(method: str, url: str, content_type: Optional[str] = None) -> requests.Response:
    """
    Makes an API call to Amazon.

    Args:
        method: The HTTP method for the request.
        url: The URL for the API endpoint.
        content_type: Optional content type for the request headers.

    Returns:
        The response object from the API call.
    """
    headers = {}
    if content_type:
        headers['Content-Type'] = content_type
        headers['Accept'] = content_type
    return requests.request(method, url, headers=headers)

