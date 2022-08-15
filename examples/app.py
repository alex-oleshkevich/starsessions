"""
This examples demonstrates base usage of this library. A CookieBackend is used.

Usage:
> uvicorn examples.app:app

Access localhost:8000/set to set test session data, and
access localhost:8000/clean to clear session data
"""
import datetime
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

from starsessions import CookieStore, SessionMiddleware


async def homepage(request: Request) -> JSONResponse:
    """Access this view (GET "/") to display session contents."""
    return JSONResponse(dict(request.session))


async def set_time(request: Request) -> RedirectResponse:
    """Access this view (GET "/set") to set session contents."""
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
middleware = [Middleware(SessionMiddleware, backend=CookieStore(secret_key='key'), autoload=True)]
app = Starlette(debug=True, routes=routes, middleware=middleware)
