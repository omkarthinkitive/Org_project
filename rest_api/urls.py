from django.urls import path, include
# from .views import post_list, post_details
from rest_framework.routers import DefaultRouter
from rest_api.views import OrganizationViewSet, PostViewSet

router = DefaultRouter()
router.register('organizations', OrganizationViewSet)
router.register('posts', PostViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

