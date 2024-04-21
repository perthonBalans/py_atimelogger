import re
import html
from datetime import datetime, tzinfo
from typing import (
    Any,
    SupportsInt,
    SupportsFloat,
    SupportsIndex,
    Iterable,
    Mapping,
    Callable,
    Optional,
    TypeAlias
)

import requests
from requests.auth import HTTPBasicAuth

Records: TypeAlias = list[dict[str, Any]]
_SupportsFloatOrIndex: TypeAlias = SupportsFloat | SupportsIndex


def timestamp_helper(
    dt: datetime | str,
    tz: tzinfo
) -> tuple[datetime, Callable[[_SupportsFloatOrIndex], datetime]]:
    """
    Convert the given datetime to a datetime with timezone and a converter function.

    Args:
        dt (datetime | str): The datetime to convert.
        tz (tzinfo): The timezone to use.

    Returns:
        A tuple containing 2 elements:
            datetime: The converted datetime with timezone.
            Callable[[_SupportsFloatOrIndex], datetime]: The converter function to convert timestamps to datetime.

    Raises:
        TypeError: If `tz` is None.
    """

    if tz is None:
        raise TypeError("tz must be a tzinfo object.")
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    dt = dt.replace(tzinfo=tz)
    converter: Callable[[_SupportsFloatOrIndex], datetime] = lambda ts: datetime.fromtimestamp(ts, tz)
    return dt, converter


