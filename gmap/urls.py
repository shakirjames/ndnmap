from django.conf.urls.defaults import patterns, url
from gmap.views import MapView


urlpatterns = patterns('gmap.views',
    url(r'^$', MapView.as_view()),
    url(r'^bw/(?P<link>\d+)/(?P<time>\d+)/(?P<rx>\d+)/(?P<tx>\d+)/$',
        'bw',
        name='bw'),
    url(r'^xhr_bw/(?P<link>\d+)/$', 'xhr_bw', name='xhr_bw'),
)
