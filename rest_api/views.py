from .serializers import PostSerializer
from .models import Post
from rest_framework import viewsets, status
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    def get_queryset(self):
        org_id = self.request.query_params.get("organization_id")
        return Post.objects.filter(organization_id=org_id)
    

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="organization_id", 
                type=int, 
                location="query",
                required=True
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization_id = serializer.validated_data.get("organization")
        instance = serializer.save()
        if organization_id:
            instance.organization_id = organization_id
            instance.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)