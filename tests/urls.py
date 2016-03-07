from django.conf.urls import patterns, url, include


urlpatterns = patterns(
    '',
    url('', include('tests.test_app.urls')),
)
