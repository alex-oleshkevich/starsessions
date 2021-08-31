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
### Standard Packages ###
from typing import Union
### Third-Party Packages ###
from fastapi.requests import Request
from pydantic import SecretStr
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
### Local Modules ###
from .exceptions import ImproperlyConfigured
from .backends.base import FastapiSeshBackend
from .backends.cookie import CookieBackend
from .session import Session
class FastapiSeshMiddleware:
  def __init__(
    self,
    app: ASGIApp,
    session_cookie: str = 'fastapi-sesh',
    max_age: int = 14 * 24 * 60 * 60,  # 14 days, in seconds
    same_site: str = 'lax',
    https_only: bool = False,
    autoload: bool = False,
    secret_key: Union[str, SecretStr] = None,
    backend: FastapiSeshBackend = None,
  ) -> None:
    self.app = app
    if backend is None:
      if secret_key is None:
        raise ImproperlyConfigured('CookieBackend requires secret_key argument.')
      backend = CookieBackend(secret_key, max_age)
    self.backend = backend
    self.session_cookie = session_cookie
    self.max_age = max_age
    self.autoload = autoload
    self.security_flags = 'httponly; samesite=' + same_site
    if https_only:  # Secure flag can be used with HTTPS only
      self.security_flags += '; secure'

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
            self.max_age,
            self.security_flags,
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
