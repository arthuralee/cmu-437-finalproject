from django.contrib.auth.models import User
from trade.models import *
from django.db.models import Q

def get_userdata(request):
  if not request.user.is_authenticated():
    return {}

  userdata = UserData.objects.get(user=request.user)
  return {'userdata' : userdata}

def nav(request):
  nav = {}
  if request.path == "/":
    nav['home'] = True
  elif 'user' in request.path and request.user.username in request.path:
    nav['profile'] = True
  elif 'manage' in request.path:
    nav['catalog'] = True
  elif 'trade' in request.path:
    nav['trade'] = True
  elif 'login' in request.path:
    nav['login'] = True
  elif 'register' in request.path:
    nav['register'] = True
  return {'nav': nav}