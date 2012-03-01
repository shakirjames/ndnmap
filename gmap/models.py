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
from datetime import datetime, timedelta
from django.conf import settings
from django.db import models


LINK_ALIVE_INTERVAL = getattr(settings, 'GMAP_LINK_ALIVE_INTERVAL', 5)
# Max number of traffic values to return (for sparkline plot)
TRAFFIC_MAX_VALUES = getattr(settings, 'GMAP_TRAFFIC_MAX_VALUES', 200)


class BandwidthManager(models.Manager):
    def rates(self, link):
        """Return a tuple of rates (rx, tx) for a link in Bps."""
        try:
            b1 = Bandwidth.objects.filter(link=link).order_by('-update_date')[0]
            b0 = Bandwidth.objects.filter(link=link).order_by('-update_date')[1]
        except IndexError:
            return (0, 0)
        else:
            alive_int = datetime.now() - b1.update_date
            if alive_int > timedelta(seconds=LINK_ALIVE_INTERVAL):
                # link is inactive
                return (0, 0)            
            t_delta = float(b1.time - b0.time)
            if t_delta == 0:
                t_delta = 0.001
            rx = (b1.rx - b0.rx ) / t_delta
            tx = (b1.tx - b0.tx ) / t_delta
            # Test for negative rates:
            #     Since we ignore 0 bit counts, this can happen if a 
            #     recent report's (rx,tx) is less than the penultimate one.
            if rx < 0: rx = 0
            if tx < 0: tx = 0
            return (rx, tx)
    
    def traffic(self, link, max_values=TRAFFIC_MAX_VALUES):
        """Return a list of bit counts [{'rx':b1, 'tx':b2}, ...]"""
        data = []
        traffic = Bandwidth.objects.filter(link=link).order_by('update_date')
        for t in traffic:
            data.append({'rx': t.rx, 'tx':t.tx})
        return data

    
class Bandwidth(models.Model):
    """Bandwidth on an NDN network link"""
    link = models.IntegerField()
    time = models.FloatField()
    rx = models.BigIntegerField()
    tx = models.BigIntegerField()
    update_date = models.DateTimeField(default=datetime.now, editable=False)

    class Meta:
        ordering = ('-update_date', )
    
    objects = BandwidthManager()
       
    def save(self, *args, **kwargs):
        if not self.rx and not self.tx:
            return
        else:
            super(Bandwidth, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return 'link {0}'.format(self.link)
