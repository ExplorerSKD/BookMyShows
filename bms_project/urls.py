"""
URL configuration for bms_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core import views as core_views

urlpatterns = [
    # Custom analytics dashboard at /admin/dashboard/ (must be before admin.site.urls)
    path('admin/dashboard/', core_views.admin_dashboard, name='admin_dashboard'),

    # Default Django admin
    path('admin/', admin.site.urls),

    # Core application URLs
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
