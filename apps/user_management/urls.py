# apps/user_management/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, VerifyTokenView, UserListView, 
    UserDetailView, AdminUserDetailView, AdminUserEditView,
    ToggleUserStatusView
)

urlpatterns = [
    # Existing routes
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', VerifyTokenView.as_view(), name='token_verify'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:id>/', UserDetailView.as_view(), name='user-detail'),
    
    # New admin routes
    path('admin/users/', AdminUserDetailView.as_view(), name='admin_users_list'),
    path('admin/users/<str:pk>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<str:pk>/edit/', AdminUserEditView.as_view(), name='admin_user_edit'),
    path('admin/users/<str:pk>/toggle-status/', ToggleUserStatusView.as_view(), name='admin_user_toggle_status'),
]