from .base import *

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

MEDIA_ROOT = os.path.join(SITE_ROOT, ".static-media/m")
STATIC_ROOT = os.path.join(SITE_ROOT, ".static-media/s")

CACHES = {
    'default' : {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

INSTALLED_APPS += (
    'debug_toolbar',
)

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

# DjDT settings
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

INTERNAL_IPS = (
    '127.0.0.1',
)

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