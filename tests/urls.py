from django.urls import path, include


urlpatterns = [
    path("", include("tests.test_app.urls")),
]
