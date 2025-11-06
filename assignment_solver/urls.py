from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Djoser authentication endpoints
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    
    # Custom endpoints
    path('api/profile/', include('accounts.urls')),
    path('api/submissions/', include('submissions.urls')),
    path('api/assignments/', include('assignments.urls')), 
    path('api/accounts/', include('accounts.urls')),
    path('accounts/', include('accounts.urls')),
]

# Media files (for development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
