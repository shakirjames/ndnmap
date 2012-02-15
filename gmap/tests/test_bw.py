"""gmap tests"""
from django.conf import settings
from django.test import TestCase
from gmap.models import Bandwidth

class BandwidthXHRTest(TestCase):
    """Tests for JSON data from XMLHttpRequests"""
    def setUp(self):
        Bandwidth.objects.all().delete()
        self.b = Bandwidth.objects.create(link=1, time=1, rx=1, tx=1)
    
    def test_non_xhr(self):
        """Test return 404 if non-AJAX request."""
        from django.core.urlresolvers import reverse 
        r = self.client.get(reverse('xhr_bw', args=(self.b.pk, )))
        self.assertEqual(r.status_code, 404)
    
    def test_xhr_request(self):
        """Test JSON data from AJAX request."""
        from django.core.urlresolvers import reverse 
        import json
        r = self.client.get(reverse('xhr_bw', args=(self.b.pk, )), 
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        j = json.loads(r.content)
        self.assertTrue(j.has_key('rx'))
        self.assertTrue(j.has_key('tx'))
    


class BandwidthManagerTest(TestCase):
    """Test for BandwidthManager rates"""
    def setUp(self):
        Bandwidth.objects.all().delete() # if any initial_data
        Bandwidth.objects.create(link=1, time=1, rx=1, tx=1)
        Bandwidth.objects.create(link=2, time=1, rx=1, tx=1)
        Bandwidth.objects.create(link=2, time=2, rx=2, tx=2)
        Bandwidth.objects.create(link=3, time=1, rx=2, tx=10)
        Bandwidth.objects.create(link=3, time=3, rx=4, tx=20)
    
    def test_no_bw(self):
        """Test no updates"""
        self.assertEqual(Bandwidth.objects.rates(999), (0, 0))
    
    def test_zero_bw(self):
        """Test one bw update"""
        self.assertEqual(Bandwidth.objects.rates(1), (0, 0))
    
    def test_one_bw(self):
        """Test 1 unit rates"""
        self.assertEqual(Bandwidth.objects.rates(2), (1.0, 1.0))
    
    def test_diff_tx_rx(self):
        """Test different rates"""
        self.assertEqual(Bandwidth.objects.rates(3), (1.0, 5.0))        
     
    def test_alive_interval(self):
        """Test link_alive_interval"""
        from datetime import timedelta        
        tdelta = timedelta(seconds=(settings.GMAP_LINK_ALIVE_INTERVAL+1))
        (b1, b0) = Bandwidth.objects.filter(link=3).order_by('-update_date')
        b1.update_date -=  tdelta
        b0.update_date -=  tdelta
        b1.save()
        b0.save()
        self.assertEqual(Bandwidth.objects.rates(3), (0, 0))
    
    def test_zero_tdelta(self):
        """Test two reports at same time"""
        from datetime import datetime
        (b1, b0) = Bandwidth.objects.filter(link=3).order_by('-update_date')
        b1.time = 1
        b0.time = 1
        b1.save()
        b0.save()
        rx, tx = Bandwidth.objects.rates(3) # no ZeroDivisionError
    
    def test_negative_rate(self):
        """Test for negative rates"""
        Bandwidth.objects.create(link=4, time=1, rx=4, tx=20)
        Bandwidth.objects.create(link=4, time=3, rx=2, tx=10)
        self.assertEqual(Bandwidth.objects.rates(4), (0, 0))
    
    