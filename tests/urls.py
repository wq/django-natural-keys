from django.conf.urls import url, include


urlpatterns = [
    url('', include('tests.test_app.urls')),
]
