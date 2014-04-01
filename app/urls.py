from django.conf.urls import patterns, include, url

# Default URL routes file for the controller.  Here we are simply matching
# URL patterns by regular expression, and choosing the actual route by
# including the appropriate route file for each application.
urlpatterns = patterns('',
    url(r'^', include('trade.urls')),
    url(r'^image/(?P<id>\d+)$', 'trade.views.get_image', name='image'),
)
