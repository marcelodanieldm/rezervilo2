// ===== CONFIGURACIÓN Y VARIABLES GLOBALES =====
const API_BASE_URL = 'http://127.0.0.1:8000/api/';

// Estado global de la aplicación
const appState = {
    currentUser: null,
    currentSection: 'dashboard',
    bots: [],
    reservations: [],
    services: [],
    currentDate: new Date()
};

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    const accessToken = localStorage.getItem('accessToken');
    
    if (!accessToken) {
        showLogin();
        return;
    }

    try {
        // Verificar si el token es válido
        const userData = await fetchUserData();
        if (userData) {
            appState.currentUser = userData;
            showDashboard();
            await loadInitialData();
            setupEventListeners();
        } else {
            showLogin();
        }
    } catch (error) {
        console.error('Error al inicializar la aplicación:', error);
        showLogin();
    }
}

// ===== FUNCIONES DE AUTENTICACIÓN =====
function showLogin() {
    document.getElementById('login-container').classList.remove('hidden');
    document.getElementById('dashboard-container').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('login-container').classList.add('hidden');
    document.getElementById('dashboard-container').classList.remove('hidden');
    
    if (appState.currentUser) {
        document.getElementById('user-name').textContent = 
            appState.currentUser.cliente?.nombre_emprendimiento || 
            appState.currentUser.user?.username || 
            'Usuario';
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}token/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('accessToken', data.access);
            localStorage.setItem('refreshToken', data.refresh);
            
            const userData = await fetchUserData();
            appState.currentUser = userData;
            
            showDashboard();
            await loadInitialData();
            setupEventListeners();
            
            errorDiv.classList.add('hidden');
        } else {
            const errorData = await response.json();
            showError(errorDiv, errorData.detail || 'Usuario o contraseña incorrectos');
        }
    } catch (error) {
        console.error('Error en login:', error);
        showError(errorDiv, 'Error de conexión. Intenta nuevamente.');
    } finally {
        showLoading(false);
    }
}

function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    appState.currentUser = null;
    appState.bots = [];
    appState.reservations = [];
    showLogin();
}

// ===== FUNCIONES DE API =====
async function fetchWithAuth(endpoint, options = {}) {
    const token = localStorage.getItem('accessToken');
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (response.status === 401) {
        // Token expirado, intentar refrescar
        const refreshed = await refreshToken();
        if (refreshed) {
            // Reintentar la petición original
            return fetchWithAuth(endpoint, options);
        } else {
            logout();
            throw new Error('Sesión expirada');
        }
    }
    
    return response;
}

