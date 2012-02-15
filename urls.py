from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('gmap.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
