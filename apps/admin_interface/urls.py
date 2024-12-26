from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardView,
    QuestionListView,
    QuestionDetailView,
    UserListView,
    UserDetailView,
    ResponseListView,
    ResponseDetailView,
    RoadmapListView,
    RoadmapDetailView,
    AIConfigView,
    AdminResponsesViewSet,
    AdminRoadmapsViewSet,
    AdminLoginView
)
app_name = 'admin_interface'
# Router pour les APIs REST
router = DefaultRouter()
router.register(r'responses', AdminResponsesViewSet, basename="admin-responses")
router.register(r'roadmaps', AdminRoadmapsViewSet, basename="admin-roadmaps")

urlpatterns = [
    # Routes pour les pages HTML
    path('login/', AdminLoginView.as_view(), name='login'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('questions/', QuestionListView.as_view(), name="questions_list"),
    path('questions/<int:pk>/', QuestionDetailView.as_view(), name="question_detail"),
    path('users/', UserListView.as_view(), name="users_list"),
    path('users/<int:pk>/', UserDetailView.as_view(), name="user_detail"),
    path('responses/', ResponseListView.as_view(), name="responses_list"),
    path('responses/<int:pk>/', ResponseDetailView.as_view(), name="response_detail"),
    path('roadmaps/', RoadmapListView.as_view(), name="roadmaps_list"),
    path('roadmaps/<int:pk>/', RoadmapDetailView.as_view(), name="roadmap_detail"),
    path('ai-config/', AIConfigView.as_view(), name="ai_config"),

    # Inclure les routes du router pour les APIs REST
    path('api/', include(router.urls)),
]
