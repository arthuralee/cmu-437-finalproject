from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required

# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator

from mimetypes import guess_type
from django.http import HttpResponse, Http404

from trade.models import *
import re
from django.core import serializers
import json


@login_required
def manage(request):
  # Sets up list of just the logged-in user's (request.user's) items
  items = Item.objects.filter(user=request.user).order_by('-date_time')
  return render(request, 'trade/index.html', {'items' : items})

def profile(request, id):
  # Sets up list of just the logged-in user's (request.user's) items
  user = User.objects.get(username = id)
  items = Item.objects.filter(user=user).order_by('-date_time')
  return render(request, 'trade/profile.html', 
    {'items' : items, 
     'username' : user.username,
     'first_name' : user.first_name,
     'last_name' : user.last_name}
    )

@login_required
def add_item(request):
  errors = []

  # Creates a new post if it is present as a parameter in the request
  if not 'desc' in request.POST or not request.POST['desc']:
    errors.append('You must enter an description')
  else:
    new_item = Item(desc=request.POST['desc'], user=request.user)
    if 'image' in request.FILES:
      new_item.image = request.FILES['image']
    new_item.save()

  items = Item.objects.filter(user=request.user).order_by('-date_time')
  context = {'items' : items, 'errors' : errors}
  return render(request, 'trade/index.html', context)

def get_image(request, id):
  item = get_object_or_404(Item, id=id)
  if not item.image:
    raise Http404
  content_type = guess_type(item.image.name)
  return HttpResponse(item.image, mimetype=content_type)

@login_required
def delete_post(request, id):
  errors = []

  # Deletes post if the logged-in user has an post matching the id
  try:
    post_to_delete = Item.objects.get(id=id, user=request.user)
    post_to_delete.delete()
  except ObjectDoesNotExist:
    errors.append('The post did not exist in your todo list.')

  items = Item.objects.filter(user=request.user).order_by('-date_time')
  context = {'items' : items, 'errors' : errors}
  return render(request, 'trade/index.html', context)

@login_required
def follow_user(request, id):
  followee = User.objects.get(username=id)
  follower = UserWithFollowers.objects.get(user=request.user.username)
  if followee not in follower.followers.all():
    follower.followers.add(followee)
  else:
    follower.followers.remove(followee)
  follower.save()
  return redirect('/trade')

@login_required
def feed(request):
  follower = UserWithFollowers.objects.get(user=request.user.username)
  all_items = []
  for bloguser in follower.followers.all():
    for post in Item.objects.filter(user=bloguser):
      all_items.append(post)
  all_items = sorted(all_items, key=lambda post: post.date_time, reverse=True)
  context = {'all_items' : all_items}
  return render(request, 'trade/home.html', context)

def register(request):
  context = {}

  # Just display the registration form if this is a GET request
  if request.method == 'GET':
    return render(request, 'trade/register.html', context)

  errors = []
  context['errors'] = errors

  # Checks the validity of the form data
  if not 'username' in request.POST or not request.POST['username']:
    errors.append('Username is required.')
  else:
    # Save the username in the request context to re-fill the username
    # field in case the form has errrors
   context['username'] = request.POST['username']

  if not 'email' in request.POST or not request.POST['email']:
    errors.append('E-mail is required.')

  if not 'first_name' in request.POST or not request.POST['first_name']:
    errors.append('First Name is required.')
  else:
    # Save the username in the request context to re-fill the username
    # field in case the form has errrors
   context['first_name'] = request.POST['first_name']

  if not 'last_name' in request.POST or not request.POST['last_name']:
    errors.append('Last Name is required.')
  else:
    # Save the username in the request context to re-fill the username
    # field in case the form has errrors
   context['last_name'] = request.POST['last_name']

  if not 'email' in request.POST or not request.POST['email']:
    errors.append('E-mail is required.')
  else:
    # Save the username in the request context to re-fill the username
    # field in case the form has errrors
   context['email'] = request.POST['email']

  if not 'password1' in request.POST or not request.POST['password1']:
    errors.append('Password is required.')

  if not 'password2' in request.POST or not request.POST['password2']:
    errors.append('Confirm password is required.')

  if 'password1' in request.POST and 'password2' in request.POST \
     and request.POST['password1'] and request.POST['password2'] \
     and request.POST['password1'] != request.POST['password2']:
     errors.append('Passwords did not match.')

  if len(User.objects.filter(username = request.POST['username'])) > 0:
    errors.append('Username is already taken.')

  if len(request.POST['username']) > 15:
    errors.append('Username too long.')

  if len(User.objects.filter(email = request.POST['email'])) > 0:
    errors.append('Email is already taken.')

  if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", 
                  request.POST['email']):
    errors.append('Invalid e-mail address.')

  if errors:
    return render(request, 'trade/register.html', context)

  # Creates the new user from the valid form data
  new_user = User.objects.create_user(username=request.POST['username'], 
                                      password=request.POST['password1'],
                                      first_name=request.POST['first_name'],
                                      last_name=request.POST['last_name'],
                                      email=request.POST['email'])
  #new_user.is_active=False
  new_user.is_active=True
  new_user.save()
  new_userWithFollowers = UserWithFollowers(user=new_user)
  new_userWithFollowers.save();
  token = default_token_generator.make_token(new_user)
  verif_url = "http://localhost:8000/verify?token="+token+"&username=" 
  verif_url += request.POST['username']
  print verif_url
  message = ("Hi " + new_user.first_name + "!\n"
             "Thanks for signing up for microBlog. \n\nClick the following link" 
             "to verify your email: \n") + verif_url + ("\nHave a "
             "good day! \n\n-microBlog Team")
  #send_mail('Blog Verification Email', message, 'microBlogTeam@andrew.cmu.edu', [request.POST['email']], fail_silently=False)
  return redirect('/')

