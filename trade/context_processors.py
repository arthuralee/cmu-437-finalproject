from django.contrib.auth.models import User
from models import UserWithFollowers

def get_users(request):
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