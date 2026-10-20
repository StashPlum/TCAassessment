import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('TCA_SECRET_KEY', 'local-demo-only-change-before-deployment')
# Hosted demo mode (TCA_DEMO=1): fictional data, local demo accounts, HTTPS only. Not a production setup.
DEMO = os.environ.get('TCA_DEMO') == '1'
DEBUG = os.environ.get('TCA_DEBUG', '1') == '1' and not DEMO
ALLOWED_HOSTS = ['127.0.0.1', 'localhost'] if DEBUG else [h.strip() for h in os.environ.get('TCA_ALLOWED_HOSTS', '').split(',') if h.strip()]
if DEMO and os.environ.get('RENDER_EXTERNAL_HOSTNAME'): ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
if DEMO and not ALLOWED_HOSTS: ALLOWED_HOSTS = ['.onrender.com']  # build step may run before the public hostname is known
CSRF_TRUSTED_ORIGINS = ['https://'+('*'+h if h.startswith('.') else h) for h in ALLOWED_HOSTS] if DEMO else []
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.debug', 'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages', 'core.context.workspace']}}]
WSGI_APPLICATION = 'config.wsgi.application'
if os.environ.get('DATABASE_URL'):
    from urllib.parse import urlparse, unquote
    url = urlparse(os.environ['DATABASE_URL'])
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': url.path.lstrip('/'), 'USER': unquote(url.username or ''),
                             'PASSWORD': unquote(url.password or ''), 'HOST': url.hostname, 'PORT': str(url.port or 5432), 'CONN_MAX_AGE': 60}}
elif os.environ.get('PGDATABASE'):
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.environ['PGDATABASE'], 'USER': os.environ.get('PGUSER', ''), 'PASSWORD': os.environ.get('PGPASSWORD', ''), 'HOST': os.environ.get('PGHOST', 'localhost'), 'PORT': os.environ.get('PGPORT', '5432')}}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': os.environ.get('TCA_SQLITE_PATH', BASE_DIR / 'local.sqlite3')}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
if DEMO:
    from django.core.exceptions import ImproperlyConfigured
    if SECRET_KEY.startswith('local-demo-only'): raise ImproperlyConfigured('Set TCA_SECRET_KEY for the hosted demo.')
    MIDDLEWARE.insert(0, 'core.health.HealthCheckMiddleware')
    MIDDLEWARE.insert(2, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'}}
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_REFERRER_POLICY = 'same-origin'
    SESSION_COOKIE_AGE = 60 * 60 * 12
    LOGGING = {'version': 1, 'disable_existing_loggers': False, 'handlers': {'console': {'class': 'logging.StreamHandler'}}, 'root': {'handlers': ['console'], 'level': 'WARNING'}}
elif not DEBUG:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured('Corporate OIDC authentication is not configured; production login is disabled.')
