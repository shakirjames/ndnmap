#
# Copyright (c) 2011 Shakir James and Washington University in St. Louis.
# All rights reserved
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    3. The name of the author or Washington University may not be used 
#       to endorse or promote products derived from this source code 
#       without specific prior written permission.
#    4. Conditions of any other entities that contributed to this are also
#       met. If a copyright notice is present from another entity, it must
#       be maintained in redistributions of the source code.
#
# THIS INTELLECTUAL PROPERTY (WHICH MAY INCLUDE BUT IS NOT LIMITED TO SOFTWARE,
# FIRMWARE, VHDL, etc) IS PROVIDED BY THE AUTHOR AND WASHINGTON UNIVERSITY 
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED 
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR WASHINGTON UNIVERSITY 
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS INTELLECTUAL PROPERTY, EVEN IF 
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from django.conf import settings
from django.core import serializers
from django.core.urlresolvers import reverse 
from django.http import HttpResponse, Http404
from gmap.models import Bandwidth
from django.template import RequestContext
from django.views.generic import TemplateView
from utils import gviz_api

BW_UPDATE_INTERVAL = getattr(settings, 'GMAP_BW_UPDATE_INTERVAL', 5)
BW_DIVISOR = 1000.0 # Kbps
BW_DECIMAL_POINTS=1

def bw(request, link , time, rx, tx):
    """Add bandwidth reports"""
    # WARNING: This is not safe!
    Bandwidth.objects.create(link=link, time=time, rx=rx, tx=tx)
    return HttpResponse('Got it.\n')


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


def json(request, file):
    f = '{0}/gmap/json/{1}.json'.format(settings.SITE_ROOT, file)    
    try:
        data = open(f, 'r').read()
    except IOError:
        raise Http404
    return HttpResponse(data, 'application/json')

def _spark_json(link, field):
    data = ({field: (round(v/BW_DIVISOR, BW_DECIMAL_POINTS))}
        for v in Bandwidth.objects.rates(field, link))
    data_table = gviz_api.DataTable({field:('number', 'Bandwidth')})
    data_table.LoadData(data)
    return data_table.ToJSon()
    
def xhr_spark_rx(request, link):
    """Return rx traffic in bits as JSON data"""
    return HttpResponse(_spark_json(link, 'rx'), 'application/json')

def xhr_spark_tx(request, link):
    """Return rx traffic in bits as JSON data"""
    return HttpResponse(_spark_json(link, 'tx'), 'application/json')


class MapView(TemplateView):
    template_name='gmap/map.html'

    def render_to_response(self, context):
        context = RequestContext(self.request, {
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


class DebugView(TemplateView):
    # simple view for django debug toolbar to show sql query
    template_name='gmap/debug.html'
        
    def render_to_response(self, context):
        link_id = 1
        context = RequestContext(self.request, {
            'rate': Bandwidth.objects.rate(link_id),
        })
        return super(DebugView, self).render_to_response(context)
    
