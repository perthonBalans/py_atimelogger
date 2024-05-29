# Py_aTimeLogger

Py_aTimeLogger is a python wrapper of [aTimeLogger](http://www.atimelogger.com/).

```python
>>> import py_atimelogger as patl
>>> intervals = patl.get_intervals('username@example.mail', 'password')
>>> intervals['intervals']
[{'guid': ..., ...}, ...]
```

api_info.json is not necessary. It indicate the api supported at the endpoint.

## Document generated by GPT-4o

### Overview

The `aTimeLogger` class is a Python wrapper for the aTimeLogger REST-API, providing methods for interacting with various endpoints of the API. This wrapper simplifies the process of sending requests and handling responses when working with aTimeLogger's data. This document provides an overview of the available methods, usage examples, and detailed descriptions of the arguments and return values for each method.

### API Information

- **API Documentation**: [aTimeLogger REST-API Documentation](http://blog.timetrack.io/rest-api)
- **API Endpoint**: `https://app.atimelogger.com/api/v2`

### Requirements

- Python 3.8+
- `requests` library

### Class: `aTimeLogger`

#### Attributes

- `username` (bytes | str): The username of the aTimeLogger account.
- `password` (bytes | str): The password of the aTimeLogger account.
- `session` (requests.Session): The session object for the API requests.
- `auth_header` (requests.auth.HTTPBasicAuth): The authentication header for the request.

#### Initialization

```python
from aTimeLogger import aTimeLogger

atl = aTimeLogger(username, password)
```

#### Methods

- `close() -> None`: Closes the session.

- `prepare_params() -> dict`: Prepares parameters for the API request.

- `request() -> requests.Response`: Sends a request to the aTimeLogger API.

- `check_response() -> None`: Checks the response status code and raises an `HTTPError` if it indicates an error.

- `decode_response() -> dict[str, Any]`: Decodes the response from the API and returns it as a dictionary.

- `get_types() -> dict[str, list[records] | bool]`: Retrieves a dictionary containing a list of types with optional filtering and pagination.

- `get_activities() -> dict[str, list[records] | dict[str, str | int] | list[str] | int]`: Retrieves a dictionary containing a list of activities with optional filtering and pagination.

- `get_intervals() -> dict[str, list[records] | dict[str, int]]`: Retrieves a dictionary containing a list of intervals with optional filtering and pagination.

### Helper Functions

- `prepare_timestamp() -> int`: Converts the given time value to a timestamp.

- `timestamp_helper() -> tuple[datetime, Callable[[float], datetime]]`: Converts the given datetime to a datetime with timezone and returns a converter function.

### Usage Examples

#### Example: Retrieving Types

```python
from aTimeLogger import get_types

username = 'your_username'
password = 'your_password'

types = get_types(username, password)
print(types)
```

#### Example: Retrieving Activities

```python
from aTimeLogger import get_activities

username = 'your_username'
password = 'your_password'

activities = get_activities(username, password, limit=10, state='active')
print(activities)
```

#### Example: Retrieving Intervals

```python
from aTimeLogger import get_intervals

username = 'your_username'
password = 'your_password'
datetime_range = ('2023-01-01T00:00:00', '2023-12-31T23:59:59')

intervals = get_intervals(username, password, datetime_range=datetime_range, limit=5)
print(intervals)
```

### Error Handling

The `check_response` method checks the response status code and raises an `HTTPError` if the response indicates an error. The error message includes the request method, URL, and any available details from the response.
