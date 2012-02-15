from gmap.models import Bandwidth
from django.contrib import admin

class BandwidthAdmin(admin.ModelAdmin,):
    # customize the admin change list
    list_display = ('link', 'time', 'rx', 'tx')
    list_filter = ('link', )
    #search_fields = ('link', )


admin.site.register(Bandwidth, BandwidthAdmin)