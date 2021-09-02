"""This examples demonstrates redis backend usage.

You can change Redis connection by specifying REDIS_URL environment variable.

This example requires `aioredis` to be installed:
> pip install aioredis

Usage:
> uvicorn examples.redis:app

Access localhost:8000/set to set test session data, and
access localhost:8000/clean to clear session data
"""
import datetime
import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

from starsessions import SessionMiddleware
from starsessions.backends.redis import RedisBackend

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost')


async def homepage(request):
    """Access this view (GET "/") to display session contents."""
    return JSONResponse(request.session.data)


async def set_time(request):
    """Access this view (GET "/set") to set session contents."""
    request.session["hello"] = 'world'
    request.session["date"] = datetime.datetime.now().isoformat()
    return RedirectResponse("/")


async def clean(request):
    """Access this view (GET "/clean") to remove all session contents."""
    request.session.clear()
    return RedirectResponse("/")


routes = [
    Route("/", endpoint=homepage),
    Route("/set", endpoint=set_time),
    Route("/clean", endpoint=clean),
]
middleware = [Middleware(SessionMiddleware, backend=RedisBackend(REDIS_URL), autoload=True)]
app = Starlette(debug=True, routes=routes, middleware=middleware)
