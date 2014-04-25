from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'trade.views.home'),
    
    url(r'^user/edit$', 'trade.views.profile_edit'),
    url(r'^user/(?P<id>.+)$', 'trade.views.profile'),

    url(r'^item/(?P<id>\d+)/question$', 'trade.views.item_question'),
    url(r'^item/(?P<id>\d+)/answer$', 'trade.views.item_answer'),
    url(r'^item/(?P<id>\d+)$', 'trade.views.item_single'),
    url(r'^item/add', 'trade.views.add_item'),
    url(r'^item/(?P<id>\d+)/delete$', 'trade.views.delete_item'),

    url(r'^trade/(?P<id>\d+)$', 'trade.views.trade_view'),
    url(r'^trade/(?P<id>\d+)/message$', 'trade.views.trade_message'),
    url(r'^trade/(?P<id>\d+)/cancel$', 'trade.views.trade_cancel'),
    url(r'^trade/(?P<id>\d+)/accept$', 'trade.views.trade_accept'),
    url(r'^trade/(?P<id>\d+)/received$', 'trade.views.trade_received'),
    url(r'^trade/new$', 'trade.views.trade_new'),
    url(r'^trade', 'trade.views.my_trades'),

    url(r'^search', 'trade.views.search'),
    # Route for built-in authentication with our own custom login page
    url(r'^login$', 'django.contrib.auth.views.login', {'template_name':'trade/login.html'}),
    # Route to logout a user and send them back to the login page
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login'),
    url(r'^register$', 'trade.views.register'),
    url(r'^verify$', 'trade.views.verify'),
    url(r'^manage$', 'trade.views.manage'),

    url(r'^afterreg$', 'trade.views.afterreg'),
)
