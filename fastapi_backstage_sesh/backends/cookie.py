#!/usr/bin/env python3
# Copyright (C) 2019-2021 All rights reserved.
# FILENAME: backends/cookie.py
# VERSION: 	0.0.1
# CREATED: 	2021-08-31 16:10
# AUTHOR: 	Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
### Standard Packages ###
from base64 import b64decode, b64encode
from json import dumps, loads
from typing import Dict, Optional, Union
### Third-Party Packages ###
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from pydantic import SecretStr
### Local Modules ###
from .base import BackstageSeshBackend

class CookieBackend(BackstageSeshBackend):
  '''
  Stores session data in the browser's cookie as a signed string.
  '''

  def __init__(self, secret_key: Union[str, SecretStr], max_age: int):
    self._signer = TimestampSigner(str(secret_key))
    self._max_age = max_age

  async def read(self, session_id: str) -> Dict:
    '''
    A session_id is a signed session value.
    '''
    try:
      data = self._signer.unsign(session_id, max_age=self._max_age)
      return loads(b64decode(data))
    except (BadSignature, SignatureExpired):
      return {}

  async def write(self, data: Dict, session_id: Optional[str] = None) -> str:
    '''
    The data is a session id in this backend.
    '''
    encoded_data = b64encode(dumps(data).encode('utf-8'))
    return self._signer.sign(encoded_data).decode('utf-8')

  async def remove(self, session_id: Optional[str] = None) -> None:
    '''
    Session data stored on client side - no way to remove it.
    '''

  async def exists(self, session_id: Optional[str] = None) -> bool:
    return False
