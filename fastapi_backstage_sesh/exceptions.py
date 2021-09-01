#!/usr/bin/env python3
# Copyright (C) 2019-2021 All rights reserved.
# FILENAME: exceptions.py
# VERSION: 	0.0.1
# CREATED: 	2021-08-31 16:10
# AUTHOR: 	Aekasitt Guruvanich <aekazitt@gmail.com>
# DESCRIPTION:
#
# HISTORY:
#*************************************************************

class SessionError(Exception):
  '''
  Base class for session exceptions
  '''

class SessionNotLoaded(SessionError):
  pass

class ImproperlyConfigured(SessionError):
  '''
  Exception is raised when some settings are missing or misconfigured
  '''
