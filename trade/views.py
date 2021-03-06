from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.html import escape

# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required

# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import login, authenticate
from django.core import serializers
from django.db.models import Q
from django.utils.datastructures import MultiValueDictKeyError

from mimetypes import guess_type
from django.http import HttpResponse, Http404

from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

from trade.models import *
import json
import re

def afterreg(request):
  return render(request, 'trade/afterreg.html', {})

def home(request):
  context = {}
  if request.user.is_authenticated():
    newitems = Item.objects.filter(status__gte=0).order_by('-date_time')[:4]
    context['newitems'] = newitems


    trades = Trade.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    notaccepted = []
    havereceived = []
    for trade in trades:
      # 1 if user == user1, 0 ow
      cur1 = request.user.id == trade.user1.id

      if trade.status == 0 and not cur1:
        notaccepted.append(trade)
      elif trade.status == 1:
        havereceived.append(trade)
      elif trade.status == 2 and not cur1:
        havereceived.append(trade) 
      elif trade.status == 3 and cur1:
        havereceived.append(trade)

    notaccepted.reverse()
    havereceived.reverse()

    context['notaccepted_trades'] = notaccepted
    context['havereceived_trades'] = havereceived

  return render(request, 'trade/home.html', context)

def search(request):
  # to be improved
  if 'q' not in request.GET:
    return redirect('/')
  criteria = Q(desc__icontains=request.GET['q']) | Q(longdesc__icontains=request.GET['q'])
  if (request.GET['q'].isdigit()):
    criteria |= Q(id=request.GET['q'])
  results = Item.objects.filter(criteria)
  results = results.filter(status__gte=0)
  results_users = User.objects.filter(username__icontains=request.GET['q'])
  return render(request, 'trade/search.html', {'items': results, 'users': results_users, 'q': request.GET['q']})

@login_required
def manage(request):
  # Sets up list of just the logged-in user's (request.user's) items
  items = Item.objects.filter(user=request.user).order_by('status')
  return render(request, 'trade/manage.html', {'items' : items.reverse()})

