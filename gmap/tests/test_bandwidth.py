# Copyright (c) 2012 Shakir James and Washington University in St. Louis.
# All rights reserved

"""gmap tests"""
from django.conf import settings
from django.test import TestCase
from gmap.models import Bandwidth

class BandwidthSaveTest(TestCase):
    """Test Bandwidth save override method"""
    link = 1
    time = 1.
    def setUp(self):
        Bandwidth.objects.all().delete()
        
    def _test_rx_tx(self, rx, tx):
        b = Bandwidth.objects.filter(link=self.link)[0]
        self.assertEqual((b.rx, b.tx), (rx, tx))
    
    def test_no_bits(self):
        """Test that zero bit counts are ignored."""
        Bandwidth.objects.create(link=self.link, time=self.time, rx=0, tx=0)
        count = Bandwidth.objects.filter(link=self.link).count()
        self.assertEquals(0, count) 
    
    def test_bits_honored(self):
        """Test bit counts honored as specified."""
        Bandwidth.objects.create(link=self.link, time=self.time, rx=1, tx=1)
        self._test_rx_tx(1, 1)
    
    def test_rx_only(self):
        """Test rx honored with zero tx."""
        Bandwidth.objects.create(link=self.link, time=self.time, rx=1, tx=0)
        self._test_rx_tx(1, 0)
    
    def test_tx_only(self):
        """Test tx honored with zero rx."""
        Bandwidth.objects.create(link=self.link, time=self.time, rx=0, tx=1)
        self._test_rx_tx(0, 1)
    

class BandwidthAddTest(TestCase):
    """Test view to add Bandwidth"""    
    def setUp(self):
        Bandwidth.objects.all().delete()
    
    def test_bw(self):
        from django.core.urlresolvers import reverse 
        d = (1, 1., 1, 1)
        r = self.client.get(reverse('bw', args=(d)))
        b = Bandwidth.objects.filter(link=1)[0]
        self.assertEqual(d, (b.link, b.time, b.rx, b.tx))
    

class BandwidthXHRTest(TestCase):
    """Test XMLHttpRequests"""
    def setUp(self):
        Bandwidth.objects.all().delete()
        self.b = Bandwidth.objects.create(link=1, time=1., rx=1, tx=1)
    
    def test_xhr_request(self):
        """Test valid JSON data from AJAX request."""
        from django.core.urlresolvers import reverse 
        import json
        r = self.client.get(reverse('xhr_bw', args=(self.b.pk, )), 
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        j = json.loads(r.content)
        self.assertTrue(j.has_key('rx'))
        self.assertTrue(j.has_key('tx'))
    

class BandwidthManagerRateTest(TestCase):
    """Test BandwidthManager rate"""
    def setUp(self):
        Bandwidth.objects.all().delete() # if any initial_data
        Bandwidth.objects.create(link=1, time=1., rx=1, tx=1)
        Bandwidth.objects.create(link=2, time=1., rx=1, tx=1)
        Bandwidth.objects.create(link=2, time=2., rx=2, tx=2)
        Bandwidth.objects.create(link=3, time=1., rx=2, tx=10)
        Bandwidth.objects.create(link=3, time=3., rx=4, tx=20)
    
    def test_no_bw(self):
        """Test no updates"""
        self.assertEqual(Bandwidth.objects.rate(999), (0, 0))
    
    def test_zero_bw(self):
        """Test one bw update"""
        self.assertEqual(Bandwidth.objects.rate(1), (0, 0))
    
    def test_one_bw(self):
        """Test 1 unit rate"""
        self.assertEqual(Bandwidth.objects.rate(2), (1.0, 1.0))
    
    def test_diff_tx_rx(self):
        """Test different rate"""
        self.assertEqual(Bandwidth.objects.rate(3), (1.0, 5.0))        
     
    def test_alive_interval(self):
        """Test link_alive_interval"""
        from datetime import timedelta        
        tdelta = timedelta(seconds=(settings.GMAP_LINK_ALIVE_INTERVAL+1))
        (b1, b0) = Bandwidth.objects.filter(link=3).order_by('-update_date')
        b1.update_date -=  tdelta
        b0.update_date -=  tdelta
        b1.save()
        b0.save()
        self.assertEqual(Bandwidth.objects.rate(3), (0, 0))
    
    def test_zero_tdelta(self):
        """Test two reports at same time"""
        from datetime import datetime
        (b1, b0) = Bandwidth.objects.filter(link=3).order_by('-update_date')
        b1.time = 1
        b0.time = 1
        b1.save()
        b0.save()
        rx, tx = Bandwidth.objects.rate(3) # no ZeroDivisionError
    
    def test_negative_rate(self):
        """Test for negative rate"""
        Bandwidth.objects.create(link=4, time=1, rx=4, tx=20)
        Bandwidth.objects.create(link=4, time=3, rx=2, tx=10)
        self.assertEqual(Bandwidth.objects.rate(4), (0, 0))

class BandwidthManagerRatesTest(TestCase):
    """Test BandwidthManager rate"""
    def setUp(self):
        Bandwidth.objects.all().delete() # if any initial_data

    def test_single_value_rates(self):
        Bandwidth.objects.create(link=1, time=1., rx=1, tx=1)
        self.assertEqual(Bandwidth.objects.rates('rx', 1, 2), [])
        self.assertEqual(Bandwidth.objects.rates('tx', 1, 2), [])
            
    def test_1s_interval_rates(self):
        """Test one-second rates"""
        Bandwidth.objects.create(link=1, time=1., rx=1, tx=1)
        Bandwidth.objects.create(link=1, time=2., rx=10, tx=2)
        Bandwidth.objects.create(link=1, time=3., rx=100, tx=4)
        self.assertEqual(Bandwidth.objects.rates('rx', 1, 2), [9., 90.])
        self.assertEqual(Bandwidth.objects.rates('tx', 1, 2), [1., 2.])
        
    def test_varable_interval_rates(self):
        Bandwidth.objects.create(link=1, time=1., rx=1, tx=1)
        Bandwidth.objects.create(link=1, time=5., rx=13, tx=1)
        Bandwidth.objects.create(link=1, time=7., rx=101, tx=1)
        Bandwidth.objects.create(link=1, time=15., rx=109, tx=1)
        self.assertEqual(Bandwidth.objects.rates('rx', 1, 2), [3., 44., 1.])
        self.assertEqual(Bandwidth.objects.rates('tx', 1, 2), [0., 0., 0.])    
    
    