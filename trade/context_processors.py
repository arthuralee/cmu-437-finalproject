from django.contrib.auth.models import User
from trade.models import *
from django.db.models import Q

def get_users(request):
  return {}
  if not request.user.is_authenticated(): 
    return {'users' : User.objects.all().order_by('username')}
  users = []
  followers = UserWithFollowers.objects.get(user=request.user.username).followers.all()
  for user in User.objects.all():
    if user in followers:
      user.btn_style = 'btn-info'
    else:
      user.btn_style = 'btn-default'
    users.append(user)
  return {'users' : sorted(users, key=lambda u: u.username)}

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