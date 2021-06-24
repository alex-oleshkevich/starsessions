import datetime

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Route

from starsessions import SessionMiddleware


async def homepage(request):
    """Access this view (GET "/") to display session contents."""
    return JSONResponse(request.session.data)


async def set_time(request):
    """Access this view (GET "/set") to set session contents."""
    request.session["date"] = datetime.datetime.now().isoformat()
    return RedirectResponse("/")


async def clean(request):
    """Access this view (GET "/clean") to remove all session contents."""
    await request.session.flush()
    return RedirectResponse("/")


routes = [
    Route("/", endpoint=homepage),
    Route("/set", endpoint=set_time),
    Route("/clean", endpoint=clean),
]
middleware = [Middleware(SessionMiddleware, secret_key="secret", autoload=True)]
app = Starlette(debug=True, routes=routes, middleware=middleware)
