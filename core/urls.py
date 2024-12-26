"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from apps.admin_interface.views import AdminLoginView  # Ajoutez cette ligne
from django.contrib.auth import views as auth_views

def redirect_to_dashboard(request):
    return redirect('admin_interface:dashboard')    # Redirige vers la vue dashboard de admin_interface

urlpatterns = [
    path('', redirect_to_dashboard, name='root'),
    path("admin/", admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='admin_interface/login.html'), name='login'),  # Modifiez cette ligne
    path('api/auth/', include('apps.user_management.urls')),
    path('api/', include('apps.question_handling.urls')),
    path('api/', include('apps.response_management.urls')), 
    path('__debug__/', include('debug_toolbar.urls')),
    path('analytics/', include('apps.analytics.urls')),  # Ajout des URLs analytics
    path('api/', include('apps.roadmap_management.urls')),  # Ajout des URLs roadmap si pas déjà incluses
    path('dashboard/', include('apps.admin_interface.urls', namespace='admin_interface')),
]