// js/dashboard-router.js
// Router principal para manejar redirección según tipo de usuario

const API_BASE_URL = 'http://127.0.0.1:8000/api/';

// Estado global del router
const dashboardRouter = {
    currentUser: null,
    dashboardType: null,
    isAuthenticated: false
};

// Configuración de rutas según tipo de usuario
const DASHBOARD_ROUTES = {
    'admin_dashboard': 'admin-dashboard.html',
    'emprendimiento_dashboard': 'emprendimiento-dashboard.html',
    'limited_dashboard': 'limited-dashboard.html',
    'login': 'login.html'
};

/**
 * Inicializa el router y determina la redirección apropiada
 */
async function initializeDashboardRouter() {
    console.log('🔄 Inicializando Dashboard Router...');
    
    const accessToken = localStorage.getItem('accessToken');
    
    if (!accessToken) {
        console.log('❌ No hay token, redirigiendo a login');
        redirectToLogin();
        return;
    }

    try {
        // Verificar token y obtener configuración del dashboard
        const dashboardConfig = await getDashboardConfiguration();
        
        if (dashboardConfig) {
            console.log('✅ Token válido, configurando dashboard:', dashboardConfig.dashboard_type);
            
            dashboardRouter.currentUser = dashboardConfig.user_info;
            dashboardRouter.dashboardType = dashboardConfig.dashboard_type;
            dashboardRouter.isAuthenticated = true;
            
            // Redirigir al dashboard apropiado si no estamos ya en él
            await redirectToDashboard(dashboardConfig.dashboard_type);
            
        } else {
            console.log('❌ Token inválido, redirigiendo a login');
            redirectToLogin();
        }
    } catch (error) {
        console.error('Error al inicializar router:', error);
        redirectToLogin();
    }
}

/**
 * Obtiene la configuración del dashboard desde el servidor
 */
async function getDashboardConfiguration() {
    try {
        const response = await fetchWithAuthRouter('/api/dashboard/config/');
        
        if (response.ok) {
            return await response.json();
        } else if (response.status === 401) {
            // Token expirado, intentar refrescar
            const refreshed = await refreshAuthToken();
            if (refreshed) {
                // Reintentar
                const retryResponse = await fetchWithAuthRouter('/api/dashboard/config/');
                if (retryResponse.ok) {
                    return await retryResponse.json();
                }
            }
        }
        
        return null;
    } catch (error) {
        console.error('Error al obtener configuración del dashboard:', error);
        return null;
    }
}

/**
 * Redirige al dashboard apropiado según el tipo de usuario
 */
async function redirectToDashboard(dashboardType) {
    const currentPage = window.location.pathname.split('/').pop();
    const targetPage = DASHBOARD_ROUTES[dashboardType];
    
    console.log(`📍 Página actual: ${currentPage}, Objetivo: ${targetPage}`);
    
    // Si ya estamos en la página correcta, no redirigir
    if (currentPage === targetPage) {
        console.log('✅ Ya estamos en el dashboard correcto');
        return;
    }
    
    // Verificar si la página actual es de login
    if (currentPage === 'login.html' || currentPage === '') {
        console.log(`🔄 Redirigiendo desde login a: ${targetPage}`);
        window.location.href = targetPage;
        return;
    }
    
    // Si estamos en un dashboard incorrecto, redirigir al correcto
    if (Object.values(DASHBOARD_ROUTES).includes(currentPage) && currentPage !== targetPage) {
        console.log(`🔄 Redirigiendo de dashboard incorrecto ${currentPage} a ${targetPage}`);
        window.location.href = targetPage;
        return;
    }
}

/**
 * Redirige a la página de login
 */
function redirectToLogin() {
    const currentPage = window.location.pathname.split('/').pop();
    
    if (currentPage !== 'login.html') {
        console.log('🔄 Redirigiendo a login');
        window.location.href = DASHBOARD_ROUTES.login;
    }
}

