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
from itertools import tee, izip
from django.conf import settings
from django.db import models


LINK_ALIVE_INTERVAL = getattr(settings, 'GMAP_LINK_ALIVE_INTERVAL', 5)
# Max number of traffic values to return (for sparkline plot)
TRAFFIC_MAX_VALUES = getattr(settings, 'GMAP_TRAFFIC_MAX_VALUES', 200)


class BandwidthManager(models.Manager):
    """Manager that calculates rates (bandwidths) from traffic"""
        
    def _pairwise(self, iterable):
        """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
        # from itertools recipe
        # http://docs.python.org/library/itertools.html#recipes
        a, b = tee(iterable)
        next(b, None)
        return izip(a, b)
    
    def _get_rate(self, attr, x0, x1):
        """Return rate (bandwidth) from traffic values"""
        t_delta = float(x1.time - x0.time)
        if t_delta == 0:
            return 0
        return (getattr(x1, attr) - getattr(x0, attr)) / t_delta
    
    def rate(self, link):
        """Return a rate tuple (rx, tx) for a link in Bps.
        Args:
            link: link id        
        """
        try:
            t1 = Bandwidth.objects.filter(link=link).order_by('-update_date')[0]
            t0 = Bandwidth.objects.filter(link=link).order_by('-update_date')[1]
        except IndexError:
            return (0, 0)
        else:
            alive_int = datetime.now() - t1.update_date
            if alive_int > timedelta(seconds=LINK_ALIVE_INTERVAL):
                # link is inactive
                return (0, 0)            
            rx, tx = self._get_rate('rx', t0, t1), self._get_rate('tx', t0, t1) 
            # Test for negative rate:
            #    Negative rates happen when the lastest report's (rx,tx) 
            #    is less than the penultimate one: a counter rolls over.
            if rx < 0: rx = 0
            if tx < 0: tx = 0
            return (rx, tx)
    
    def rates(self, direction, link):
        """Return a list of average rates
        
        Args:
            direction: 'rx' or 'tx' traffic
            link: link id
        """
        itr = Bandwidth.objects.filter(link=link).order_by('update_date').iterator()
        rates = []
        for t0, t1 in self._pairwise(itr):
            if t1 is not None:
                rates.append(self._get_rate(direction, t0, t1))
        return rates
    

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
