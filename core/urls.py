from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import DetailUserViewSet, OrganizationOwnerViewSet, OrganizationUserViewSet, OrganizationViewSet
from rest_api.views import DetailPostViewset, PostViewSet

router = DefaultRouter()
router.register('organizations', OrganizationViewSet, basename="organizations")


urlpatterns = router.urls + [
    path(
        "organizations/<int:id>/user",
        OrganizationUserViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "organizations/<int:id>/owner",
        OrganizationOwnerViewSet.as_view(
            {
                "get": "list",
            }
        ),
    ),
    path(
        "organizations/<int:id>/user/<int:uid>",
        DetailUserViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                'delete': 'destroy',
            }
        ),
    ),
    path(
        "organizations/<int:id>/posts",
        PostViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        )
    ),
    path(
        "organizations/<int:id>/posts/<int:pid>",
        DetailPostViewset.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                'delete': 'destroy',
            }
        )
    ),
]
