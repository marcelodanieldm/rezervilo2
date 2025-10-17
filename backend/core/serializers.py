# core/serializers.py
from rest_framework import serializers
from .models import Bot, Servicio, Reserva, Cliente
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser', 'is_active'] # Campos completos para tests

class ClienteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # Mostrar datos del usuario anidado
    cantidad_bots = serializers.ReadOnlyField()
    cantidad_bots_activos = serializers.ReadOnlyField()
    cantidad_reservas = serializers.ReadOnlyField()
    cantidad_reservas_mes_actual = serializers.ReadOnlyField()
    puede_crear_bot = serializers.ReadOnlyField()
    dias_desde_registro = serializers.ReadOnlyField()
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'user', 'nombre_emprendimiento', 'telefono', 'status', 
            'max_bots_allowed', 'fecha_registro', 'fecha_ultimo_acceso', 
            'notas_admin', 'cantidad_bots', 'cantidad_bots_activos', 
            'cantidad_reservas', 'cantidad_reservas_mes_actual', 
            'puede_crear_bot', 'dias_desde_registro'
        ]
        read_only_fields = ['fecha_registro', 'dias_desde_registro']


class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de emprendimientos con paginación"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    is_active = serializers.CharField(source='user.is_active', read_only=True)
    cantidad_bots = serializers.ReadOnlyField()
    cantidad_reservas = serializers.ReadOnlyField()
    dias_desde_registro = serializers.ReadOnlyField()
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'nombre_emprendimiento', 'username', 'email', 'is_active',
            'status', 'max_bots_allowed', 'cantidad_bots', 'cantidad_reservas',
            'fecha_registro', 'fecha_ultimo_acceso', 'dias_desde_registro'
        ]


class ClienteDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para el perfil de emprendimiento"""
    user = UserSerializer(read_only=True)
    bots = serializers.SerializerMethodField()
    cantidad_bots = serializers.ReadOnlyField()
    cantidad_bots_activos = serializers.ReadOnlyField()
    cantidad_reservas = serializers.ReadOnlyField()
    cantidad_reservas_mes_actual = serializers.ReadOnlyField()
    puede_crear_bot = serializers.ReadOnlyField()
    dias_desde_registro = serializers.ReadOnlyField()
    
    class Meta:
        model = Cliente
        fields = [
            'id', 'user', 'nombre_emprendimiento', 'telefono', 'status', 
            'max_bots_allowed', 'fecha_registro', 'fecha_ultimo_acceso', 
            'notas_admin', 'cantidad_bots', 'cantidad_bots_activos', 
            'cantidad_reservas', 'cantidad_reservas_mes_actual', 
            'puede_crear_bot', 'dias_desde_registro', 'bots'
        ]
        read_only_fields = ['fecha_registro', 'dias_desde_registro', 'bots']
    
    def get_bots(self, obj):
        """Obtiene los bots del emprendimiento con información detallada"""
        bots = obj.bots.all()
        return BotDetailSerializer(bots, many=True).data

class ServicioSerializer(serializers.ModelSerializer):
    bot_nombre = serializers.CharField(source='bot.nombre', read_only=True)
    
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'precio', 'bot', 'bot_nombre']

class BotSerializer(serializers.ModelSerializer):
    servicios = ServicioSerializer(many=True, read_only=True)
    total_reservas = serializers.SerializerMethodField()
    cliente_nombre = serializers.CharField(source='cliente.nombre_emprendimiento', read_only=True)
    esta_operativo = serializers.ReadOnlyField()
    reservas_pendientes = serializers.ReadOnlyField()
    
    class Meta:
        model = Bot
        fields = [
            'id', 'nombre', 'descripcion', 'activo', 'bloqueado', 'prompt_sistema', 
            'whatsapp_phone_id', 'servicios', 'total_reservas', 'cliente', 
            'cliente_nombre', 'esta_operativo', 'reservas_pendientes',
            'fecha_creacion', 'fecha_modificacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_total_reservas(self, obj):
        return obj.reservas.count()
    
    def create(self, validated_data):
        # Asegurar que se incluya el campo activo
        if 'activo' not in validated_data:
            validated_data['activo'] = True
        return super().create(validated_data)


class BotDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para bots en el perfil de emprendimiento"""
    servicios = ServicioSerializer(many=True, read_only=True)
    total_reservas = serializers.ReadOnlyField()
    reservas_pendientes = serializers.ReadOnlyField()
    esta_operativo = serializers.ReadOnlyField()
    reservas_recientes = serializers.SerializerMethodField()
    
    class Meta:
        model = Bot
        fields = [
            'id', 'nombre', 'descripcion', 'activo', 'bloqueado', 'prompt_sistema', 
            'whatsapp_phone_id', 'servicios', 'total_reservas', 'reservas_pendientes',
            'esta_operativo', 'fecha_creacion', 'fecha_modificacion', 'reservas_recientes'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def get_reservas_recientes(self, obj):
        """Obtiene las 5 reservas más recientes del bot"""
        reservas = obj.reservas.order_by('-fecha_hora_inicio')[:5]
        return ReservaSerializer(reservas, many=True).data


class BotManagementSerializer(serializers.ModelSerializer):
    """Serializer para gestión de bots desde superusuario"""
    cliente_nombre = serializers.CharField(source='cliente.nombre_emprendimiento', read_only=True)
    total_reservas = serializers.ReadOnlyField()
    reservas_pendientes = serializers.ReadOnlyField()
    esta_operativo = serializers.ReadOnlyField()
    
    class Meta:
        model = Bot
        fields = [
            'id', 'nombre', 'descripcion', 'activo', 'bloqueado', 'cliente',
            'cliente_nombre', 'total_reservas', 'reservas_pendientes', 
            'esta_operativo', 'fecha_creacion', 'fecha_modificacion'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion', 'cliente']

class ReservaSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    bot_nombre = serializers.CharField(source='bot.nombre', read_only=True)
    cliente_nombre = serializers.CharField(source='bot.cliente.nombre_emprendimiento', read_only=True)
    
    class Meta:
        model = Reserva
        fields = ['id', 'bot', 'bot_nombre', 'servicio', 'servicio_nombre', 
                  'cliente_nombre', 'cliente_final_nombre', 'cliente_final_telefono', 
                  'fecha_hora_inicio', 'fecha_hora_fin', 'estado', 'puede_cancelar',
                  'notas']
        read_only_fields = ['puede_cancelar', 'bot_nombre', 'servicio_nombre', 'cliente_nombre']