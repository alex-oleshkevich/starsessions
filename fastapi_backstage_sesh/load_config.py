#!/usr/bin/env python3
# Copyright (C) 2019-2020 All rights reserved.
# FILENAME:  load_config.py
# VERSION: 	 0.0.1
# CREATED: 	 2021-09-01 11:58
# AUTHOR: 	 Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
from typing import Optional, Union
from pydantic import BaseConfig, BaseModel, SecretStr, StrictBool, StrictInt, StrictStr, validator
### Local Modules ###
from .backends import BackstageSeshBackend

BaseConfig.arbitrary_types_allowed = True
class LoadConfig(BaseModel):
  https_only: StrictBool                  = False
  autoload: StrictBool                    = False
  # In case of using cookies
  cookie_samesite: StrictStr              = 'none'
  max_age: StrictInt                      = 14 * 24 * 60 * 60  # 14 days, in seconds
  session_cookie: StrictStr               = 'fastapi-backstage-sesh'
  secret_key: Union[str, SecretStr]       = None
  backend: Optional[BackstageSeshBackend] = None

  @validator('cookie_samesite')
  def validate_cookie_samesite(cls, value):
    if value not in { 'strict', 'lax', 'none' }:
      raise ValueError('The "cookie_samesite" must be between "strict", "lax", or "none".')
    return value
