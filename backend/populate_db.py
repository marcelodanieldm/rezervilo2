# populate_db.py - Script para poblar la base de datos con datos de prueba
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel_admin.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Cliente, Bot, Servicio, Reserva
from datetime import datetime, timedelta
from django.utils import timezone

def create_test_data():
    print("Creando datos de prueba...")
    
    # Crear usuario cliente de prueba
    user_cliente, created = User.objects.get_or_create(
        username='cliente_test',
        defaults={
            'email': 'cliente@test.com',
            'first_name': 'Cliente',
            'last_name': 'Test'
        }
    )
    if created:
        user_cliente.set_password('password123')
        user_cliente.save()
        print(f"✅ Usuario cliente creado: {user_cliente.username}")
    
    # Crear perfil de cliente
    cliente, created = Cliente.objects.get_or_create(
        user=user_cliente,
        defaults={
            'nombre_emprendimiento': 'Estética Bella Vida',
            'telefono': '+573001234567'
        }
    )
    if created:
        print(f"✅ Cliente creado: {cliente.nombre_emprendimiento}")
    
    # Crear bots de prueba
    bot1, created = Bot.objects.get_or_create(
        cliente=cliente,
        nombre='Estela Bot',
        defaults={
            'descripcion': 'Bot principal para reservas de tratamientos estéticos',
            'prompt_sistema': 'Eres Estela, asistente virtual de Estética Bella Vida. Ayudas a los clientes a reservar citas para tratamientos de belleza.',
            'whatsapp_phone_id': 'test_phone_001',
            'activo': True
        }
    )
    if created:
        print(f"✅ Bot creado: {bot1.nombre}")
    
    bot2, created = Bot.objects.get_or_create(
        cliente=cliente,
        nombre='Ana Asistente',
        defaults={
            'descripcion': 'Bot secundario para consultas generales',
            'prompt_sistema': 'Eres Ana, asistente de información general. Respondes preguntas sobre horarios y servicios.',
            'whatsapp_phone_id': 'test_phone_002',
            'activo': False
        }
    )
    if created:
        print(f"✅ Bot creado: {bot2.nombre}")
    
    # Crear servicios
    servicio1, created = Servicio.objects.get_or_create(
        bot=bot1,
        nombre='Limpieza Facial',
        defaults={
            'descripcion': 'Limpieza profunda facial con extracción de puntos negros',
            'precio': 50000.00
        }
    )
    if created:
        print(f"✅ Servicio creado: {servicio1.nombre}")
    
    servicio2, created = Servicio.objects.get_or_create(
        bot=bot1,
        nombre='Masaje Relajante',
        defaults={
            'descripcion': 'Masaje corporal relajante de 60 minutos',
            'precio': 80000.00
        }
    )
    if created:
        print(f"✅ Servicio creado: {servicio2.nombre}")
    
    servicio3, created = Servicio.objects.get_or_create(
        bot=bot1,
        nombre='Manicure y Pedicure',
        defaults={
            'descripcion': 'Manicure y pedicure completo con esmaltado',
            'precio': 35000.00
        }
    )
    if created:
        print(f"✅ Servicio creado: {servicio3.nombre}")
    
    # Crear reservas de prueba
    reservas_data = [
        {
            'servicio': servicio1,
            'cliente_final_nombre': 'María González',
            'cliente_final_telefono': '+573009876543',
            'fecha_hora_inicio': timezone.now() + timedelta(days=1, hours=9),
            'estado': 'Confirmada',
            'notas': 'Primera vez, cliente nueva'
        },
        {
            'servicio': servicio2,
            'cliente_final_nombre': 'Ana Rodríguez',
            'cliente_final_telefono': '+573007654321',
            'fecha_hora_inicio': timezone.now() + timedelta(days=2, hours=14),
            'estado': 'Confirmada',
            'notas': 'Cliente frecuente, prefiere música relajante'
        },
        {
            'servicio': servicio3,
            'cliente_final_nombre': 'Laura Martínez',
            'cliente_final_telefono': '+573005432109',
            'fecha_hora_inicio': timezone.now() + timedelta(days=3, hours=11),
            'estado': 'Pendiente',
            'notas': 'Confirmar color de esmalte'
        },
        {
            'servicio': servicio1,
            'cliente_final_nombre': 'Carmen Silva',
            'cliente_final_telefono': '+573008765432',
            'fecha_hora_inicio': timezone.now() - timedelta(days=1, hours=10),
            'estado': 'Confirmada',
            'notas': 'Reserva completada'
        },
        {
            'servicio': servicio2,
            'cliente_final_nombre': 'Sofía López',
            'cliente_final_telefono': '+573006543210',
            'fecha_hora_inicio': timezone.now() + timedelta(days=5, hours=16),
            'estado': 'Confirmada',
            'notas': 'Regalo de cumpleaños'
        }
    ]
    
    for reserva_data in reservas_data:
        fecha_inicio = reserva_data['fecha_hora_inicio']
        fecha_fin = fecha_inicio + timedelta(hours=1)
        
        reserva, created = Reserva.objects.get_or_create(
            bot=bot1,
            fecha_hora_inicio=fecha_inicio,
            defaults={
                'servicio': reserva_data['servicio'],
                'cliente_final_nombre': reserva_data['cliente_final_nombre'],
                'cliente_final_telefono': reserva_data['cliente_final_telefono'],
                'fecha_hora_fin': fecha_fin,
                'estado': reserva_data['estado'],
                'notas': reserva_data['notas']
            }
        )
        if created:
            print(f"✅ Reserva creada: {reserva.cliente_final_nombre} - {reserva.servicio.nombre}")
    
    print("\n🎉 ¡Datos de prueba creados exitosamente!")
    print("\n📋 Credenciales para el frontend:")
    print(f"   Usuario: cliente_test")
    print(f"   Contraseña: password123")
    print(f"   Emprendimiento: {cliente.nombre_emprendimiento}")
    print(f"\n🤖 Bots creados: {Bot.objects.filter(cliente=cliente).count()}")
    print(f"🛍️ Servicios creados: {Servicio.objects.filter(bot__cliente=cliente).count()}")
    print(f"📅 Reservas creadas: {Reserva.objects.filter(bot__cliente=cliente).count()}")

if __name__ == '__main__':
    create_test_data()