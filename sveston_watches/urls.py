from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Secret prefix loaded from settings (default: 'sv-cd6n-lugl')
urlpatterns = [
    path('', include('store.urls')),
    path('account/', include('accounts.urls')),
    path('portal/admin/', include('admin_panel.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
