from rest_framework import routers
from .views import NaturalKeyChildViewSet, ModelWithNaturalKeyViewSet


router = routers.DefaultRouter()
router.register(r'naturalkeychilds', NaturalKeyChildViewSet)
router.register(r'modelwithnaturalkeys', ModelWithNaturalKeyViewSet)

urlpatterns = router.urls
