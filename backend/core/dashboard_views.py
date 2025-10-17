# core/dashboard_views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Cliente, Bot, Reserva
import json


def get_dashboard_type(user):
    """
    Determina el tipo de dashboard según el tipo de usuario
    """
    if user.is_superuser or user.is_staff:
        return 'admin_dashboard'
    elif hasattr(user, 'cliente'):
        return 'emprendimiento_dashboard'
    else:
        return 'limited_dashboard'


@api_view(['POST'])
@permission_classes([])  # Sin permisos requeridos para login
def dashboard_login(request):
    """
    Vista de login que redirige según el tipo de usuario
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username y password son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        if user.is_active:
            # Determinar tipo de dashboard
            dashboard_type = get_dashboard_type(user)
            
            # Generar tokens JWT
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'dashboard_type': dashboard_type,
                'user_info': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'has_cliente_profile': hasattr(user, 'cliente')
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Cuenta desactivada'
            }, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({
            'error': 'Credenciales inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_config(request):
    """
    Retorna la configuración del dashboard según el tipo de usuario
    """
    user = request.user
    dashboard_type = get_dashboard_type(user)
    
    config = {
        'dashboard_type': dashboard_type,
        'user_info': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
    }
    
    if dashboard_type == 'admin_dashboard':
        # Configuración para superusuario
        from django.contrib.auth.models import User
        config.update({
            'features': [
                'user_management',
                'cliente_management', 
                'global_bot_management',
                'global_reservations',
                'system_stats',
                'admin_tools'
            ],
            'stats': {
                'total_users': User.objects.count(),
                'total_clientes': Cliente.objects.count(),
                'total_bots': Bot.objects.count(),
                'total_reservations': Reserva.objects.count()
            },
            'navigation': [
                {'name': 'Dashboard', 'icon': 'fas fa-tachometer-alt', 'section': 'dashboard'},
                {'name': 'Usuarios', 'icon': 'fas fa-users', 'section': 'users'},
                {'name': 'Clientes', 'icon': 'fas fa-building', 'section': 'clientes'},
                {'name': 'Bots Globales', 'icon': 'fas fa-robot', 'section': 'bots'},
                {'name': 'Reservas Globales', 'icon': 'fas fa-calendar', 'section': 'reservations'},
                {'name': 'Estadísticas', 'icon': 'fas fa-chart-bar', 'section': 'stats'},
                {'name': 'Configuración', 'icon': 'fas fa-cog', 'section': 'settings'}
            ]
        })
    
    elif dashboard_type == 'emprendimiento_dashboard':
        # Configuración para usuario emprendimiento
        cliente = user.cliente
        user_bots = Bot.objects.filter(cliente=cliente)
        user_reservations = Reserva.objects.filter(bot__cliente=cliente)
        
        config.update({
            'cliente_info': {
                'id': cliente.id,
                'nombre_emprendimiento': cliente.nombre_emprendimiento,
                'telefono': cliente.telefono
            },
            'features': [
                'bot_management',
                'reservations_management',
                'services_management',
                'calendar',
                'client_stats'
            ],
            'stats': {
                'total_bots': user_bots.count(),
                'active_bots': user_bots.filter(activo=True).count(),
                'total_reservations': user_reservations.count(),
                'pending_reservations': user_reservations.filter(estado='Pendiente').count()
            },
            'navigation': [
                {'name': 'Dashboard', 'icon': 'fas fa-tachometer-alt', 'section': 'dashboard'},
                {'name': 'Mis Bots', 'icon': 'fas fa-robot', 'section': 'bots'},
                {'name': 'Calendario', 'icon': 'fas fa-calendar-alt', 'section': 'calendar'},
                {'name': 'Reservas', 'icon': 'fas fa-clipboard-list', 'section': 'reservations'},
                {'name': 'Servicios', 'icon': 'fas fa-concierge-bell', 'section': 'services'},
                {'name': 'Mi Perfil', 'icon': 'fas fa-user-circle', 'section': 'profile'}
            ]
        })
    
    else:
        # Configuración para usuario limitado
        config.update({
            'features': ['limited_access'],
            'stats': {},
            'navigation': [
                {'name': 'Información', 'icon': 'fas fa-info-circle', 'section': 'info'},
                {'name': 'Contacto', 'icon': 'fas fa-envelope', 'section': 'contact'}
            ],
            'message': 'Tu cuenta tiene acceso limitado. Contacta al administrador para más información.'
        })
    
    return Response(config, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dashboard_logout(request):
    """
    Vista de logout que invalida la sesión
    """
    try:
        # En una implementación completa, aquí se invalidaría el refresh token
        # Por ahora retornamos éxito
        return Response({
            'message': 'Logout exitoso',
            'redirect_to': '/login'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Error durante el logout'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard_stats(request):
    """
    Estadísticas específicas para el dashboard de administrador
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({
            'error': 'Acceso denegado'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from django.contrib.auth.models import User
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    # Estadísticas generales
    stats = {
        'users': {
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count(),
            'staff': User.objects.filter(is_staff=True).count()
        },
        'clientes': {
            'total': Cliente.objects.count(),
            'with_bots': Cliente.objects.annotate(
                bot_count=Count('bots')
            ).filter(bot_count__gt=0).count()
        },
        'bots': {
            'total': Bot.objects.count(),
            'active': Bot.objects.filter(activo=True).count(),
            'inactive': Bot.objects.filter(activo=False).count()
        },
        'reservations': {
            'total': Reserva.objects.count(),
            'confirmed': Reserva.objects.filter(estado='Confirmada').count(),
            'pending': Reserva.objects.filter(estado='Pendiente').count(),
            'cancelled': Reserva.objects.filter(estado='Cancelada').count()
        }
    }
    
    # Estadísticas de tiempo
    now = datetime.now()
    last_30_days = now - timedelta(days=30)
    
    stats['recent_activity'] = {
        'new_users_30d': User.objects.filter(date_joined__gte=last_30_days).count(),
        'new_reservations_30d': Reserva.objects.filter(fecha_hora_inicio__gte=last_30_days).count()
    }
    
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emprendimiento_dashboard_stats(request):
    """
    Estadísticas específicas para el dashboard de emprendimiento
    """
    if not hasattr(request.user, 'cliente'):
        return Response({
            'error': 'Usuario sin perfil de cliente'
        }, status=status.HTTP_403_FORBIDDEN)
    
    cliente = request.user.cliente
    user_bots = Bot.objects.filter(cliente=cliente)
    user_reservations = Reserva.objects.filter(bot__cliente=cliente)
    
    from datetime import datetime, timedelta
    now = datetime.now()
    this_month = now.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    stats = {
        'bots': {
            'total': user_bots.count(),
            'active': user_bots.filter(activo=True).count(),
            'inactive': user_bots.filter(activo=False).count()
        },
        'reservations': {
            'total': user_reservations.count(),
            'confirmed': user_reservations.filter(estado='Confirmada').count(),
            'pending': user_reservations.filter(estado='Pendiente').count(),
            'cancelled': user_reservations.filter(estado='Cancelada').count(),
            'this_month': user_reservations.filter(
                fecha_hora_inicio__gte=this_month
            ).count(),
            'last_month': user_reservations.filter(
                fecha_hora_inicio__gte=last_month,
                fecha_hora_inicio__lt=this_month
            ).count()
        },
        'upcoming_reservations': user_reservations.filter(
            fecha_hora_inicio__gt=now,
            estado__in=['Confirmada', 'Pendiente']
        ).order_by('fecha_hora_inicio')[:5].values(
            'id', 'fecha_hora_inicio', 'estado', 'servicio__nombre'
        )
    }
    
    return Response(stats, status=status.HTTP_200_OK)