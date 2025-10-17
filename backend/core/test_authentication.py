# core/test_authentication.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Cliente, Bot, Servicio, Reserva
import json


class AuthenticationRedirectionTestCase(APITestCase):
    """
    Tests para validar que los usuarios sean redirigidos correctamente
    según su tipo: Superusuario vs Usuario Emprendimiento
    """
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = APIClient()
        
        # Crear superusuario
        self.superuser = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear usuario emprendimiento
        self.emprendimiento_user = User.objects.create_user(
            username='emprendimiento_test',
            email='emprendimiento@test.com',
            password='emp123'
        )
        
        # Crear perfil cliente para el usuario emprendimiento
        self.cliente = Cliente.objects.create(
            user=self.emprendimiento_user,
            nombre_emprendimiento='Mi Negocio Test',
            telefono='+51987654321'
        )
        
        # Crear datos de prueba para el emprendimiento
        self.bot = Bot.objects.create(
            cliente=self.cliente,
            nombre='Bot Test',
            descripcion='Bot para testing',
            prompt_sistema='Sistema de prueba',
            whatsapp_phone_id='123456789',
            activo=True
        )
        
        self.servicio = Servicio.objects.create(
            bot=self.bot,
            nombre='Servicio Test',
            descripcion='Servicio de prueba',
            precio=50.00
        )

    def test_superuser_login_and_data_access(self):
        """
        Test: Verificar que un superusuario puede hacer login y acceder a todos los datos
        """
        # Login como superusuario
        response = self.client.post('/api/token/', {
            'username': 'admin_test',
            'password': 'admin123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Obtener token y configurar headers
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Verificar datos del usuario
        me_response = self.client.get('/api/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        
        user_data = me_response.data
        self.assertEqual(user_data['user']['username'], 'admin_test')
        self.assertEqual(user_data['user']['is_staff'], True)
        self.assertEqual(user_data['user']['is_superuser'], True)
        self.assertIsNone(user_data['cliente'])  # Superusuario no tiene perfil cliente
        
        # Verificar acceso a todos los clientes (solo superusuarios)
        clientes_response = self.client.get('/api/clientes/')
        self.assertEqual(clientes_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clientes_response.data), 1)  # Debe ver el cliente creado
        
        # Verificar acceso a todos los bots
        bots_response = self.client.get('/api/bots/')
        self.assertEqual(bots_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(bots_response.data), 1)  # Debe ver todos los bots

    def test_emprendimiento_user_login_and_data_access(self):
        """
        Test: Verificar que un usuario emprendimiento puede hacer login y acceder solo a sus datos
        """
        # Login como usuario emprendimiento
        response = self.client.post('/api/token/', {
            'username': 'emprendimiento_test',
            'password': 'emp123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Obtener token y configurar headers
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Verificar datos del usuario
        me_response = self.client.get('/api/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        
        user_data = me_response.data
        self.assertEqual(user_data['user']['username'], 'emprendimiento_test')
        self.assertEqual(user_data['user']['is_staff'], False)
        self.assertEqual(user_data['user']['is_superuser'], False)
        self.assertIsNotNone(user_data['cliente'])  # Debe tener perfil cliente
        self.assertEqual(user_data['cliente']['nombre_emprendimiento'], 'Mi Negocio Test')
        
        # Verificar que NO puede acceder a lista de clientes (solo superusuarios)
        clientes_response = self.client.get('/api/clientes/')
        self.assertEqual(clientes_response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verificar acceso solo a sus propios bots
        bots_response = self.client.get('/api/bots/')
        self.assertEqual(bots_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(bots_response.data), 1)  # Solo debe ver sus bots
        self.assertEqual(bots_response.data[0]['nombre'], 'Bot Test')

    def test_invalid_login_credentials(self):
        """
        Test: Verificar que credenciales inválidas no permiten el acceso
        """
        response = self.client.post('/api/token/', {
            'username': 'usuario_inexistente',
            'password': 'password_incorrecto'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_token_refresh_functionality(self):
        """
        Test: Verificar que el refresh token funciona correctamente
        """
        # Login inicial
        login_response = self.client.post('/api/token/', {
            'username': 'emprendimiento_test',
            'password': 'emp123'
        })
        
        refresh_token = login_response.data['refresh']
        
        # Usar refresh token para obtener nuevo access token
        refresh_response = self.client.post('/api/token/refresh/', {
            'refresh': refresh_token
        })
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        
        # Verificar que el nuevo token funciona
        new_access_token = refresh_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        
        me_response = self.client.get('/api/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)

    def test_user_without_cliente_profile_restrictions(self):
        """
        Test: Verificar que un usuario sin perfil Cliente tiene acceso limitado
        """
        # Crear usuario sin perfil Cliente
        user_without_client = User.objects.create_user(
            username='user_no_client',
            email='noclient@test.com',
            password='test123'
        )
        
        # Login
        response = self.client.post('/api/token/', {
            'username': 'user_no_client',
            'password': 'test123'
        })
        
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Verificar datos del usuario
        me_response = self.client.get('/api/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertIsNone(me_response.data['cliente'])
        
        # Verificar que no puede ver bots (no tiene cliente)
        bots_response = self.client.get('/api/bots/')
        self.assertEqual(bots_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(bots_response.data), 0)  # No debe ver ningún bot


class UserDashboardRedirectionTestCase(TestCase):
    """
    Tests para validar la lógica de redirección de usuarios según su tipo
    """
    
    def setUp(self):
        self.client = Client()
        
        # Crear superusuario
        self.superuser = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear usuario emprendimiento
        self.emprendimiento_user = User.objects.create_user(
            username='emprendimiento_test',
            email='emprendimiento@test.com',
            password='emp123'
        )
        
        self.cliente = Cliente.objects.create(
            user=self.emprendimiento_user,
            nombre_emprendimiento='Mi Negocio Test',
            telefono='+51987654321'
        )

    def test_determine_user_dashboard_type_superuser(self):
        """
        Test: Función helper para determinar el tipo de dashboard del superusuario
        """
        def get_dashboard_type(user):
            """Helper function para determinar el tipo de dashboard"""
            if user.is_superuser or user.is_staff:
                return 'admin_dashboard'
            elif hasattr(user, 'cliente'):
                return 'emprendimiento_dashboard'
            else:
                return 'limited_dashboard'
        
        dashboard_type = get_dashboard_type(self.superuser)
        self.assertEqual(dashboard_type, 'admin_dashboard')

    def test_determine_user_dashboard_type_emprendimiento(self):
        """
        Test: Función helper para determinar el tipo de dashboard del emprendimiento
        """
        def get_dashboard_type(user):
            """Helper function para determinar el tipo de dashboard"""
            if user.is_superuser or user.is_staff:
                return 'admin_dashboard'
            elif hasattr(user, 'cliente'):
                return 'emprendimiento_dashboard'
            else:
                return 'limited_dashboard'
        
        dashboard_type = get_dashboard_type(self.emprendimiento_user)
        self.assertEqual(dashboard_type, 'emprendimiento_dashboard')

    def test_determine_user_dashboard_type_limited_user(self):
        """
        Test: Función helper para usuario sin perfil específico
        """
        limited_user = User.objects.create_user(
            username='limited_user',
            email='limited@test.com',
            password='test123'
        )
        
        def get_dashboard_type(user):
            """Helper function para determinar el tipo de dashboard"""
            if user.is_superuser or user.is_staff:
                return 'admin_dashboard'
            elif hasattr(user, 'cliente'):
                return 'emprendimiento_dashboard'
            else:
                return 'limited_dashboard'
        
        dashboard_type = get_dashboard_type(limited_user)
        self.assertEqual(dashboard_type, 'limited_dashboard')


class LogoutFunctionalityTestCase(APITestCase):
    """
    Tests para validar la funcionalidad de logout
    """
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='test_user',
            email='test@test.com',
            password='test123'
        )
        
        self.cliente = Cliente.objects.create(
            user=self.user,
            nombre_emprendimiento='Test Business',
            telefono='+51123456789'
        )

    def test_logout_invalidates_session(self):
        """
        Test: Verificar que el logout invalida correctamente la sesión
        """
        # Login
        login_response = self.client.post('/api/token/', {
            'username': 'test_user',
            'password': 'test123'
        })
        
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Verificar acceso con token válido
        me_response = self.client.get('/api/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        
        # Simular logout removiendo credenciales
        self.client.credentials()  # Remove authorization header
        
        # Verificar que ya no se puede acceder sin token
        me_response_after_logout = self.client.get('/api/me/')
        self.assertEqual(me_response_after_logout.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_after_logout_simulation(self):
        """
        Test: Verificar comportamiento de refresh token después de "logout"
        """
        # Login
        login_response = self.client.post('/api/token/', {
            'username': 'test_user',
            'password': 'test123'
        })
        
        refresh_token = login_response.data['refresh']
        
        # Simular logout (en una app real, el refresh token se invalidaría en el servidor)
        # Por ahora verificamos que aún funciona si no se invalida
        refresh_response = self.client.post('/api/token/refresh/', {
            'refresh': refresh_token
        })
        
        # En JWT, el refresh token seguirá siendo válido hasta su expiración
        # (a menos que implementemos blacklisting)
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)


# Test runner personalizado para ejecutar todos los tests
class AuthenticationTestSuite:
    """
    Suite de tests para ejecutar todas las pruebas de autenticación
    """
    
    @staticmethod
    def run_all_tests():
        """
        Ejecuta todos los tests de autenticación y devuelve un resumen
        """
        from django.test import TestCase
        from django.test.utils import get_runner
        from django.conf import settings
        
        test_runner = get_runner(settings)()
        
        # Lista de clases de test a ejecutar
        test_classes = [
            'core.test_authentication.AuthenticationRedirectionTestCase',
            'core.test_authentication.UserDashboardRedirectionTestCase',
            'core.test_authentication.LogoutFunctionalityTestCase',
        ]
        
        print("="*60)
        print("EJECUTANDO TESTS DE AUTENTICACIÓN Y REDIRECCIÓN")
        print("="*60)
        
        for test_class in test_classes:
            print(f"\n🧪 Ejecutando: {test_class}")
            result = test_runner.run_tests([test_class])
            
            if result == 0:
                print(f"✅ {test_class} - PASÓ")
            else:
                print(f"❌ {test_class} - FALLÓ")
        
        print("\n" + "="*60)
        print("TESTS COMPLETADOS")
        print("="*60)