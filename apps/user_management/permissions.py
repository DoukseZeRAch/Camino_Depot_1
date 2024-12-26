# apps/user_management/permissions.py
from rest_framework import permissions

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'MANAGER'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permission pour permettre aux utilisateurs de voir uniquement leurs propres données,
    tandis que les managers et admins peuvent tout voir
    """
    def has_object_permission(self, request, view, obj):
        # Les admins et managers peuvent tout voir
        if request.user.role in ['ADMIN', 'MANAGER']:
            return True
            
        # Les utilisateurs peuvent voir uniquement leurs propres données
        return obj.id == request.user.id

class HasRoadmapAccess(permissions.BasePermission):
    """
    Permission pour l'accès aux roadmaps
    """
    def has_object_permission(self, request, view, obj):
        # Les admins et managers peuvent voir toutes les roadmaps
        if request.user.role in ['ADMIN', 'MANAGER']:
            return True
            
        # Les utilisateurs peuvent voir uniquement leurs propres roadmaps
        return obj.user_id == request.user.id