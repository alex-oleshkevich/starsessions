## Starsessions

Advanced sessions for Starlette and FastAPI frameworks

![PyPI](https://img.shields.io/pypi/v/starsessions)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/alex-oleshkevich/starsessions/Lint%20and%20test)
![GitHub](https://img.shields.io/github/license/alex-oleshkevich/starsessions)
![Libraries.io dependency status for latest release](https://img.shields.io/librariesio/release/pypi/starsessions)
![PyPI - Downloads](https://img.shields.io/pypi/dm/starsessions)
![GitHub Release Date](https://img.shields.io/github/release-date/alex-oleshkevich/starsessions)

## Installation

Install `starsessions` using PIP or poetry:

```bash
pip install starsessions
# or
poetry add starsessions
```

Use `redis` extra for [Redis support](#redis).

## Quick start

See example application in [`examples/`](examples) directory of this repository.

## Usage

1. Add `starsessions.SessionMiddleware` to your application to enable session support,
2. Configure session store and pass it to the middleware,
3. Load session in your view using `load_session` utility.

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


session_lifetime = 3600 * 24 * 14  # 14 days
session_store = CookieStore(secret_key='TOP SECRET')

app = Starlette(
    middleware=[
        Middleware(SessionMiddleware, store=session_store, lifetime=session_lifetime),
    ],
    routes=[
        Route('/', index_view),
    ]
)
```

### Cookie security

By default, the middleware uses strict default.
The cookie lifetime is limited to session and only HTTPS protocol allowed. You can change these defaults by using
`cookie_https_only` and `lifetime` arguments:

```python
from starlette.middleware import Middleware

from starsessions import CookieStore, SessionMiddleware

session_store = CookieStore(secret_key='TOP SECRET')

middleware = [
    Middleware(SessionMiddleware, store=session_store, cookie_https_only=False, lifetime=3600 * 24 * 14),
]
```

The example above will let session usage over insecure HTTP transport and the session lifetime will be extended to 14
days.

### Session autoload

For performance reasons session is not autoloaded by default. Sometimes it is annoying to call `load_session` too often.
We ship `SessionAutoloadMiddleware` to reduce amount of boilerplate code by autoloading session.

You have to options: always autoload or autoload for specific paths only. Here are examples:

```python

from starlette.middleware import Middleware

from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

session_lifetime = 3600 * 24 * 14  # 14 days
session_store = CookieStore(secret_key='TOP SECRET')

# Autoload session for every request

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

### Cookie path

You can pass `cookie_path` argument to bind session cookie to specific URLs. For example, to activate session cookie only
for admin area (which is hosted under `/admin` path prefix), use `cookie_path="/admin"` middleware argument.

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, cookie_path='/admin'),
]
```

All other URLs not matching value of `cookie_path` will not receive cookie thus session will be unavailable.

### Cookie domain

You can also specify which hosts can receive a cookie by passing `cookie_domain` argument to the middleware.

```python
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, cookie_domain='example.com'),
]
```

> Note, this makes session cookie available for subdomains too.
> For example, when you set `cookie_domain=example.com` then session cookie will be available on subdomains
> like `app.example.com`.

### Session-only cookies

If you want session cookie to automatically remove from tbe browser when tab closes then set `lifetime` to `0`.
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

Simply stores data in memory. The data is cleared after server restart. Mostly for use with unit tests.

### CookieStore

Class: `starsessions.CookieStore`

Stores session data in a signed cookie on the client.

### Redis

Class: `starsessions.stores.redis.RedisStore`

> Requires [aioredis](https://aioredis.readthedocs.io/en/latest/getting-started/),
> use `pip install starsessions[redis]` or `poetry add starsessions[redis]`

Stores session data in a Redis server. The store accepts either connection URL or an instance of `aioredis.Redis`.

```python
import aioredis

from starsessions.stores.redis import RedisStore

store = RedisStore('redis://localhost')
# or
redis = aioredis.from_url('redis://localhost')

store = RedisStore(connection=redis)
```

#### Redis key expiry

The store will use `lifetime` to set key expiration TTL.

It's important to note that on every session write, the Redis expiry resets.
For example, if you set the Redis expire time for 10 seconds, and you perform another write to the session
in those 10 seconds, the expiry will be extended by 10 seconds.

## Custom store

Creating new stores is quite simple. All you need is to extend `starsessions.SessionStore`
class and implement abstract methods.

Here is an example of how we can create a memory-based session store. Note, it is important that `write` method
returns session ID as a string value.

```python
from typing import Dict

from starsessions import SessionStore


# instance of class which manages session persistence

class InMemoryStore(SessionStore):
    def __init__(self):
        self._storage = {}

    async def read(self, session_id: str, lifetime: int) -> Dict:
        """ Read session data from a data source using session_id. """
        return self._storage.get(session_id, {})

    async def write(self, session_id: str, data: Dict, lifetime: int) -> str:
        """ Write session data into data source and return session id. """
        self._storage[session_id] = data
        return session_id

    async def remove(self, session_id: str):
        """ Remove session data. """
        del self._storage[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self._storage
```

## Serializers

Sometimes you cannot pass raw session data to the store. The data must be serialized into something the store can
handle.

Some stores (like `RedisStore`) optionally accept `serializer` argument that will be used to serialize and
deserialize session data. By default, we provide (and use) `starsessions.JsonSerializer` but you can implement your own
by extending `starsessions.Serializer` class.

## Session termination

The middleware will remove session data and cookie if session has no data. Use `request.session.clear` to empty data.

## Regenerating session ID

Sometimes you need a new session ID to avoid session fixation attacks (for example, after successful signs in).
For that, use `starsessions.session.regenerate_session_id(connection)` utility.

```python
from starsessions.session import regenerate_session_id
from starlette.responses import Response


def login(request):
    regenerate_session_id(request)
    return Response('successfully signed in')
```
