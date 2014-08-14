from .base import ELASTIC_SEARCH_CONNECTION

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SUBDOMAIN = 'foo'
HOSTNAME = 'example.com'

CELERY_ALWAYS_EAGER = True
TEST = True

ELASTIC_SEARCH_CONNECTION['index'] = "mlp_test"
