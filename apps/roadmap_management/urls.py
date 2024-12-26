from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GlobalAIConfigurationView, RoadmapViewSet, AdminRoadmapListView, AdminRoadmapDetailView,
    RegenerateRoadmapView, ArchiveRoadmapView, update_prompt, fetch_questions_and_responses
)



router = DefaultRouter()
router.register(r'roadmaps', RoadmapViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('admin/roadmaps/', AdminRoadmapListView.as_view(), name='admin_roadmaps_list'),
    path('admin/roadmaps/<str:pk>/', AdminRoadmapDetailView.as_view(), name='admin_roadmap_detail'),
    path('admin/roadmaps/<str:pk>/regenerate/', RegenerateRoadmapView.as_view(), name='admin_roadmap_regenerate'),
    path('admin/roadmaps/<str:pk>/archive/', ArchiveRoadmapView.as_view(), name='admin_roadmap_archive'),
    path('ai-config/', GlobalAIConfigurationView.as_view(), name='global_ai_config'),
    path('update-prompt/', update_prompt, name='update_prompt'),
    path('roadmap/<int:roadmap_id>/questions-responses/', fetch_questions_and_responses, name='fetch_questions_and_responses'),
]