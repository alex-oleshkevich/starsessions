# Starsessions

Advanced sessions for Starlette and FastAPI frameworks

![PyPI](https://img.shields.io/pypi/v/starsessions)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/alex-oleshkevich/starsessions/qa.yml?branch=master)
![GitHub](https://img.shields.io/github/license/alex-oleshkevich/starsessions)
![Libraries.io dependency status for latest release](https://img.shields.io/librariesio/release/pypi/starsessions)
![PyPI - Downloads](https://img.shields.io/pypi/dm/starsessions)
![GitHub Release Date](https://img.shields.io/github/release-date/alex-oleshkevich/starsessions)

## Installation

Install `starsessions` package:

```bash
pip install starsessions
```

Use the `redis` extra for [Redis support](#redis):

```bash
pip install starsessions[redis]
```

## Quick start

See example applications in the [`examples/`](examples) directory:
- `fastapi_app.py` — FastAPI integration with autoloading
- `login.py` — login/logout flow with session ID regeneration
- `rolling.py` — rolling session expiration
- `redis_.py` — Redis-backed sessions with lifespan management

## Usage

1. Add `SessionMiddleware` to your application to enable session support.
2. Configure a session store and pass it to the middleware.
3. Load the session in your view by calling `load_session(connection)`.

```python
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from starsessions import CookieStore, load_session, SessionMiddleware


async def index_view(request):
    await load_session(request)

    session_data = request.session
    return JSONResponse(session_data)


session_store = CookieStore(secret_key='TOP SECRET')

app = Starlette(
    middleware=[
        Middleware(SessionMiddleware, store=session_store, lifetime=3600 * 24 * 14),
    ],
    routes=[
        Route('/', index_view),
    ]
)
```

### Cookie security

By default, the middleware uses strict defaults: the cookie lifetime is limited to the browser session and is only sent over HTTPS.
You can relax these defaults via `cookie_https_only`, `lifetime`, and `cookie_same_site`:

```python
from starlette.middleware import Middleware

from starsessions import CookieStore, SessionMiddleware

session_store = CookieStore(secret_key='TOP SECRET')

middleware = [
    Middleware(
        SessionMiddleware,
        store=session_store,
        cookie_https_only=False,
        cookie_same_site='lax',
        lifetime=3600 * 24 * 14,
    ),
]
```

The example above allows sessions over HTTP and sets the lifetime to 14 days.

The `lifetime` parameter also accepts `datetime.timedelta`:

```python
import datetime
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, lifetime=datetime.timedelta(days=14)),
]
```

### Loading session

Session data is not loaded automatically. Call `load_session` before accessing it.

```python
async def index_view(request):
    await load_session(request)
    request.session['key'] = 'value'
```

Accessing an unloaded session raises `SessionNotLoaded`:

```python
async def index_view(request):
    request.session['key'] = 'value'  # raises SessionNotLoaded
```

You can avoid calling `load_session` manually by using `SessionAutoloadMiddleware`.

### Session autoload

For performance reasons, the session is not autoloaded by default. Sometimes it is annoying to call `load_session` too
often. We provide `SessionAutoloadMiddleware` to reduce the boilerplate by autoloading the session for you.

There are two options: always autoload or autoload for specific paths only.

```python
from starlette.middleware import Middleware

from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

session_store = CookieStore(secret_key='TOP SECRET')

# Always autoload
middleware = [
    Middleware(SessionMiddleware, store=session_store),
    Middleware(SessionAutoloadMiddleware),
]

# Autoload for selected paths only
middleware = [
    Middleware(SessionMiddleware, store=session_store),
    Middleware(SessionAutoloadMiddleware, paths=['/admin', '/app']),
]

# Regex patterns are also supported
import re

middleware = [
    Middleware(SessionMiddleware, store=session_store),
    Middleware(SessionAutoloadMiddleware, paths=[re.compile(r'/admin.*')]),
]
```

### Rolling sessions

The default behavior of `SessionMiddleware` is to expire the cookie after `lifetime` seconds after it was set.
For example, if you create a session with `lifetime=3600`, the session will be terminated exactly in 3600 seconds.
Sometimes this may not be what you need, so we provide an alternate expiration strategy — rolling sessions.

When rolling sessions are activated, the cookie expiration time will be extended by `lifetime` on every response.
For example: on the first response you create a new session with `lifetime=3600`, then the user makes another request
and the session gets extended by another 3600 seconds, and so on. This approach is useful when you want short-lived
sessions that don't interrupt an active user. With the rolling strategy, a session expires only after a period of
inactivity.

To enable the rolling strategy set `rolling=True`.

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, lifetime=300, rolling=True),
]
```

The snippet above will drop the session after 300 seconds (5 minutes) of inactivity, but automatically extend it
while the user is active.

### Cookie path

Bind the session cookie to a specific URL prefix with `cookie_path`:

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, cookie_path='/admin'),
]
```

Requests to other paths will not send or receive the session cookie.

### Cookie domain

Restrict the cookie to specific hosts with `cookie_domain`:

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, cookie_domain='example.com'),
]
```

> Note: setting `cookie_domain` makes the cookie available to subdomains as well (e.g. `app.example.com`).

### Session-only cookies

Set `lifetime=0` to create a session-only cookie that the browser removes when closed.

> Note: this depends on browser implementation.

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, lifetime=0),
]
```

## Built-in stores

### Memory

Class: `starsessions.InMemoryStore`

Stores data in process memory. Data is lost on server restart. Suitable for tests and development.

### CookieStore

Class: `starsessions.CookieStore`

Stores session data in a signed cookie on the client. No server-side storage required.

### Redis

Class: `starsessions.stores.redis.RedisStore`

Stores session data in a Redis server.

> Requires [redis-py](https://github.com/redis/redis-py): `pip install starsessions[redis]`

```python
from redis.asyncio import Redis

from starsessions.stores.redis import RedisStore

client = Redis.from_url('redis://localhost')
store = RedisStore(connection=client)

# close connection on shutdown
await client.aclose()
```

> Note: redis-py requires an explicit connection close. The library does not handle it for you.
> The recommended solution is to pass a `Redis` instance to the store and call `.aclose()` on application shutdown,
> for example using a lifespan handler.
> See [redis-py asyncio docs](https://redis-py.readthedocs.io/en/latest/examples/asyncio_examples.html) for details.

#### Redis key prefix

All keys are prefixed with `starsessions.` by default. Override with the `prefix` argument:

```python
from redis.asyncio import Redis
from starsessions.stores.redis import RedisStore

client = Redis.from_url('redis://localhost')
store = RedisStore(connection=client, prefix='my_sessions.')
```

`prefix` can also be a callable:

```python
from redis.asyncio import Redis
from starsessions.stores.redis import RedisStore


def make_prefix(key: str) -> str:
    return 'my_sessions_' + key


client = Redis.from_url('redis://localhost')
store = RedisStore(connection=client, prefix=make_prefix)
```

#### Key expiration

Key TTL is managed automatically. For session-only cookies (`lifetime=0`) the exact expiry is unknown, so a fallback TTL of 30 days is used. Override it with `gc_ttl`:

```python
from redis.asyncio import Redis
from starsessions.stores.redis import RedisStore

client = Redis.from_url('redis://localhost')
store = RedisStore(connection=client, gc_ttl=3600)  # max 1 hour
```

## Custom store

Creating new stores is quite simple. Extend `starsessions.SessionStore` and implement the abstract methods.
Note that the `write` method must return the session ID as a string.

```python
from starsessions import SessionStore


class InMemoryStore(SessionStore):
    def __init__(self) -> None:
        self._storage: dict[str, bytes] = {}

    async def read(self, session_id: str, lifetime: int) -> bytes:
        """Read session data from a data source using session_id."""
        return self._storage.get(session_id, b"")

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        """Write session data into the data source and return session ID."""
        self._storage[session_id] = data
        return session_id

    async def remove(self, session_id: str) -> None:
        """Remove session data."""
        self._storage.pop(session_id, None)
```

### lifetime and ttl

The `write` method accepts two special arguments: `lifetime` and `ttl`.
The difference is that `lifetime` is the total session duration (set by the middleware)
and `ttl` is the remaining session time. After `ttl` seconds the data can be safely deleted from the storage.

> Your custom backend must correctly handle cases when `lifetime=0`.
> In such cases you don't have an exact expiration value, and you would have to find a way to extend the session TTL
> on the storage side, if any.

## Serializers

Session data is serialized to JSON by default (`starsessions.JsonSerializer`). Implement `starsessions.Serializer` to use a custom format:

```python
import json
from starlette.middleware import Middleware
from starsessions import Serializer, SessionMiddleware


class MySerializer(Serializer):
    def serialize(self, data: object) -> bytes:
        return json.dumps(data).encode('utf-8')

    def deserialize(self, data: bytes) -> dict[str, object]:
        return json.loads(data)


middleware = [
    Middleware(SessionMiddleware, serializer=MySerializer()),
]
```

## Session termination

The middleware automatically removes the session cookie and backend data when the session is empty. To clear the session manually:

```python
request.session.clear()
```

## Regenerating session ID

Sometimes you need a new session ID to avoid session fixation attacks (for example, after successful sign-in).
For that, use the `regenerate_session_id(connection)` utility.

```python
from starsessions import regenerate_session_id
from starlette.responses import Response


async def login(request):
    regenerate_session_id(request)
    return Response('successfully signed in')
```
