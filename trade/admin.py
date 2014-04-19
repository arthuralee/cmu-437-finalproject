from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from trade.models import *

admin.site.register(Item)
admin.site.register(UserWithFollowers)
admin.site.register(Trade)
admin.site.register(TradeMsg)
admin.site.register(ItemQuestion)
admin.site.register(UserReview)