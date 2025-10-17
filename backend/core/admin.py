from django.contrib import admin

# Register your models here.
# core/admin.py
from django.contrib import admin
from .models import Cliente, Bot, Servicio, Horario, Reserva

class BotAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cliente', 'whatsapp_phone_id')

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_emprendimiento', 'user')

admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Bot, BotAdmin)
admin.site.register(Servicio)
admin.site.register(Horario)
admin.site.register(Reserva)
