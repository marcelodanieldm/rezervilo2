from django.db import models

# Create your models here.
# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Cliente(models.Model):
    STATUS_CHOICES = [
        ('activo', 'Activo'),
        ('suspendido', 'Suspendido'),
        ('inactivo', 'Inactivo'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre_emprendimiento = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    
    # Nuevos campos para gestión desde superusuario
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='activo',
        help_text="Estado del emprendimiento"
    )
    max_bots_allowed = models.PositiveIntegerField(
        default=3,
        help_text="Cantidad máxima de bots que puede crear este emprendimiento"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Fecha de registro del emprendimiento"
    )
    fecha_ultimo_acceso = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha del último acceso al sistema"
    )
    notas_admin = models.TextField(
        blank=True,
        help_text="Notas del administrador sobre este emprendimiento"
    )
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = "Emprendimiento"
        verbose_name_plural = "Emprendimientos"
    
    @property
    def cantidad_bots(self):
        """Retorna la cantidad actual de bots del emprendimiento"""
        return self.bots.count()
    
    @property
    def cantidad_bots_activos(self):
        """Retorna la cantidad de bots activos del emprendimiento"""
        return self.bots.filter(activo=True).count()
    
    @property
    def cantidad_reservas(self):
        """Retorna la cantidad total de reservas del emprendimiento"""
        return Reserva.objects.filter(bot__cliente=self).count()
    
    @property
    def cantidad_reservas_mes_actual(self):
        """Retorna la cantidad de reservas del mes actual"""
        from django.utils import timezone
        now = timezone.now()
        inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Reserva.objects.filter(
            bot__cliente=self,
            fecha_hora_inicio__gte=inicio_mes
        ).count()
    
    @property
    def puede_crear_bot(self):
        """Verifica si el emprendimiento puede crear más bots"""
        return self.cantidad_bots < self.max_bots_allowed and self.status == 'activo'
    
    @property
    def dias_desde_registro(self):
        """Retorna los días transcurridos desde el registro"""
        from django.utils import timezone
        return (timezone.now() - self.fecha_registro).days
    
    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha del último acceso"""
        from django.utils import timezone
        self.fecha_ultimo_acceso = timezone.now()
        self.save(update_fields=['fecha_ultimo_acceso'])
    
    def __str__(self): 
        return f"{self.nombre_emprendimiento} ({self.get_status_display()})"

class Bot(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="bots")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, help_text="Descripción del bot")
    prompt_sistema = models.TextField(help_text="Las instrucciones de IA para Gemini")
    whatsapp_phone_id = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True, help_text="Bot activo o inactivo")
    
    # Nuevos campos para gestión
    bloqueado = models.BooleanField(
        default=False, 
        help_text="Bot bloqueado por el administrador"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Bot"
        verbose_name_plural = "Bots"
    
    @property
    def esta_operativo(self):
        """Verifica si el bot está operativo (activo y no bloqueado)"""
        return self.activo and not self.bloqueado and self.cliente.status == 'activo'
    
    @property
    def total_reservas(self):
        """Retorna el total de reservas de este bot"""
        return self.reservas.count()
    
    @property
    def reservas_pendientes(self):
        """Retorna las reservas pendientes de este bot"""
        return self.reservas.filter(estado='Pendiente').count()
    
    def save(self, *args, **kwargs):
        # Validar límite de bots antes de crear
        if not self.pk:  # Solo en creación
            if not self.cliente.puede_crear_bot:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"El emprendimiento {self.cliente.nombre_emprendimiento} "
                    f"ha alcanzado su límite de {self.cliente.max_bots_allowed} bots."
                )
        super().save(*args, **kwargs)
    
    def __str__(self): 
        return f"{self.nombre} (de {self.cliente.nombre_emprendimiento})"

class Servicio(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="servicios")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self): return self.nombre

class Horario(models.Model):
    DIA_CHOICES = [(0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')]
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.IntegerField(choices=DIA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

class Reserva(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="reservas")
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True)
    cliente_final_nombre = models.CharField(max_length=100)
    cliente_final_telefono = models.CharField(max_length=20)
    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()
    estado = models.CharField(
        max_length=20, 
        choices=[
            ('Confirmada', 'Confirmada'), 
            ('Pendiente', 'Pendiente'),
            ('Cancelada', 'Cancelada')
        ], 
        default='Confirmada'
    )
    notas = models.TextField(blank=True, help_text="Notas adicionales de la reserva")

    class Meta:
        unique_together = ('bot', 'fecha_hora_inicio')

    @property
    def puede_cancelar(self):
        limite = self.fecha_hora_inicio - timedelta(hours=24)
        return timezone.now() < limite

    def __str__(self):
        return f"Reserva {self.servicio.nombre if self.servicio else 'Sin servicio'} - {self.fecha_hora_inicio}"
