// js/api.js
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Función principal para peticiones autenticadas
async function fetchWithAuth(endpoint, options = {}) {
    const token = localStorage.getItem('accessToken');

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/${endpoint}`, { ...options, headers });

    if (response.status === 401) {
        // Token inválido o expirado.
        // Intenta refrescar el token.
        const newAccessToken = await refreshToken();
        if (newAccessToken) {
            // Si el refresh funciona, reintenta la petición original
            headers['Authorization'] = `Bearer ${newAccessToken}`;
            const retryResponse = await fetch(`${API_BASE_URL}/${endpoint}`, { ...options, headers });
            if (retryResponse.status === 401) {
                // Si el refresh también falla, desloguear.
                logout();
                return retryResponse;
            }
            return retryResponse;
        } else {
            logout(); // Desloguea si el refresh falla
        }
    }

    return response;
}

// Intenta refrescar el token
async function refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) return null;

    try {
        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: refreshToken })
        });

        if (!response.ok) throw new Error('Refresh token fallido');

        const data = await response.json();
        localStorage.setItem('accessToken', data.access);
        return data.access;
    } catch (error) {
        console.error("Error al refrescar token:", error);
        return null;
    }
}