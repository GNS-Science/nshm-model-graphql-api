"""
Django settings for cookbook project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

## Monkey path to support older ES 6.8.0
#  see https://stackoverflow.com/a/70833150
import django
from django.utils.encoding import force_str
django.utils.encoding.force_text = force_str
## end monkey patch

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-*6mdqrx8xj5fkb4d@iy3yc#6u2@3hnsh1tc_a&p9os6z%o6xlg"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.getenv("DEBUG"))

ALLOWED_HOSTS = ["5qwlrdxd4a.execute-api.ap-southeast-2.amazonaws.com", "localhost"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "nshm",
    "pipeline",
    "graphene_django",
    "django_extensions",
    "django_elasticsearch_dsl"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nzshm_model_graphql_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "nzshm_model_graphql_api.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# https://django-extensions.readthedocs.io/en/latest/graph_models.html
GRAPH_MODELS = {
    "all_applications": False,
    "group_models": True,
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

"""
The following resolves issue https://github.com/GNS-Science/nshm-model-graphql-api/issues/10
 providing a static prefix that works both locally and on AWS. Notes:
   - Using django `manage.py runserver`, DEPLOYMENT_STAGE variable is not set.
   - using `sls wsgi serve`, DEPLOYMENT_STAGE is set to `LOCAL` in serverless.yml
   - on AWS the DEPLOYMENT_STAGE must be DEV, TEST or PROD.

Also, for some reason, we get the DEPLOYMENT_STAGE prefix set automatically by django if DEBUG==TRUE.
"""
DEPLOYMENT_STAGE = os.getenv("DEPLOYMENT_STAGE", "LOCAL").upper()
STATIC_URL = (
    "static/" if DEPLOYMENT_STAGE == "LOCAL" or DEBUG else f"{DEPLOYMENT_STAGE}/static/"
)
STATIC_ROOT = str(BASE_DIR / "staticfiles")

# using whitenoise to simplify static resources
# ref https://whitenoise.readthedocs.io/en/latest/#quickstart-for-django-apps
STORAGES = {
    # ...
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

SECURE_REFERRER_POLICY = "origin"
SECURE_CONTENT_TYPE_NOSNIFF = False
WHITENOISE_STATIC_PREFIX = "/static/"

#ref https://django-elasticsearch-dsl.readthedocs.io/en/latest/quickstart.html
ELASTICSEARCH_DSL={
    'default': {
        'hosts': 'localhost:9200'
    },
}