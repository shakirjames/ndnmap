# Copyright (c) 2012 Shakir James and Washington University in St. Louis.
# See LICENSE for details.

from django.conf.urls.defaults import patterns, url
from gmap.views import MapView, SparkLine, DebugView


urlpatterns = patterns('gmap.views',
    # respond with HTML for the homepage, the map
    url(r'^$', MapView.as_view()),
    # add reports on link rates from CCN nodes, respond with ACK ('Got it')
    url(r'^bw/(?P<link>\d+)/(?P<time>\d+\.\d+)/(?P<rx>\d+)/(?P<tx>\d+)/$','bw', name='bw'),
    # respond to XMLHttpRequests from the map script to display link rates
    url(r'^xhr_bw/(?P<link>[+\d]+)/$', 'xhr_bw', name='xhr_bw'),
    # respond with HTML for a sparklinke, bandwidth graph
    url(r'^sparkline/(?P<link>\d+)/$', SparkLine.as_view()),
    # respond with json files to avoid cross-site scripting
    url(r'^json/(?P<file>\w+)/$', 'json'),
    # debug
    url(r'^xhr_sparkline/rx/(?P<link>\d+)/$', 'xhr_spark_rx', name='xhr_spark_rx'),
    url(r'^xhr_sparkline/tx/(?P<link>\d+)/$', 'xhr_spark_tx', name='xhr_spark_tx'),
    #url(r'^debug/$', DebugView.as_view()),
)
