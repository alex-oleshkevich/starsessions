"""
This example demonstrates base usage of this library. The session will expire in 10 seconds of inactivity but will be
extended by another 10 seconds while you use the demo.

Usage:
> uvicorn examples.rolling:app

Open http://localhost:8000 for demo page.
"""
import datetime
import json
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware


async def homepage(request: Request) -> HTMLResponse:
    """Access this view (GET "/") to display session contents."""
    return HTMLResponse(
        f"<div>session data: {json.dumps(request.session)}</div>"
        "<ol>"
        '<li><a href="/set">set example data</a></li>'
        '<li><a href="/clean">clear example data</a></li>'
        "</ol>"
    )


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
middleware = [
    Middleware(
        SessionMiddleware,
        store=CookieStore(secret_key="key"),
        rolling=True,
        cookie_https_only=False,
        lifetime=10,
    ),
    Middleware(SessionAutoloadMiddleware),
]
app = Starlette(debug=True, routes=routes, middleware=middleware)
