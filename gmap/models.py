from datetime import datetime, timedelta
from django.conf import settings
from django.db import models


LINK_ALIVE_INTERVAL = getattr(settings, 'GMAP_LINK_ALIVE_INTERVAL', 5)


class BandwidthManager(models.Manager):
    """Return a tuple of rates (rx, tx) for a link in Bps."""
    def rates(self, link):
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
    


class Bandwidth(models.Model):
    """Bandwidth on an NDN network link"""
    link = models.IntegerField()
    time = models.FloatField()
    rx = models.BigIntegerField()
    tx = models.BigIntegerField()
    update_date = models.DateTimeField(default=datetime.now, editable=False)
      
    objects = BandwidthManager()
       
    def save(self, *args, **kwargs):
        if not self.rx and not self.tx:
            return
        else:
            super(Bandwidth, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return 'link {0}'.format(self.link)
