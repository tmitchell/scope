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

# DjDT settings
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

INTERNAL_IPS = (
    '127.0.0.1',
)