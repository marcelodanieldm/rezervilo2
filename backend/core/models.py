from django.db import models

# Create your models here.
# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre_emprendimiento = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    def __str__(self): return self.nombre_emprendimiento

class Bot(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="bots")
    nombre = models.CharField(max_length=100)
    prompt_sistema = models.TextField(help_text="Las instrucciones de IA para Gemini")
    whatsapp_phone_id = models.CharField(max_length=50, unique=True)
    def __str__(self): return f"{self.nombre} (de {self.cliente.nombre_emprendimiento})"

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
    estado = models.CharField(max_length=20, choices=[('Confirmada', 'Confirmada'), ('Cancelada', 'Cancelada')], default='Confirmada')

    class Meta:
        unique_together = ('bot', 'fecha_hora_inicio')

    @property
    def puede_cancelar(self):
        limite = self.fecha_hora_inicio - timedelta(hours=24)
        return timezone.now() < limite
