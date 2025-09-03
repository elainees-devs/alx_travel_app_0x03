from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.shortcuts import redirect


schema_view = get_schema_view(
    openapi.Info(
        title="Travel App API",
        default_version='v1',
        description="API documentation for the travel app",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('', lambda request: redirect('schema-swagger-ui')),  # Redirect / to /swagger/

    path('admin/', admin.site.urls),
    path('api/', include('alx_travel_app.listings.urls')),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
