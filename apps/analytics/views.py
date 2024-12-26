# apps/analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.db.models import Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from django.db import connection
from apps.question_handling.models import Questions
from apps.response_management.models import Responses
from apps.roadmap_management.models import Roadmaps
from apps.user_management.models import Users
from .models import AnalyticsCache
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
import json






class BaseAnalyticsView(APIView):
    """Classe de base pour les vues d'analytics avec gestion du cache"""
    permission_classes = [IsAuthenticated]
    cache_timeout = 300  # 5 minutes

    def get_cache_key(self, **params):
        """Génère une clé de cache unique basée sur les paramètres"""
        sorted_params = sorted(params.items())
        params_str = '_'.join(f"{k}:{v}" for k, v in sorted_params)
        return f"{self.__class__.__name__}_{params_str}"

    def get_cached_data(self, cache_type, **params):
        key = self.get_cache_key(**params)
        try:
            cache = AnalyticsCache.objects.get(
                key=key,
                cache_type=cache_type,
                expires_at__gt=timezone.now()
            )
            return cache.data
        except AnalyticsCache.DoesNotExist:
            return None

    def cache_data(self, data, cache_type, **params):
        key = self.get_cache_key(**params)
        expires_at = timezone.now() + timedelta(seconds=self.cache_timeout)
        AnalyticsCache.objects.update_or_create(
            key=key,
            cache_type=cache_type,
            defaults={
                'data': data,
                'expires_at': expires_at,
                'parameters': params
            }
        )

class QuestionsAnalyticsView(BaseAnalyticsView):
    def get(self, request):
        period = request.query_params.get('period', 'all')
        
        # Check cache first
        cached_data = self.get_cached_data('QUESTIONS', period=period)
        if cached_data:
            return Response(cached_data)

        # Base query
        query = Questions.objects.all()

        # Apply period filter
        if period != 'all':
            time_threshold = timezone.now()
            if period == 'day':
                time_threshold -= timedelta(days=1)
            elif period == 'week':
                time_threshold -= timedelta(weeks=1)
            elif period == 'month':
                time_threshold -= timedelta(days=30)
            elif period == 'year':
                time_threshold -= timedelta(days=365)
            
            query = query.filter(created_at__gte=time_threshold)

        # Calculate statistics
        stats = {
            'total_questions': query.count(),
            'active_questions': query.filter(is_active=True).count(),
            'by_type': list(
                query.values('type')
                .annotate(count=Count('id'))
                .order_by('type')
            ),
            'by_category': list(
                query.values('category')
                .annotate(count=Count('id'))
                .order_by('category')
            )
        }

        # Cache the results
        self.cache_data(stats, 'QUESTIONS', period=period)
        return Response(stats)

class ResponsesAnalyticsView(BaseAnalyticsView):
    def get(self, request):
        period = request.query_params.get('period', 'all')
        
        cached_data = self.get_cached_data('RESPONSES', period=period)
        if cached_data:
            return Response(cached_data)

        query = Responses.objects.all()

        if period != 'all':
            time_threshold = timezone.now()
            if period == 'day':
                time_threshold -= timedelta(days=1)
            elif period == 'week':
                time_threshold -= timedelta(weeks=1)
            elif period == 'month':
                time_threshold -= timedelta(days=30)
            elif period == 'year':
                time_threshold -= timedelta(days=365)
            
            query = query.filter(created_at__gte=time_threshold)

        stats = {
            'total_responses': query.count(),
            'completion_rate': (
                query.filter(is_complete=True).count() / query.count() * 100
                if query.exists() else 0
            ),
            'validity_rate': (
                query.filter(is_valid=True).count() / query.count() * 100
                if query.exists() else 0
            ),
            'by_question_type': list(
                query.values('question__type')
                .annotate(count=Count('id'))
                .order_by('question__type')
            )
        }

        self.cache_data(stats, 'RESPONSES', period=period)
        return Response(stats)

class RoadmapsAnalyticsView(BaseAnalyticsView):
    def get(self, request):
        period = request.query_params.get('period', 'all')
        
        cached_data = self.get_cached_data('ROADMAPS', period=period)
        if cached_data:
            return Response(cached_data)

        query = Roadmaps.objects.all()

        if period != 'all':
            time_threshold = timezone.now()
            if period == 'day':
                time_threshold -= timedelta(days=1)
            elif period == 'week':
                time_threshold -= timedelta(weeks=1)
            elif period == 'month':
                time_threshold -= timedelta(days=30)
            elif period == 'year':
                time_threshold -= timedelta(days=365)
            
            query = query.filter(created_at__gte=time_threshold)

        stats = {
            'total_roadmaps': query.count(),
            'by_status': list(
                query.values('status')
                .annotate(count=Count('id'))
                .order_by('status')
            ),
            'average_version': query.aggregate(avg_version=Avg('version'))['avg_version'] or 0,
            'recent_roadmaps': list(
                query.order_by('-created_at')
                .values('id', 'title', 'status', 'created_at')[:5]
            )
        }

        self.cache_data(stats, 'ROADMAPS', period=period)
        return Response(stats)

