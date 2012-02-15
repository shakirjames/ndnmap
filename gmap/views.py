from django.conf import settings
from django.core import serializers
from django.core.urlresolvers import reverse 
from django.http import HttpResponse, Http404
from gmap.models import Bandwidth
from django.template import RequestContext
from django.views.generic import TemplateView


BW_UPDATE_INTERVAL = getattr(settings, 'GMAP_BW_UPDATE_INTERVAL', 5)


class MapView(TemplateView):
    template_name='gmap/map.html'
    
    def render_to_response(self, context):
        context = RequestContext(self.request, {
            'bw_url': reverse('xhr_bw', args=(0, )).split('0')[0],
            'bw_update_interval': BW_UPDATE_INTERVAL*1000, # ms
        })
        return super(MapView, self).render_to_response(context)
    

def bw(request, link , time, rx, tx):
    """Add bandwidth reports"""
    # WARNING: This is not safe!
    Bandwidth.objects.create(link=link, time=time, rx=rx, tx=tx)
    return HttpResponse('Got it.\n')


def xhr_bw(request, link):
    """Return JSON data for XMLHttpRequests."""
    import json    
    rx, tx = Bandwidth.objects.rates(link)
    data = json.dumps({'rx': rx, 'tx': tx})
    return HttpResponse(data, 'application/json')


def json(request, file):
    f = '{0}/gmap/json/{1}.json'.format(settings.SITE_ROOT, file)    
    try:
        data = open(f, 'r').read()
    except IOError:
        raise Http404
    return HttpResponse(data, 'application/json')
