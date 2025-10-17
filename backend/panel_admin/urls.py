"""
URL configuration for panel_admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# panel_admin/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'clientes', views.ClienteViewSet)
router.register(r'bots', views.BotViewSet, basename='bot')
router.register(r'servicios', views.ServicioViewSet, basename='servicio')
router.register(r'reservas', views.ReservaViewSet, basename='reserva')

urlpatterns = [
    # Panel de Superadmin
    path('admin/', admin.site.urls),

    # API Endpoints
    path('api/', include(router.urls)),
    path('api/me/', views.get_me, name='get_me'), # Endpoint 'get_me'

    # API Auth Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
