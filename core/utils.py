from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import jwt
from urllib.parse import urlencode, urljoin
    
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
    query = urlencode({"token": token})
    accept_url = urljoin(origin, f"accept_invite?{query}")
    subject = 'Invitation to join organization'
    message = render_to_string('email/invitation_email.html', {'invitation': invitation, 'accept_url':accept_url})
    plain_message = strip_tags(message)
    sender_email = invitation.invited_by.email
    recipient_email = invitation.invitee.email

    send_mail(subject, plain_message, sender_email, [recipient_email], html_message=message)

