"""
Core template views (non-API)
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.contents.models import Content
from apps.offers.models import Offer
from apps.loi.models import LOI


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.role == 'admin'


@login_required
@user_passes_test(is_admin, login_url='/')
def admin_dashboard_view(request):
    """
    Admin dashboard template view
    Screen 19: /admin
    ADM-001~005
    """
    # Get period from query params (default 7d)
    period = request.GET.get('period', '7d')
    if period not in ['7d', '30d']:
        period = '7d'

    # Calculate period start date
    days = 7 if period == '7d' else 30
    period_start = timezone.now() - timedelta(days=days)

    # Summary statistics (all time)
    summary = {
        'total_users': User.objects.count(),
        'total_producers': User.objects.filter(role=User.Role.CREATOR).count(),
        'total_buyers': User.objects.filter(role=User.Role.BUYER).count(),
        'total_contents': Content.objects.exclude(status='deleted').count(),
        'total_offers': Offer.objects.count(),
        'pending_offers': Offer.objects.filter(status='pending').count(),
        'total_lois': LOI.objects.count(),
    }

    # Period statistics
    period_stats = {
        'new_users': User.objects.filter(date_joined__gte=period_start).count(),
        'new_contents': Content.objects.filter(created_at__gte=period_start).count(),
        'new_offers': Offer.objects.filter(created_at__gte=period_start).count(),
        'new_lois': LOI.objects.filter(created_at__gte=period_start).count(),
    }

    # Recent users (last 10)
    recent_users = User.objects.order_by('-date_joined')[:10]

    # Recent contents (last 10)
    recent_contents = Content.objects.select_related('producer').order_by('-created_at')[:10]

    # Recent offers (last 10)
    recent_offers = Offer.objects.select_related(
        'buyer', 'content__producer'
    ).order_by('-created_at')[:10]

    return render(request, 'core/admin_dashboard.html', {
        'summary': summary,
        'period_stats': period_stats,
        'period': period,
        'recent_users': recent_users,
        'recent_contents': recent_contents,
        'recent_offers': recent_offers,
    })


def tutorial_view(request):
    """
    Tutorial page view
    Shows how to use the ShortDeal platform
    """
    return render(request, 'tutorial.html')


def company_intro_view(request):
    """
    Company introduction page view
    Shows information about B.able Company
    """
    return render(request, 'company_intro.html')
