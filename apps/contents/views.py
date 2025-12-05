"""
Template-based views for content browsing and management
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Content
from apps.booths.models import Booth
from apps.core.constants import CONTENT_STATUS_PUBLIC, CONTENT_STATUS_DELETED


def browse_view(request):
    """
    콘텐츠 브라우징 화면 (/browse)
    - BRW-001~006: 카드 리스트, 검색, 필터, 페이지네이션
    - 권한: AllowAny (전체 공개)
    """
    # Get all public contents
    contents = Content.objects.filter(status=CONTENT_STATUS_PUBLIC).select_related('producer')

    # Search (BRW-002)
    search_query = request.GET.get('q', '').strip()
    if search_query:
        contents = contents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(producer__company_name__icontains=search_query)
        )

    # Genre filter (BRW-003)
    genre_filter = request.GET.getlist('genre')
    if genre_filter:
        for genre in genre_filter:
            contents = contents.filter(genre_tags__contains=[genre])

    # Price range filter (BRW-004)
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if price_min:
        try:
            contents = contents.filter(price__gte=float(price_min))
        except ValueError:
            pass

    if price_max:
        try:
            contents = contents.filter(price__lte=float(price_max))
        except ValueError:
            pass

    # Sorting
    ordering = request.GET.get('ordering', '-created_at')
    if ordering in ['-created_at', 'created_at', 'price', '-price']:
        contents = contents.order_by(ordering)

    # Pagination (BRW-005: 20개 단위)
    paginator = Paginator(contents, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Genre choices for filter
    genre_choices = [
        'drama', 'comedy', 'romance', 'action', 'thriller',
        'horror', 'documentary', 'education', 'business',
        'lifestyle', 'food', 'travel', 'music', 'sports', 'gaming'
    ]

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'genre_filter': genre_filter,
        'price_min': price_min,
        'price_max': price_max,
        'ordering': ordering,
        'genre_choices': genre_choices,
        'total_count': paginator.count,
    }

    return render(request, 'contents/browse.html', context)


def content_detail_view(request, content_id):
    """
    콘텐츠 상세 화면 (/content/:contentId)
    - CNT-001~004: 기본 정보, 제작사 정보, 링크, 오퍼 버튼
    - 권한: AllowAny (전체 공개)
    """
    content = get_object_or_404(
        Content.objects.select_related('producer'),
        pk=content_id,
        status=CONTENT_STATUS_PUBLIC
    )

    # Increment view count (CNT-001)
    content.increment_view_count()

    # Check if user can submit offer (CNT-004)
    can_submit_offer = False
    if request.user.is_authenticated and request.user.role == 'buyer':
        # Check if there's already an accepted offer for this content
        from apps.offers.models import Offer
        from apps.core.constants import OFFER_STATUS_ACCEPTED

        has_accepted_offer = Offer.objects.filter(
            content=content,
            status=OFFER_STATUS_ACCEPTED
        ).exists()

        # Can submit offer only if no accepted offer exists
        can_submit_offer = not has_accepted_offer

    context = {
        'content': content,
        'can_submit_offer': can_submit_offer,
    }

    return render(request, 'contents/detail.html', context)


def booth_view(request, slug):
    """
    제작사 부스 화면 (/booth/:slug)
    - BTH-001~002: 제작사 정보, 콘텐츠 리스트
    - 권한: AllowAny (전체 공개)
    """
    booth = get_object_or_404(Booth.objects.select_related('producer'), slug=slug)

    # Increment booth view count
    booth.increment_view_count()

    # Get producer's public contents (BTH-002)
    contents = Content.objects.filter(
        producer=booth.producer,
        status=CONTENT_STATUS_PUBLIC
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(contents, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'booth': booth,
        'producer': booth.producer,
        'page_obj': page_obj,
        'total_count': paginator.count,
    }

    return render(request, 'booths/detail.html', context)


# ========== Studio Views (Producer Content Management) ==========

@login_required
def studio_content_list_view(request):
    """
    [제작사] 콘텐츠 관리 (/studio/contents)
    - STD-001~004: 목록, 추가, 수정, 삭제
    - 권한: IsAuthenticated + IsProducer + IsOnboarded
    """
    # Check if user is producer
    if request.user.role != 'creator':
        messages.error(request, 'This page is only for producers.')
        return redirect('home')

    # Check onboarding
    if not request.user.is_onboarded:
        messages.warning(request, 'Please complete onboarding first.')
        return redirect('accounts:onboarding_producer')

    # Get producer's contents (exclude deleted)
    contents = Content.objects.filter(
        producer=request.user
    ).exclude(
        status=CONTENT_STATUS_DELETED
    ).annotate(
        offer_count=Count('offer_set')
    ).order_by('-created_at')

    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        contents = contents.filter(status=status_filter)

    # Pagination
    paginator = Paginator(contents, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'total_count': paginator.count,
    }

    return render(request, 'contents/studio_list.html', context)


@login_required
def studio_content_create_view(request):
    """
    [제작사] 콘텐츠 업로드 (/studio/contents/new)
    - UPL-001~007: 제목, 썸네일, 시놉시스, 희망가, 링크, 장르, 공개
    - 권한: IsAuthenticated + IsProducer + IsOnboarded
    """
    # Check if user is producer
    if request.user.role != 'creator':
        messages.error(request, 'This page is only for producers.')
        return redirect('home')

    # Check onboarding
    if not request.user.is_onboarded:
        messages.warning(request, 'Please complete onboarding first.')
        return redirect('accounts:onboarding_producer')

    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        poster = request.FILES.get('poster')
        teaser_video = request.FILES.get('teaser_video')
        rating = request.POST.get('rating', 'all')
        price = request.POST.get('price')
        currency = request.POST.get('currency', 'USD')
        video_url = request.POST.get('video_url', '').strip()
        screener_url = request.POST.get('screener_url', '').strip()
        release_target = request.POST.get('release_target', '').strip()
        duration_seconds = request.POST.get('duration_seconds', '0')
        genre_tags = request.POST.getlist('genre_tags')

        # Validation
        errors = []

        if not title or len(title) < 2 or len(title) > 200:
            errors.append('Title must be between 2 and 200 characters.')

        if not description or len(description) > 2000:
            errors.append('Description is required and must be 2000 characters or less.')

        if poster and poster.size > 5 * 1024 * 1024:  # 5MB
            errors.append('Poster must be 5MB or less.')

        if teaser_video and teaser_video.size > 200 * 1024 * 1024:  # 200MB
            errors.append('Teaser video must be 200MB or less.')

        if rating not in ['all', '12', '15', '19']:
            errors.append('Invalid rating selected.')

        try:
            price = float(price)
            if price <= 0:
                errors.append('Price must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Please enter a valid price.')

        if not video_url:
            errors.append('Content link is required.')

        try:
            duration_seconds = int(duration_seconds)
            if duration_seconds <= 0:
                errors.append('Duration must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Please enter a valid duration.')

        if not genre_tags or len(genre_tags) < 1 or len(genre_tags) > 3:
            errors.append('Please select 1-3 genres.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create content
            content = Content.objects.create(
                producer=request.user,
                title=title,
                description=description,
                poster=poster,
                teaser_video=teaser_video,
                rating=rating,
                price=price,
                currency=currency,
                video_url=video_url,
                screener_url=screener_url,
                release_target=release_target if release_target else None,
                duration_seconds=duration_seconds,
                genre_tags=genre_tags,
                status=CONTENT_STATUS_PUBLIC  # UPL-007: public
            )

            messages.success(request, f'Content "{content.title}" has been created successfully!')
            return redirect('contents:studio_list')

    # Genre choices
    genre_choices = [
        'drama', 'comedy', 'romance', 'action', 'thriller',
        'horror', 'documentary', 'education', 'business',
        'lifestyle', 'food', 'travel', 'music', 'sports', 'gaming'
    ]

    context = {
        'genre_choices': genre_choices,
    }

    return render(request, 'contents/studio_create.html', context)


@login_required
def studio_content_edit_view(request, content_id):
    """
    [제작사] 콘텐츠 수정 (/studio/contents/:contentId/edit)
    - UPL-001~007: 수정 및 삭제
    - 권한: IsAuthenticated + IsProducer + IsOwner
    """
    # Get content (only producer's own)
    content = get_object_or_404(
        Content.objects.exclude(status=CONTENT_STATUS_DELETED),
        pk=content_id,
        producer=request.user
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete':
            # Check if content has offers (STD-004)
            offer_count = content.offer_set.count()
            if offer_count > 0:
                messages.error(
                    request,
                    f'Cannot delete content with {offer_count} existing offer(s). '
                    'Please wait until all offers are resolved.'
                )
            else:
                # Soft delete
                content_title = content.title
                content.soft_delete()
                messages.success(request, f'Content "{content_title}" has been deleted.')
                return redirect('contents:studio_list')

        elif action == 'update':
            # Get form data
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            poster = request.FILES.get('poster')
            teaser_video = request.FILES.get('teaser_video')
            rating = request.POST.get('rating', 'all')
            price = request.POST.get('price')
            currency = request.POST.get('currency', 'USD')
            video_url = request.POST.get('video_url', '').strip()
            screener_url = request.POST.get('screener_url', '').strip()
            release_target = request.POST.get('release_target', '').strip()
            duration_seconds = request.POST.get('duration_seconds')
            genre_tags = request.POST.getlist('genre_tags')

            # Validation
            errors = []

            if not title or len(title) < 2 or len(title) > 200:
                errors.append('Title must be between 2 and 200 characters.')

            if not description or len(description) > 2000:
                errors.append('Description is required and must be 2000 characters or less.')

            if poster and poster.size > 5 * 1024 * 1024:  # 5MB
                errors.append('Poster must be 5MB or less.')

            if teaser_video and teaser_video.size > 200 * 1024 * 1024:  # 200MB
                errors.append('Teaser video must be 200MB or less.')

            if rating not in ['all', '12', '15', '19']:
                errors.append('Invalid rating selected.')

            try:
                price = float(price)
                if price <= 0:
                    errors.append('Price must be greater than 0.')
            except (ValueError, TypeError):
                errors.append('Please enter a valid price.')

            if not video_url:
                errors.append('Content link is required.')

            try:
                duration_seconds = int(duration_seconds)
                if duration_seconds <= 0:
                    errors.append('Duration must be greater than 0.')
            except (ValueError, TypeError):
                errors.append('Please enter a valid duration.')

            if not genre_tags or len(genre_tags) < 1 or len(genre_tags) > 3:
                errors.append('Please select 1-3 genres.')

            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                # Update content
                content.title = title
                content.description = description
                if poster:
                    content.poster = poster
                if teaser_video:
                    content.teaser_video = teaser_video
                content.rating = rating
                content.price = price
                content.currency = currency
                content.video_url = video_url
                content.screener_url = screener_url
                content.release_target = release_target if release_target else None
                content.duration_seconds = duration_seconds
                content.genre_tags = genre_tags
                content.save()

                messages.success(request, f'Content "{content.title}" has been updated successfully!')
                return redirect('contents:studio_list')

    # Genre choices
    genre_choices = [
        'drama', 'comedy', 'romance', 'action', 'thriller',
        'horror', 'documentary', 'education', 'business',
        'lifestyle', 'food', 'travel', 'music', 'sports', 'gaming'
    ]

    context = {
        'content': content,
        'genre_choices': genre_choices,
    }

    return render(request, 'contents/studio_edit.html', context)
