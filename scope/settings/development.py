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