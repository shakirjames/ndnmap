from django.conf.urls.defaults import patterns, url
from gmap.views import MapView

urlpatterns = patterns('gmap.views',
    url(r'^$', MapView.as_view()),
    url(r'^bw_test/$', TemplateView.as_view(template_name='gmap/bw_test.html')),
    url(r'^xhr_bw/(?P<link>\d+)/$', 'xhr_bw', name='xhr_bw'),    
)
