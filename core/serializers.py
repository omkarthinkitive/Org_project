from rest_framework import serializers
from organizations.models import  OrganizationInvitation, OrganizationUser, OrganizationOwner
from .models import NestedOrganization
        
class OrganizationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = NestedOrganization
        fields = '__all__'   
                      
class OrganizationInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation
        fields = '__all__'
        
class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
    
class NestedOrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = NestedOrganization
        exclude =('created', 'modified', 'slug')  
    
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['sub_organizations'] = [
            self.to_representation(child)
            for child in instance.child_organizations.all()
        ]
        return rep
    
class OrganizationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = '__all__'
        
        
class OrganizationOwnerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = OrganizationOwner
        fields = '__all__'


