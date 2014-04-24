from django.conf.urls import patterns, include, url
from django.contrib import admin

# Default URL routes file for the controller.  Here we are simply matching
# URL patterns by regular expression, and choosing the actual route by
# including the appropriate route file for each application.
# 

admin.autodiscover()
 
urlpatterns = patterns('',
    url(r'^', include('trade.urls')),
    url(r'^image/(?P<id>\d+)$', 'trade.views.get_item_image', name='image'),
    url(r'^image/user/(?P<username>.+)$', 'trade.views.get_user_image', name='user_image'),
    url(r'^admin/', include(admin.site.urls)),
)
