"""
This example demonstrates Database store usage.

You can change database connection by specifying DATABASE_URL environment variable.

This example requires `databases` to be installed:
> pip install databases

Usage:
> uvicorn examples.database:app

Open http://localhost:8000 for management panel.
"""

import contextlib
import datetime
import json
import os
import typing

from databases import Database
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from starsessions import SessionAutoloadMiddleware, SessionMiddleware
from starsessions.stores.database import DatabaseStore, create_table

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://starsessions_demo")


async def homepage(request: Request) -> HTMLResponse:
    """Access this view (GET "/") to display session contents."""

    # built-in json.dumps cannot serialize Session object, convert it to dict first
    return HTMLResponse(
        f"<div>session data: {json.dumps(request.session)}</div>"
        "<ol>"
        '<li><a href="/set">set example data</a></li>'
        '<li><a href="/clean">clear example data</a></li>'
        "</ol>"
    )


async def set_time(request: Request) -> RedirectResponse:
    """Access this view (GET "/set") to set session contents."""
    request.session["hello"] = "world"
    request.session["date"] = datetime.datetime.now().isoformat()
    return RedirectResponse("/")


async def clean(request: Request) -> RedirectResponse:
    """Access this view (GET "/clean") to remove all session contents."""
    request.session.clear()
    return RedirectResponse("/")


database = Database(DATABASE_URL)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> typing.AsyncGenerator[typing.Dict[str, typing.Any], None]:
    async with database:
        await database.connect()

        # In normal operation Alembic should be used to create tables instead of calling create_table
        await create_table(database)

        yield {}

        await database.disconnect()


routes = [
    Route("/", endpoint=homepage),
    Route("/set", endpoint=set_time),
    Route("/clean", endpoint=clean),
]
middleware = [
    Middleware(SessionMiddleware, store=DatabaseStore(database=database), lifetime=10, rolling=True),
    Middleware(SessionAutoloadMiddleware),
]
app = Starlette(debug=True, routes=routes, middleware=middleware, lifespan=lifespan)
