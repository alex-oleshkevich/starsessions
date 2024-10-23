"""
This example demonstrates session-only cookies.

1. open http://localhost:8000 and set session data
2. return to http://localhost:8000 and check that session data is set
3. close the browser
4. open the browser, navigate to http://localhost:8000
5. see that session was removed

Note, the actual behavior depends on browser. If you use Chrome then you may need to close all Chrome processes.

Usage:
> uvicorn examples.session_only:app

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
    Middleware(SessionMiddleware, store=CookieStore(secret_key="key"), cookie_https_only=False),
    Middleware(SessionAutoloadMiddleware),
]
app = Starlette(debug=True, routes=routes, middleware=middleware)
