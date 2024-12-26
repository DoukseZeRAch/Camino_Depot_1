# backend/apps/response_management/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminResponseDetailView, AdminResponseListView, ResponsesViewSet, ResponsesBackupViewSet, SaveTemporaryResponse, SubmitFinalResponses
from apps.response_management.views import SaveTemporaryResponse



router = DefaultRouter()
router.register(r'responses', ResponsesViewSet)
router.register(r'responses-backup', ResponsesBackupViewSet)

urlpatterns = [
   path('', include(router.urls)),
   path('save-temporary-response/', SaveTemporaryResponse.as_view(), name='save_temporary_response'),
   path('submit-final-responses/', SubmitFinalResponses.as_view(), name='submit_final_responses'),
   path('admin/responses/', AdminResponseListView.as_view(), name='admin_responses_list'),
   path('admin/responses/<str:pk>/', AdminResponseDetailView.as_view(), name='admin_response_detail'),
]