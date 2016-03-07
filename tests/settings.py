SECRET_KEY = '1234'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
ROOT_URLCONF = "tests.urls"
REST_FRAMEWORK = {
    'UNAUTHENTICATED_USER': None,
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'wq.db.rest',
    'tests.test_app',
]
