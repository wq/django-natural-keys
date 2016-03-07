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
    'tests.test_app',
]
