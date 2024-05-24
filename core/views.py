
from django.conf import settings
import jwt
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from core.utils import send_invitation_email, update_organization_owner
from core.models import NestedOrganization
from core.permission import (
    IsOrganizationCreateAllowed, 
    IsOrganizationOwner, 
    IsOrganizationOwnerOrAdmin, 
    IsOrganizationUser
)
from .serializers import  (
    AcceptInvitationSerializer, 
    NestedOrganizationSerializer, 
    OrganizationInvitationSerializer, 
    OrganizationOwnerSerializer, 
    OrganizationUserSerializer
)
from rest_framework import viewsets
from organizations.models import (
    OrganizationUser, 
    OrganizationOwner, 
    OrganizationInvitation
)
from rest_framework.decorators import action
from rest_framework.permissions import  AllowAny
from django.shortcuts import render
  
class OrganizationViewSet(viewsets.ModelViewSet):
    
    queryset = NestedOrganization.objects.all()
    serializer_class = NestedOrganizationSerializer
    
    def get_serializer_class(self):
        if self.action == "organization_invitations":
            return OrganizationInvitationSerializer
        if self.action == "accept_invite":
            return AcceptInvitationSerializer
        return super().get_serializer_class()
    
    def get_permissions(self):
        permission_classes = []
        if self.action == 'create':
            permission_classes = [IsOrganizationCreateAllowed]
        elif self.action == "accept-invite":
            permission_classes=[AllowAny]
        elif self.action in ["retrieve", "questions"]:
            permission_classes = [IsOrganizationUser]
        elif self.action in ["partial_update", "update", "organization_invitations"]:
            permission_classes = [IsOrganizationOwnerOrAdmin]
        elif self.action in ["destroy"]:
            permission_classes = [IsOrganizationOwner]
        return [permission() for permission in permission_classes]

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        organization_ids = OrganizationUser.objects.filter(user=user).values_list('organization', flat=True)
        return NestedOrganization.objects.filter(id__in=organization_ids)

    def create(self, request):
        with transaction.atomic():
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            parent_org = serializer.validated_data.get("parent_orgnaization")
            user_id = (
                self.request.user.id 
                if not parent_org
                else OrganizationOwner.objects.filter(
                    organization=parent_org
                ).first().organization_user.user_id
            )

            org_user = OrganizationUser.objects.create(
                user_id=user_id,
                organization_id=serializer.data["id"],
            )
            org_owner = OrganizationOwner.objects.create(
                organization_user_id=org_user.id, organization_id=serializer.data["id"]
            )
            org_owner.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def partial_update(self, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            serializer = self.serializer_class(data=self.request.data, instance=instance, partial=True)
            serializer.is_valid(raise_exception=True)
            parent = serializer.validated_data.get("parent_organization")
            if parent and parent != instance.parent:
                old_user_id = OrganizationOwner.objects.filter(
                    organization=instance
                ).first().organization_user.user_id
                new_user_id =  OrganizationOwner.objects.filter(
                    organization=parent
                ).first().organization_user.user_id
                if old_user_id != new_user_id:
                    update_organization_owner(instance, new_user_id)
            serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=["GET", "POST"], url_path="invitations")
    def organization_invitations(self, request, pk):
        if request.method == "GET":
            invitations = OrganizationInvitation.objects.filter(
                organization=pk
            )
            serializer = self.get_serializer(invitations, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == "POST":
            try:
                with transaction.atomic():
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    instance = serializer.save(organization_id=pk)

                    if instance.invitee.email:
                        send_invitation_email(request, instance)
            except Exception as e:
                return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    @action(detail=False, methods=["POST"], url_path="accept_invite", permission_classes=[AllowAny])
    def accept_invite(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['token']

        try:
            data = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"], verify=True
            )
        except (jwt.DecodeError, jwt.ExpiredSignatureError) as e:
            return Response(
                {"detail": "Invalid invite URL", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            invitation_id = data.get('invitation_id')
            user_id = data.get('user_id')
            org_id = data.get('org_id')
            invite = OrganizationInvitation.objects.filter(id=invitation_id, invitee_id=user_id, organization_id=org_id).first()

            if not invite:
                return Response(
                    {"detail": "Invalid invite URL", "error": "Invitation not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if OrganizationUser.objects.filter(user_id=user_id, organization_id=org_id).exists():
                return Response(
                    {"detail": "User is already a member of the organization"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            OrganizationUser.objects.create(
                user_id=user_id,
                organization_id=org_id,
            )

            invite.delete()
            return Response({"detail": "Invitation successfully accepted"}, status=status.HTTP_200_OK)


class OrganizationOwnerViewSet(viewsets.ModelViewSet):
    queryset = OrganizationOwner.objects.all()
    serializer_class = OrganizationOwnerSerializer
    lookup_field = "id"
    
    def get_queryset(self, *args, **kwargs):
        organization_owner = OrganizationOwner.objects.filter(organization_id = self.kwargs["id"])
        return organization_owner
    
class OrganizationUserViewSet(viewsets.ModelViewSet):
    queryset = OrganizationUser.objects.all()
    serializer_class = OrganizationUserSerializer
    
    def get_queryset(self, *args, **kwargs):
        organization_user = OrganizationUser.objects.filter(organization_id = self.kwargs["id"])
        return organization_user
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization_id = request.data.get('organization_id')
        user_id = request.data.get('user_id')
        if not organization_id:
            return Response({'error': 'Organization ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user_id:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if OrganizationUser.objects.filter(organization_id=organization_id, user_id=user_id).exists():
            return Response({'error': 'User already exists in this organization.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
class DetailUserViewSet(viewsets.ModelViewSet):
    queryset = OrganizationUser.objects.all()
    serializer_class = OrganizationUserSerializer
    
    def retrieve(self, request,  *args, **kwargs):
        try:
            organization_user = OrganizationUser.objects.get(organization_id=self.kwargs["id"], user_id=self.kwargs["uid"])
        except OrganizationUser.DoesNotExist:
            return Response({'error': 'User not found in this organization.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrganizationUserSerializer(organization_user)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        try:
            organization_user = OrganizationUser.objects.get(organization_id=self.kwargs["id"], user_id=self.kwargs["uid"])
        except OrganizationUser.DoesNotExist:
            return Response({'error': 'User not found in this organization.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrganizationUserSerializer(organization_user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        try:
            organization_user = OrganizationUser.objects.get(organization_id=self.kwargs["id"], user_id=self.kwargs["uid"])
        except OrganizationUser.DoesNotExist:
            return Response({'error': 'User not found in this organization.'}, status=status.HTTP_404_NOT_FOUND)
        
        organization_user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'])
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, organization_id=self.kwargs["id"], user_id=self.kwargs["uid"])
