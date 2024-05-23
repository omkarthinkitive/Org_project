from organizations.models import Organization
from django.db import models

class NestedOrganization(Organization):
    parent_organization = models.ForeignKey('self', related_name='child_organizations', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name
    