class aTimeLogger:
    """
    A Python wrapper for aTimeLogger REST-API.

    aTimeLogger API info: http://blog.timetrack.io/rest-api
    aTimeLogger API endpoint: https://app.atimelogger.com/api/v2

    Parameters:
    ----------
    - username: (bytes | str) The username of aTimeLogger account.
    - password: (bytes | str) The password of aTimeLogger account.

    Attributes:
    ----------
    - _username: (bytes | str) The username of aTimeLogger account.
    - _password: (bytes | str) The password of aTimeLogger account.
    - session: (requests.Session) The session object for the API requests.
    - auth_header: (requests.auth.HTTPBasicAuth) The authentication header for the request.

    Notes:
    ----------
    The datetime without time zone is assumed to be in local time zone.
    The time-limited step is `curl_request`.
    """

    REQUEST_MAX = 0x7FFF_FFFF
    MODELs = (
        'intervals',
        'types',
        'activities',
        'goals',
        'statistics',
    )
    ENDPOINT = 'https://app.atimelogger.com/api/v2'

    def __init__(
        self,
        username: bytes | str,
        password: bytes | str,
    ):
        self._username = username
        self._password = password
        self.session = requests.Session()
        self.session.auth = self.auth_header = HTTPBasicAuth(
            self.username, self.password
        )

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        self.session.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._username}, {self._password})"

    def __str__(self) -> str:
        return f"aTimeLogger user {self._username}"

    def prepare_timestamp(self, time: str | datetime | SupportsInt) -> int:
        """
        Converts the given time value to a timestamp.

        Args:
            time (str | datetime | SupportsInt): The time value to be converted.

        Returns:
            int: The converted timestamp.

        Raises:
            TypeError: If the type of time is not supported.
        """
        if isinstance(time, (str, datetime)):
            if isinstance(time, str):
                dt = datetime.fromisoformat(time)
            elif isinstance(time, datetime):
                dt = time
            ts = dt.timestamp()
        elif isinstance(time, SupportsInt):
            ts = time
        else:
            raise TypeError(f"unsupported type for time: {type(time)}")
        return int(ts)

    def prepare_params(
        self,
        offset: int = 0,
        limit: int = 100,
        order: str = 'asc',
        from_: Optional[str | datetime | SupportsInt] = None,
        to: Optional[str | datetime | SupportsInt] = None,
        types: Optional[Iterable[str]] = None,
        state: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Prepare the parameters for the API request.

        Args:
            offset (int): The offset value for pagination. Defaults to 0.
            limit (int): The limit value for pagination. Defaults to 100.
            order (str): The order of the results. Defaults to 'asc'.
            from_ (str | datetime, optional): The starting datetime for the results. Defaults to None, meaning no limit of start time.
            to (str | datetime, optional): The ending datetime for the results. Defaults to None, meaning no limit of end time.
            types (Iterable[str], optional): The type guids of the intervals to retrieve. Default is None, meaning all types.
            state (str, optional): The state of the activities to include. Defaults to None, meaning all states.
            **kwargs: Additional parameters for the API request.

        Returns:
            dict: The prepared parameters for the API request.
        """

        params = {
            'limit': limit,
            'offset': offset,
            'order': order,
        }
        if from_:
            params['from'] = self.prepare_timestamp(from_)
        if to:
            params['to'] = self.prepare_timestamp(to)
        if types:
            params['types'] = ','.join(types)
        if state:
            params['state'] = state

        params.update(kwargs)
        return params

    def curl_request(
        self,
        method: str,
        model: str,
        guid: str = '',
        params: Optional[Mapping] = None,
        json: Optional[Any] = None,
        **kwargs,
    ) -> requests.Response:
        """
        Send a request to the aTimeLogger API.

        Args:
            method (str): The HTTP method to use.
            model (str): The model to request.
            guid (str): The guid of the model to request. Defaults to ''.
            params (Mapping, optional): The parameters for the request. Defaults to None.
            json (Any, optional): The JSON data for the request. Defaults to None.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            requests.Response: The response object from the request.
        """

        url = f"{self.ENDPOINT}/{model}/{guid}"
        response = self.session.request(
            method, 
            url, 
            params=params, 
            json=json, 
            **kwargs
        )
        return response

    @staticmethod
    def check_response(response: requests.Response) -> None:
        """
        Check the response status code and raise an `HTTPError` if it indicates an error.

        Args:
            response (requests.Response): The response object to check.

        Raises:
            `HTTPError`: If the response status code indicates an error.
        """

        if 400 <= response.status_code < 600:
            request_info = f"{response.request.method} {response.request.url}"
            try:
                title = re.search(
                    r"<title>(.*)</title>", 
                    response.text, 
                    re.IGNORECASE
                ).group(1)
                reasons = html.unescape(re.search(
                    r"<p><b>Message<\/b> (.*?)<\/p>", 
                    response.text, 
                    re.IGNORECASE
                ).group(1))
                details = html.unescape(re.search(
                    r"<p><b>Description<\/b> (.*?)<\/p>", 
                    response.text, 
                    re.IGNORECASE
                ).group(1))
                error_msg = f"{title}: {reasons} for {request_info}.\n{details}"

            except AttributeError:
                if response.status_code < 500:
                    error_type = "Client Error"
                else:
                    error_type = "Server Error"
                error_msg = f"{response.status_code} {error_type}: for {request_info}"

            raise requests.HTTPError(error_msg, response=response)

    def get_types(
        self,
        guid: str = '',
        order: str = 'asc',
        **kwargs,
    ) -> dict[str, Records | bool]:
        """
        Retrieve a dict containing a list of types with optional filtering and pagination.

        Args:
            guid (str): The GUID of the type to retrieve. Default is ''.
            order (str): The order in which the types should be sorted. Default is 'asc'.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            dict[str, Records | bool]:
                "types" (Records): A list of dictionaries (with string keys) representing the types.
                "success" (bool): A boolean indicating the success of the porcess in server.

        Raises:
            Exception: If the API response is not successful.
        """
        params = self.prepare_params(
            offset=None, 
            limit=None, 
            order=order
        )
        response = self.curl_request(
            method='get', 
            model='types', 
            guid=guid, 
            params=params,
            **kwargs
        )
        self.check_response(response)
        return response.json()

    def get_activities(
        self,
        offset: int = 0,
        limit: int = REQUEST_MAX,
        state: Optional[str] = None,
        order: str = 'asc',
        **kwargs,
    ) -> dict[str, Records | dict | list | int]:
        """
        Retrieve a dict containing a list of activities with optional filtering and pagination.

        Args:
            offset (int): The offset for pagination. Default is 0.
            limit (int): The maximum number of activities to retrieve.\
                  Default is 2147483647:=0x7FFF_FFFF (`REQUEST_MAX`).
            state (str, optional): The state of the activities to retrieve. Default is None.
            order (str): The order in which the activities should be sorted. Default is 'asc'.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            dict[str, Records | dict | list | int]:
                "activities" (Records): A list of dictionaries (with string keys) representing the activities.
                "types" (Records): A list of dictionaries (with string keys) representing the types.
                "account" (dict): A dictionary representing the account.
                "guid" (list): A list of GUIDs.
                "revision" (int): The revision number.

        Raises:
            Exception: If the API response is not successful.
        """
        params = self.prepare_params(
            offset=offset, 
            limit=limit, 
            state=state,
            order=order
        )
        response = self.curl_request(
            method='get', 
            model='activities', 
            params=params,
            **kwargs
        )
        self.check_response(response)
        return response.json()

    def get_intervals(
        self,
        offset: int = 0,
        limit: int = REQUEST_MAX,
        from_: Optional[str | datetime] = None,
        to: Optional[str | datetime] = None,
        types: Optional[Iterable[str]] = None,
        order: str = 'asc',
        **kwargs,
    ) -> dict[str, Records | dict]:
        """
        Retrieve a dict containing a list of intervals with optional filtering and pagination.

        Args:
            offset (int): The offset for pagination. Default is 0.
            limit (int): The maximum number of intervals to retrieve.\
                  Default is 2147483647:=0x7FFF_FFFF (`REQUEST_MAX`).
            from_ (str | datetime, optional): The starting datetime for the intervals. Default is None.
            to (str | datetime, optional): The ending datetime for the intervals. Default is None.
            types (Iterable[str], optional): The type guids of the intervals to retrieve. Default is None.
            order (str): The order in which the intervals should be sorted. Default is 'asc'.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            dict[str, Records | dict]:
                "intervals" (Records): A list of dictionaries (with string keys) representing the intervals.
                "meta" (dict): A dictionary representing the meta information.

        Raises:
            Exception: If the API response is not successful.
        """
        params = self.prepare_params(
            offset=offset, 
            limit=limit, 
            from_=from_,
            to=to,
            types=types,
            order=order
        )
        response = self.curl_request(
            method='get', 
            model='intervals', 
            params=params,
            **kwargs
        )
        self.check_response(response)
        json = response.json()
        del json['']
        return json


def get_types(
    username: bytes | str,
    password: bytes | str,
    guid: str = '',
    order: str = 'asc',
    **kwargs,
) -> dict[str, Records | bool]:
    """
    Retrieve a dict containing a list of types with optional filtering and pagination.

    Args:
        username (bytes | str): The username of aTimeLogger account.
        password (bytes | str): The password of aTimeLogger account.
        guid (str): The GUID of the type to retrieve. Default is an empty string.
        order (str): The order in which the types should be sorted. Default is 'asc'.
        **kwargs: Additional keyword arguments for the request.

    Returns:
        dict[str, Records | bool]:
            "types" (Records): A list of dictionaries (with string keys) representing the types.
            "success" (bool): A boolean indicating the success of the porcess in server.

    Raises:
        Exception: If the API response is not successful.
    """
    with aTimeLogger(username, password) as atl:
        return atl.get_types(guid, order, **kwargs)


def get_activities(
    username: bytes | str,
    password: bytes | str,
    offset: int = 0,
    limit: int = aTimeLogger.REQUEST_MAX,
    state: Optional[str] = None,
    order: str = 'asc',
    **kwargs,
) -> dict[str, Records | dict | list | int]:
    """
    Retrieve a dict containing a list of activities with optional filtering and pagination.

    Args:
        username (bytes | str): The username of aTimeLogger account.
        password (bytes | str): The password of aTimeLogger account.
        offset (int): The offset for pagination. Default is 0.
        limit (int): The maximum number of activities to retrieve.\
              Default is 2147483647:=0x7FFF_FFFF (`REQUEST_MAX`).
        state (str, optional): The state of the activities to retrieve. Default is None.
        order (str): The order in which the activities should be sorted. Default is 'asc'.
        **kwargs: Additional keyword arguments for the request.

    Returns:
        dict[str, Records | dict | list | int]:
            "activities" (Records): A list of dictionaries (with string keys) representing the activities.
            "types" (Records): A list of dictionaries (with string keys) representing the types.
            "account" (dict): A dictionary representing the account.
            "guid" (list): A list of GUIDs.
            "revision" (int): The revision number.

    Raises:
        Exception: If the API response is not successful.
    """
    with aTimeLogger(username, password) as atl:
        return atl.get_activities(offset, limit, state, order, **kwargs)


def get_intervals(
    username: bytes | str,
    password: bytes | str,
    offset: int = 0,
    limit: int = aTimeLogger.REQUEST_MAX,
    from_: Optional[str | datetime] = None,
    to: Optional[str | datetime] = None,
    types: Optional[Iterable[str]] = None,
    order: str = 'asc',
    **kwargs,
) -> dict[str, Records | dict]:
    """
    Retrieve a dict containing a list of intervals with optional filtering and pagination.

    Args:
        username (bytes | str): The username of aTimeLogger account.
        password (bytes | str): The password of aTimeLogger account.
        offset (int): The offset for pagination. Default is 0.
        limit (int): The maximum number of intervals to retrieve.\
              Default is 2147483647:=0x7FFF_FFFF (`REQUEST_MAX`).
        from_ (str | datetime, optional): The starting datetime for the intervals. Default is None.
        to (str | datetime, optional): The ending datetime for the intervals. Default is None.
        types (Iterable[str], optional): The type guids of the intervals to retrieve. Default is None.
        order (str): The order in which the intervals should be sorted. Default is 'asc'.
        **kwargs: Additional keyword arguments for the request.

    Returns:
        dict[str, Records | dict]:
            "intervals" (Records): A list of dictionaries (with string keys) representing the intervals.
            "meta" (dict): A dictionary representing the meta information.

    Raises:
        Exception: If the API response is not successful.
    """
    with aTimeLogger(username, password) as atl:
        return atl.get_intervals(offset, limit, from_, to, types, order, **kwargs)
