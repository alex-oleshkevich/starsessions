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
from fastapi.testclient import TestClient
from pydantic import BaseModel
### Local Modules ###
from fastapi_backstage_sesh import ( 
  BackstageSeshMiddleware, InMemoryBackend
)

def testclient_cookie(app: FastAPI = FastAPI()) -> TestClient:
  # middleware
  class CookieBackstageSettings(BaseModel):
    autoload: bool  = True
    secret_key: str = 'asecrettoeverybody'
  @BackstageSeshMiddleware.load_config
  def get_backstage_config():
    return CookieBackstageSettings()
  app.add_middleware(BackstageSeshMiddleware)
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
  # returns
  return TestClient(app)

def testclient_memory(app: FastAPI = FastAPI()) -> TestClient:
  # middleware
  class InMemoryBackstageSettings(BaseModel):
    autoload: bool           = True
    backend: InMemoryBackend = InMemoryBackend()
  @BackstageSeshMiddleware.load_config
  def get_backstage_config():
    return InMemoryBackstageSettings()
  app.add_middleware(BackstageSeshMiddleware)
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
  # returns
  return TestClient(app)

def testclient_secondapp(second_app: FastAPI = FastAPI()) -> TestClient:
  app: TestClient = testclient_cookie()
  # middleware
  class CookieBackstageSettings(BaseModel):
    autoload: bool  = True
    secret_key: str = 'example'
  @BackstageSeshMiddleware.load_config
  def get_backstage_config():
    return CookieBackstageSettings()
  second_app.add_middleware(BackstageSeshMiddleware)
  # routes
  @second_app.get('/view_session', response_class=JSONResponse)
  async def view_session(request: Request):
    return { 'session': request.session.data }
  @second_app.post('/update_session', response_class=JSONResponse)
  async def update_session(request: Request):
    request.session.update(await request.json())
    return { 'session': request.session.data }
  @second_app.post('/clear_session', response_class=JSONResponse)
  async def clear_session(request: Request):
    await request.session.flush()
    return { 'session': request.session.data }
  # returns
  app.mount('/second_app', second_app)
  return app
