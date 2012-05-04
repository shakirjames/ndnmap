# local settings for ndnmap project.
from os import path, environ

DEBUG = True
TEMPLATE_DEBUG = True


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', 
        'NAME': path.join(path.dirname(__file__), 'local.sqlite'),
        'USER': '',      
        'PASSWORD': '',  
        'HOST': '',      
        'PORT': '',      
    }
}

#GMAP_BW_UPDATE_INTERVAL = 10
