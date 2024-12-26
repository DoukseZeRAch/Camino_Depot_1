# backend/apps/question_handling/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuestionsViewSet

router = DefaultRouter()
router.register(r'questions', QuestionsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]