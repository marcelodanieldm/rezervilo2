# core/emprendimiento_views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from .models import Cliente, Bot, Servicio, Reserva
from .serializers import (
    ClienteSerializer, ClienteListSerializer, ClienteDetailSerializer,
    BotSerializer, BotDetailSerializer, BotManagementSerializer,
    UserSerializer
)
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.utils import timezone


class EmprendimientoPagination(PageNumberPagination):
    """Paginación personalizada para emprendimientos"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class EmprendimientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de emprendimientos desde superusuario
    """
    queryset = Cliente.objects.all()
    pagination_class = EmprendimientoPagination
    permission_classes = [permissions.IsAdminUser]  # Solo superusuarios
    
    def get_serializer_class(self):
        """Selecciona el serializer según la acción"""
        if self.action == 'list':
            return ClienteListSerializer
        elif self.action == 'retrieve':
            return ClienteDetailSerializer
        return ClienteSerializer
    
    def get_queryset(self):
        """Aplica filtros según los parámetros de consulta"""
        queryset = Cliente.objects.all()
        
        # Filtros
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nombre_emprendimiento__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Ordenamiento
        ordering = self.request.query_params.get('ordering', '-fecha_registro')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Lista paginada de emprendimientos con estadísticas"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Crea un nuevo emprendimiento"""
        try:
            # Crear usuario primero
            user_data = request.data.get('user_data', {})
            username = user_data.get('username')
            email = user_data.get('email')
            password = user_data.get('password')
            
            if not all([username, email, password]):
                return Response({
                    'error': 'Username, email y password son requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar que el username no exista
            if User.objects.filter(username=username).exists():
                return Response({
                    'error': 'El nombre de usuario ya existe'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', '')
            )
            
            # Crear cliente
            cliente_data = request.data.copy()
            cliente_data['user'] = user.id
            
            serializer = self.get_serializer(data=cliente_data)
            serializer.is_valid(raise_exception=True)
            cliente = serializer.save(user=user)
            
            # Actualizar fecha de registro si no se estableció
            if not cliente.fecha_registro:
                cliente.fecha_registro = timezone.now()
                cliente.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Error al crear emprendimiento: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Actualiza un emprendimiento"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Manejar actualización de datos del usuario
        user_data = request.data.get('user_data', {})
        if user_data:
            user = instance.user
            for field in ['email', 'first_name', 'last_name', 'is_active']:
                if field in user_data:
                    setattr(user, field, user_data[field])
            user.save()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Cambia el status del emprendimiento"""
        cliente = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['activo', 'suspendido', 'inactivo']:
            return Response({
                'error': 'Status inválido. Debe ser: activo, suspendido o inactivo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = cliente.status
        cliente.status = new_status
        cliente.save()
        
        # Si se suspende o inactiva, desactivar todos sus bots
        if new_status in ['suspendido', 'inactivo']:
            cliente.bots.update(activo=False)
        
        return Response({
            'message': f'Status cambiado de {old_status} a {new_status}',
            'status': new_status
        })
    
    @action(detail=True, methods=['post'])
    def update_bot_limit(self, request, pk=None):
        """Actualiza el límite de bots del emprendimiento"""
        cliente = self.get_object()
        new_limit = request.data.get('max_bots_allowed')
        
        try:
            new_limit = int(new_limit)
            if new_limit < 0:
                raise ValueError("El límite no puede ser negativo")
            
            # Verificar si la reducción afectaría bots existentes
            current_bots = cliente.cantidad_bots
            if new_limit < current_bots:
                return Response({
                    'error': f'No se puede establecer límite de {new_limit}. '
                           f'El emprendimiento tiene {current_bots} bots actualmente.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            old_limit = cliente.max_bots_allowed
            cliente.max_bots_allowed = new_limit
            cliente.save()
            
            return Response({
                'message': f'Límite de bots actualizado de {old_limit} a {new_limit}',
                'max_bots_allowed': new_limit,
                'current_bots': current_bots
            })
            
        except (ValueError, TypeError):
            return Response({
                'error': 'El límite de bots debe ser un número entero válido'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Obtiene el perfil completo del emprendimiento"""
        cliente = self.get_object()
        serializer = ClienteDetailSerializer(cliente)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def bots(self, request, pk=None):
        """Lista los bots del emprendimiento"""
        cliente = self.get_object()
        bots = cliente.bots.all()
        serializer = BotDetailSerializer(bots, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_bot(self, request, pk=None):
        """Crea un nuevo bot para el emprendimiento"""
        cliente = self.get_object()
        
        # Verificar límites
        if not cliente.puede_crear_bot:
            return Response({
                'error': f'No se puede crear más bots. '
                        f'Límite: {cliente.max_bots_allowed}, '
                        f'Actual: {cliente.cantidad_bots}, '
                        f'Status: {cliente.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear bot
        bot_data = request.data.copy()
        bot_data['cliente'] = cliente.id
        
        serializer = BotSerializer(data=bot_data)
        serializer.is_valid(raise_exception=True)
        bot = serializer.save(cliente=cliente)
        
        return Response(BotDetailSerializer(bot).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def emprendimientos_stats(request):
    """
    Estadísticas generales de emprendimientos para el dashboard de admin
    """
    total_emprendimientos = Cliente.objects.count()
    emprendimientos_activos = Cliente.objects.filter(status='activo').count()
    emprendimientos_suspendidos = Cliente.objects.filter(status='suspendido').count()
    emprendimientos_inactivos = Cliente.objects.filter(status='inactivo').count()
    
    # Estadísticas de tiempo
    now = timezone.now()
    ultimo_mes = now - timedelta(days=30)
    nuevos_ultimo_mes = Cliente.objects.filter(fecha_registro__gte=ultimo_mes).count()
    
    # Promedio de bots por emprendimiento
    from django.db.models import Avg
    promedio_bots = Cliente.objects.aggregate(
        avg_bots=Avg('bots__id')
    )['avg_bots'] or 0
    
    # Top emprendimientos por reservas
    top_emprendimientos = Cliente.objects.annotate(
        total_reservas=Count('bots__reservas')
    ).order_by('-total_reservas')[:5]
    
    top_data = []
    for emp in top_emprendimientos:
        top_data.append({
            'id': emp.id,
            'nombre': emp.nombre_emprendimiento,
            'total_reservas': emp.total_reservas,
            'cantidad_bots': emp.cantidad_bots
        })
    
    return Response({
        'total_emprendimientos': total_emprendimientos,
        'emprendimientos_activos': emprendimientos_activos,
        'emprendimientos_suspendidos': emprendimientos_suspendidos,
        'emprendimientos_inactivos': emprendimientos_inactivos,
        'nuevos_ultimo_mes': nuevos_ultimo_mes,
        'promedio_bots': round(promedio_bots, 1),
        'top_emprendimientos': top_data
    })


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAdminUser])
def bot_management(request, cliente_id, bot_id=None):
    """
    Gestión de bots desde superusuario
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'GET':
        if bot_id:
            # Obtener bot específico
            bot = get_object_or_404(Bot, id=bot_id, cliente=cliente)
            serializer = BotDetailSerializer(bot)
            return Response(serializer.data)
        else:
            # Listar todos los bots del emprendimiento
            bots = cliente.bots.all()
            serializer = BotDetailSerializer(bots, many=True)
            return Response(serializer.data)
    
    elif request.method == 'POST':
        # Crear nuevo bot
        if not cliente.puede_crear_bot:
            return Response({
                'error': f'No se puede crear más bots para {cliente.nombre_emprendimiento}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        bot_data = request.data.copy()
        serializer = BotSerializer(data=bot_data)
        serializer.is_valid(raise_exception=True)
        bot = serializer.save(cliente=cliente)
        
        return Response(BotDetailSerializer(bot).data, status=status.HTTP_201_CREATED)
    
    elif request.method == 'PUT':
        # Actualizar bot
        bot = get_object_or_404(Bot, id=bot_id, cliente=cliente)
        serializer = BotManagementSerializer(bot, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(BotDetailSerializer(bot).data)
    
    elif request.method == 'DELETE':
        # Eliminar bot
        bot = get_object_or_404(Bot, id=bot_id, cliente=cliente)
        bot_name = bot.nombre
        bot.delete()
        
        return Response({
            'message': f'Bot "{bot_name}" eliminado exitosamente'
        })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def toggle_bot_block(request, cliente_id, bot_id):
    """
    Bloquea/desbloquea un bot desde superusuario
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    bot = get_object_or_404(Bot, id=bot_id, cliente=cliente)
    
    bot.bloqueado = not bot.bloqueado
    bot.save()
    
    action = "bloqueado" if bot.bloqueado else "desbloqueado"
    
    return Response({
        'message': f'Bot "{bot.nombre}" {action} exitosamente',
        'bot_id': bot.id,
        'bloqueado': bot.bloqueado,
        'esta_operativo': bot.esta_operativo
    })


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def emprendimiento_activity_log(request, cliente_id):
    """
    Obtiene el log de actividad de un emprendimiento
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Simular log de actividad (en producción esto vendría de un modelo de auditoría)
    activity_log = [
        {
            'fecha': cliente.fecha_ultimo_acceso or cliente.fecha_registro,
            'accion': 'Último acceso al sistema',
            'detalle': 'Usuario accedió al dashboard'
        },
        {
            'fecha': cliente.fecha_registro,
            'accion': 'Emprendimiento registrado',
            'detalle': 'Cuenta creada en el sistema'
        }
    ]
    
    # Agregar actividad de bots
    for bot in cliente.bots.all():
        if bot.fecha_creacion:
            activity_log.append({
                'fecha': bot.fecha_creacion,
                'accion': f'Bot "{bot.nombre}" creado',
                'detalle': f'Bot creado {" y bloqueado" if bot.bloqueado else ""}'
            })
    
    # Ordenar por fecha descendente
    activity_log.sort(key=lambda x: x['fecha'] or timezone.now(), reverse=True)
    
    return Response({
        'emprendimiento': cliente.nombre_emprendimiento,
        'activity_log': activity_log[:20]  # Últimas 20 actividades
    })