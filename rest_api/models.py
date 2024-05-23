from django.db import models
from core.models import NestedOrganization

class Post(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    email = models.EmailField(default="")
    organization = models.ForeignKey(NestedOrganization, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return self.title

