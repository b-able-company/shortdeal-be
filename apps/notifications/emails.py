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
    """
    print(f"[EMAIL] Starting to send password reset email to {user.email}")
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

    print(f"[EMAIL] Calling send_mail with:")
    print(f"  - From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"  - To: {user.email}")
    print(f"  - Subject: {subject}")
    print(f"[EMAIL] SMTP Settings:")
    print(f"  - HOST: {settings.EMAIL_HOST}")
    print(f"  - PORT: {settings.EMAIL_PORT}")
    print(f"  - USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"  - USER: {settings.EMAIL_HOST_USER}")

    try:
        # Add timeout to prevent infinite hang
        from django.core.mail import get_connection
        connection = get_connection(
            backend=settings.EMAIL_BACKEND,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            timeout=30,  # 30 second timeout
        )
        print(f"[EMAIL] Connection object created, attempting to open...")
        connection.open()
        print(f"[EMAIL] Connection opened successfully!")

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            connection=connection,
        )
        connection.close()
        print(f"[EMAIL] send_mail completed successfully")
    except Exception as e:
        print(f"[EMAIL] ✗✗✗ EXCEPTION in send_mail ✗✗✗")
        print(f"[EMAIL] Error type: {type(e).__name__}")
        print(f"[EMAIL] Error message: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise  # Re-raise to be caught by the view
