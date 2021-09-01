#!/usr/bin/env python3
# Copyright (C) 2019-2021 All rights reserved.
# FILENAME: tests/middleware.py
# VERSION: 	0.0.1
# CREATED: 	2021-08-31 16:10
# AUTHOR: 	Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
### Standard Packages ###
from re import Match, search
from typing import Callable
### Third-Party Packages ###
import pytest
from fastapi.responses import Response
from fastapi.testclient import TestClient
### Local Modules ###
from . import (
  testclient_cookie, testclient_memory, testclient_secondapp
)

@pytest.mark.parametrize('setup', [testclient_cookie, testclient_memory])
def test_session(setup: Callable):
  client: TestClient     = setup()
  response: Response     = client.get('/view_session')
  assert response.json() == {'session': {}}
  response: Response     = client.post('/update_session', json={'some': 'data'})
  assert response.json() == {'session': {'some': 'data'}}
  # check cookie max-age
  set_cookie             = response.headers['set-cookie']
  max_age_matches: Match = search(r'; Max-Age=([0-9]+);', set_cookie)
  assert max_age_matches is not None
  assert int(max_age_matches[1]) == 14 * 24 * 3600
  response: Response     = client.get('/view_session')
  assert response.json() == { 'session': { 'some': 'data' }}
  response: Response     = client.post('/clear_session')
  assert response.json() == { 'session': {} }
  response: Response     = client.get('/view_session')
  assert response.json() == { 'session': {} }

@pytest.mark.parametrize('setup', [testclient_cookie, testclient_memory])
def test_empty_session(setup: Callable):
  client: TestClient     = setup()
  headers: dict          = { 'cookie': 'session=someid' }
  response: Response     = client.get('/view_session', headers=headers)
  assert response.json() == {'session': {}}

@pytest.mark.parametrize('setup', [testclient_cookie, testclient_memory])
def test_session_expires(setup: Callable):
  client: TestClient           = setup()
  response: Response           = client.post('/update_session', json={'some': 'data'})
  assert response.json()       == { 'session': { 'some': 'data' }}
  # requests removes expired cookies from response.cookies, we need to
  # fetch session id from the headers and pass it explicitly
  expired_cookie_header        = response.headers['set-cookie']
  expired_session_value: Match = search(r'session=([^;]*);', expired_cookie_header)[1]
  response: Response           = client.get('/view_session', cookies={'session': expired_session_value})
  assert response.json() == {'session': {}}

# @pytest.mark.parametrize('setup', [testclient_cookie, testclient_memory])
# def test_secure_session(setup: Callable):
#   client: TestClient    = setup()
#   secure_client         = TestClient(app, base_url='https://testserver')
#   unsecure_client       = TestClient(app, base_url='http://testserver')
#   response = unsecure_client.get('/view_session')
#   assert response.json() == {'session': {}}
#   response = unsecure_client.post('/update_session', json={'some': 'data'})
#   assert response.json() == {'session': {'some': 'data'}}
#   response = unsecure_client.get('/view_session')
#   assert response.json() == {'session': {}}
#   response = secure_client.get('/view_session')
#   assert response.json() == {'session': {}}
#   response = secure_client.post('/update_session', json={'some': 'data'})
#   assert response.json() == {'session': {'some': 'data'}}
#   response = secure_client.get('/view_session')
#   assert response.json() == {'session': {'some': 'data'}}
#   response = secure_client.post('/clear_session')
#   assert response.json() == {'session': {}}
#   response = secure_client.get('/view_session')
#   assert response.json() == {'session': {}}

@pytest.mark.parametrize('setup', [ testclient_secondapp ])
def test_session_cookie_subpath(setup: Callable):
  client: TestClient = setup()
  response           = client.post('/second_app/update_session', json={'some': 'data'})
  cookie             = response.headers['set-cookie']
  cookie_path: Match = search(r'; path=(\S+);', cookie).groups()[0]
  assert cookie_path == '/second_app' # TODO Unfails
