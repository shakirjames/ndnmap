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


BW_UPDATE_INTERVAL = getattr(settings, 'GMAP_BW_UPDATE_INTERVAL', 5)


def _get_traffic_json(link):
    """Return Traiffic in bits"""
    from utils import gviz_api
    from math import ceil
    description = {'rx':('number','Received'), 'tx': ('number','Sent')}
    data_table = gviz_api.DataTable(description)
    data_table.LoadData(Bandwidth.objects.traffic(link))
    json = data_table.ToJSon()
    return json


def bw(request, link , time, rx, tx):
    """Add bandwidth reports"""
    # WARNING: This is not safe!
    Bandwidth.objects.create(link=link, time=time, rx=rx, tx=tx)
    return HttpResponse('Got it.\n')


def xhr_bw(request, link):
    """Return JSON data with link rates in Bps."""
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


def xhr_traffic(request, link):
    """Return traffic JSON data in bits"""
    return HttpResponse(_get_traffic_json(link), 'application/json')


class MapView(TemplateView):
    template_name='gmap/map.html'

    def render_to_response(self, context):
        context = RequestContext(self.request, {
            'bw_url': reverse('xhr_bw', args=(0, )).split('0')[0],
            'traffic_url': reverse('xhr_traffic', args=(0, )).split('0')[0],
            'bw_update_interval': BW_UPDATE_INTERVAL*1000, # ms
        })
        return super(MapView, self).render_to_response(context)

class SparkLine(TemplateView):
    template_name='gmap/sparkline.html'

    def render_to_response(self, context):
        context = RequestContext(self.request, {
            'json_data': _get_traffic_json(self.kwargs['link']),
        })
        return super(SparkLine, self).render_to_response(context)

