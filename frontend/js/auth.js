// js/auth.js
const loginForm = document.getElementById("login-form");
const logoutBtn = document.getElementById("logout-btn");

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const errorMsg = document.getElementById("error-msg");
        errorMsg.textContent = '';

        try {
            // Llama a la API de Django (DRF SimpleJWT)
            const response = await fetch('http://127.0.0.1:8000/api/token/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) throw new Error('Usuario o contraseña incorrecta');

            const data = await response.json();

            // Guarda los Tokens
            localStorage.setItem('accessToken', data.access);
            localStorage.setItem('refreshToken', data.refresh);

            window.location.href = 'index.html'; // Redirige al panel

        } catch (error) {
            errorMsg.textContent = error.message;
        }
    });
}

if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
}

// Función global de logout
function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = 'login.html';
}