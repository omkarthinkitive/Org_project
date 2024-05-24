from .serializers import PostSerializer
from .models import Post
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    
    def get_queryset(self, *args, **kwargs):
        org_id = Post.objects.filter(organization_id = self.kwargs["id"])
        return org_id

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
    
class DetailPostViewset(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def retrieve(self, request,  *args, **kwargs):
        post = Post.objects.get(organization_id=self.kwargs["id"], id=self.kwargs["pid"])
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        try:
            post = Post.objects.get(organization_id=self.kwargs["id"], id=self.kwargs["pid"])
        except Post.DoesNotExist:
            return Response({'error': 'Post not found in this organization.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        post = Post.objects.get(organization_id=self.kwargs["id"], id=self.kwargs["pid"])
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'])
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, organization_id=self.kwargs["id"], id=self.kwargs["pid"])
        