from django.db import models

# User class for built-in authentication module
from django.contrib.auth.models import User

class Item(models.Model):
  desc = models.CharField(max_length=200)
  user = models.ForeignKey(User)
  date_time = models.DateTimeField(auto_now=True)
  image = models.ImageField(upload_to="items", blank=True)
  def __unicode__(self):
	 return self.text

class UserWithFollowers(models.Model):
  user = models.CharField(max_length=200)
  followers = models.ManyToManyField(User)