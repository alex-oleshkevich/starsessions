#!/usr/bin/env python3
# Copyright (C) 2019-2020 All rights reserved.
# FILENAME:  tests/__init__.py
# VERSION: 	 0.1.9
# CREATED: 	 2021-09-01 19:03
# AUTHOR: 	 Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
### Third-Party Packages ###
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
### Local Modules ###
from fastapi_backstage_sesh import ( 
  BackstageSeshMiddleware, InMemoryBackend
)

def create_app(app: FastAPI = FastAPI()) -> FastAPI:
  # routes
  @app.get('/view_session', response_class=JSONResponse)
  async def view_session(request: Request):
    return { 'session': request.session.data }
  @app.post('/update_session', response_class=JSONResponse)
  async def update_session(request: Request):
    request.session.update(await request.json())
    return { 'session': request.session.data }
  @app.post('/clear_session', response_class=JSONResponse)
  async def clear_session(request: Request):
    await request.session.flush()
    return { 'session': request.session.data }
  return app

def setup_cookie(app: FastAPI = create_app()) -> FastAPI:
  # middleware
  class CookieBackstageSettings(BaseModel):
    autoload: bool  = True
    secret_key: str = 'asecrettoeverybody'
  @BackstageSeshMiddleware.load_config
  def get_backstage_config():
    return CookieBackstageSettings()
  app.add_middleware(BackstageSeshMiddleware)
  # returns
  return app

def setup_memory(app: FastAPI = create_app()) -> FastAPI:
  # middleware
  class InMemoryBackstageSettings(BaseModel):
    autoload: bool           = True
    backend: InMemoryBackend = InMemoryBackend()
  @BackstageSeshMiddleware.load_config
  def get_backstage_config():
    return InMemoryBackstageSettings()
  app.add_middleware(BackstageSeshMiddleware)
  # returns
  return app

def setup_secondapp(app: FastAPI = create_app()) -> FastAPI:
  second_app: FastAPI = setup_cookie()
  # returns
  app.mount('/second_app', second_app)
  return app

def setup_httpsonly(app: FastAPI = create_app()) -> FastAPI:
  # middleware
  class HttpsOnlyCookieSettings(BaseModel):
    autoload: bool   = True
    secret_key: str  = 'asecrettoeverybody'
    https_only: bool = True
  @BackstageSeshMiddleware.load_config
  def get_backstage_config(): return HttpsOnlyCookieSettings()
  app.add_middleware(BackstageSeshMiddleware)
  # returns
  return app

def setup_instantexpiry(app: FastAPI = create_app()) -> FastAPI:
  # middleware
  class InstantExpiryCookieSettings(BaseModel):
    autoload: bool  = True
    secret_key: str = 'asecrettoeverybody'
    max_age: int    = -1
  @BackstageSeshMiddleware.load_config
  def get_backstage_config(): return InstantExpiryCookieSettings()
  app.add_middleware(BackstageSeshMiddleware)
  # returns
  return app
