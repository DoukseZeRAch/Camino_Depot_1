# backend/apps/response_management/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.response_management.serializers import ResponsesSerializer, ResponsesBackupSerializer
from apps.response_management.models import Responses, ResponsesBackup
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

import json
import logging






logger = logging.getLogger(__name__)

class ResponsesViewSet(viewsets.ModelViewSet):
   queryset = Responses.objects.all()
   serializer_class = ResponsesSerializer
   permission_classes = [IsAuthenticated]

   def get_queryset(self):
       if self.request.user.role in ['MANAGER', 'ADMIN']:
           return Responses.objects.all()
       return Responses.objects.filter(user=self.request.user)
   
   def perform_create(self, serializer):
       token = self.request.auth.token if self.request.auth else None
       serializer.save(user=self.request.user, token=token)

   def perform_update(self, serializer):
       token = self.request.auth.token if self.request.auth else None
       serializer.save(token=token)

class ResponsesBackupViewSet(viewsets.ReadOnlyModelViewSet):
   queryset = ResponsesBackup.objects.all()
   serializer_class = ResponsesBackupSerializer
   permission_classes = [IsAuthenticated]

   def get_queryset(self):
       if self.request.user.role in ['MANAGER', 'ADMIN']:
           return ResponsesBackup.objects.all()
       return ResponsesBackup.objects.filter(user=self.request.user)
   
@method_decorator(csrf_exempt, name='dispatch')
class SaveTemporaryResponse(APIView):
    """
    API View pour sauvegarder temporairement les réponses dans la session.
    Les réponses sont stockées jusqu'à la soumission finale.
    """
    permission_classes = [IsAuthenticated]

    def validate_response_data(self, question_id, answer):
        """Valide les données de la réponse"""
        if not question_id:
            raise ValidationError("L'ID de la question est requis")
        if answer is None:
            raise ValidationError("La réponse ne peut pas être vide")
        
        # Convertir question_id en string pour utilisation comme clé
        return str(question_id), answer

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            question_id = data.get("question_id")
            answer = data.get("answer")

            # Validation
            if not question_id or not answer:
                return Response({"error": "Données invalides"}, status=status.HTTP_400_BAD_REQUEST)

            # Sauvegarder temporairement
            if "temp_responses" not in request.session:
                request.session["temp_responses"] = {}

            request.session["temp_responses"][question_id] = {
                "answer": answer,
                "user_id": str(request.user.id),
            }
            request.session.modified = True

            return Response({"message": "Réponse sauvegardée temporairement"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde temporaire : {e}")
            return Response({"error": "Erreur serveur"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        """Récupère les réponses temporaires"""
        temp_responses = request.session.get("temp_responses", {})
        return Response(temp_responses, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class SubmitFinalResponses(APIView):
    """
    API View pour soumettre les réponses finales.
    Utilise les réponses temporaires stockées en session.
    """
    permission_classes = [IsAuthenticated]

    async def post(self, request, *args, **kwargs):
        try:
            temp_responses = request.session.get("temp_responses", {})

            if not temp_responses:
                return Response({"error": "Aucune réponse à soumettre"}, status=status.HTTP_400_BAD_REQUEST)

            # Préparer les données pour OpenAI
            from apps.roadmap_management.services.ai_service import RoadmapAIService
            ai_service = RoadmapAIService()

            prompt = f"Générer une roadmap basée sur ces réponses : {temp_responses}"
            structured_data = {"responses": temp_responses}

            # Envoi à OpenAI
            generation_result = await ai_service.generate_roadmap(prompt, structured_data)

            # Nettoyer les réponses temporaires
            del request.session["temp_responses"]
            request.session.modified = True

            return Response({"message": "Réponses soumises avec succès", "result": generation_result}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erreur lors de la soumission finale : {e}")
            return Response({"error": "Erreur serveur"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class AdminResponseListView(LoginRequiredMixin, ListView):
    model = Responses
    template_name = 'admin_interface/responses/list.html'
    context_object_name = 'responses'
    paginate_by = 10
    
    def get_queryset(self):
        if not (self.request.user.role in ['MANAGER', 'ADMIN']):
            return Responses.objects.none()
        return Responses.objects.all().select_related('user', 'question').order_by('-created_at')

class AdminResponseDetailView(LoginRequiredMixin, DetailView):
    model = Responses
    template_name = 'admin_interface/responses/detail.html'
    context_object_name = 'response'
    
    def get_queryset(self):
        if not (self.request.user.role in ['MANAGER', 'ADMIN']):
            return Responses.objects.none()
        return Responses.objects.select_related('user', 'question').prefetch_related('backups')
# Create your views here.