def verify(request):
  context = {}
  errors = []
  content = []
  context['errors'] = errors
  context['content'] = content
  tok = request.GET['token']
  try:
    user = User.objects.get(username = request.GET['username'])
    token = default_token_generator.make_token(user)
  except User.DoesNotExist:
    errors.append('Error: User Does Not Exist')
    content.append("Sorry, unable to verify account. ")
    return render(request, 'trade/verify.html', context)
  if user.is_active:
    errors.append("Error: Your account has already been verified")
  if tok != token:
    errors.append("Error: Incorrect Verification Token")
  if errors:
    content.append("Sorry, unable to verify account. ")
    return render(request, 'trade/verify.html', context)
  else:
    user.is_active = True
    user.save()
    content.append("Hey " + user.first_name + " " + user.last_name + ".")  
    content.append("Your account " + user.username + " has been verified!")
    return render(request, 'trade/verify.html', context)

def update_users(request):
  users =  list(User.objects.all().order_by('username'))
  if not request.user.is_authenticated(): 
    followers = []
  else:
    userwf = UserWithFollowers.objects.get(user=request.user.username)
    followers = userwf.followers.all()
  return render(request, 'trade/users.xml', 
                {'users':users, 
                 'followers':followers}, 
                content_type='application/xml')

@login_required
def trade_single(request, id):
  # Sets up list of just the logged-in user's (request.user's) items
  trade = Trade.objects.get(id=id)
  user1selectitems = []
  user1restitems = []
  user2selectitems = []
  user2restitems = []
  items1 = Item.objects.filter(user=trade.user1).order_by('-date_time')
  items2 = Item.objects.filter(user=trade.user2).order_by('-date_time')
  for item in items1:
    if item in trade.items.all():
      user1selectitems.append(item)
    else:
      user1restitems.append(item)
  for item in items2:
    if item in trade.items.all():
      user2selectitems.append(item)
    else:
      user2restitems.append(item)
  return render(request, 'trade/trade_modify.html', 
    {
      'id': trade.id,
      'user1': trade.user1,
      'user2': trade.user2, 
      'user1selectitems': user1selectitems,
      'user2selectitems': user2selectitems,
      'user1restitems': user1restitems,
      'user2restitems': user2restitems,
    })

@login_required
def trade_action(request):
  if 'action' not in request.GET:
    return redirect('/')

  ac = request.GET['action']

  if ac == 'start':
    # create trade, redirect
    user2 = User.objects.get(username=request.GET['with'])
    newtrade = Trade(user1=request.user, user2=user2)
    newtrade.save()
    return redirect('/trade/' + str(newtrade.id));
  elif ac == 'cancel':
    try:
      trade = Trade.objects.get(id=request.GET['id'])
      trade.delete()
    except ObjectDoesNotExist:
      pass
    return redirect('/') # show successful message
  else:
    return redirect('/')

@login_required
def trade_modify(request, id):
  trade = Trade.objects.get(id=id)
  def getItem(item_id): return Item.objects.get(id=item_id)
  if 'user1selectitems' in request.POST:
    user1selectitems = map(getItem, request.POST.getlist('user1selectitems'))
  else:
    user1selectitems = []
  if 'user2selectitems' in request.POST:
    user2selectitems = map(getItem, request.POST.getlist('user2selectitems'))
  else:
    user2selectitems = []
  trade.items = user1selectitems + user2selectitems
  return redirect('/trade/' + str(id))

   

def search(request):
  # to be improved
  if 'q' not in request.GET:
    return redirect('/')

  results = Item.objects.filter(desc__icontains=request.GET['q'])
  return render(request, 'trade/search.html', {'items': results, 'q': request.GET['q']})

def item_single(request, id):
  item = Item.objects.get(id=id)
  questions = ItemQuestion.objects.filter(item=item)
  return render(request, 'trade/item.html', {'item': item, 'questions': questions})

def item_question(request, id):
  if request.method == 'POST':
    item = Item.objects.get(id=id)
    q = ItemQuestion(user=request.user, item=item, q=request.POST['q'])
    q.save()
    return redirect('/item/' + str(id))
  return redirect('/')

def trade_message(request, id):
  result = {}
  trade = Trade.objects.get(id=id)
  if request.method == 'GET':
    msgs = TradeMsg.objects.filter(trade=trade).order_by('date')
    result = list(msgs.values('user', 'body'))
    for v in result:
      user = User.objects.get(id=v['user'])
      v['username'] = user.username
  elif request.method == 'POST':
    msg = TradeMsg(user=request.user, trade=trade, body=request.POST['body'])
    msg.save()
    return redirect('/trade/' + str(id))

  return HttpResponse(json.dumps(result), content_type="application/json")