class DashboardOverviewView(BaseAnalyticsView):
    """
    Vue pour fournir les statistiques générales du tableau de bord analytics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Vérification des données en cache
        cached_data = self.get_cached_data('DASHBOARD')
        if cached_data:
            return Response(cached_data)

        # Définir une période par défaut : 30 derniers jours
        time_threshold = timezone.now() - timedelta(days=30)

        # Collecte des statistiques
        stats = {
            'users': {
                'total': Users.objects.count(),
                'active': Users.objects.filter(is_active=True).count(),
                'by_role': list(
                    Users.objects.values('role')
                    .annotate(count=Count('id'))
                    .order_by('role')
                )
            },
            'questions': {
                'total': Questions.objects.count(),
                'active': Questions.objects.filter(is_active=True).count(),
                'by_category': list(
                    Questions.objects.values('category')
                    .annotate(count=Count('id'))
                    .order_by('category')
                )
            },
            'responses': {
                'total': Responses.objects.count(),
                'complete': Responses.objects.filter(is_complete=True).count(),
                'by_question_type': list(
                    Responses.objects.values('question__type')
                    .annotate(count=Count('id'))
                    .order_by('question__type')
                )
            },
            'roadmaps': {
                'total': Roadmaps.objects.count(),
                'by_status': list(
                    Roadmaps.objects.values('status')
                    .annotate(count=Count('id'))
                    .order_by('status')
                ),
                'recent': list(
                    Roadmaps.objects.filter(created_at__gte=time_threshold)
                    .values('id', 'title', 'status', 'created_at')
                    .order_by('-created_at')[:5]
                )
            },
            'recent_activity': {
                'new_users': list(
                    Users.objects.filter(created_at__gte=time_threshold)
                    .values('id', 'email', 'created_at')
                    .order_by('-created_at')[:5]
                ),
                'new_responses': list(
                    Responses.objects.filter(created_at__gte=time_threshold)
                    .values('id', 'user__email', 'question__text', 'created_at')
                    .order_by('-created_at')[:5]
                )
            }
        }

        # Mise en cache des données
        self.cache_data(stats, 'DASHBOARD')
        return Response(stats)
class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_interface/dashboard/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # KPIs
        context['active_users_count'] = Users.objects.filter(is_active=True).count()
        context['roadmaps_count'] = Roadmaps.objects.count()
        context['active_questions_count'] = Questions.objects.filter(is_active=True).count()
        
        total_responses = Responses.objects.count()
        completed_responses = Responses.objects.filter(is_complete=True).count()
        context['completion_rate'] = round((completed_responses / total_responses * 100) if total_responses > 0 else 0)

        # Réponses par catégorie
        responses_by_category = Questions.objects.filter(responses__isnull=False).values('category').annotate(count=Count('responses'))
        context['responses_categories'] = json.dumps([item['category'] for item in responses_by_category])
        context['responses_data'] = json.dumps([item['count'] for item in responses_by_category])

        # Roadmaps par statut
        roadmaps_by_status = Roadmaps.objects.values('status').annotate(count=Count('id'))
        context['roadmaps_statuses'] = json.dumps([item['status'] for item in roadmaps_by_status])
        context['roadmaps_status_data'] = json.dumps([item['count'] for item in roadmaps_by_status])

        # Activités récentes
        recent_activities = []
        
        # Dernières roadmaps
        recent_roadmaps = Roadmaps.objects.select_related('user').order_by('-created_at')[:5]
        for roadmap in recent_roadmaps:
            recent_activities.append({
                'type': 'roadmap',
                'description': f"Roadmap générée pour {roadmap.user.email}",
                'timestamp': roadmap.created_at
            })

        # Dernières réponses
        recent_responses = Responses.objects.select_related('user', 'question').order_by('-created_at')[:5]
        for response in recent_responses:
            recent_activities.append({
                'type': 'response',
                'description': f"{response.user.email} a répondu à '{response.question.text[:50]}...'",
                'timestamp': response.created_at
            })

        # Trier les activités par date
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        context['recent_activities'] = recent_activities[:10]

        return context

# Create your views here.
