# apps/analytics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('questions/', views.QuestionsAnalyticsView.as_view(), name='questions-analytics'),
    path('responses/', views.ResponsesAnalyticsView.as_view(), name='responses-analytics'),
    path('roadmaps/', views.RoadmapsAnalyticsView.as_view(), name='roadmaps-analytics'),
    path('dashboard/', views.DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('admin/dashboard/analytics/', views.AdminDashboardView.as_view(), name='admin_dashboard_analytics'),
    
]