
import json
from django.conf import settings
from django.http import HttpRequest, HttpResponse
import jwt
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from core.utils import send_invitation_email
from .serializers import  OrganizationInvitationSerializer
from rest_framework import viewsets
from organizations.models import Organization, OrganizationUser, OrganizationOwner, OrganizationInvitation
from core.serializers import OrganizationSerializer
from rest_framework.decorators import action
from rest_framework.permissions import  AllowAny
from drf_spectacular.utils import OpenApiParameter, extend_schema

    
class OrganizationViewSet(viewsets.ModelViewSet):
    
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    
    def get_serializer_class(self):
        if self.action == "organization_invitations":
            return OrganizationInvitationSerializer
        return super().get_serializer_class()

    
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        organization_ids = OrganizationUser.objects.filter(user=user).values_list('organization', flat=True)
        return Organization.objects.filter(id__in=organization_ids)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        org_user = OrganizationUser.objects.create(
            user_id=self.request.user.id,
            organization_id=serializer.data["id"],
        )
        org_owner = OrganizationOwner.objects.create(
            organization_user_id=org_user.id, organization_id=serializer.data["id"]
        )
        org_owner.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
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
        
class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="token", type=str, location="query"),
        ],
    )
    def get(self, request: HttpRequest):
        token = request.GET.get("token")

        try:
            data = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"], verify=True
            )
        except (jwt.DecodeError, jwt.ExpiredSignatureError) as e:
            return HttpResponse(
                json.dumps({"detail": "Invalid invite url", "error": str(e)})
            )
        with transaction.atomic():
            invitation_id= data.get('invitation_id', None)
            user_id= data.get('user_id', None)
            org_id= data.get('org_id', None)
            invite = OrganizationInvitation.objects.filter(id=invitation_id, invitee_id=user_id, organization_id=org_id).first()
            if not invite:
                return HttpResponse(
                    json.dumps({"detail": "Invalid invite url", "error": str(e)})
                )
                
            if OrganizationUser.objects.filter(user_id=user_id, organization_id=org_id).exists():
                return HttpResponse(
                    json.dumps({"detail": "User is already a member of the organization"}),
                    status=400
                )

            OrganizationUser.objects.create(
                user_id=user_id,
                organization_id=org_id,
            )

            invite.delete()
            return HttpResponse("Invitation successfully accepted", status=200)
        
