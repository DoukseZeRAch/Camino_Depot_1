from django.http import JsonResponse
from rest_framework.viewsets import ModelViewSet
from django.views.generic import TemplateView, ListView, DetailView
from apps.response_management.models import Responses

from apps.response_management.serializers import ResponsesSerializer
from apps.roadmap_management.models import Roadmaps
from apps.roadmap_management.serializers import RoadmapSerializer
from apps.user_management.models import Users
from apps.question_handling.models import Questions
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView

class AdminLoginView(LoginView):
    template_name = 'admin_interface/login.html'
    redirect_authenticated_user = True

# API REST pour les réponses
class AdminResponsesViewSet(ModelViewSet):
    queryset = Responses.objects.all()
    serializer_class = ResponsesSerializer

# API REST pour les roadmaps
class AdminRoadmapsViewSet(ModelViewSet):
    queryset = Roadmaps.objects.all()
    serializer_class = RoadmapSerializer

# Tableau de bord
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin_interface/dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajout d'activités récentes
        context["recent_activities"] = [
            {"description": "Nouvelle roadmap créée", "timestamp": "2024-12-09 14:23", "type": "roadmap"},
            {"description": "Réponse soumise", "timestamp": "2024-12-09 13:45", "type": "response"},
        ]
        return context

def analytics_dashboard_data(request):
    """
    Endpoint pour fournir les données JSON utilisées dans analytics.html.
    """
    data = {
        "users": {
            "active": 120,
            "by_role": [
                {"role": "Admin", "count": 5},
                {"role": "Manager", "count": 15},
                {"role": "Utilisateur", "count": 100},
            ]
        },
        "questions": {
            "by_category": [
                {"category": "Catégorie A", "count": 50},
                {"category": "Catégorie B", "count": 30},
                {"category": "Autre", "count": 20},
            ]
        }
    }
    return JsonResponse(data)

# Gestion des questions
class QuestionListView(ListView):
    model = Questions
    template_name = "admin_interface/questions/list.html"
    context_object_name = "questions"

class QuestionDetailView(DetailView):
    model = Questions
    template_name = "admin_interface/questions/detail.html"

# Gestion des utilisateurs
class UserListView(ListView):
    model = Users
    template_name = "admin_interface/users/list.html"
    context_object_name = "users"

class UserDetailView(DetailView):
    model = Users
    template_name = "admin_interface/users/detail.html"

# Gestion des réponses
class ResponseListView(ListView):
    model = Responses
    template_name = "admin_interface/responses/list.html"
    context_object_name = "responses"

class ResponseDetailView(DetailView):
    model = Responses
    template_name = "admin_interface/responses/detail.html"

# Gestion des roadmaps
class RoadmapListView(ListView):
    model = Roadmaps
    template_name = "admin_interface/roadmaps/list.html"
    context_object_name = "roadmaps"

class RoadmapDetailView(DetailView):
    model = Roadmaps
    template_name = "admin_interface/roadmaps/detail.html"

# Configuration IA
class AIConfigView(TemplateView):
    template_name = "admin_interface/config.html"


# Create your views here.
