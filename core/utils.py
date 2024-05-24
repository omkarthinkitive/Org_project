from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import jwt
from urllib.parse import urljoin
from organizations.models import OrganizationOwner, OrganizationUser

def send_invitation_email(request, invitation):
    token = jwt.encode(
        {
            "invitation_id": invitation.pk,
            "user_id": invitation.invitee.pk,
            "org_id": invitation.organization.pk
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    origin = request.headers.get("Origin")
    accept_url = urljoin(origin, "organizations/accept_invite/") 
    subject = 'Invitation to join organization'
    message = render_to_string('email/invitation_email.html', {
        'invitation': invitation,
        'accept_url': accept_url,
        'token': token
    })
    plain_message = strip_tags(message)
    sender_email = invitation.invited_by.email
    recipient_email = invitation.invitee.email

    send_mail(subject, plain_message, sender_email, [recipient_email], html_message=message)


def update_organization_owner(org_instance, new_user_id):
    new_org_user = OrganizationUser.objects.create(
        user_id=new_user_id,
        organization_id=org_instance.id,
    )
    owner = OrganizationOwner.objects.filter(
        organization=org_instance
    ).first()
    owner.organization_user_id=new_org_user.id
    owner.save()
    child_orgs = org_instance.children.all()
    for child in child_orgs:
        update_organization_owner(child, new_user_id)