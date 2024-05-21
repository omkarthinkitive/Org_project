from rest_framework import serializers
from organizations.models import Organization, OrganizationInvitation

        
class OrganizationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Organization
        fields = '__all__'   
             
             

class OrganizationInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation
        fields = '__all__'

