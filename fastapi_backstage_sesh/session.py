#!/usr/bin/env python3
# Copyright (C) 2019-2021 All rights reserved.
# FILENAME: session.py
# VERSION: 	0.0.1
# CREATED: 	2021-08-31 16:10
# AUTHOR: 	Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************
### Standard Packages ###
from typing import Any, Dict, ItemsView, KeysView, ValuesView
### Local Modules ###
from .backends import BackstageSeshBackend
from .exceptions import SessionNotLoaded

class Session:
  def __init__(self, backend: BackstageSeshBackend, session_id: str = None) -> None:
    self.session_id = session_id
    self._data: Dict[str, Any] = {}
    self._backend = backend
    self.is_loaded = False
    self._is_modified = False

  @property
  def is_empty(self) -> bool:
    '''
    Check if session has data.
    '''
    return len(self.keys()) == 0

  @property
  def is_modified(self) -> bool:
    '''
    Check if session data has been modified,
    '''
    return self._is_modified

  @property
  def data(self) -> Dict:
    if not self.is_loaded:
      raise SessionNotLoaded("Session is not loaded.")
    return self._data

  @data.setter
  def data(self, value: Dict[str, Any]) -> None:
    self._data = value

  async def load(self) -> None:
    '''
    Load data from the backend. Subsequent calls do not take any effect.
    '''
    if self.is_loaded:
      return
    if not self.session_id:
      self.data = {}
    else:
      self.data = await self._backend.read(self.session_id)
    self.is_loaded = True

  async def persist(self) -> str:
    self.session_id = await self._backend.write(self.data, self.session_id)
    return self.session_id

  async def delete(self) -> None:
    if self.session_id:
      self.data = {}
      self._is_modified = True
      await self._backend.remove(self.session_id)

  async def flush(self) -> str:
    self._is_modified = True
    await self.delete()
    return await self.regenerate_id()

  async def regenerate_id(self) -> str:
    self.session_id = await self._backend.generate_id()
    self._is_modified = True
    return self.session_id

  def keys(self) -> KeysView[str]:
    return self.data.keys()

  def values(self) -> ValuesView[Any]:
    return self.data.values()

  def items(self) -> ItemsView[str, Any]:
    return self.data.items()

  def pop(self, key: str, default: Any = None) -> Any:
    self._is_modified = True
    return self.data.pop(key, default)

  def get(self, name: str, default: Any = None) -> Any:
    return self.data.get(name, default)

  def setdefault(self, key: str, default: Any) -> None:
    self._is_modified = True
    self.data.setdefault(key, default)

  def clear(self) -> None:
    self._is_modified = True
    self.data.clear()

  def update(self, *args: Any, **kwargs: Any) -> None:
    self._is_modified = True
    self.data.update(*args, **kwargs)

  def __contains__(self, key: str) -> bool:
    return key in self.data

  def __setitem__(self, key: str, value: Any) -> None:
    self._is_modified = True
    self.data[key] = value

  def __getitem__(self, key: str) -> Any:
    return self.data[key]

  def __delitem__(self, key: str) -> None:
    self._is_modified = True
    del self.data[key]
