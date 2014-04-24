from django.db import models

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
  date_time = models.DateTimeField(auto_now=True)
  image = models.ImageField(upload_to="items", blank=True)
  in_trades = models.ManyToManyField(Trade, blank=True)
  acc_trade = models.ForeignKey(Trade, blank=True, null=True, related_name="acc_trade")
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