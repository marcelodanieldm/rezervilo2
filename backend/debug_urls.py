#!/usr/bin/env python
"""
Debug script para identificar problemas con las URLs
"""
import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path de Python
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel_admin.settings')

try:
    # Intentar configurar Django
    django.setup()
    print("✓ Django setup exitoso")
    
    # Intentar importar las URLs
    from panel_admin import urls
    print("✓ Import de URLs exitoso")
    
    # Verificar que urlpatterns es una lista
    print(f"✓ urlpatterns type: {type(urls.urlpatterns)}")
    print(f"✓ urlpatterns length: {len(urls.urlpatterns)}")
    
    # Mostrar cada patrón URL
    for i, pattern in enumerate(urls.urlpatterns):
        print(f"✓ Pattern {i}: {pattern}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()