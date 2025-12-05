"""
Template-based views for offer management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from .models import Offer
from apps.contents.models import Content
from apps.core.constants import CONTENT_STATUS_PUBLIC, OFFER_STATUS_PENDING


@login_required
def offer_create_view(request, content_id):
    """
    오퍼 작성 화면 (/content/:contentId/offer)
    - OFR-001~006: 제안가, 메모, 유효기간, 콘텐츠 확인, 제출, 중복 방지
    - 권한: IsAuthenticated + IsBuyer
    """
    # Check if user is buyer
    if request.user.role != 'buyer':
        messages.error(request, 'Only buyers can submit offers.')
        return redirect('contents:detail', content_id=content_id)

    # Get content
    content = get_object_or_404(
        Content.objects.select_related('producer'),
        pk=content_id,
        status=CONTENT_STATUS_PUBLIC
    )

    # Check if content already has an accepted offer
    from apps.core.constants import OFFER_STATUS_ACCEPTED
    has_accepted_offer = Offer.objects.filter(
        content=content,
        status=OFFER_STATUS_ACCEPTED
    ).exists()

    if request.method == 'POST':
        if has_accepted_offer:
            messages.error(
                request,
                'This content already has an accepted offer and is no longer available.'
            )
            return redirect('contents:detail', content_id=content_id)

        # Get form data
        offered_price = request.POST.get('offered_price')
        message_text = request.POST.get('message', '').strip()
        validity_days = request.POST.get('validity_days', '7')

        # Validation
        errors = []

        try:
            offered_price = float(offered_price)
            if offered_price <= 0:
                errors.append('Offered price must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Please enter a valid price.')

        if message_text and len(message_text) > 500:
            errors.append('Message must be 500 characters or less.')

        try:
            validity_days = int(validity_days)
            if validity_days not in [7, 14, 30]:
                errors.append('Please select a valid validity period.')
        except (ValueError, TypeError):
            errors.append('Please select a valid validity period.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create offer
            try:
                offer = Offer.objects.create(
                    content=content,
                    buyer=request.user,
                    offered_price=offered_price,
                    currency=content.currency,  # Match content currency
                    message=message_text,
                    validity_days=validity_days
                )

                messages.success(
                    request,
                    f'Your offer of ${offered_price:.2f} has been submitted successfully! '
                    f'The producer will respond within {validity_days} days.'
                )
                return redirect('offers:buyer_detail', offer_id=offer.id)

            except IntegrityError:
                # This shouldn't happen, but handle gracefully
                messages.error(
                    request,
                    'An error occurred while creating your offer. Please try again.'
                )
                return redirect('contents:detail', content_id=content_id)

    context = {
        'content': content,
        'has_accepted_offer': has_accepted_offer,
        'validity_choices': [
            {'days': 7, 'label': '7 days'},
            {'days': 14, 'label': '14 days'},
            {'days': 30, 'label': '30 days'},
        ],
    }

    return render(request, 'offers/create.html', context)


@login_required
def buyer_offer_list_view(request):
    """
    [바이어] 내 오퍼 목록 (/my/offers)
    - OFR-010~011: 목록 표시, 상세 이동
    - 권한: IsAuthenticated + IsBuyer
    """
    # Check if user is buyer
    if request.user.role != 'buyer':
        messages.error(request, 'This page is only for buyers.')
        return redirect('home')

    # Get buyer's offers
    offers = Offer.objects.filter(buyer=request.user).select_related(
        'content', 'content__producer'
    ).order_by('-created_at')

    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        offers = offers.filter(status=status_filter)

    # Pagination
    paginator = Paginator(offers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'total_count': paginator.count,
    }

    return render(request, 'offers/buyer_list.html', context)


@login_required
def buyer_offer_detail_view(request, offer_id):
    """
    [바이어] 오퍼 상세 (/my/offers/:offerId)
    - OFR-020~021: 오퍼 정보 표시, LOI 링크
    - 권한: IsAuthenticated + IsBuyer + IsOwner
    """
    # Get offer (only buyer's own offers)
    offer = get_object_or_404(
        Offer.objects.select_related('content', 'content__producer'),
        pk=offer_id,
        buyer=request.user
    )

    # Check if LOI exists (for accepted offers)
    loi = None
    if offer.status == 'accepted':
        loi = getattr(offer, 'loi', None)

    context = {
        'offer': offer,
        'loi': loi,
    }

    return render(request, 'offers/buyer_detail.html', context)


# ========== Producer Offer Views ==========

@login_required
def producer_offer_list_view(request):
    """
    [제작사] 오퍼 관리 (/studio/offers)
    - OFR-030: 오퍼 목록, 필터, 요약
    - 권한: IsAuthenticated + IsProducer
    """
    # Check if user is producer
    if request.user.role != 'creator':
        messages.error(request, 'This page is only for producers.')
        return redirect('home')

    # Get offers for producer's contents
    from apps.contents.models import Content
    producer_contents = Content.objects.filter(producer=request.user)

    offers = Offer.objects.filter(
        content__in=producer_contents
    ).select_related('content', 'buyer').order_by('-created_at')

    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        offers = offers.filter(status=status_filter)

    # Pagination
    paginator = Paginator(offers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Summary stats
    from apps.core.constants import OFFER_STATUS_PENDING
    summary = {
        'total': Offer.objects.filter(content__in=producer_contents).count(),
        'pending': Offer.objects.filter(content__in=producer_contents, status=OFFER_STATUS_PENDING).count(),
    }

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'summary': summary,
        'total_count': paginator.count,
    }

    return render(request, 'offers/producer_list.html', context)


@login_required
def producer_offer_detail_view(request, offer_id):
    """
    [제작사] 오퍼 상세 및 응답 (/studio/offers/:offerId)
    - OFR-040~043: 오퍼 정보, 희망가 비교, 수락/거절
    - 권한: IsAuthenticated + IsProducer + IsOwner
    """
    # Get offer (only for producer's own contents)
    from apps.contents.models import Content
    producer_contents = Content.objects.filter(producer=request.user)

    offer = get_object_or_404(
        Offer.objects.select_related('content', 'buyer'),
        pk=offer_id,
        content__in=producer_contents
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        response_message = request.POST.get('response_message', '').strip()

        if action == 'accept':
            if offer.status != 'pending':
                messages.error(request, 'This offer has already been responded to.')
            elif offer.is_expired:
                messages.error(request, 'This offer has expired.')
            else:
                try:
                    offer.accept(producer_response=response_message)
                    messages.success(request, 'Offer accepted! An LOI has been created.')
                    return redirect('offers:producer_detail', offer_id=offer.id)
                except ValueError as e:
                    messages.error(request, str(e))

        elif action == 'reject':
            if offer.status != 'pending':
                messages.error(request, 'This offer has already been responded to.')
            else:
                try:
                    offer.reject(producer_response=response_message)
                    messages.success(request, 'Offer rejected.')
                    return redirect('offers:producer_detail', offer_id=offer.id)
                except ValueError as e:
                    messages.error(request, str(e))

    context = {
        'offer': offer,
    }

    return render(request, 'offers/producer_detail.html', context)
