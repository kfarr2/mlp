import os
from fnmatch import fnmatch
from django.core.urlresolvers import reverse_lazy
from django.contrib.messages import constants as messages
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP, LOGGING, AUTHENTICATION_BACKENDS
from varlet import variable
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError: # pragma: no cover
    pass

here = lambda *path: os.path.normpath(os.path.join(os.path.dirname(__file__), *path))
ROOT = lambda *path: here("../", *path)

DEBUG = variable("DEBUG", False)
TEMPLATE_DEBUG = DEBUG 

FFMPEG_BINARY = ROOT("bin/ffmpeg")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': variable("DB_NAME", 'language'),
        'USER': variable("DB_USERNAME", 'root'),
        'PASSWORD': variable("DB_PASSWORD", ""),
        'HOST': variable("DB_HOST", 'localhost'),
        'PORT': '',

    },
}

ALLOWED_HOSTS = [".pdx.edu"]

DEFAULT_FROM_EMAIL = SERVER_EMAIL = 'no-reply@pdx.edu'

# in test mode?
TEST = False
TEST_RUNNER = "mlp.runner.MLPRunner"

LOGIN_URL = reverse_lazy("home")
LOGIN_REDIRECT_URL = reverse_lazy("users-home")
LOGOUT_URL = reverse_lazy("home")

ELASTIC_SEARCH_CONNECTION = {
    "urls": [variable("ELASTIC_SEARCH_HOST", "http://localhost:9200/")],
    "index": variable("ELASTIC_SEARCH_INDEX_NAME", "mlp_dev"),
}

ELASTIC_SEARCH_SETTINGS = {
    "settings": {
        "analysis": {
            "analyzer": {
                "snowball": {
                    "type": "snowball",
                    "stopwords": "_none_"
                }
            }
        }
    }
}


BROKER_URL = variable("BROKER_URL", 'amqp://guest:guest@localhost//')
CELERY_ACKS_LATE = True

# uncomment to use CAS. You need to update requirements.txt too
# CAS_SERVER_URL = 'https://sso.pdx.edu/cas/'
# AUTHENTICATION_BACKENDS += ('djangocas.backends.CASBackend',)

ITEMS_PER_PAGE = 25

# file upload stuff
MAX_UPLOAD_SIZE = 8 * 2**30 # Roughly 8.59 gigs
CHUNK_SIZE = 1 * 2**20 # Roughly 1 mb

AUTH_USER_MODEL = 'users.User'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# allow the use of wildcards in the INTERAL_IPS setting
class IPList(list):
    # do a unix-like glob match
    # E.g. '192.168.1.100' would match '192.*'
    def __contains__(self, ip): # pragma: no cover
        for ip_pattern in self:
            if fnmatch(ip, ip_pattern):
                return True
        return False

INTERNAL_IPS = IPList(['10.*', '192.168.*'])


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    #'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'bootstrapform',
    'elasticmodels',
    'arcutils',
    'permissions',
    'cloak',
    'celery',
    'mlp.home',
    'mlp.users',
    'mlp.files',
    'mlp.tags',
    'mlp.groups',
    'mlp.utils',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'djangocas.middleware.CASMiddleware',
    'cloak.middleware.CloakMiddleware',

)

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

ROOT_URLCONF = 'mlp.urls'

WSGI_APPLICATION = 'mlp.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Los_Angeles'

USE_I18N = False

USE_L10N = False

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = ROOT("static")

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    here("static"),
)

MEDIA_URL = '/media/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ROOT("media")

TMP_ROOT = ROOT("tmp")

TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    here("templates"),
)

SECRET_KEY = variable("SECRET_KET", os.urandom(64).decode("latin1"))
