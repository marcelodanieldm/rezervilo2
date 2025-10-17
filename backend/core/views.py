# core/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Bot, Servicio, Reserva, Cliente
from .serializers import (
    UserSerializer, ClienteSerializer, BotSerializer, 
    ServicioSerializer, ReservaSerializer
)
from .permissions import IsOwnerOrAdmin
from datetime import datetime, timedelta
from django.utils import timezone

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_me(request):
    """
    Endpoint custom para que el usuario obtenga sus propios datos
    y los de su emprendimiento.
    """
    user = request.user
    user_serializer = UserSerializer(user)
    try:
        cliente = request.user.cliente
        cliente_serializer = ClienteSerializer(cliente)
        data = {
            'user': user_serializer.data,
            'cliente': cliente_serializer.data
        }
    except Cliente.DoesNotExist:
        data = {
            'user': user_serializer.data,
            'cliente': None # Es un admin sin perfil de cliente
        }
    return Response(data, status=status.HTTP_200_OK)


class ClienteViewSet(viewsets.ModelViewSet):
    """ API para Superadmin: CRUD de Clientes """
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAdminUser] # Solo Admins

class BotViewSet(viewsets.ModelViewSet):
    """ API para Clientes: CRUD de sus Bots """
    serializer_class = BotSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Bot.objects.all() # Admin ve todo
        if not hasattr(self.request.user, 'cliente'):
            return Bot.objects.none() # Usuario sin cliente no ve nada
        return Bot.objects.filter(cliente=self.request.user.cliente)

    def perform_create(self, serializer):
        # Asegurar que el bot se asigne al cliente autenticado
        if hasattr(self.request.user, 'cliente'):
            serializer.save(cliente=self.request.user.cliente)
        else:
            # Si no tiene cliente, no puede crear bots
            return Response(
                {'error': 'Usuario sin perfil de cliente no puede crear bots'}, 
                status=status.HTTP_403_FORBIDDEN
            )

class ServicioViewSet(viewsets.ModelViewSet):
    """ API para Clientes: CRUD de Servicios """
    serializer_class = ServicioSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        # Filtra por bot, y el bot por cliente
        if self.request.user.is_staff:
            return Servicio.objects.all()
        if not hasattr(self.request.user, 'cliente'):
            return Servicio.objects.none()
        return Servicio.objects.filter(bot__cliente=self.request.user.cliente)

    def perform_create(self, serializer):
        # Aquí necesitarías la lógica para asignar a un bot específico
        # Por ahora, lo dejamos así y el frontend debe enviar el bot_id
        serializer.save()

class ReservaViewSet(viewsets.ModelViewSet):
    """ API para Clientes: CRUD de Reservas """
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Reserva.objects.all()
        if not hasattr(self.request.user, 'cliente'):
            return Reserva.objects.none()

        # Filtra por fecha si se provee el query param
        queryset = Reserva.objects.filter(bot__cliente=self.request.user.cliente)
        fecha = self.request.query_params.get('fecha', None)
        if fecha is not None:
            queryset = queryset.filter(fecha_hora_inicio__date=fecha)
        return queryset.order_by('-fecha_hora_inicio')

    def perform_create(self, serializer):
        # Crear reserva con datos adicionales
        fecha = self.request.data.get('fecha')
        hora = self.request.data.get('hora')
        servicio_id = self.request.data.get('servicio')
        bot_id = self.request.data.get('bot')
        notas = self.request.data.get('notas', '')

        try:
            # Combinar fecha y hora
            fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            fecha_hora_inicio = timezone.make_aware(fecha_hora)
            
            # Obtener servicio para calcular duración (asumimos 1 hora por defecto)
            servicio = Servicio.objects.get(id=servicio_id)
            fecha_hora_fin = fecha_hora_inicio + timedelta(hours=1)
            
            # Obtener bot
            bot = Bot.objects.get(id=bot_id, cliente=self.request.user.cliente)
            
            serializer.save(
                bot=bot,
                servicio=servicio,
                fecha_hora_inicio=fecha_hora_inicio,
                fecha_hora_fin=fecha_hora_fin,
                cliente_final_nombre="Cliente Web",  # Por ahora un valor por defecto
                cliente_final_telefono="000000000",  # Por ahora un valor por defecto
                estado="Confirmada"
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """Actualización parcial para cancelar reservas"""
        instance = self.get_object()
        
        # Solo permitir cambio de estado
        if 'estado' in request.data:
            instance.estado = request.data['estado']
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        return super().partial_update(request, *args, **kwargs)