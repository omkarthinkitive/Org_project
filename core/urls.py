from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import OrganizationViewSet

router = DefaultRouter()
router.register('organizations', OrganizationViewSet, basename="organizations")

urlpatterns = router.urls
