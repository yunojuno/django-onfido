from os import getenv

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv('TEST_DB_NAME', 'postgres'),
        'USER': getenv('TEST_DB_USER', 'postgres'),
        'PASSWORD': getenv('TEST_DB_PASSWORD', 'postgres'),
        'HOST': getenv('TEST_DB_HOST', 'localhost'),
        'PORT': getenv('TEST_DB_PORT', '6432'),
    }
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'onfido',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)

SECRET_KEY = "onfido"

ROOT_URLCONF = 'urls'

APPEND_SLASH = True

STATIC_URL = '/static/'

TIME_ZONE = 'UTC'

USE_TZ = True

SITE_ID = 1

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        # 'null': {
        #     'level': 'DEBUG',
        #     'class': 'django.utils.log.NullHandler',
        # },
    },
    'loggers': {
        # '': {
        #     'handlers': ['null'],
        #     'propagate': True,
        #     'level': 'DEBUG',
        # },
        # 'django': {
        #     'handlers': ['console'],
        #     'level': getenv('LOGGING_LEVEL_DJANGO', 'WARNING'),
        #     'propagate': False,
        # },
        # 'django.db.backends': {
        #     'level': 'ERROR',
        #     'handlers': ['console'],
        #     'propagate': False,
        # },
        'onfido': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

assert DEBUG is True, "This project is only intended to be used for testing."

ONFIDO_WEBHOOK_TOKEN=getenv('ONFIDO_WEBHOOK_TOKEN')

