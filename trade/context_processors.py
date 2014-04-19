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

def get_trades(request):
  if request.user.is_authenticated():
    trades = Trade.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    return {'trades': trades}
  else:
    return {'trades': []}