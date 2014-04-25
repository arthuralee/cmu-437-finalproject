from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

# User class for built-in authentication module
from django.contrib.auth.models import User

class UserData(models.Model):
  user = models.OneToOneField(User)
  loc = models.CharField(max_length=255)
  rep = models.IntegerField(default=0)
  image = models.ImageField(upload_to="users", blank=True)

class Trade(models.Model):
  user1 = models.ForeignKey(User, related_name='user1')
  user2 = models.ForeignKey(User, related_name='user2')
  date_created = models.DateTimeField(auto_now=True)
  date_completed = models.DateTimeField(blank=True, null=True)
  status = models.IntegerField(default=0)
  # 0 -> user1 accepted

  # 1 -> both accepted
  # 2 -> user1 recieved items
  # 3 -> user2 recieved items

  # -1 -> complete
  # -2 -> cancelled

class Item(models.Model):
  desc = models.CharField(max_length=200)
  longdesc = models.CharField(max_length=1000)
  user = models.ForeignKey(User)
  date_time = models.DateTimeField(auto_now_add=True)
  image = models.ImageField(upload_to="items", blank=True)
  in_trades = models.ManyToManyField(Trade, blank=True)
  acc_trade = models.ForeignKey(Trade, blank=True, null=True, on_delete=models.SET_NULL, related_name="acc_trade")
  status = models.IntegerField(default=0)
  # < 0 : dead
  # == 0: available
  # > 0: in trade
  def __unicode__(self):
   return self.desc

class TradeMsg(models.Model):
  date = models.DateTimeField(auto_now=True)
  user = models.ForeignKey(User)
  trade = models.ForeignKey(Trade)
  body = models.CharField(max_length=1000)

class ItemQuestion(models.Model):
  date = models.DateTimeField(auto_now=True)
  user = models.ForeignKey(User)
  item = models.ForeignKey(Item)
  q = models.CharField(max_length=1000)
  a = models.CharField(max_length=1000, blank=True)

class UserReview(models.Model):
  reviewer = models.ForeignKey(User, related_name='reviewer')
  reviewee = models.ForeignKey(User, related_name='reviewee')
  rating = models.IntegerField()
  body = models.CharField(max_length=1000)
  date_time = models.DateTimeField(auto_now_add=True, null=True)

@receiver(pre_save, sender=Trade)
def trade_state_change(sender, **kwargs):
  if not kwargs.get('instance', False): return
  
  trade = kwargs.get('instance')
  id = trade.id
  status = trade.status

  try:
    old_trade = Trade.objects.get(id=id)
    if old_trade.status == status: return
  except Trade.DoesNotExist:
    pass

  if status == 0:
    return
  elif status == 1:
    header = "Trade #" + str(id) + " accepted by " + trade.user2.username
    body = "Your trade request has been accepted by " + trade.user1.username + '. You may now exchange your items.'
    to = [trade.user1.email]
  elif status == 2:
    header = "Trade #" + str(id) + ": Items received by " + trade.user1.username
    body = "Your items have been received by " + trade.user1.username + '. Remember to mark trade as completed when you receive your items.'
    to = [trade.user2.email]
  elif status == 3:
    header = "Trade #" + str(id) + ": Items received by " + trade.user2.username
    body = "Your items have been received by " + trade.user2.username + '. Remember to mark trade as completed when you receive your items.'
    to = [trade.user1.email]
  elif status == -1:
    header = "Trade #" + str(id) + " completed"
    body = "Congratulations! Trade #" + str(id) + " involving " + trade.user1.username + ' and '  + trade.user2.username +  ' is now complete.'
    to = [trade.user1.email, trade.user2.email]
  elif status == -2:
    header = "Trade #" + str(id) + " cancelled"
    body = "Unfortunately, trade #" + str(id) + " involving " + trade.user1.username + ' and '  + trade.user2.username +  ' has been cancelled.'
    to = [trade.user1.email, trade.user2.email]

  plaintext = get_template('email-notif.txt')
  htmly     = get_template('email-notif.html')

  trade_link = 'https://tradingpost.ngrok.com/trade/' + str(id)
  d = Context({ 'header': header, 'body': body, 'trade_link':trade_link })

  subject, from_email = 'Trading Post', 'no-reply@tradingpost.ngrok.com'
  text_content = plaintext.render(d)
  html_content = htmly.render(d)
  msg = EmailMultiAlternatives(subject, text_content, from_email, to)
  msg.attach_alternative(html_content, "text/html")
  msg.send()