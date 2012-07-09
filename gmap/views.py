# Copyright (c) 2012 Shakir James and Washington University in St. Louis.
# See LICENSE for details.

from django.conf import settings
from django.core import serializers
from django.core.urlresolvers import reverse 
from django.http import HttpResponse, Http404
from gmap.models import Bandwidth
from django.template import RequestContext
from django.views.generic import TemplateView
from utils import gviz_api

MAP_API_KEY = getattr(settings, 'GMAP_API_KEY', '')
BW_UPDATE_INTERVAL = getattr(settings, 'GMAP_BW_UPDATE_INTERVAL', 5)
BW_DIVISOR = 1000.0 # Kbps
BW_DECIMAL_POINTS=1

def bw(request, link , time, rx, tx):
    """Add bandwidth reports."""
    # WARNING: This is not safe!
    Bandwidth.objects.create(link=link, time=time, rx=rx, tx=tx)
    return HttpResponse('Got it.\n')

def json(request, file):
    """Return the content of a json file."""
    # http://ndnmap.arl.wustl.edu/json/ec2regions/
    f = '{0}/gmap/json/{1}.json'.format(settings.SITE_ROOT, file)    
    try:
        data = open(f, 'r').read()
    except IOError:
        raise Http404
    return HttpResponse(data, 'application/json')

def xhr_bw(request, link):
    """Return JSON data with link rate."""
    import json
    links = link.strip('+').split('+')
    data = []
    for link in links :
        rx, tx = Bandwidth.objects.rate(link)
        rx = round(rx/BW_DIVISOR, BW_DECIMAL_POINTS)
        tx = round(tx/BW_DIVISOR, BW_DECIMAL_POINTS)
        data.append( {'id':link, 'rx':rx, 'tx':tx} )
    # Backward compatability
    if len(data) == 1 :
        data = data[0]
    data = json.dumps(data)
    return HttpResponse(data, 'application/json')

def _spark_json(link, field):
    data = ({field: (round(v/BW_DIVISOR, BW_DECIMAL_POINTS))}
        for v in Bandwidth.objects.rates(field, link))
    data_table = gviz_api.DataTable({field:('number', 'Bandwidth')})
    data_table.LoadData(data)
    return data_table.ToJSon()

class MapView(TemplateView):
    template_name='gmap/map.html'

    def render_to_response(self, context):
        context = RequestContext(self.request, {
            'api_key': MAP_API_KEY,
            'bw_url': reverse('xhr_bw', args=(0, )).split('0')[0],
            'spark_rx_url': reverse('xhr_spark_rx', args=(0, )).split('0')[0],
            'spark_tx_url': reverse('xhr_spark_tx', args=(0, )).split('0')[0],
            'bw_update_interval': BW_UPDATE_INTERVAL*1000, # ms
            'bw_divisor': BW_DIVISOR,
        })
        return super(MapView, self).render_to_response(context)

class SparkLine(TemplateView):
    template_name='gmap/sparkline.html'

    def render_to_response(self, context):
        link = self.kwargs['link']
        context = RequestContext(self.request, {
            'rx_data': _spark_json(link, 'rx'),
            'tx_data': _spark_json(link, 'tx'),
        })
        return super(SparkLine, self).render_to_response(context)


###
### Debug views
###
def xhr_spark_rx(request, link):
    """Return rx traffic in bits as JSON data"""
    # http://ndnmap.arl.wustl.edu/xhr_sparkline/rx/1
    return HttpResponse(_spark_json(link, 'rx'), 'application/json')

def xhr_spark_tx(request, link):
    """Return rx traffic in bits as JSON data"""
    # http://ndnmap.arl.wustl.edu/xhr_sparkline/tx/1
    return HttpResponse(_spark_json(link, 'tx'), 'application/json')

class DebugView(TemplateView):
    # http://ndnmap.arl.wustl.edu/debug
    # simple view for django debug toolbar to show SQL query
    template_name='gmap/debug.html'
        
    def render_to_response(self, context):
        link_id = 1
        context = RequestContext(self.request, {
            'rate': Bandwidth.objects.rate(link_id),
        })
        return super(DebugView, self).render_to_response(context)
    
