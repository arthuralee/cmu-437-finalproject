from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required

# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.datastructures import MultiValueDictKeyError

from mimetypes import guess_type
from django.http import HttpResponse, Http404

from trade.models import *
import re
from django.core import serializers
from django.db.models import Q
import json

def bitch(request):
  for trade in Trade.objects.all():
    trade.delete()
  return redirect('/')

def bitch2(request):
  for hi in ItemData.objects.all():
    hi.delete()
  for item in Item.objects.all():
    new = ItemData(item=item)
    new.save()
  for trade in ItemData.objects.all():
    trade.acc_trade = 0
    trade.in_trades = []
    trade.save()
  return redirect('/')

def home(request):
  context = {}
  return render(request, 'trade/home.html', context)

def search(request):
  # to be improved
  if 'q' not in request.GET:
    return redirect('/')

  results = Item.objects.filter(Q(desc__icontains=request.GET['q']) | Q(longdesc__icontains=request.GET['q']))
  results = results.filter(status__gte=0)
  return render(request, 'trade/search.html', {'items': results, 'q': request.GET['q']})

@login_required
def manage(request):
  # Sets up list of just the logged-in user's (request.user's) items
  items = Item.objects.filter(user=request.user).order_by('-date_time')
  return render(request, 'trade/manage.html', {'items' : items})

@login_required
def profile(request, id):
  # Sets up list of just the logged-in user's (request.user's) items
  user = User.objects.get(username=id)
  userdata = UserData.objects.get(user=user)
  all_items = Item.objects.filter(user=user)
  items = all_items.filter(status__gte=0).order_by('-date_time')
  deaditems = all_items.exclude(status__gte=0).order_by('-date_time')
  user = {
    'id': user.id,
    'username': user.username,
    'first_name': user.first_name,
    'last_name': user.last_name,
    'rep': userdata.rep,
    'loc': userdata.loc,
    'img': userdata.image
  }
  return render(request, 'trade/profile.html', 
    {'items' : items,
     'deaditems': deaditems,
     'profile_user': user}
    )

@login_required
def profile_edit(request):
  user = request.user
  userdata = UserData.objects.get(user=user)

  try:
    user.first_name = request.POST['first_name']
    user.last_name = request.POST['last_name']
    userdata.loc = request.POST['loc']
    if 'image' in request.FILES:
      userdata.image = request.FILES['image']
    user.save()
    userdata.save()
    return redirect('/user/' + user.username)
  except MultiValueDictKeyError:
    pass
  return redirect('/')  

##########################
#     Item functions     #
##########################

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
  return redirect('/manage')

def get_image(request, id):
  item = get_object_or_404(Item, id=id)
  if not item.image:
    raise Http404
  content_type = guess_type(item.image.name)
  return HttpResponse(item.image, mimetype=content_type)

@login_required
def get_user_image(request, username):
  user = get_object_or_404(User, username=username)
  userdata = UserData.objects.get(user=user)
  if not userdata.image:
    image_data = open(settings.MEDIA_ROOT + "users/avatar-blank.jpg", "rb").read()
    return HttpResponse(image_data, mimetype="image/png")
    raise Http404
  content_type = guess_type(userdata.image.name)
  return HttpResponse(userdata.image, mimetype=content_type)

@login_required
def delete_item(request, id):
  errors = []
  # Deletes item if the logged-in user has an item matching the id
  try:
    item_to_delete = Item.objects.get(id=id, user=request.user)
    item_to_delete.delete()
  except ObjectDoesNotExist:
    errors.append('The item does not exist.')

  return redirect('/manage')

def item_single(request, id):
  item = Item.objects.get(id=id)
  item_data = ItemData.objects.get(item=item)
  trades = []
  for trade in item_data.in_trades.all():
    trades.append(trade)
  trades.reverse()
  questions = ItemQuestion.objects.filter(item=item)
  return render(request, 'trade/item.html', {'item': item,
                                             'trades': trades, 
                                             'questions': questions})

def item_question(request, id):
  if request.method == 'POST':
    item = Item.objects.get(id=id)
    q = ItemQuestion(user=request.user, item=item, q=request.POST['q'])
    q.save()
    return redirect('/item/' + str(id))
  return redirect('/')

##########################
#    Trade functions     #
##########################

@login_required
def trade_action(request):
  if 'action' not in request.GET:
    # My trades screen
    return my_trades(request)
  else:
    # execute some action
    ac = request.GET['action']

    if ac == 'start':
      # create trade, redirect
      user2 = User.objects.get(username=request.GET['with'])
      newtrade = Trade(user1=request.user, user2=user2)
      newtrade.status = 0
      newtrade.save()
      return redirect('/trade/new/' + str(newtrade.id));
    elif ac == 'cancel':
      try:
        trade = Trade.objects.get(id=request.GET['id'])
        trade.status = -2
        for item in trade.items.all():
          item_data = ItemData.objects.get(item=item)
          item_data.in_trades.remove(trade)
          if item_data.acc_trade == trade.id:
            item.status = 0
            item_data.acc_trade = 0
            item.save()
          item_data.save()
        trade.save()
      except ObjectDoesNotExist:
        pass
      return redirect('/trade') # show successful message
    elif ac == 'accept':
      try:
        trade_id = int(request.GET['id'])
        trade = Trade.objects.get(id=trade_id)
        trade.status = 1
        for item in trade.items.all():
          item.status = -2
          item_data = ItemData.objects.get(item=item)
          item_data.acc_trade = trade.id
          item_data.save()
          item.save()
        trade.save()
      except ObjectDoesNotExist:
        pass
      return redirect('/trade/view/'+str(trade_id)) 
    elif ac == 'modify':
      try:
        trade_id = request.GET['id']
      except ObjectDoesNotExist:
        redirect('/trade')
      return trade_modify(request, trade_id) 
    elif ac == 'received':
      try:
        trade_id = request.GET['id']
        trade = Trade.objects.get(id=trade_id)
        if (trade.status == 2) or (trade.status == 3):
          # trade complete
          trade.status = -1
        elif trade.status == 1:
          cur1 = 0
          if request.user.id == trade.user1.id: cur1 = 1
          if cur1: trade.status = 2
          else: trade.status = 3
        trade.save()
      except ObjectDoesNotExist:
        pass
      return redirect('/trade/view/'+str(trade_id)) 
    else:
      return redirect('/trade')

