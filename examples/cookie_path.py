"""
This examples demonstrates base usage of this library. A CookieBackend is used.

Usage:
> uvicorn examples.app:app

Access localhost:8000/ to see that no session cookie available
access localhost:8000/admin to see session data
access localhost:8000/admin/set to set session data
access localhost:8000/admin/clean to clear session data
"""
import datetime
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

from starsessions import CookieBackend, SessionMiddleware


async def landing(request: Request) -> JSONResponse:
    """Access this view (GET "/") to display session contents."""
    return JSONResponse(dict(request.session))


async def homepage(request: Request) -> JSONResponse:
    """Access this view (GET "/admin") to display session contents."""
    return JSONResponse(dict(request.session))


async def set_time(request: Request) -> RedirectResponse:
    """Access this view (GET "/admin/set") to set session contents."""
    request.session["date"] = datetime.datetime.now().isoformat()
    return RedirectResponse("/admin")


async def clean(request: Request) -> RedirectResponse:
    """Access this view (GET "/admin/clean") to remove all session contents."""
    request.session.clear()
    return RedirectResponse("/admin")


routes = [
    Route("/", endpoint=landing),
    Route("/admin", endpoint=homepage),
    Route("/admin/set", endpoint=set_time),
    Route("/admin/clean", endpoint=clean),
]
middleware = [
    Middleware(SessionMiddleware, backend=CookieBackend(secret_key='key', max_age=18000), autoload=True, path='/admin')
]
app = Starlette(debug=True, routes=routes, middleware=middleware)
