"""Permissões compartilhadas entre os apps."""

from rest_framework import permissions


class EhDonoOuSomenteLeitura(permissions.BasePermission):
    """
    Leitura liberada; escrita só para o dono do objeto.

    O campo do dono é definido na view por `campo_dono` (padrão: "locador").
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        campo = getattr(view, "campo_dono", "locador")
        return getattr(obj, f"{campo}_id", None) == getattr(request.user, "id", None)
