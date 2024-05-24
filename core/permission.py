
from rest_framework.permissions import BasePermission
from organizations.models import OrganizationUser, OrganizationOwner

class IsOrganizationUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        org_id = None
        if view.kwargs.get("pk"):
            org_id = view.kwargs.get("pk")
        elif view.kwargs.get("id"):
            org_id = view.kwargs.get("id")

        if not org_id:
            return False
        
        if not OrganizationUser.objects.filter(user_id=request.user.id, organization_id=org_id).exists():
            return False

        return True
    
class IsOrganizationCreateAllowed(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        parent_id = request.data.get('parent')
        if parent_id:
            org_user = OrganizationUser.objects.filter(
                user_id=request.user.id, 
                organization_id=parent_id,
            ).first()
            
            org_owner = OrganizationOwner.objects.filter(
                organization_user=org_user, organization_id=parent_id
            )
            if not (org_user and org_user.is_admin) and not org_owner:
                return False
            
        return True

class IsOrganizationOwner(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = None
        if view.kwargs.get("pk"):
            org_id = view.kwargs.get("pk")
        elif view.kwargs.get("id"):
            org_id = view.kwargs.get("id")

        if not org_id:
            return False
        
        org_user = OrganizationUser.objects.filter(
            user_id=request.user.id, 
            organization_id=org_id,
        ).first()
            
        if not ( org_user and OrganizationOwner.objects.filter(
                organization_user=org_user, organization_id=org_id
            ).exists()
        ):
          return False  
        return True

class IsOrganizationOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        org_id = None
        if view.kwargs.get("pk"):
            org_id = view.kwargs.get("pk")
        elif view.kwargs.get("id"):
            org_id = view.kwargs.get("id")

        if not org_id:
            return False
        
        org_user = OrganizationUser.objects.filter(
            user_id=request.user.id, 
            organization_id=org_id,
        ).first()
        
        org_owner = OrganizationOwner.objects.filter(
            organization_user=org_user, organization_id=org_id
        )
        if not (org_user and org_user.is_admin) and not org_owner:
            return False
        
        return True
