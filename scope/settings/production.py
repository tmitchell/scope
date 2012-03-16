from .base import *

DEBUG = TEMPLATE_DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

MEDIA_ROOT = '/var/www/django/media' 
STATIC_ROOT = '/var/www/django/static' 
STATIC_URL = '/django/static/'
MEDIA_URL = '/django/media/'

CACHES = {
    'default' : {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': { 'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s' },
        'simple': { 'format': '%(levelname)s %(message)s' },
    },
    'filters': { },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'project':{
            'level':'DEBUG',
            'class':'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(SITE_ROOT, 'logs', 'scope.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers':['null'],
            'propagate': False,
            'level':'DEBUG'
        },
        '': {
            'handlers': ['project'],
            'propagate': True,
            'level': 'DEBUG'
        },
    }
}
