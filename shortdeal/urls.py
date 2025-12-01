from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # API URLs (JWT-based)
    path('api/v1/auth/', include('apps.accounts.api_urls')),
    path('api/v1/contents/', include('apps.contents.api_urls')),
    path('api/v1/booths/', include('apps.booths.api_urls')),
    path('api/v1/studio/contents/', include('apps.contents.studio_urls')),

    # Template-based URLs (session-based, for testing)
    path('accounts/', include('apps.accounts.urls')),
]

# Debug toolbar (개발환경)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    
    # Media 파일 서빙
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
