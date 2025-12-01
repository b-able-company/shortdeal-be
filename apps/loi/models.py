"""
LOI (Letter of Intent) model for accepted offers
"""
from django.db import models
from django.conf import settings


class LOI(models.Model):
    """Letter of Intent - generated when offer is accepted"""

    offer = models.OneToOneField(
        'offers.Offer',
        on_delete=models.CASCADE,
        related_name='loi',
        verbose_name='Offer'
    )

    # LOI document number (LOI-YYYY-NNNN)
    document_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name='Document number'
    )

    # Snapshot fields (captured at LOI creation)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buyer_lois',
        verbose_name='Buyer'
    )
    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='producer_lois',
        verbose_name='Producer'
    )

    # Content snapshot
    content_title = models.CharField(max_length=200, verbose_name='Content title')
    content_description = models.TextField(verbose_name='Content description')

    # Deal details snapshot
    agreed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Agreed price'
    )
    currency = models.CharField(max_length=3, verbose_name='Currency')

    # Company details snapshot
    buyer_company = models.CharField(max_length=200, verbose_name='Buyer company')
    buyer_country = models.CharField(max_length=100, verbose_name='Buyer country')
    producer_company = models.CharField(max_length=200, verbose_name='Producer company')
    producer_country = models.CharField(max_length=100, verbose_name='Producer country')

    # PDF generation
    pdf_file = models.FileField(
        upload_to='loi_pdfs/',
        blank=True,
        null=True,
        verbose_name='PDF file'
    )
    pdf_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='PDF generated at'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated at')

    class Meta:
        verbose_name = 'LOI'
        verbose_name_plural = 'LOIs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', '-created_at']),
            models.Index(fields=['producer', '-created_at']),
        ]

    def __str__(self):
        return f"{self.document_number} - {self.content_title}"

    @property
    def is_pdf_ready(self):
        """Check if PDF has been generated"""
        return bool(self.pdf_file)

    @classmethod
    def generate_document_number(cls):
        """Generate unique LOI document number (LOI-YYYY-NNNN)"""
        from django.utils import timezone
        year = timezone.now().year

        # Get last LOI number for this year
        last_loi = cls.objects.filter(
            document_number__startswith=f'LOI-{year}-'
        ).order_by('-document_number').first()

        if last_loi:
            last_num = int(last_loi.document_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f'LOI-{year}-{next_num:04d}'

    def generate_pdf(self):
        """Generate PDF file for this LOI"""
        from django.core.files.base import ContentFile
        from django.utils import timezone
        from .pdf_generator import generate_loi_pdf

        # Generate PDF content
        pdf_data = generate_loi_pdf(self)

        # Save PDF file
        filename = f"{self.document_number}.pdf"
        self.pdf_file.save(filename, ContentFile(pdf_data), save=False)
        self.pdf_generated_at = timezone.now()
        self.save(update_fields=['pdf_file', 'pdf_generated_at'])

    @classmethod
    def create_from_offer(cls, offer):
        """Create LOI from accepted offer"""
        # Generate document number
        doc_number = cls.generate_document_number()

        # Create LOI with snapshot data
        loi = cls.objects.create(
            offer=offer,
            document_number=doc_number,
            buyer=offer.buyer,
            producer=offer.content.producer,
            content_title=offer.content.title,
            content_description=offer.content.description,
            agreed_price=offer.offered_price,
            currency=offer.currency,
            buyer_company=offer.buyer.company_name or offer.buyer.username,
            buyer_country=offer.buyer.country or 'Unknown',
            producer_company=offer.content.producer.company_name or offer.content.producer.username,
            producer_country=offer.content.producer.country or 'Unknown'
        )

        # Generate PDF immediately (for now; can be async later)
        loi.generate_pdf()

        return loi