@login_required
def profile(request, id):
  # Sets up list of just the logged-in user's (request.user's) items
  user = User.objects.get(username=id)
  userdata = UserData.objects.get(user=user)
  userreviews = UserReview.objects.filter(reviewee=user).order_by('-date_time')
  all_items = Item.objects.filter(user=user)
  items = all_items.filter(status__gte=0).order_by('-date_time')
  deaditems = all_items.exclude(status__gte=0).order_by('-date_time')
  user = {
    'id': user.id,
    'username': user.username,
    'first_name': user.first_name,
    'last_name': user.last_name,
    'email': user.email,
    'rep': userdata.rep,
    'loc': userdata.loc,
    'img': userdata.image
  }
  return render(request, 'trade/profile.html', 
    {'items' : items,
     'deaditems': deaditems,
     'profile_user': user,
     'reviews': userreviews}
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
    new_item = Item(desc=request.POST['desc'], longdesc=request.POST['longdesc'], user=request.user)
    if 'image' in request.FILES:
      new_item.image = request.FILES['image']
    new_item.save()
  return redirect('/manage')

def get_item_image(request, id):
  item = get_object_or_404(Item, id=id)
  if not item.image:
    image_data = open(settings.MEDIA_ROOT + "items/no-image.jpg", "rb").read()
    return HttpResponse(image_data, mimetype="image/jpeg")
  content_type = guess_type(item.image.name)
  return HttpResponse(item.image, mimetype=content_type)

def get_user_image(request, username):
  user = get_object_or_404(User, username=username)
  userdata = UserData.objects.get(user=user)
  if not userdata.image:
    image_data = open(settings.MEDIA_ROOT + "users/avatar-blank.jpg", "rb").read()
    return HttpResponse(image_data, mimetype="image/jpeg")
  content_type = guess_type(userdata.image.name)
  return HttpResponse(userdata.image, mimetype=content_type)

@login_required
def delete_item(request, id):
  errors = []
  # Deletes item if the logged-in user has an item matching the id
  item_to_delete = get_object_or_404(Item, id=id, user=request.user)
  cancel_trades_with_item(item_to_delete, None)
  item_to_delete.status = -1
  item_to_delete.save()
  return redirect('/manage')

def item_single(request, id):
  item = get_object_or_404(Item, id=id)
  owner = UserData.objects.get(user=item.user)
  is_owner = item.user == request.user
  owner = {
    'username': item.user.username,
    'rep': owner.rep,
    'loc': owner.loc
  }
  trades = []
  for trade in item.in_trades.all():
    if trade.status == 0 :
      trades.append(trade)
  trades.reverse()
  questions = ItemQuestion.objects.filter(item=item)
  return render(request, 'trade/item.html', {'item': item,
                                             'activetrades': trades,
                                             'owner': owner, 
                                             'questions': questions,
                                             'is_owner': is_owner})

@login_required
def item_question(request, id):
  if request.method == 'POST':
    item = get_object_or_404(Item, id=id)
    q = ItemQuestion(user=request.user, item=item, q=request.POST['q'])
    q.save()
    return redirect('/item/' + str(id))
  return redirect('/')

@login_required
def item_answer(request, id):
  if request.method == 'POST':
    q = ItemQuestion.objects.get(item=get_object_or_404(Item, id=id))
    if request.user != q.item.user:
      raise Http404
    q.a = request.POST['answer']
    q.save()
    return redirect('/item/' + str(id))
  return redirect('/')

##########################
#    Trade functions     #
##########################

@login_required
def trade_accept(request, id):
  try:
    trade = get_object_or_404(Trade, id=id)
    if trade.user2.id != request.user.id: raise Http404
    trade.status = 1
    for item in Item.objects.filter(in_trades=trade):
      item.status = -2
      item.acc_trade = trade
      cancel_trades_with_item(item, trade.id)
      item.save()
    trade.save()
  except ObjectDoesNotExist:
    pass
  return redirect('/trade/'+str(id))

# cancel all trades associated with item, except trade with id id
@login_required
def cancel_trades_with_item(item, id):
  for trade in item.in_trades.all():
    if (trade.id != id) and (trade.status == 0) :
      cancel_trade(trade)
  return

def cancel_trade(trade):
  trade.status = -2
  for item in Item.objects.filter(in_trades=trade):
    if item.acc_trade == trade:
      item.status = 0
      item.acc_trade = None
      item.save()
    item.save()
  trade.save()
  return

@login_required
def trade_cancel(request, id):
  try:
    trade = get_object_or_404(Trade, id=id)
    if trade.status < 0 or trade.status > 1:
      raise Http404
    if not((trade.user2.id == request.user.id) or (trade.user1.id == request.user.id)): 
      raise Http404
    cancel_trade(trade)
  except ObjectDoesNotExist:
    pass
  return redirect('/trade?message=cancelled') # show successful message

@login_required
def trade_received(request, id):
  if 'comments' not in request.POST: raise Http404
  comments = request.POST['comments']
  rating = {'positive': 1, 'neutral':0, 'negative':-1}[request.POST['rating']]

  trade = get_object_or_404(Trade, id=id)
  if (not((trade.user2.id == request.user.id) or (trade.user1.id == request.user.id)) or
     (trade.status <= 0)): 
    raise Http404

  rating_user = trade.user2 if request.user == trade.user1 else trade.user1

  review = UserReview(reviewer=request.user, reviewee=rating_user,rating=rating,body=request.POST['comments'])
  review.save()

  rating_userdata = get_object_or_404(UserData, user=rating_user)
  rating_userdata.rep += rating
  rating_userdata.save()

  if (trade.status == 2) or (trade.status == 3):
    # trade complete
    trade.status = -1
  elif trade.status == 1:
    cur1 = 0
    if request.user.id == trade.user1.id: cur1 = 1
    if cur1: trade.status = 2
    else: trade.status = 3
  trade.save()
  return redirect('/trade/'+str(id))

@login_required
def trade_new(request):
  if request.method == 'GET':
    return trade_new_get(request)
  elif request.method == 'POST':
    return trade_new_post(request)

@login_required
def trade_new_get(request):
  context = {}
  # Sets up list of just the logged-in user's (request.user's) items
  if 'with' not in request.GET or not request.GET['with']:
    return redirect('/')

  if request.GET['with'] == request.user.username:
    raise Http404

  from_trade_items = []

  if 'from' in request.GET:
    from_trade = get_object_or_404(Trade, id=request.GET['from'])
    if not((from_trade.user2.id == request.user.id) or (from_trade.user1.id == request.user.id)): 
      raise Http404
    from_trade_items = list(Item.objects.filter(in_trades=from_trade))
    context['from'] = from_trade.id

  user1 = request.user
  user2 = get_object_or_404(User, username=request.GET['with'])
  user1selectitems = []
  user1restitems = []
  user1semideaditems = []
  user2selectitems = []
  user2restitems = []
  user2semideaditems = []
  items1 = Item.objects.filter(user=user1).filter(status__gte=0).order_by('-date_time')
  items2 = Item.objects.filter(user=user2).filter(status__gte=0).order_by('-date_time')

  for item in items1:
    if item in from_trade_items:
      user1selectitems.append(item)
    else:
      if item.acc_trade == None:
        user1restitems.append(item)
      else: user1semideaditems.append(item)
  for item in items2:
    if item in from_trade_items:
      user2selectitems.append(item)
    else:
      if item.acc_trade == None:
        user2restitems.append(item)
      else: user2semideaditems.append(item)

  context['user1'] = user1
  context['user2'] = user2
  context['user1selectitems'] = user1selectitems
  context['user2selectitems'] = user2selectitems
  context['user1semideaditems'] = user1semideaditems
  context['user1restitems'] = user1restitems
  context['user2restitems'] = user2restitems
  context['user2semideaditems'] = user2semideaditems
  return render(request, 'trade/new_trade.html', context)

@login_required
def trade_new_post(request):
  # create trade, confirm trade
  user2 = get_object_or_404(User, id=request.POST['user2'])
  newtrade = Trade(user1=request.user, user2=user2)
  newtrade.status = 0
  newtrade.save()
  return trade_confirm(request, str(newtrade.id))

@login_required
def trade_confirm(request, id):
  trade = get_object_or_404(Trade, id=id)
  if not((trade.user2.id == request.user.id) or (trade.user1.id == request.user.id)): 
    raise Http404
  cur1 = request.user.id == trade.user1.id
  def getItem1(item_id): return get_object_or_404(Item, id=item_id, user=trade.user1)
  def getItem2(item_id): return get_object_or_404(Item, id=item_id, user=trade.user2)

  if 'user1selectitems' in request.POST:
    user1selectitems = map(getItem1, request.POST.getlist('user1selectitems'))
  else:
    user1selectitems = []
  if 'user2selectitems' in request.POST:
    user2selectitems = map(getItem2, request.POST.getlist('user2selectitems'))
  else:
    user2selectitems = []

  # update item status, user1 accepted
  for item in user1selectitems:
    item.in_trades.add(trade)
    item.acc_trade = trade
    item.save()
  # add affiliated trade
  for item in user2selectitems:
    item.in_trades.add(trade)
    item.save()

  trade.save()
  return redirect('/trade/' + id + '?created=true')

@login_required
def trade_view(request, id):
  trade = get_object_or_404(Trade, id=id)
  if not((trade.user2.id == request.user.id) or (trade.user1.id == request.user.id)): 
    raise Http404
  cur1 = request.user.id == trade.user1.id
  user1selectitems = []
  user2selectitems = []
  for item in Item.objects.filter(in_trades=trade):
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

@login_required
def trade_message(request, id):
  result = {}
  trade = get_object_or_404(Trade, id=id)
  if request.method == 'GET':
    msgs = TradeMsg.objects.filter(trade=trade).order_by('date')
    result = list(msgs.values('user', 'body'))
    for v in result:
      user = get_object_or_404(User, id=v['user'])
      v['username'] = user.username
  elif request.method == 'POST':
    msg_body = request.POST['body']
    msg_body = escape(msg_body)
    msg = TradeMsg(user=request.user, trade=trade, body=msg_body)
    msg.save()
    return redirect('/trade/' + str(id))

  return HttpResponse(json.dumps(result), content_type="application/json")

@login_required
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
      havereceived.append(trade)
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
  new_user.is_active=False
  new_user.save()
  new_userData = UserData(user=new_user)
  new_userData.save();
  token = default_token_generator.make_token(new_user)
  verif_url = "https://tradingpost.ngrok.com/verify?token="+token+"&username=" 
  verif_url += request.POST['username']



  plaintext = get_template('email-reg.txt')
  htmly     = get_template('email-reg.html')

  d = Context({ 'first_name': new_user.first_name, 'verify_url': verif_url })

  subject, from_email, to = 'Trading Post Verification', 'no-reply@tradingpost.ngrok.com', request.POST['email']
  text_content = plaintext.render(d)
  html_content = htmly.render(d)
  msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
  msg.attach_alternative(html_content, "text/html")
  msg.send()



  return redirect('/afterreg')

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