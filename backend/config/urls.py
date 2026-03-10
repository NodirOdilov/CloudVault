from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API routes
    path('api/auth/', include('apps.accounts.urls')),
    path('api/files/', include('apps.files.urls')),
    path('api/folders/', include('apps.folders.urls')),
    path('api/sharing/', include('apps.sharing.urls')),
    path('api/trash/', include('apps.trash.urls')),
    path('api/search/', include('apps.search.urls')),
    path('api/activity/', include('apps.activity.urls')),
    path('api/teams/', include('apps.teams.urls')),
    path('api/notifications/', include('apps.notifications.urls')),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
