from django.db import models
from django.utils.translation import ugettext as _


class Bandwidth(models.Model):
    """Bandwidth on an NDN network link"""
    link = models.IntegerField()
    rx = models.IntegerField()
    tx = models.IntegerField()
    timestamp = models.IntegerField()
