#!/usr/bin/env python3
# Copyright (C) 2019-2021 All rights reserved.
# FILENAME: examples/cookie.py
# VERSION: 	0.0.1
# CREATED: 	2021-09-01 01:17
# AUTHOR: 	Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
### Standard Pacakges ###
import datetime
### Third-Party Packages ###
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
### Local Modules ###
from fastapi_backstage_sesh import BackstageSeshMiddleware

app = FastAPI()

class BackstageSettings(BaseModel):
  autoload: bool  = True
  secret_key: str = 'asecrettoeverybody'

@BackstageSeshMiddleware.load_config
def get_backstage_config():
  return BackstageSettings()

app.add_middleware(BackstageSeshMiddleware)

@app.get('/', response_class=JSONResponse)
async def homepage(request: Request):
  '''
  Access this view (GET '/') to display session contents.
  '''
  return request.session.data

@app.get('/set', response_class=RedirectResponse)
async def set_time(request: Request):
  '''
  Access this view (GET '/set') to set session contents.
  '''
  request.session['date'] = datetime.datetime.now().isoformat()
  return '/'

@app.get('/clean', response_class=RedirectResponse)
async def clean(request: Request):
  '''
  Access this view (GET '/clean') to remove all session contents.
  '''
  await request.session.flush()
  return '/'
