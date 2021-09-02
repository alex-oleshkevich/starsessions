## Pluggable session support for Starlette and FastAPI frameworks

This package is based on this long standing [pull request](https://github.com/encode/starlette/pull/499) in the
mainstream by the same author.

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

## Enable session support

In order to enable session support add `starsessions.SessionMiddleware` to your application.

```python
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starsessions import SessionMiddleware

middleware = [
    Middleware(SessionMiddleware, secret_key='TOP SECRET'),
]

app = Starlette(middleware=middleware, **other_options)
```

### Session autoloading

Note, for performance reasons session won't be autoloaded by default, you need to explicitly
call `await request.session.load()` before accessing the session otherwise `SessionNotLoaded` exception will be raised.
You can change this behavior by passing `autoload=True` to your middleware settings:

```python
Middleware(SessionMiddleware, secret_key='TOP SECRET', autoload=True)
```

### Default session backend

The default backend is `CookieBackend`. You don't need to configure it just pass `secret_key` argument and the backend
will be automatically configured for you.

## Change default backend

When you want to use a custom session storage then pass a desired backend instance via `backend` argument of the
middleware.

```python
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.sessions import CookieBackend

backend = CookieBackend(secret_key='secret', max_age=3600)

app = Starlette()
app.add_middleware(SessionMiddleware, backend=backend)
```

## Built-in backends

### Memory

Class: `starsessions.InMemoryBackend`

Simply stores data in memory. The data is cleared after server restart. Mostly for use with unit tests.

### CookieBackend

Class: `starsessions.CookieBackend`

Stores session data in a signed cookie on the client. This is the default backend.

### Redis

Class: `starsessions.backends.redis.RedisBackend`

> Requires [aioredis](https://aioredis.readthedocs.io/en/latest/getting-started/),
> use `pip install starsessions[redis]` or `poetry add starsessions[redis]`

Stores session data in a Redis server. The backend accepts either connection URL or an instance of `aioredis.Redis`.

```python
import aioredis
from starsessions.backends.redis import RedisBackend

backend = RedisBackend('redis://localhost')
# or
redis = aioredis.from_url('redis://localhost')

backend = RedisBackend(connection=redis)
```

## Custom backend

Creating new backends is quite simple. All you need is to extend `starsessions.SessionBackend`
class and implement abstract methods.

Here is an example of how we can create a memory-based session backend. Note, it is important that `write` method
returns session ID as a string value.

```python
from starlette.sessions import SessionBackend
from typing import Dict


# instance of class which manages session persistence

class InMemoryBackend(SessionBackend):
    def __init__(self):
        self._storage = {}

    async def read(self, session_id: str) -> Dict:
        """ Read session data from a data source using session_id. """
        return self._storage.get(session_id, {})

    async def write(self, data: Dict, session_id: str = None) -> str:
        """ Write session data into data source and return session id. """
        session_id = session_id or await self.generate_id()
        self._storage[session_id] = data
        return session_id

    async def remove(self, session_id: str):
        """ Remove session data. """
        del self._storage[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self._storage
```

## Serializers

Sometimes you cannot pass raw session data to the backend. The data must be serialized into something the backend can
handle.

Some backends (like `RedisBackend`) optionally accept `serializer` argument that will be used to serialize and
deserialize session data. By default, we provide (and use) `starsessions.JsonSerializer` but you can implement your own
by extending `starsessions.Serializer` class.
