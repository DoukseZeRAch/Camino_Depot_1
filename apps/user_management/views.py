from django.contrib.auth import authenticate
from django.urls import reverse_lazy
from rest_framework_simplejwt.views import TokenVerifyView
from django.utils import timezone
import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Users
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer
from .permissions import IsManager, IsAdmin, IsOwnerOrStaff
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import DetailView
from .forms import UserEditForm
from django.http.response import JsonResponse
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from django.views import View




logger = logging.getLogger(__name__)

class VerifyTokenView(TokenVerifyView):
    permission_classes = []
    
class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            logger.warning("Login attempt with missing credentials.")
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = authenticate(email=email, password=password)
            if user:
                # Mise à jour last_login
                user.last_login = timezone.now()
                user.save()

                # Création des tokens
                refresh = RefreshToken.for_user(user)
                
                # Log pour MANAGER et ADMIN
                if user.role in ['MANAGER', 'ADMIN']:
                    logger.info(f"Login successful for {user.role}: {user.email}")

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            
            logger.warning(f"Failed login attempt for email: {email}")
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response(
                {'error': 'An error occurred during login'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            logger.warning("Logout attempt without refresh token.")
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"Logout successful for user: {request.user.email}")
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout failed for user: {request.user.email}, Error: {e}")
            return Response(
                {'error': 'The token is invalid or expired'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class UserListView(generics.ListCreateAPIView):
    """
    GET: Liste tous les utilisateurs (ADMIN/MANAGER)
    POST: Crée un nouvel utilisateur (ADMIN seulement)
    """
    queryset = Users.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated & (IsAdmin | IsManager)]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        # Log pour les accès admin/manager
        logger.info(f"User list accessed by {self.request.user.email} ({self.request.user.role})")
        return super().get_queryset()
    
    def perform_create(self, serializer):
        # Seuls les admins peuvent créer des managers/admins
        role = serializer.validated_data.get('role', 'USER')
        if role in ['MANAGER', 'ADMIN'] and self.request.user.role != 'ADMIN':
            raise PermissionError("Only admins can create manager/admin users")
            
        user = serializer.save()
        logger.info(f"New user created by {self.request.user.email}: {user.email} ({user.role})")

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Voir les détails d'un utilisateur
    PUT/PATCH: Modifier un utilisateur
    DELETE: Désactiver un utilisateur
    """
    queryset = Users.objects.all()
    lookup_field = 'id'
    permission_classes = [IsAuthenticated & (IsOwnerOrStaff)]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def perform_update(self, serializer):
        # Vérifier les permissions pour modification de rôle
        old_role = self.get_object().role
        new_role = serializer.validated_data.get('role', old_role)
        
        if old_role != new_role:
            if self.request.user.role != 'ADMIN':
                raise PermissionError("Only admins can change user roles")
            logger.info(f"Role change by {self.request.user.email}: {self.get_object().email} from {old_role} to {new_role}")
        
        serializer.save()

    def perform_destroy(self, instance):
        # Soft delete - désactive l'utilisateur au lieu de le supprimer
        instance.is_active = False
        instance.save()
        logger.info(f"User deactivated by {self.request.user.email}: {instance.email}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Log pour les accès admin/manager aux données d'autres utilisateurs
        if request.user.role in ['ADMIN', 'MANAGER'] and request.user.id != instance.id:
            logger.info(f"User details accessed by {request.user.email} ({request.user.role}): {instance.email}")
        return super().retrieve(request, *args, **kwargs)
    

class AdminUserDetailView(LoginRequiredMixin, DetailView):
    model = Users
    template_name = 'admin_interface/users/detail.html'
    context_object_name = 'user'
    
    def get_queryset(self):
        if not (self.request.user.role in ['MANAGER', 'ADMIN']):
            return Users.objects.none()
        return Users.objects.all()
    
class AdminUserEditView(LoginRequiredMixin, UpdateView):
    model = Users
    template_name = 'admin_interface/users/edit.html'
    form_class = UserEditForm
    
    def get_success_url(self):
        return reverse_lazy('admin_user_detail', kwargs={'pk': self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

class ToggleUserStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role != 'ADMIN':
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            user = Users.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()
            return JsonResponse({
                'status': 'success',
                'is_active': user.is_active
            })
        except Users.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)