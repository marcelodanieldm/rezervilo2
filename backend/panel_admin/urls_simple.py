# panel_admin/urls.py - VERSION SIMPLIFICADA PARA DEPURAR
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def test_view(request):
    return HttpResponse("¡Django está funcionando!")

urlpatterns = [
    path('', test_view, name='test'),
    path('admin/', admin.site.urls),
]