async function refreshToken() {
    const refreshTokenValue = localStorage.getItem('refreshToken');
    if (!refreshTokenValue) return false;
    
    try {
        const response = await fetch(`${API_BASE_URL}token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: refreshTokenValue })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('accessToken', data.access);
            return true;
        }
    } catch (error) {
        console.error('Error al refrescar token:', error);
    }
    
    return false;
}

async function fetchUserData() {
    try {
        const response = await fetchWithAuth('me/');
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Error al obtener datos del usuario:', error);
    }
    return null;
}

// ===== CARGA INICIAL DE DATOS =====
async function loadInitialData() {
    try {
        await Promise.all([
            loadBots(),
            loadReservations(),
            loadServices(),
            updateDashboardStats()
        ]);
        
        // Renderizar secciones iniciales
        renderBotsSection();
        renderCalendar();
        renderReservationsTable();
    } catch (error) {
        console.error('Error al cargar datos iniciales:', error);
    }
}

async function loadBots() {
    try {
        const response = await fetchWithAuth('bots/');
        if (response.ok) {
            appState.bots = await response.json();
        }
    } catch (error) {
        console.error('Error al cargar bots:', error);
    }
}

async function loadReservations() {
    try {
        const response = await fetchWithAuth('reservas/');
        if (response.ok) {
            appState.reservations = await response.json();
        }
    } catch (error) {
        console.error('Error al cargar reservas:', error);
    }
}

async function loadServices() {
    try {
        const response = await fetchWithAuth('servicios/');
        if (response.ok) {
            appState.services = await response.json();
        }
    } catch (error) {
        console.error('Error al cargar servicios:', error);
    }
}

// ===== NAVEGACIÓN =====
function switchSection(sectionName) {
    // Ocultar todas las secciones
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Mostrar la sección seleccionada
    document.getElementById(`${sectionName}-section`).classList.add('active');
    
    // Actualizar navegación
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    document.querySelector(`[data-section="${sectionName}"]`).parentElement.classList.add('active');
    
    appState.currentSection = sectionName;
    
    // Cargar contenido específico de la sección
    switch (sectionName) {
        case 'dashboard':
            updateDashboardStats();
            break;
        case 'bots':
            renderBotsSection();
            break;
        case 'calendar':
            renderCalendar();
            break;
        case 'reservations':
            renderReservationsTable();
            break;
    }
}

// ===== DASHBOARD =====
async function updateDashboardStats() {
    try {
        const activeBots = appState.bots.filter(bot => bot.activo).length;
        const activeReservations = appState.reservations.filter(r => r.estado !== 'Cancelada').length;
        const pendingReservations = appState.reservations.filter(r => r.estado === 'Pendiente').length;
        
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        const monthlyBookings = appState.reservations.filter(r => {
            const reservationDate = new Date(r.fecha_hora_inicio);
            return reservationDate.getMonth() === currentMonth && 
                   reservationDate.getFullYear() === currentYear;
        }).length;
        
        document.getElementById('total-bots').textContent = activeBots;
        document.getElementById('total-reservations').textContent = activeReservations;
        document.getElementById('pending-reservations').textContent = pendingReservations;
        document.getElementById('monthly-bookings').textContent = monthlyBookings;
        
        renderUpcomingReservations();
        renderBotStatus();
        
    } catch (error) {
        console.error('Error al actualizar estadísticas:', error);
    }
}

function renderUpcomingReservations() {
    const container = document.getElementById('upcoming-reservations');
    const now = new Date();
    
    const upcoming = appState.reservations
        .filter(r => new Date(r.fecha_hora_inicio) > now && r.estado !== 'Cancelada')
        .sort((a, b) => new Date(a.fecha_hora_inicio) - new Date(b.fecha_hora_inicio))
        .slice(0, 5);
    
    if (upcoming.length === 0) {
        container.innerHTML = '<p class="text-secondary">No hay reservas próximas</p>';
        return;
    }
    
    container.innerHTML = upcoming.map(reservation => `
        <div class="reservation-item" style="padding: 1rem; border-left: 4px solid var(--primary-color); margin-bottom: 0.5rem; background: var(--bg-secondary); border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${reservation.servicio_nombre || 'Servicio'}</strong>
                    <br>
                    <small style="color: var(--text-secondary);">
                        ${formatDate(reservation.fecha_hora_inicio)} - ${formatTime(reservation.fecha_hora_inicio)}
                    </small>
                </div>
                <span class="status-badge status-${reservation.estado.toLowerCase()}">${reservation.estado}</span>
            </div>
        </div>
    `).join('');
}

function renderBotStatus() {
    const container = document.getElementById('bot-status');
    
    if (appState.bots.length === 0) {
        container.innerHTML = '<p class="text-secondary">No hay bots configurados</p>';
        return;
    }
    
    container.innerHTML = appState.bots.map(bot => `
        <div class="bot-status-item" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; margin-bottom: 0.5rem; background: var(--bg-secondary); border-radius: 4px;">
            <div>
                <strong>${bot.nombre}</strong>
                <br>
                <small style="color: var(--text-secondary);">${bot.descripcion || 'Sin descripción'}</small>
            </div>
            <span class="bot-status ${bot.activo ? 'active' : 'inactive'}">
                ${bot.activo ? 'Activo' : 'Inactivo'}
            </span>
        </div>
    `).join('');
}

// ===== GESTIÓN DE BOTS =====
function renderBotsSection() {
    const container = document.getElementById('bots-grid');
    
    if (appState.bots.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                <i class="fas fa-robot" style="font-size: 4rem; color: var(--text-light); margin-bottom: 1rem;"></i>
                <h3 style="color: var(--text-secondary); margin-bottom: 0.5rem;">No hay bots configurados</h3>
                <p style="color: var(--text-light);">Crea tu primer bot para comenzar a gestionar reservas</p>
                <button class="primary-btn mt-2" onclick="openBotModal()">
                    <i class="fas fa-plus"></i> Crear Primer Bot
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = appState.bots.map(bot => `
        <div class="bot-card">
            <div class="bot-header">
                <div class="bot-info">
                    <h4>${bot.nombre}</h4>
                    <p>${bot.descripcion || 'Sin descripción disponible'}</p>
                </div>
                <span class="bot-status ${bot.activo ? 'active' : 'inactive'}">
                    ${bot.activo ? 'Activo' : 'Inactivo'}
                </span>
            </div>
            <div class="bot-actions">
                <button class="btn-small btn-edit" onclick="editBot(${bot.id})">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="btn-small btn-delete" onclick="deleteBot(${bot.id})">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
        </div>
    `).join('');
}

function openBotModal(botId = null) {
    const modal = document.getElementById('bot-modal');
    const title = document.getElementById('bot-modal-title');
    const form = document.getElementById('bot-form');
    
    form.reset();
    
    if (botId) {
        const bot = appState.bots.find(b => b.id === botId);
        if (bot) {
            title.textContent = 'Editar Bot';
            document.getElementById('bot-name').value = bot.nombre;
            document.getElementById('bot-description').value = bot.descripcion || '';
            document.getElementById('bot-active').value = bot.activo.toString();
            form.dataset.botId = botId;
        }
    } else {
        title.textContent = 'Agregar Bot';
        delete form.dataset.botId;
    }
    
    showModal(modal);
}

function editBot(botId) {
    openBotModal(botId);
}

async function deleteBot(botId) {
    if (!confirm('¿Estás seguro de que deseas eliminar este bot?')) return;
    
    try {
        showLoading(true);
        const response = await fetchWithAuth(`bots/${botId}/`, { method: 'DELETE' });
        
        if (response.ok) {
            await loadBots();
            renderBotsSection();
            updateDashboardStats();
            showNotification('Bot eliminado exitosamente', 'success');
        } else {
            showNotification('Error al eliminar el bot', 'error');
        }
    } catch (error) {
        console.error('Error al eliminar bot:', error);
        showNotification('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleBotForm(event) {
    event.preventDefault();
    
    const form = event.target;
    const botId = form.dataset.botId;
    const isEdit = !!botId;
    
    const botData = {
        nombre: document.getElementById('bot-name').value,
        descripcion: document.getElementById('bot-description').value,
        activo: document.getElementById('bot-active').value === 'true'
    };
    
    try {
        showLoading(true);
        
        const url = isEdit ? `bots/${botId}/` : 'bots/';
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetchWithAuth(url, {
            method: method,
            body: JSON.stringify(botData)
        });
        
        if (response.ok) {
            hideModal(document.getElementById('bot-modal'));
            await loadBots();
            renderBotsSection();
            updateDashboardStats();
            showNotification(
                isEdit ? 'Bot actualizado exitosamente' : 'Bot creado exitosamente', 
                'success'
            );
        } else {
            const errorData = await response.json();
            showNotification('Error al guardar el bot: ' + (errorData.detail || 'Error desconocido'), 'error');
        }
    } catch (error) {
        console.error('Error al guardar bot:', error);
        showNotification('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

// ===== CALENDARIO =====
function renderCalendar() {
    const calendarContainer = document.getElementById('calendar');
    const currentMonthYear = document.getElementById('current-month-year');
    
    const year = appState.currentDate.getFullYear();
    const month = appState.currentDate.getMonth();
    
    currentMonthYear.textContent = new Intl.DateTimeFormat('es-ES', {
        month: 'long',
        year: 'numeric'
    }).format(appState.currentDate);
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    let calendarHTML = `
        <table class="calendar">
            <thead>
                <tr>
                    <th>Dom</th>
                    <th>Lun</th>
                    <th>Mar</th>
                    <th>Mié</th>
                    <th>Jue</th>
                    <th>Vie</th>
                    <th>Sáb</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let currentWeekDate = new Date(startDate);
    
    for (let week = 0; week < 6; week++) {
        calendarHTML += '<tr>';
        
        for (let day = 0; day < 7; day++) {
            const cellDate = new Date(currentWeekDate);
            const isCurrentMonth = cellDate.getMonth() === month;
            const isToday = isDateToday(cellDate);
            const hasEvents = hasReservationsOnDate(cellDate);
            
            let cellClass = '';
            if (isToday) cellClass += ' today';
            if (hasEvents) cellClass += ' has-events';
            if (!isCurrentMonth) cellClass += ' other-month';
            
            calendarHTML += `
                <td class="${cellClass}" data-date="${cellDate.toISOString().split('T')[0]}" onclick="selectCalendarDate('${cellDate.toISOString().split('T')[0]}')">
                    ${cellDate.getDate()}
                    ${hasEvents ? '<div class="event-indicator"></div>' : ''}
                </td>
            `;
            
            currentWeekDate.setDate(currentWeekDate.getDate() + 1);
        }
        
        calendarHTML += '</tr>';
    }
    
    calendarHTML += '</tbody></table>';
    
    calendarContainer.innerHTML = calendarHTML;
}

function navigateMonth(direction) {
    appState.currentDate.setMonth(appState.currentDate.getMonth() + direction);
    renderCalendar();
}

function hasReservationsOnDate(date) {
    const dateString = date.toISOString().split('T')[0];
    return appState.reservations.some(reservation => {
        const reservationDate = new Date(reservation.fecha_hora_inicio).toISOString().split('T')[0];
        return reservationDate === dateString && reservation.estado !== 'Cancelada';
    });
}

function selectCalendarDate(dateString) {
    const selectedDate = new Date(dateString);
    const reservationsOnDate = appState.reservations.filter(reservation => {
        const reservationDate = new Date(reservation.fecha_hora_inicio).toISOString().split('T')[0];
        return reservationDate === dateString;
    });
    
    if (reservationsOnDate.length > 0) {
        // Mostrar reservas del día
        showDayReservations(selectedDate, reservationsOnDate);
    } else {
        // Abrir modal para nueva reserva con fecha preseleccionada
        openReservationModal(dateString);
    }
}

function showDayReservations(date, reservations) {
    const dateStr = new Intl.DateTimeFormat('es-ES', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(date);
    
    const reservationsList = reservations.map(r => `
        <div class="reservation-item" style="padding: 1rem; margin-bottom: 0.5rem; background: var(--bg-secondary); border-radius: 4px; border-left: 4px solid var(--primary-color);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${r.servicio_nombre || 'Servicio'}</strong>
                    <br>
                    <small>${formatTime(r.fecha_hora_inicio)} - ${formatTime(r.fecha_hora_fin)}</small>
                    <br>
                    <small style="color: var(--text-secondary);">Bot: ${r.bot_nombre || 'N/A'}</small>
                </div>
                <span class="status-badge status-${r.estado.toLowerCase()}">${r.estado}</span>
            </div>
        </div>
    `).join('');
    
    alert(`Reservas para ${dateStr}:\n\n${reservations.map(r => 
        `${formatTime(r.fecha_hora_inicio)} - ${r.servicio_nombre} (${r.estado})`
    ).join('\n')}`);
}

// ===== GESTIÓN DE RESERVAS =====
function renderReservationsTable() {
    const tbody = document.getElementById('reservations-tbody');
    
    if (appState.reservations.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                    <i class="fas fa-calendar-times" style="font-size: 3rem; margin-bottom: 1rem; display: block;"></i>
                    No hay reservas registradas
                </td>
            </tr>
        `;
        return;
    }
    
    const sortedReservations = [...appState.reservations].sort((a, b) => 
        new Date(b.fecha_hora_inicio) - new Date(a.fecha_hora_inicio)
    );
    
    tbody.innerHTML = sortedReservations.map(reservation => `
        <tr>
            <td>${formatDate(reservation.fecha_hora_inicio)}</td>
            <td>${formatTime(reservation.fecha_hora_inicio)}</td>
            <td>${reservation.servicio_nombre || 'N/A'}</td>
            <td>${reservation.bot_nombre || 'N/A'}</td>
            <td><span class="status-badge status-${reservation.estado.toLowerCase()}">${reservation.estado}</span></td>
            <td>
                <button class="btn-small btn-edit" onclick="editReservation(${reservation.id})" style="margin-right: 0.5rem;">
                    <i class="fas fa-edit"></i>
                </button>
                ${reservation.estado !== 'Cancelada' ? `
                    <button class="btn-small btn-delete" onclick="cancelReservation(${reservation.id})">
                        <i class="fas fa-times"></i>
                    </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

function openReservationModal(preselectedDate = null) {
    const modal = document.getElementById('reservation-modal');
    const form = document.getElementById('reservation-form');
    
    form.reset();
    
    if (preselectedDate) {
        document.getElementById('reservation-date').value = preselectedDate;
    }
    
    // Llenar select de servicios
    const serviceSelect = document.getElementById('reservation-service');
    serviceSelect.innerHTML = '<option value="">Seleccionar servicio...</option>' +
        appState.services.map(service => 
            `<option value="${service.id}">${service.nombre} - $${service.precio}</option>`
        ).join('');
    
    // Llenar select de bots
    const botSelect = document.getElementById('reservation-bot');
    const activeBots = appState.bots.filter(bot => bot.activo);
    botSelect.innerHTML = '<option value="">Seleccionar bot...</option>' +
        activeBots.map(bot => 
            `<option value="${bot.id}">${bot.nombre}</option>`
        ).join('');
    
    showModal(modal);
}

async function handleReservationForm(event) {
    event.preventDefault();
    
    const reservationData = {
        fecha: document.getElementById('reservation-date').value,
        hora: document.getElementById('reservation-time').value,
        servicio: document.getElementById('reservation-service').value,
        bot: document.getElementById('reservation-bot').value,
        notas: document.getElementById('reservation-notes').value
    };
    
    try {
        showLoading(true);
        
        const response = await fetchWithAuth('reservas/', {
            method: 'POST',
            body: JSON.stringify(reservationData)
        });
        
        if (response.ok) {
            hideModal(document.getElementById('reservation-modal'));
            await loadReservations();
            renderReservationsTable();
            renderCalendar();
            updateDashboardStats();
            showNotification('Reserva creada exitosamente', 'success');
        } else {
            const errorData = await response.json();
            showNotification('Error al crear la reserva: ' + (errorData.detail || 'Error desconocido'), 'error');
        }
    } catch (error) {
        console.error('Error al crear reserva:', error);
        showNotification('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

async function cancelReservation(reservationId) {
    if (!confirm('¿Estás seguro de que deseas cancelar esta reserva?')) return;
    
    try {
        showLoading(true);
        const response = await fetchWithAuth(`reservas/${reservationId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ estado: 'Cancelada' })
        });
        
        if (response.ok) {
            await loadReservations();
            renderReservationsTable();
            renderCalendar();
            updateDashboardStats();
            showNotification('Reserva cancelada exitosamente', 'success');
        } else {
            showNotification('Error al cancelar la reserva', 'error');
        }
    } catch (error) {
        console.error('Error al cancelar reserva:', error);
        showNotification('Error de conexión', 'error');
    } finally {
        showLoading(false);
    }
}

// ===== FUNCIONES DE UI =====
function showModal(modal) {
    modal.classList.remove('hidden');
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function hideModal(modal) {
    modal.classList.remove('show');
    setTimeout(() => {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }, 200);
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        max-width: 400px;
    `;
    
    // Colores según el tipo
    const colors = {
        success: '#22c55e',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    
    notification.style.backgroundColor = colors[type] || colors.info;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Mostrar notificación
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Ocultar automáticamente
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

function showError(element, message) {
    element.textContent = message;
    element.classList.remove('hidden');
}

// ===== FUNCIONES DE UTILIDAD =====
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    }).format(date);
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-ES', {
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function isDateToday(date) {
    const today = new Date();
    return date.toDateString() === today.toDateString();
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.currentTarget.dataset.section;
            switchSection(section);
        });
    });
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Bots section
    document.getElementById('add-bot-btn').addEventListener('click', () => openBotModal());
    document.getElementById('bot-form').addEventListener('submit', handleBotForm);
    
    // Calendar navigation
    document.getElementById('prev-month').addEventListener('click', () => navigateMonth(-1));
    document.getElementById('next-month').addEventListener('click', () => navigateMonth(1));
    
    // Reservations
    document.getElementById('new-reservation-btn').addEventListener('click', () => openReservationModal());
    document.getElementById('reservation-form').addEventListener('submit', handleReservationForm);
    
    // Modal close buttons
    document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            hideModal(modal);
        });
    });
    
    // Close modals on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal(modal);
            }
        });
    });
}