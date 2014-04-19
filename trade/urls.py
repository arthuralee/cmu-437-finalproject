from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'trade.views.feed'),
    url(r'^user/(?P<id>.+)$', 'trade.views.profile'),
    url(r'^follow/(?P<id>.+)$', 'trade.views.follow_user'),
    url(r'^add-item', 'trade.views.add_item'),
    url(r'^delete-item/(?P<id>\d+)$', 'trade.views.delete_post'),
    url(r'^item/(?P<id>.+)/question$', 'trade.views.item_question'),
    url(r'^item/(?P<id>.+)$', 'trade.views.item_single'),
    url(r'^trade/(?P<id>.+)/message$', 'trade.views.trade_message'),
    url(r'^trade/(?P<id>.+)$', 'trade.views.trade_single'),
    url(r'^trade', 'trade.views.trade_action'),
    url(r'^search', 'trade.views.search'),
    # Route for built-in authentication with our own custom login page
    url(r'^login$', 'django.contrib.auth.views.login', {'template_name':'trade/login.html'}),
    # Route to logout a user and send them back to the login page
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^register$', 'trade.views.register'),
    url(r'^verify$', 'trade.views.verify'),
    url(r'^manage$', 'trade.views.manage'),
    url(r'^update$', 'trade.views.update_users'),
)
