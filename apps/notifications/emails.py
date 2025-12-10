"""
Email notification utilities
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_new_offer_notification(offer):
    """
    NTF-001: Send email to producer when new offer is received
    """
    producer = offer.content.producer
    subject = f"New Offer Received for '{offer.content.title}'"

    context = {
        'producer_name': producer.company_name or producer.username,
        'content_title': offer.content.title,
        'buyer_name': offer.buyer.company_name or offer.buyer.username,
        'offered_price': f"{offer.currency} {offer.offered_price:,.2f}",
        'buyer_message': offer.buyer_message,
        'expires_at': offer.expires_at.strftime('%B %d, %Y'),
    }

    message = f"""
Hello {context['producer_name']},

You have received a new offer for your content '{context['content_title']}'.

Buyer: {context['buyer_name']}
Offered Price: {context['offered_price']}
Expires: {context['expires_at']}

Message from buyer:
{context['buyer_message']}

Please log in to review and respond to this offer.

Best regards,
ShortDeal Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[producer.email],
        fail_silently=False,
    )


def send_offer_accepted_notification(offer):
    """
    NTF-002: Send email to buyer when offer is accepted
    """
    buyer = offer.buyer
    subject = f"Your Offer for '{offer.content.title}' Has Been Accepted"

    context = {
        'buyer_name': buyer.company_name or buyer.username,
        'content_title': offer.content.title,
        'producer_name': offer.content.producer.company_name or offer.content.producer.username,
        'offered_price': f"{offer.currency} {offer.offered_price:,.2f}",
        'producer_response': offer.producer_response,
    }

    message = f"""
Hello {context['buyer_name']},

Great news! Your offer for '{context['content_title']}' has been accepted by {context['producer_name']}.

Offered Price: {context['offered_price']}

Producer's response:
{context['producer_response']}

A Letter of Intent (LOI) has been generated for this deal. Please log in to view and download it.

Best regards,
ShortDeal Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[buyer.email],
        fail_silently=False,
    )


def send_offer_rejected_notification(offer):
    """
    NTF-003: Send email to buyer when offer is rejected
    """
    buyer = offer.buyer
    subject = f"Your Offer for '{offer.content.title}' Has Been Rejected"

    context = {
        'buyer_name': buyer.company_name or buyer.username,
        'content_title': offer.content.title,
        'producer_name': offer.content.producer.company_name or offer.content.producer.username,
        'producer_response': offer.producer_response,
    }

    message = f"""
Hello {context['buyer_name']},

Unfortunately, your offer for '{context['content_title']}' has been rejected by {context['producer_name']}.

Producer's response:
{context['producer_response']}

You may submit a new offer with revised terms if you wish to continue negotiations.

Best regards,
ShortDeal Team
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[buyer.email],
        fail_silently=False,
    )


def send_loi_created_notification(loi):
    """
    NTF-004: Send email to both buyer and producer when LOI is created
    """
    buyer = loi.buyer
    producer = loi.producer

    subject = f"LOI Generated for '{loi.content_title}'"

    # Email to buyer
    buyer_message = f"""
Hello {loi.buyer_company},

A Letter of Intent (LOI) has been generated for your accepted offer.

Document Number: {loi.document_number}
Content: {loi.content_title}
Agreed Price: {loi.currency} {loi.agreed_price:,.2f}

Please log in to view and download the LOI document.

Best regards,
ShortDeal Team
"""

    send_mail(
        subject=subject,
        message=buyer_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[buyer.email],
        fail_silently=False,
    )

    # Email to producer
    producer_message = f"""
Hello {loi.producer_company},

A Letter of Intent (LOI) has been generated for your accepted offer.

Document Number: {loi.document_number}
Content: {loi.content_title}
Agreed Price: {loi.currency} {loi.agreed_price:,.2f}

Please log in to view and download the LOI document.

Best regards,
ShortDeal Team
"""

    send_mail(
        subject=subject,
        message=producer_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[producer.email],
        fail_silently=False,
    )


def send_password_reset_email(user, reset_url):
    """
    Send password reset email with token link
    Uses SendGrid HTTP API if available, otherwise falls back to SMTP
    """
    subject = "Reset Your Password - ShortDeal"
    username = user.company_name or user.username

    message = f"""
Hello {username},

You have requested to reset your password for your ShortDeal account.

Please click the link below to reset your password:
{reset_url}

This link will expire in 24 hours for security reasons.

If you did not request a password reset, please ignore this email and your password will remain unchanged.

Need help? Contact our support team.

Best regards,
ShortDeal Team
"""

    # Try SendGrid HTTP API first (bypasses Railway SMTP port blocking)
    sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', None) or settings.EMAIL_HOST_PASSWORD

    if sendgrid_api_key and sendgrid_api_key.startswith('SG.'):
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content

            sg_mail = Mail(
                from_email=Email(settings.DEFAULT_FROM_EMAIL),
                to_emails=To(user.email),
                subject=subject,
                plain_text_content=Content("text/plain", message)
            )

            sg = SendGridAPIClient(sendgrid_api_key)
            response = sg.send(sg_mail)

            if response.status_code >= 200 and response.status_code < 300:
                return
            else:
                raise Exception(f"SendGrid API error: {response.status_code}")

        except ImportError:
            pass  # Fall back to SMTP
        except Exception:
            # Fall back to SMTP if SendGrid fails
            pass

    # Fallback to SMTP
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
