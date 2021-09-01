#!/usr/bin/env python3
# Copyright (C) 2019-2021 All rights reserved.
# FILENAME: middleware.py
# VERSION: 	0.0.1
# CREATED: 	2021-08-31 16:10
# AUTHOR: 	Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
### Third-Party Packages ###
from fastapi.requests import Request
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
### Local Modules ###
from .backends import BackstageSeshBackend
from .backstage_config import BackstageConfig
from .session import Session

class BackstageSeshMiddleware(BackstageConfig):

  def __init__(self, app: ASGIApp):
    self._app = app

  @property
  def app(self) -> ASGIApp:
    return self._app

  @property
  def autoload(self) -> bool:
    return self._autoload

  @property
  def backend(self) -> BackstageSeshBackend:
    return self._backend

  @property
  def max_age(self) -> int:
    return self._max_age

  @property
  def security_flags(self) -> str:
    return self._security_flags

  @property
  def session_cookie(self) -> str:
    return self._session_cookie

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    if scope['type'] not in ('http', 'websocket'):  # pragma: no cover
      await self.app(scope, receive, send)
      return
    connection = Request(scope)
    session_id = connection.cookies.get(self.session_cookie, None)
    scope['session'] = Session(self.backend, session_id)
    if self.autoload:
      await scope['session'].load()
    async def send_wrapper(message: Message) -> None:
      if message['type'] == 'http.response.start':
        path = scope.get('root_path', '') or '/'
        if scope['session'].is_modified:
          # We have session data to persist (data was changed, cleared, etc).
          nonlocal session_id
          session_id = await scope['session'].persist()
          headers = MutableHeaders(scope=message)
          header_value = '%s=%s; path=%s; Max-Age=%d; %s' % (
            self.session_cookie,
            session_id,
            path,
            self.max_age, self.security_flags,
          )
          headers.append('Set-Cookie', header_value)
        elif scope['session'].is_loaded and scope['session'].is_empty:
          # no interactions to session were done
          headers = MutableHeaders(scope=message)
          header_value = '{}={}; {}'.format(
            self.session_cookie,
            f'null; path={path}; expires=Thu, 01 Jan 1970 00:00:00 GMT;',
            self.security_flags,
          )
          headers.append('Set-Cookie', header_value)
      await send(message)
    await self.app(scope, receive, send_wrapper)
