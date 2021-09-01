import datetime

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse

from starsessions import SessionMiddleware

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key='secret', autoload=True)

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
