# Copyright (c) 2012 Shakir James and Washington University in St. Louis.
# See LICENSE for details.

from gmap.models import Bandwidth
from django.contrib import admin

class BandwidthAdmin(admin.ModelAdmin,):
    # customize the admin change list
    list_display = ('link', 'time', 'rx', 'tx')
    list_filter = ('link', )
    search_fields = ('link', 'rx', 'tx')


admin.site.register(Bandwidth, BandwidthAdmin)