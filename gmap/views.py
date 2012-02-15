from django.conf import settings
from django.core import serializers
from django.http import Http404, HttpResponse
from gmap.models import Bandwidth
from django.template import RequestContext
from django.views.generic import TemplateView


BW_UPDATE_INTERVAL = getattr(settings, 'GMAP_BW_UPDATE_INTERVAL', 5)


class MapView(TemplateView):
    template_name='gmap/map.html'
    
    def render_to_response(self, context):
        context = RequestContext(self.request, {
            'bw_update_interval': BW_UPDATE_INTERVAL,
        })
        return super(MapView, self).render_to_response(context)
    

def bw(request, link , time, rx, tx):
    """Add bandwidth reports"""
    ## TODO add to bandwith table    
    pass


def xhr_bw(request, link):
    """Return JSON data for XMLHttpRequests."""
    if not request.is_ajax():
        raise Http404
    import json    
    mimetype = 'application/javascript'
    rx, tx = Bandwidth.objects.rates(link)
    data = json.dumps({'rx': rx, 'tx': tx})
    return HttpResponse(data, mimetype)


