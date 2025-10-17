# core/frontend_views.py
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os

def serve_login_page(request):
    """Servir la página de login"""
    try:
        # Construir la ruta al archivo frontend
        frontend_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'frontend', 'login.html')
        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        raise Http404("Página de login no encontrada")

def serve_admin_dashboard(request):
    """Servir el dashboard de administrador"""
    try:
        # Construir la ruta al archivo frontend
        frontend_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'frontend', 'admin-dashboard.html')
        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        raise Http404("Dashboard de admin no encontrado")

def serve_emprendimiento_dashboard(request):
    """Servir el dashboard de emprendimiento"""
    try:
        # Construir la ruta al archivo frontend
        frontend_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'frontend', 'emprendimiento-dashboard.html')
        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        raise Http404("Dashboard de emprendimiento no encontrado")

def serve_index_page(request):
    """Servir la página index"""
    try:
        # Construir la ruta al archivo frontend
        frontend_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'frontend', 'index.html')
        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        raise Http404("Página index no encontrada")