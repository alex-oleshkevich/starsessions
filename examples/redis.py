"""
This examples demonstrates redis store usage.

You can change Redis connection by specifying REDIS_URL environment variable.

This example requires `aioredis` to be installed:
> pip install aioredis

Usage:
> uvicorn examples.redis:app

Open http://localhost:8000 for management panela
"""
import datetime
import json
import os
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from starsessions import SessionAutoloadMiddleware, SessionMiddleware
from starsessions.stores.redis import RedisStore

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost')


async def homepage(request: Request) -> HTMLResponse:
    """Access this view (GET "/") to display session contents."""

    # built-in json.dumps cannot serialize Session object, convert it to dict first
    return HTMLResponse(
        f'<div>session data: {json.dumps(request.session)}</div>'
        '<ol>'
        '<li><a href="/set">set example data</a></li>'
        '<li><a href="/clean">clear example data</a></li>'
        '</ol>'
    )


async def set_time(request: Request) -> RedirectResponse:
    """Access this view (GET "/set") to set session contents."""
    request.session["hello"] = 'world'
    request.session["date"] = datetime.datetime.now().isoformat()
    return RedirectResponse("/")


async def clean(request: Request) -> RedirectResponse:
    """Access this view (GET "/clean") to remove all session contents."""
    request.session.clear()
    return RedirectResponse("/")


routes = [
    Route("/", endpoint=homepage),
    Route("/set", endpoint=set_time),
    Route("/clean", endpoint=clean),
]
middleware = [
    Middleware(SessionMiddleware, store=RedisStore(REDIS_URL)),
    Middleware(SessionAutoloadMiddleware),
]
app = Starlette(debug=True, routes=routes, middleware=middleware)
