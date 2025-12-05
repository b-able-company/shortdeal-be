from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # API URLs (JWT-based)
    path('api/v1/auth/', include('apps.accounts.api_urls')),
    path('api/v1/contents/', include('apps.contents.api_urls')),
    path('api/v1/booths/', include('apps.booths.api_urls')),
    path('api/v1/studio/contents/', include('apps.contents.studio_urls')),
    path('api/v1/offers/', include('apps.offers.api_urls')),
    path('api/v1/loi/', include('apps.loi.api_urls')),
    path('api/v1/settings/', include('apps.accounts.settings_urls')),
    path('api/v1/admin/', include('apps.core.admin_urls')),

    # Template-based URLs (session-based, for testing)
    path('accounts/', include('apps.accounts.urls')),
    path('', include('apps.contents.urls')),
    path('booth/', include('apps.booths.urls')),
    path('offers/', include('apps.offers.urls')),
    path('loi/', include('apps.loi.urls')),
    path('', include('apps.core.urls')),
]

# Debug toolbar (개발환경)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Media 파일 서빙 (개발 및 프로덕션)
if settings.DEBUG:
    # 개발환경: static() 헬퍼 사용
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # 프로덕션: 명시적 URL 패턴으로 서빙
    # Railway Volume을 사용하면 재배포 시에도 파일 유지
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
