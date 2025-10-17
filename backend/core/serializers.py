# core/serializers.py
from rest_framework import serializers
from .models import Bot, Servicio, Reserva, Cliente
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff'] # is_staff nos dirá si es Admin

class ClienteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # Mostrar datos del usuario anidado
    class Meta:
        model = Cliente
        fields = ['id', 'user', 'nombre_emprendimiento', 'telefono']

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'precio']

class BotSerializer(serializers.ModelSerializer):
    servicios = ServicioSerializer(many=True, read_only=True)
    class Meta:
        model = Bot
        fields = ['id', 'nombre', 'prompt_sistema', 'whatsapp_phone_id', 'servicios']

class ReservaSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    class Meta:
        model = Reserva
        fields = ['id', 'bot', 'servicio', 'servicio_nombre', 'cliente_final_nombre', 
                  'cliente_final_telefono', 'fecha_hora_inicio', 'fecha_hora_fin', 
                  'estado', 'puede_cancelar']
        read_only_fields = ['puede_cancelar']