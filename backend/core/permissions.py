# core/permissions.py
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso custom para permitir solo a los dueños de un objeto o a un admin
    verlo o editarlo.
    """
    def has_object_permission(self, request, view, obj):
        # Admin tiene permiso siempre
        if request.user.is_staff:
            return True

        # Determina el 'dueño' basado en el modelo
        owner = None
        if hasattr(obj, 'cliente'): # Para el modelo Bot
            owner = obj.cliente
        elif hasattr(obj, 'bot'): # Para Servicio o Reserva
            owner = obj.bot.cliente

        # El usuario logueado debe tener un 'cliente' asociado
        if not hasattr(request.user, 'cliente'):
            return False

        # Compara si el dueño del objeto es el cliente logueado
        return owner == request.user.cliente