/**
 * Maneja el login y determina la redirección apropiada
 */
async function handleDashboardLogin(username, password) {
    try {
        console.log('🔐 Intentando login...');
        
        const response = await fetch(`${API_BASE_URL}dashboard/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            
            // Guardar tokens
            localStorage.setItem('accessToken', data.access);
            localStorage.setItem('refreshToken', data.refresh);
            
            // Actualizar estado del router
            dashboardRouter.currentUser = data.user_info;
            dashboardRouter.dashboardType = data.dashboard_type;
            dashboardRouter.isAuthenticated = true;
            
            console.log('✅ Login exitoso:', data.dashboard_type);
            
            // Redirigir al dashboard apropiado
            await redirectToDashboard(data.dashboard_type);
            
            return { success: true, dashboardType: data.dashboard_type };
        } else {
            const errorData = await response.json();
            console.log('❌ Login fallido:', errorData.error);
            return { success: false, error: errorData.error };
        }
    } catch (error) {
        console.error('Error en login:', error);
        return { success: false, error: 'Error de conexión' };
    }
}

/**
 * Maneja el logout universal
 */
async function handleDashboardLogout() {
    try {
        console.log('🚪 Cerrando sesión...');
        
        // Intentar logout en el servidor
        await fetchWithAuthRouter('/api/dashboard/logout/', { method: 'POST' });
        
        // Limpiar estado local
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        
        dashboardRouter.currentUser = null;
        dashboardRouter.dashboardType = null;
        dashboardRouter.isAuthenticated = false;
        
        console.log('✅ Logout exitoso');
        
        // Redirigir a login
        redirectToLogin();
        
    } catch (error) {
        console.error('Error en logout:', error);
        // Aún así limpiar el estado local
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        redirectToLogin();
    }
}

/**
 * Fetch con autenticación para el router
 */
async function fetchWithAuthRouter(endpoint, options = {}) {
    const token = localStorage.getItem('accessToken');
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint.replace('/api/', '')}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    
    return fetch(url, { ...defaultOptions, ...options });
}

/**
 * Refresca el token de autenticación
 */
async function refreshAuthToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) return false;
    
    try {
        console.log('🔄 Refrescando token...');
        
        const response = await fetch(`${API_BASE_URL}token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: refreshToken })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('accessToken', data.access);
            console.log('✅ Token refrescado exitosamente');
            return true;
        }
    } catch (error) {
        console.error('Error al refrescar token:', error);
    }
    
    return false;
}

/**
 * Obtiene información del usuario actual
 */
function getCurrentUser() {
    return dashboardRouter.currentUser;
}

/**
 * Verifica si el usuario está autenticado
 */
function isAuthenticated() {
    return dashboardRouter.isAuthenticated && localStorage.getItem('accessToken');
}

/**
 * Obtiene el tipo de dashboard actual
 */
function getDashboardType() {
    return dashboardRouter.dashboardType;
}

/**
 * Verifica si el usuario es superusuario
 */
function isSuperUser() {
    return dashboardRouter.currentUser?.is_superuser || false;
}

/**
 * Verifica si el usuario es staff
 */
function isStaffUser() {
    return dashboardRouter.currentUser?.is_staff || false;
}

/**
 * Verifica si el usuario tiene perfil de cliente
 */
function hasClientProfile() {
    return dashboardRouter.currentUser?.has_cliente_profile || false;
}

// Funciones para tests
window.dashboardRouter = dashboardRouter;
window.initializeDashboardRouter = initializeDashboardRouter;
window.handleDashboardLogin = handleDashboardLogin;
window.handleDashboardLogout = handleDashboardLogout;
window.getCurrentUser = getCurrentUser;
window.isAuthenticated = isAuthenticated;
window.getDashboardType = getDashboardType;
window.isSuperUser = isSuperUser;
window.isStaffUser = isStaffUser;
window.hasClientProfile = hasClientProfile;

console.log('📁 Dashboard Router cargado');