@login_required
def trade_single(request, id):
  # Sets up list of just the logged-in user's (request.user's) items
  trade = Trade.objects.get(id=id)
  user1selectitems = []
  user1restitems = []
  user1deaditems = []
  user2selectitems = []
  user2restitems = []
  user2deaditems = []
  items1 = Item.objects.filter(user=trade.user1).filter(status__gte=0).order_by('-date_time')
  items2 = Item.objects.filter(user=trade.user2).filter(status__gte=0).order_by('-date_time')
  for item in items1:
    if item in trade.items.all():
      user1selectitems.append(item)
    else:
      if item.status > 0:
        user1deaditems.append(trade)
      else: user1restitems.append(item)
  for item in items2:
    if item in trade.items.all():
      user2selectitems.append(item)
    else:
      if item.status > 0:
        user2deaditems.append(trade)
      else: user2restitems.append(item)
  return render(request, 'trade/new_trade.html', 
    {
      'id': trade.id,
      'user1': trade.user1,
      'user2': trade.user2, 
      'user1selectitems': user1selectitems,
      'user2selectitems': user2selectitems,
      'user1deaditems': user1deaditems,
      'user1restitems': user1restitems,
      'user2restitems': user2restitems,
      'user2deaditems': user2deaditems,
    })

@login_required
def trade_modify(request, id):
  old_trade = Trade.objects.get(id=id)
  new_trade = Trade(user1=old_trade.user2, 
                    user2=old_trade.user1)
  new_trade.save()
  new_trade.items = old_trade.items.all()
  new_trade.status = 0
  new_trade.save()
  old_trade.status = -2 # cancel old trade
  old_trade.save()
  return redirect('/trade/new/' + str(new_trade.id))

@login_required
def trade_confirm(request, id):
  trade = Trade.objects.get(id=id)
  cur1 = 0 # 1 if user == user1, 0 ow
  if request.user.id == trade.user1.id: cur1 = 1
  def getItem(item_id): return Item.objects.get(id=item_id)
  if 'user1selectitems' in request.POST:
    user1selectitems = map(getItem, request.POST.getlist('user1selectitems'))
  else:
    user1selectitems = []
  if 'user2selectitems' in request.POST:
    user2selectitems = map(getItem, request.POST.getlist('user2selectitems'))
  else:
    user2selectitems = []

  # update item status, user1 accepted

  for item in user1selectitems:
    item_data = ItemData.objects.get(item=item)
    item_data.in_trades.add(trade)
    item_data.acc_trade = trade.id
    item_data.save()
  # add affiliated trade
  for item in user2selectitems:
    item_data = ItemData.objects.get(item=item)
    item_data.in_trades.add(trade)
    item_data.save()

  trade.items = user1selectitems + user2selectitems
  trade.save()
  return render(request, 'trade/view_trade.html', 
    {
      'trade': trade,
      'user1selectitems': user1selectitems,
      'user2selectitems': user2selectitems,
      'received': -1,
      'cur1': cur1,
    })

@login_required
def trade_view(request, id):
  trade = Trade.objects.get(id=id)
  cur1 = 0 # 1 if user == user1, 0 ow
  if request.user.id == trade.user1.id: cur1 = 1
  user1selectitems = []
  user2selectitems = []
  for item in trade.items.all():
    if item.user.id == trade.user1.id:
      user1selectitems.append(item)
    else:
      user2selectitems.append(item)
  if ((cur1 and (trade.status == 2)) or
      ((not cur1) and (trade.status == 3))):
    received = 1
  else: received = 0
  return render(request, 'trade/view_trade.html', 
    {
      'trade': trade,
      'user1selectitems': user1selectitems,
      'user2selectitems': user2selectitems,
      'received': received,
      'cur1': cur1,
    })

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

def my_trades(request):
  trades = Trade.objects.filter(Q(user1=request.user) | Q(user2=request.user))
  accepted = []
  notaccepted = []
  cancelled = []
  completed = []
  havereceived = []
  havenotreceived = []
  for trade in trades:
    # 1 if user == user1, 0 ow
    cur1 = request.user.id == trade.user1.id

    if trade.status == -1:
      completed.append(trade)
    elif trade.status == 0:
      if cur1: accepted.append(trade)
      else: notaccepted.append(trade) 
    elif trade.status == 1:
      havenotreceived.append(trade)
    elif trade.status == 2:
      if not cur1: havereceived.append(trade)
      else: havenotreceived.append(trade) 
    elif trade.status == 3:
      if cur1: havereceived.append(trade)
      else: havenotreceived.append(trade)
    else:
      cancelled.append(trade)
  accepted.reverse()
  notaccepted.reverse()
  cancelled.reverse()
  completed.reverse()
  havereceived.reverse()
  havenotreceived.reverse()
  return render(request, 'trade/my_trades.html', {'accepted_trades': accepted,
                                                  'notaccepted_trades': notaccepted,
                                                  'havereceived_trades': havereceived,
                                                  'havenotreceived_trades': havenotreceived,
                                                  'cancelled_trades': cancelled,
                                                  'completed_trades': completed})

##########################
# Registration functions #
##########################

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