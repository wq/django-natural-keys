from django.conf.urls import patterns, url, include
from wq.db import rest


urlpatterns = patterns(
    '',
    url('', include(rest.router.urls)),
)
