#!/usr/bin/env python3
# Copyright (C) 2019-2021 All rights reserved.
# FILENAME: backends/in_memory.py
# VERSION: 	0.0.1
# CREATED: 	2021-08-31 16:10
# AUTHOR: 	Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
### Standard Packages ###
from typing import Dict, Optional
### Local Modules ###
from .base import BackstageSeshBackend

class InMemoryBackend(BackstageSeshBackend):
  '''
  Stores session data in a dictionary.
  '''

  def __init__(self) -> None:
    self.data: dict = {}

  async def read(self, session_id: str) -> Dict:
    return self.data.get(session_id, {}).copy()

  async def write(self, data: Dict, session_id: Optional[str] = None) -> str:
    session_id = session_id or await self.generate_id()
    self.data[session_id] = data
    return session_id

  async def remove(self, session_id: str) -> None:
    del self.data[session_id]

  async def exists(self, session_id: str) -> bool:
    return session_id in self.data
