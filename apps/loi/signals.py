"""
Signal handlers for LOI auto-generation
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.offers.models import Offer
from .models import LOI


@receiver(post_save, sender=Offer)
def create_loi_on_offer_accept(sender, instance, **kwargs):
    """
    Auto-create LOI when offer is accepted.
    Business Rule: Offer accept → LOI auto-create
    """
    # Only create LOI if offer was just accepted and LOI doesn't exist
    if instance.status == 'accepted' and not hasattr(instance, 'loi'):
        try:
            loi = LOI.create_from_offer(instance)

            # Send email notification to both parties (NTF-004)
            from apps.notifications.emails import send_loi_created_notification
            try:
                send_loi_created_notification(loi)
            except Exception:
                pass  # Don't fail LOI creation if email fails

        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create LOI for offer {instance.id}: {str(e)}", exc_info=True)
