import os
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, abspath(join(dirname(__file__), "../../")))

os.environ['DJANGO_SETTINGS_MODULE'] = 'sfnews.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
