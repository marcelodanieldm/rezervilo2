# core/admin.py
from django.contrib import admin
from .models import Cliente, Bot, Servicio, Horario, Reserva

class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre_emprendimiento', 'user', 'telefono']
    search_fields = ['nombre_emprendimiento', 'user__username']

class BotAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cliente', 'activo', 'whatsapp_phone_id']
    list_filter = ['activo', 'cliente']
    search_fields = ['nombre', 'cliente__nombre_emprendimiento']
    fields = ['cliente', 'nombre', 'descripcion', 'activo', 'whatsapp_phone_id', 'prompt_sistema']

class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'bot', 'precio']
    list_filter = ['bot__cliente']
    search_fields = ['nombre', 'bot__nombre']

class HorarioAdmin(admin.ModelAdmin):
    list_display = ['bot', 'dia_semana', 'hora_inicio', 'hora_fin']
    list_filter = ['dia_semana', 'bot__cliente']

class ReservaAdmin(admin.ModelAdmin):
    list_display = ['bot', 'servicio', 'cliente_final_nombre', 'fecha_hora_inicio', 'estado']
    list_filter = ['estado', 'bot__cliente', 'fecha_hora_inicio']
    search_fields = ['cliente_final_nombre', 'bot__nombre']
    readonly_fields = ['puede_cancelar']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('bot', 'servicio', 'estado')
        }),
        ('Cliente Final', {
            'fields': ('cliente_final_nombre', 'cliente_final_telefono')
        }),
        ('Fecha y Hora', {
            'fields': ('fecha_hora_inicio', 'fecha_hora_fin')
        }),
        ('Adicional', {
            'fields': ('notas', 'puede_cancelar')
        })
    )

# Registrar los modelos
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Bot, BotAdmin)
admin.site.register(Servicio, ServicioAdmin)
admin.site.register(Horario, HorarioAdmin)
admin.site.register(Reserva, ReservaAdmin)
