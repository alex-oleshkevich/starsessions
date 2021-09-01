#!/usr/bin/env python3
# Copyright (C) 2019-2020 All rights reserved.
# FILENAME:  backstage_config.py
# VERSION: 	 0.0.1
# CREATED: 	 2021-09-01 11:58
# AUTHOR: 	 Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
from typing import Callable, List, Optional, Union
from pydantic import SecretStr, ValidationError
from .backends import BackstageSeshBackend, CookieBackend
from .exceptions import ImproperlyConfigured
from .load_config import LoadConfig

class BackstageConfig(object):
  _https_only: bool                        = False
  _autoload: bool                          = False
  _security_flags: str                     = ''
  # In case of using cookies
  _cookie_samesite: str                    = 'none'
  _max_age: int                            = 14 * 24 * 60 * 60  # 14 days, in seconds
  _session_cookie: str                     = 'fastapi-backstage-sesh'
  _secret_key: Union[str, SecretStr]       = None
  _backend: Optional[BackstageSeshBackend] = None

  @classmethod
  def load_config(cls, settings: Callable[..., List[tuple]]) -> 'BackstageConfig':
    try:
      config = LoadConfig(**{key.lower(): value for key,value in settings()})
      cls._https_only       = config.https_only
      cls._autoload         = config.autoload
      cls._cookie_samesite  = config.cookie_samesite
      cls._max_age          = config.max_age
      cls._session_cookie   = config.session_cookie
      if config.backend is None:
        if config.secret_key is None:
          raise ImproperlyConfigured('CookieBackend requires secret_key argument.')
      cls._secret_key       = config.secret_key
      cls._backend          = config.backend or CookieBackend(secret_key=cls._secret_key, max_age=cls._max_age)
      cls._security_flags   = 'httponly; samesite=' + config.cookie_samesite
      if config.https_only: # Secure flag can be used with HTTPS only
        cls._security_flags += '; secure'
    except ValidationError: raise
    except Exception:
      raise TypeError('BackstageConfig must be pydantic "BaseSettings" or list of tuple')
