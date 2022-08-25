"""
This examples demonstrates integration with FastAPI.

This example requires `fastapi` to be installed:
> pip install fastapi

Usage:
> uvicorn examples.fastapi_app:app

Access localhost:8000/set to set test session data, and
access localhost:8000/clean to clear session data
"""
import datetime
import typing
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse

from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

app = FastAPI()
app.add_middleware(SessionAutoloadMiddleware)
app.add_middleware(SessionMiddleware, store=CookieStore(secret_key="key"))


@app.get("/", response_class=JSONResponse)
async def homepage(request: Request) -> typing.Mapping[str, typing.Any]:
    """Access this view (GET '/') to display session contents."""
    return request.session


@app.get("/set", response_class=RedirectResponse)
async def set_time(request: Request) -> str:
    """Access this view (GET '/set') to set session contents."""
    request.session["date"] = datetime.datetime.now().isoformat()
    return "/"


@app.get("/clean", response_class=RedirectResponse)
async def clean(request: Request) -> str:
    """Access this view (GET '/clean') to remove all session contents."""
    request.session.clear()
    return "/"
