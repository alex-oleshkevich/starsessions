from sqlite3 import connect

## Starsessions

Advanced sessions for Starlette and FastAPI frameworks

![PyPI](https://img.shields.io/pypi/v/starsessions)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/alex-oleshkevich/starsessions/lint_and_test.yml?branch=master)
![GitHub](https://img.shields.io/github/license/alex-oleshkevich/starsessions)
![Libraries.io dependency status for latest release](https://img.shields.io/librariesio/release/pypi/starsessions)
![PyPI - Downloads](https://img.shields.io/pypi/dm/starsessions)
![GitHub Release Date](https://img.shields.io/github/release-date/alex-oleshkevich/starsessions)

## Installation

Install `starsessions` package:

```bash
pip install starsessions
```

Use `redis` extra for [Redis support](#redis).

## Quick start

See the example application in [`examples/`](examples) directory of this repository.

## Usage

1. Add `starsessions.SessionMiddleware` to your application to enable session support,
2. Configure the session store and pass it to the middleware,
3. Load the session in your view/middleware by calling `load_session(connection)` utility.

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

By default, the middleware uses strict defaults.
The cookie lifetime is limited to the browser session and sent via HTTPS protocol only.
You can change these defaults by changing `cookie_https_only` and `lifetime` arguments:

```python
from starlette.middleware import Middleware

from starsessions import CookieStore, SessionMiddleware

session_store = CookieStore(secret_key='TOP SECRET')

middleware = [
    Middleware(SessionMiddleware, store=session_store, cookie_https_only=False, lifetime=3600 * 24 * 14),
]
```

The example above will let session usage over insecure HTTP transport and the session lifetime will be set to 14 days.

### Loading session

The session data is not loaded by default. Call `load_session` to load data from the store.

```python
async def index_view(request):
    await load_session(request)
    request.session['key'] = 'value'
```

However, if you try to access an uninitialized session, `SessionNotLoaded` exception will be raised.

```python
async def index_view(request):
    request.session['key'] = 'value'  # raises SessionNotLoaded
```

You can automatically load a session by using `SessionAutoloadMiddleware` middleware.

### Session autoload

For performance reasons, the session is not autoloaded by default. Sometimes it is annoying to call `load_session` too
often.
We provide `SessionAutoloadMiddleware` class to reduce the boilerplate code by autoloading the session for you.

There are two options: always autoload or autoload for specific paths only.
Here are examples:

```python
from starlette.middleware import Middleware

from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

session_store = CookieStore(secret_key='TOP SECRET')

# Always autoload

middleware = [
    Middleware(SessionMiddleware, store=session_store),
    Middleware(SessionAutoloadMiddleware),
]

# Autoload session for selected paths

middleware = [
    Middleware(SessionMiddleware, store=session_store),
    Middleware(SessionAutoloadMiddleware, paths=['/admin', '/app']),
]

# regex patterns also supported
import re

admin_rx = re.compile('/admin*')

middleware = [
    Middleware(SessionMiddleware, store=session_store),
    Middleware(SessionAutoloadMiddleware, paths=[admin_rx]),
]
```

### Rolling sessions

The default behavior of `SessionMiddleware` is to expire the cookie after `lifetime` seconds after it was set.
For example, if you create a session with `lifetime=3600`, the session will be terminated exactly in 3600 seconds.
Sometimes this may not be what you need, so we provide an alternate expiration strategy - rolling sessions.

When rolling sessions are activated, the cookie expiration time will be extended by `lifetime` value on every response.
Let's see how it works for example. First, on the first response you create a new session with `lifetime=3600`,
then the user does another request, and the session gets extended by another 3600 seconds, and so on.
This approach is useful when you want to use short-timed sessions but don't want them to interrupt in the middle of
the user's operation. With the rolling strategy, a session cookie will expire only after some period of the user's
inactivity.

To enable the rolling strategy set `rolling=True`.

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, lifetime=300, rolling=True),
]
```

The snippet above demonstrates an example setup where the session will be dropped after 300 seconds (5 minutes) of
inactivity, but will be automatically extended by another 5 minutes while the user is online.

### Cookie path

You can pass `cookie_path` argument to bind the session cookies to specific URLs. For example, to activate a session
cookie
only for the admin area, use `cookie_path="/admin"` middleware argument.

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, cookie_path='/admin'),
]
```

All other URLs not matching the value of `cookie_path` will not receive cookies thus session will be unavailable.

### Cookie domain

You can also specify which hosts can receive a cookie by passing `cookie_domain` argument to the middleware.

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, cookie_domain='example.com'),
]
```

> Note, this makes session cookies available for subdomains too.
> For example, when you set `cookie_domain=example.com` then session cookie will be available on subdomains
> like `app.example.com`.

### Session-only cookies

If you want the session cookie to be automatically removed from the browser when the tab closes set `lifetime` to `0`.
> Note, this depends on browser implementation!

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

Simply stores data in memory. The data is cleared after the server restart. Mostly for use with unit tests.

### CookieStore

Class: `starsessions.CookieStore`

Stores session data in a signed cookie on the client.

### Redis

Class: `starsessions.stores.redis.RedisStore`

Stores session data in a Redis server. The store accepts either a connection URL or an instance of `Redis`.

> Requires [redis-py](https://github.com/redis/redis-py),
> use `pip install starsessions[redis]`

> Note, redis-py requires explicit disconnect of connection. The library does not handle it for you at the moment.
> The recommended solution is to pass a Redis instance to the store and call `.close()` on application shutdown.
> For example, you can close the connection using lifespan handler.
> See more https://redis-py.readthedocs.io/en/latest/examples/asyncio_examples.html

```python
from redis.asyncio import Redis

from starsessions.stores.redis import RedisStore

client = Redis.from_url('redis://localhost')
store = RedisStore(connection=client)

store = RedisStore(connection=client)

# close connection on shutdown
await client.close()
```

#### Redis key prefix

By default, all keys in Redis prefixed with `starsessions.`. If you want to change this use `prefix` argument.

```python
from starsessions.stores.redis import RedisStore

store = RedisStore(url='redis://localhost', prefix='my_sessions')
```

Prefix can be a callable:

```python
from starsessions.stores.redis import RedisStore


def make_prefix(key: str) -> str:
    return 'my_sessions_' + key


store = RedisStore(url='redis://localhost', prefix=make_prefix)
```

#### Key expiration

The library automatically manages key expiration, usually you have nothing to do with it.
But for cases when `lifetime=0` we don't know when the session will be over, and we have to heuristically calculate TTL,
otherwise the data will remain in Redis forever. At this moment, we just set 30 days TTL. You can change it by
setting `gc_ttl` value on the store.

```python
from starsessions.stores.redis import RedisStore

store = RedisStore(url='redis://localhost', gc_ttl=3600)  # max 1 hour
```

## Custom store

Creating new stores is quite simple. All you need is to extend `starsessions.SessionStore`
class and implement abstract methods.

Here is an example of how we can create a memory-based session store. Note, that it is important that `write` method
returns session ID as a string value.

```python
from typing import Dict

from starsessions import SessionStore


# instance of class that manages session persistence

class InMemoryStore(SessionStore):
    def __init__(self):
        self._storage = {}

    async def read(self, session_id: str, lifetime: int) -> bytes:
        """ Read session data from a data source using session_id. """
        return self._storage.get(session_id, {})

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        """ Write session data into the data source and return session ID. """
        self._storage[session_id] = data
        return session_id

    async def remove(self, session_id: str):
        """ Remove session data. """
        del self._storage[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self._storage
```

### lifetime and ttl

The `write` accepts two special arguments: `lifetime` and `ttl`.
The difference is that `lifetime` is the total session duration (set by the middleware)
and `ttl` is the remaining session time. After `ttl` seconds the data can be safely deleted from the storage.

> Your custom backend has to correctly handle cases when `lifetime = 0`.
> In such cases, you don't have an exact expiration value, and you would have to find a way to extend session TTL on the
> storage
> side, if any.

## Serializers

The library automatically serializes session data to string using JSON.
By default, we use `starsessions.JsonSerializer` but you can implement your own by extending `starsessions.Serializer`
class.

```python
import json
import typing

from starlette.middleware import Middleware

from starsessions import Serializer, SessionMiddleware


class MySerializer(Serializer):
    def serialize(self, data: typing.Any) -> bytes:
        return json.dumps(data).encode('utf-8')

    def deserialize(self, data: bytes) -> typing.Dict[str, typing.Any]:
        return json.loads(data)


middleware = [
    Middleware(SessionMiddleware, serializer=MySerializer()),
]
```

## Session termination

The middleware will remove session data and cookies if the session has no data. Use `request.session.clear` to empty
data.

## Regenerating session ID

Sometimes you need a new session ID to avoid session fixation attacks (for example, after successful signs-in).
For that, use `starsessions.session.regenerate_session_id(connection)` utility.

```python
from starsessions.session import regenerate_session_id
from starlette.responses import Response


def login(request):
    regenerate_session_id(request)
    return Response('successfully signed in')
```
