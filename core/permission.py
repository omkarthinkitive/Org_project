from rest_framework.permissions import BasePermission
from organizations.models import OrganizationOwner, OrganizationUser


class IsOwnerOrAdminOfParentOrganization(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user = request.user
        parent_org_id = request.data.get('parent_organization')
        
        if not parent_org_id:
            return True 
        
        is_admin = OrganizationUser.objects.filter(
            user=user, organization_id=parent_org_id, is_admin=True
        ).exists()
        
        is_owner = OrganizationOwner.objects.filter(
            organization_user__user=user, organization_id=parent_org_id
        ).exists()
        
        return is_owner or is_admin
    
class IsOwnerToDeleteOrganization(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method == 'DELETE':        
            user = request.user
            org_id = view.kwargs.get('pk')
            
            if not org_id:
                return False
                
            is_owner = OrganizationOwner.objects.filter(
                organization_user__user=user, organization_id=org_id
            ).exists()
            
            return is_owner
        return True
