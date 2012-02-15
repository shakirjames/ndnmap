# local settings for sfnews project.
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

AWS_SECRET_ACCESS_KEY = environ['AWS_SECRET_ACCESS_KEY']
AWS_ACCESS_KEY_ID = environ['AWS_ACCESS_KEY_ID']
