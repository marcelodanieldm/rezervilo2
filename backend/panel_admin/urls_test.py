from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# Función básica para la home
def home_view(request):
    return HttpResponse("""
    <h1>🏆 Rezervilo - Sistema de Gestión</h1>
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h2>Acceso al Sistema</h2>
        <div style="border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px;">
            <h3>🔧 Panel de Administrador (Superusuario)</h3>
            <p><strong>URL:</strong> <a href="/admin/" target="_blank">http://localhost:8000/admin/</a></p>
            <p><strong>Usuario:</strong> admin</p>
            <p><strong>Contraseña:</strong> admin123</p>
        </div>
        
        <div style="border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px;">
            <h3>🏪 Dashboard Emprendimiento</h3>
            <p><strong>URL:</strong> <a href="/emprendimiento-dashboard/" target="_blank">http://localhost:8000/emprendimiento-dashboard/</a></p>
            <p><strong>Usuario:</strong> cafeteria_central</p>
            <p><strong>Contraseña:</strong> cafe123</p>
        </div>
        
        <div style="border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px;">
            <h3>👑 Dashboard Superusuario</h3>
            <p><strong>URL:</strong> <a href="/admin-dashboard/" target="_blank">http://localhost:8000/admin-dashboard/</a></p>
            <p><strong>Usuario:</strong> admin</p>
            <p><strong>Contraseña:</strong> admin123</p>
        </div>
        
        <h3>ℹ️ Información del Sistema</h3>
        <ul>
            <li>Base de datos: SQLite (poblada con datos de prueba)</li>
            <li>API REST: <a href="/api/" target="_blank">http://localhost:8000/api/</a></li>
            <li>Panel Django Admin: <a href="/admin/" target="_blank">http://localhost:8000/admin/</a></li>
        </ul>
    </div>
    """)

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
]