# core/test_dashboard_integration.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json
from .models import Cliente, Bot, Servicio, Reserva


class DashboardIntegrationTestCase(APITestCase):
    """
    Tests de integración para validar el flujo completo de redirección
    desde login hasta dashboard correspondiente
    """
    
    def setUp(self):
        """Configuración inicial para los tests de integración"""
        self.client = APIClient()
        
        # Crear superusuario para tests
        self.superuser = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear usuario emprendimiento
        self.emprendimiento_user = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='password123'
        )
        
        # Crear perfil cliente
        self.cliente = Cliente.objects.create(
            user=self.emprendimiento_user,
            nombre_emprendimiento='Estética Bella Vida',
            telefono='+51987654321'
        )

    def test_complete_superuser_flow(self):
        """
        Test: Flujo completo de superusuario desde login hasta dashboard
        """
        print("\n🧪 Testing: Flujo completo de Superusuario")
        
        # 1. Login como superusuario usando el endpoint dashboard
        login_response = self.client.post('/api/dashboard/login/', {
            'username': 'admin_test',
            'password': 'admin123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        login_data = login_response.data
        
        # Verificar respuesta del login
        self.assertIn('access', login_data)
        self.assertIn('refresh', login_data)
        self.assertEqual(login_data['dashboard_type'], 'admin_dashboard')
        self.assertEqual(login_data['user_info']['username'], 'admin_test')
        self.assertTrue(login_data['user_info']['is_superuser'])
        
        print("✅ Login de superusuario exitoso")
        
        # 2. Configurar token y obtener configuración del dashboard
        access_token = login_data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        config_response = self.client.get('/api/dashboard/config/')
        self.assertEqual(config_response.status_code, status.HTTP_200_OK)
        
        config_data = config_response.data
        self.assertEqual(config_data['dashboard_type'], 'admin_dashboard')
        self.assertIn('user_management', config_data['features'])
        self.assertIn('cliente_management', config_data['features'])
        self.assertIn('global_bot_management', config_data['features'])
        
        print("✅ Configuración de dashboard de admin obtenida")
        
        # 3. Verificar acceso a estadísticas de admin
        stats_response = self.client.get('/api/dashboard/admin/stats/')
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        
        stats_data = stats_response.data
        self.assertIn('users', stats_data)
        self.assertIn('clientes', stats_data)
        self.assertIn('bots', stats_data)
        self.assertIn('reservations', stats_data)
        
        print("✅ Estadísticas de admin accesibles")
        
        # 4. Verificar acceso a gestión de clientes (solo admin)
        clientes_response = self.client.get('/api/clientes/')
        self.assertEqual(clientes_response.status_code, status.HTTP_200_OK)
        
        print("✅ Acceso a gestión de clientes confirmado")
        
        # 5. Logout
        logout_response = self.client.post('/api/dashboard/logout/')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        print("✅ Logout de superusuario exitoso")
        print("🎯 Flujo completo de superusuario: PASÓ")

    def test_complete_emprendimiento_flow(self):
        """
        Test: Flujo completo de usuario emprendimiento desde login hasta dashboard
        """
        print("\n🧪 Testing: Flujo completo de Emprendimiento")
        
        # 1. Login como emprendimiento
        login_response = self.client.post('/api/dashboard/login/', {
            'username': 'cliente_test',
            'password': 'password123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        login_data = login_response.data
        
        # Verificar respuesta del login
        self.assertEqual(login_data['dashboard_type'], 'emprendimiento_dashboard')
        self.assertEqual(login_data['user_info']['username'], 'cliente_test')
        self.assertFalse(login_data['user_info']['is_superuser'])
        self.assertTrue(login_data['user_info']['has_cliente_profile'])
        
        print("✅ Login de emprendimiento exitoso")
        
        # 2. Configurar token y obtener configuración del dashboard
        access_token = login_data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        config_response = self.client.get('/api/dashboard/config/')
        self.assertEqual(config_response.status_code, status.HTTP_200_OK)
        
        config_data = config_response.data
        self.assertEqual(config_data['dashboard_type'], 'emprendimiento_dashboard')
        self.assertIn('bot_management', config_data['features'])
        self.assertIn('reservations_management', config_data['features'])
        self.assertIn('calendar', config_data['features'])
        self.assertEqual(config_data['cliente_info']['nombre_emprendimiento'], 'Estética Bella Vida')
        
        print("✅ Configuración de dashboard de emprendimiento obtenida")
        
        # 3. Verificar acceso a estadísticas de emprendimiento
        stats_response = self.client.get('/api/dashboard/emprendimiento/stats/')
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        
        stats_data = stats_response.data
        self.assertIn('bots', stats_data)
        self.assertIn('reservations', stats_data)
        
        print("✅ Estadísticas de emprendimiento accesibles")
        
        # 4. Verificar que NO puede acceder a gestión de clientes
        clientes_response = self.client.get('/api/clientes/')
        self.assertEqual(clientes_response.status_code, status.HTTP_403_FORBIDDEN)
        
        print("✅ Restricción de acceso a gestión de clientes confirmada")
        
        # 5. Verificar acceso a sus propios bots
        bots_response = self.client.get('/api/bots/')
        self.assertEqual(bots_response.status_code, status.HTTP_200_OK)
        
        print("✅ Acceso a bots propios confirmado")
        
        # 6. Logout
        logout_response = self.client.post('/api/dashboard/logout/')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        print("✅ Logout de emprendimiento exitoso")
        print("🎯 Flujo completo de emprendimiento: PASÓ")

    def test_access_restriction_enforcement(self):
        """
        Test: Verificar que las restricciones de acceso se respetan correctamente
        """
        print("\n🧪 Testing: Restricciones de acceso")
        
        # Login como emprendimiento
        login_response = self.client.post('/api/dashboard/login/', {
            'username': 'cliente_test',
            'password': 'password123'
        })
        
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 1. Verificar que no puede acceder a stats de admin
        admin_stats_response = self.client.get('/api/dashboard/admin/stats/')
        self.assertEqual(admin_stats_response.status_code, status.HTTP_403_FORBIDDEN)
        
        print("✅ Restricción de acceso a estadísticas de admin confirmada")
        
        # 2. Crear otro cliente para verificar aislamiento de datos
        other_user = User.objects.create_user(
            username='otro_cliente',
            email='otro@test.com',
            password='test123'
        )
        
        other_cliente = Cliente.objects.create(
            user=other_user,
            nombre_emprendimiento='Otro Negocio',
            telefono='+51111111111'
        )
        
        other_bot = Bot.objects.create(
            cliente=other_cliente,
            nombre='Bot Ajeno',
            descripcion='Bot de otro cliente',
            prompt_sistema='Sistema ajeno',
            whatsapp_phone_id='999999999',
            activo=True
        )
        
        # 3. Verificar que el cliente actual no puede ver bots de otros clientes
        bots_response = self.client.get('/api/bots/')
        self.assertEqual(bots_response.status_code, status.HTTP_200_OK)
        
        # No debe ver el bot del otro cliente
        bot_names = [bot['nombre'] for bot in bots_response.data]
        self.assertNotIn('Bot Ajeno', bot_names)
        
        print("✅ Aislamiento de datos entre clientes confirmado")
        print("🎯 Restricciones de acceso: PASÓ")

    def test_invalid_credentials_handling(self):
        """
        Test: Verificar manejo correcto de credenciales inválidas
        """
        print("\n🧪 Testing: Manejo de credenciales inválidas")
        
        # 1. Usuario inexistente
        response = self.client.post('/api/dashboard/login/', {
            'username': 'usuario_inexistente',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        
        print("✅ Usuario inexistente manejado correctamente")
        
        # 2. Contraseña incorrecta
        response = self.client.post('/api/dashboard/login/', {
            'username': 'cliente_test',
            'password': 'password_incorrecto'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        
        print("✅ Contraseña incorrecta manejada correctamente")
        
        # 3. Campos faltantes
        response = self.client.post('/api/dashboard/login/', {
            'username': 'cliente_test'
            # password faltante
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        print("✅ Campos faltantes manejados correctamente")
        print("🎯 Manejo de credenciales inválidas: PASÓ")

    def test_dashboard_type_determination(self):
        """
        Test: Verificar que el tipo de dashboard se determina correctamente
        """
        print("\n🧪 Testing: Determinación del tipo de dashboard")
        
        # 1. Usuario sin perfil cliente
        user_without_profile = User.objects.create_user(
            username='sin_perfil',
            email='sin_perfil@test.com',
            password='test123'
        )
        
        login_response = self.client.post('/api/dashboard/login/', {
            'username': 'sin_perfil',
            'password': 'test123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data['dashboard_type'], 'limited_dashboard')
        
        print("✅ Usuario sin perfil → limited_dashboard")
        
        # 2. Usuario staff (no superuser)
        staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@test.com',
            password='test123',
            is_staff=True
        )
        
        login_response = self.client.post('/api/dashboard/login/', {
            'username': 'staff_user',
            'password': 'test123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data['dashboard_type'], 'admin_dashboard')
        
        print("✅ Usuario staff → admin_dashboard")
        
        # 3. Superusuario
        login_response = self.client.post('/api/dashboard/login/', {
            'username': 'admin_test',
            'password': 'admin123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data['dashboard_type'], 'admin_dashboard')
        
        print("✅ Superusuario → admin_dashboard")
        
        # 4. Usuario con perfil cliente
        login_response = self.client.post('/api/dashboard/login/', {
            'username': 'cliente_test',
            'password': 'password123'
        })
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data['dashboard_type'], 'emprendimiento_dashboard')
        
        print("✅ Usuario con perfil cliente → emprendimiento_dashboard")
        print("🎯 Determinación del tipo de dashboard: PASÓ")


class DashboardTestSuite:
    """
    Suite de tests completa para el sistema de dashboards
    """
    
    @staticmethod
    def run_all_tests():
        """
        Ejecuta todos los tests del sistema de dashboards
        """
        print("="*80)
        print("🧪 EJECUTANDO SUITE COMPLETA DE TESTS DE DASHBOARD")
        print("="*80)
        
        # Tests de autenticación básica
        print("\n📋 FASE 1: Tests de Autenticación Básica")
        from django.core.management import call_command
        call_command('test', 'core.test_authentication', verbosity=1)
        
        # Tests de integración de dashboard
        print("\n📋 FASE 2: Tests de Integración de Dashboard")
        call_command('test', 'core.test_dashboard_integration', verbosity=2)
        
        print("\n" + "="*80)
        print("✅ SUITE DE TESTS COMPLETADA")
        print("="*80)
        
        # Resumen de funcionalidades validadas
        validated_features = [
            "✅ Login con redirección automática según tipo de usuario",
            "✅ Dashboard de Superusuario con acceso completo",
            "✅ Dashboard de Emprendimiento con acceso limitado",
            "✅ Restricciones de acceso correctamente aplicadas",
            "✅ Logout funcional para ambos tipos de usuario",
            "✅ Manejo de errores y credenciales inválidas",
            "✅ Aislamiento de datos entre clientes",
            "✅ Determinación correcta del tipo de dashboard"
        ]
        
        print("\n🎯 FUNCIONALIDADES VALIDADAS:")
        for feature in validated_features:
            print(f"   {feature}")
        
        return True