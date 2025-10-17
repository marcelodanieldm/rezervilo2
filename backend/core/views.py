from django.shortcuts import render

# Create your views here.
# core/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Bot, Servicio, Reserva, Cliente
from .serializers import (
    UserSerializer, ClienteSerializer, BotSerializer, 
    ServicioSerializer, ReservaSerializer
)
from .permissions import IsOwnerOrAdmin

@action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
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
        serializer.save(cliente=self.request.user.cliente)

class ServicioViewSet(viewsets.ModelViewSet):
    """ API para Clientes: CRUD de Servicios (anidado bajo un Bot) """
    serializer_class = ServicioSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        # Filtra por bot, y el bot por cliente
        if self.request.user.is_staff:
            return Servicio.objects.all()
        if not hasattr(self.request.user, 'cliente'):
            return Servicio.objects.none()
        return Servicio.objects.filter(bot__cliente=self.request.user.cliente)

    # (Necesitarías pasar el 'bot_id' en el POST para crear uno)

class ReservaViewSet(viewsets.ReadOnlyModelViewSet):
    """ API para Clientes: Ver sus Reservas """
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
        return queryset