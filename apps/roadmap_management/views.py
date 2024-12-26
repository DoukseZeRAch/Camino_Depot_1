from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async
from django.db.transaction import atomic
from typing import Any, Dict
from .models import AIConfiguration, Roadmaps
from .serializers import AIConfigurationSerializer, RoadmapSerializer, RoadmapDetailSerializer, RoadmapUpdateSerializer
from .services.ai_preparation_service import AIDataPreparationService
from .services.ai_service import AIService, RoadmapAIService
from apps.user_management.permissions import HasRoadmapAccess
import logging
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from apps.roadmap_management.services.prompt_validation_service import PromptValidationService
from apps.roadmap_management.services.ai_prompt_service import AIPromptService


@csrf_exempt
@api_view(['POST'])
def update_prompt(request):
    """
    Endpoint pour mettre à jour le prompt d'une configuration IA d'une roadmap.
    """
    try:
        data = request.data
        roadmap_id = data.get('roadmap_id')
        prompt_template = data.get('prompt_template')

        # Valider les entrées
        if not roadmap_id or not prompt_template:
            raise ValidationError("L'identifiant de la roadmap et le prompt sont requis.")

        # Récupérer la roadmap et sa configuration IA
        roadmap = Roadmaps.objects.get(id=roadmap_id)
        ai_config = roadmap.ai_configs.first()  # Suppose une relation one-to-one ou one-to-many
        if not ai_config:
            raise ValidationError("Aucune configuration IA associée à cette roadmap.")

        # Valider le prompt avec le service de validation
        validation_result = PromptValidationService.validate_prompt_template(prompt_template)
        if not validation_result['is_valid']:
            return Response(
                {'success': False, 'error': validation_result['error_message']},
                status=400
            )

        # Sauvegarder le nouveau prompt
        ai_config.prompt_template = prompt_template
        ai_config.save()

        return Response({'success': True, 'message': 'Prompt mis à jour avec succès.'})

    except ValidationError as e:
        return Response({'success': False, 'error': str(e)}, status=400)
    except Roadmaps.DoesNotExist:
        return Response({'success': False, 'error': 'Roadmap introuvable.'}, status=404)
    except Exception as e:
        return Response({'success': False, 'error': f"Erreur interne : {e}"}, status=500)


@csrf_exempt
@api_view(['GET'])
def fetch_questions_and_responses(request, roadmap_id):
    """
    Endpoint pour récupérer les questions et réponses associées à une roadmap.
    """
    try:
        # Récupérer les données associées à la roadmap
        roadmap = Roadmaps.objects.get(id=roadmap_id)
        questions = roadmap.questions.all().values('id', 'text', 'type')
        responses = roadmap.responses.all().values('id', 'content', 'is_complete')

        return Response({
            'success': True,
            'questions': list(questions),
            'responses': list(responses),
        })

    except Roadmaps.DoesNotExist:
        return Response({'success': False, 'error': 'Roadmap introuvable.'}, status=404)
    except Exception as e:
        return Response({'success': False, 'error': f"Erreur interne : {e}"}, status=500)



logger = logging.getLogger(__name__)

class RoadmapViewSet(viewsets.ModelViewSet):
    queryset = Roadmaps.objects.all()
    serializer_class = RoadmapSerializer
    permission_classes = [IsAuthenticated, HasRoadmapAccess]

    async def get_queryset(self):
        user = self.request.user
        if user.role in ['MANAGER', 'ADMIN']:
            return await Roadmaps.objects.all().aasync_all()
        return await Roadmaps.objects.filter(user=user).aasync_all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoadmapDetailSerializer
        if self.action in ['update', 'partial_update']:
            return RoadmapUpdateSerializer
        return RoadmapSerializer

    async def perform_create(self, serializer):
        await sync_to_async(serializer.save)(
            user=self.request.user,
            status='DRAFT',
            version=1,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

    @action(detail=True, methods=['post'])
    async def generate(self, request, pk=None):
        roadmap = await sync_to_async(self.get_object)()
        
        try:
            if not await sync_to_async(roadmap.can_generate)():
                return Response(
                    {"error": "La roadmap ne peut pas être générée"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            temp_responses = request.session.get("temp_responses", {})
            if not temp_responses:
                return Response(
                    {"error": "Aucune réponse trouvée"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validation de la configuration AI
            ai_config = {}
            if 'ai_config' in request.data:
                try:
                    ai_config = await sync_to_async(self._validate_ai_config)(request.data['ai_config'])
                except ValidationError as e:
                    return Response(
                        {"error": f"Configuration AI invalide: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            preparation_service = AIDataPreparationService()
            ai_service = RoadmapAIService()

            @atomic
            async def generate_content():
                roadmap.status = 'GENERATING'
                await sync_to_async(roadmap.save)()

                try:
                    generation_data = await preparation_service.prepare_complete_generation_data(
                        temp_responses,
                        request.user
                    )

                    generation_result = await ai_service.generate_roadmap(
                        generation_data["prompt"],
                        generation_data["data"],
                        **ai_config
                    )

                    roadmap.content = generation_result["content"]
                    roadmap.status = 'COMPLETED'
                    await sync_to_async(roadmap.increment_version)()
                    roadmap.updated_at = timezone.now()
                    await sync_to_async(roadmap.save)()

                    if "temp_responses" in request.session:
                        del request.session["temp_responses"]
                        request.session.modified = True

                    return generation_result

                except Exception as e:
                    roadmap.status = 'ERROR'
                    await sync_to_async(roadmap.save)()
                    raise e

            result = await generate_content()

            return Response({
                "message": "Roadmap générée avec succès",
                "roadmap_id": roadmap.id,
                "status": roadmap.status,
                "version": roadmap.version,
                "used_config": ai_config,
                "metadata": result.get("metadata", {})
            })

        except Exception as e:
            logger.error(f"Erreur génération roadmap {roadmap.id}: {str(e)}")
            return Response(
                {"error": "Erreur lors de la génération"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    async def status(self, request, pk=None):
        roadmap = await sync_to_async(self.get_object)()
        return Response({
            "status": roadmap.status,
            "version": roadmap.version,
            "updated_at": roadmap.updated_at
        })

    @action(detail=True, methods=['post'])
    async def regenerate(self, request, pk=None):
        roadmap = await sync_to_async(self.get_object)()
        
        try:
            if roadmap.status == 'GENERATING':
                return Response(
                    {"error": "Déjà en cours de génération"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            @atomic
            async def update_roadmap():
                roadmap.version += 1
                roadmap.status = 'GENERATING'
                roadmap.updated_at = timezone.now()
                await sync_to_async(roadmap.save)()

            await update_roadmap()
            return await self.generate(request, pk)

        except Exception as e:
            logger.error(f"Erreur régénération roadmap {roadmap.id}: {str(e)}")
            return Response(
                {"error": "Erreur lors de la régénération"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    async def history(self, request, pk=None):
        roadmap = await sync_to_async(self.get_object)()
        
        try:
            previous_versions = await Roadmaps.objects.filter(
                user=roadmap.user,
                created_at__lt=roadmap.created_at
            ).order_by('-created_at').aasync_all()

            serializer = RoadmapDetailSerializer(previous_versions, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Erreur récupération historique: {str(e)}")
            return Response(
                {"error": "Erreur lors de la récupération de l'historique"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    async def drafts(self, request):
        drafts = await Roadmaps.objects.filter(status='DRAFT').aasync_all()
        serializer = self.get_serializer(drafts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    async def archive(self, request, pk=None):
        roadmap = await sync_to_async(self.get_object)()
        
        try:
            if roadmap.status == 'ARCHIVED':
                return Response(
                    {"error": "Déjà archivée"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            @atomic
            async def archive_roadmap():
                roadmap.status = 'ARCHIVED'
                roadmap.updated_at = timezone.now()
                await sync_to_async(roadmap.save)()

            await archive_roadmap()

            return Response({
                "message": "Roadmap archivée avec succès",
                "roadmap_id": roadmap.id
            })

        except Exception as e:
            logger.error(f"Erreur archivage roadmap {roadmap.id}: {str(e)}")
            return Response(
                {"error": "Erreur lors de l'archivage"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    async def duplicate(self, request, pk=None):
        roadmap = await sync_to_async(self.get_object)()
        
        try:
            @atomic
            async def create_duplicate():
                new_roadmap = await Roadmaps.objects.acreate(
                    user=request.user,
                    title=f"Copie de {roadmap.title}",
                    content=roadmap.content,
                    status='DRAFT',
                    version=1,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                return new_roadmap

            new_roadmap = await create_duplicate()
            serializer = RoadmapDetailSerializer(new_roadmap)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Erreur duplication roadmap {roadmap.id}: {str(e)}")
            return Response(
                {"error": "Erreur lors de la duplication"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def destroy(self, request, *args, **kwargs):
        try:
            roadmap = await sync_to_async(self.get_object)()
            
            if not await sync_to_async(roadmap.can_delete)():
                return Response(
                    {"error": "Cette roadmap ne peut pas être supprimée"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            await sync_to_async(roadmap.delete)()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f"Erreur suppression roadmap: {str(e)}")
            return Response(
                {"error": "Erreur lors de la suppression"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _validate_ai_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validation synchrone de la configuration AI"""
        validated_config = {}
        
        if 'temperature' in config:
            try:
                temp = float(config['temperature'])
                if 0 <= temp <= 1:
                    validated_config['temperature'] = temp
                else:
                    raise ValidationError("La température doit être entre 0 et 1")
            except ValueError:
                raise ValidationError("La température doit être un nombre")

        allowed_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        if 'model' in config and config['model'] in allowed_models:
            validated_config['model'] = config['model']

        if 'max_tokens' in config:
            try:
                tokens = int(config['max_tokens'])
                if 1000 <= tokens <= 32000:
                    validated_config['max_tokens'] = tokens
                else:
                    raise ValidationError("max_tokens doit être entre 1000 et 32000")
            except ValueError:
                raise ValidationError("max_tokens doit être un nombre entier")

        return validated_config

    @action(detail=True, methods=['get'])
    async def analyze_context(self, request, pk=None):
        try:
            temp_responses = request.session.get("temp_responses", {})
            if not temp_responses:
                return Response(
                    {"error": "Aucune réponse trouvée pour l'analyse"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            preparation_service = AIDataPreparationService()
            ai_service = RoadmapAIService()

            structured_data = await preparation_service.prepare_complete_generation_data(
                temp_responses,
                request.user
            )
            
            context_analysis = ai_service.analyze_context(structured_data)

            return Response({
                "context_analysis": context_analysis,
                "suggested_config": {
                    "temperature": min(0.7, 1 - context_analysis['technical_precision'])
                }
            })

        except Exception as e:
            logger.error(f"Erreur analyse du contexte: {str(e)}")
            return Response(
                {"error": "Erreur lors de l'analyse du contexte"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class AdminRoadmapListView(LoginRequiredMixin, ListView):
    model = Roadmaps
    template_name = 'admin_interface/roadmaps/list.html'
    context_object_name = 'roadmaps'
    paginate_by = 10

    def get_queryset(self):
        if not self.request.user.role in ['MANAGER', 'ADMIN']:
            return Roadmaps.objects.none()
        return Roadmaps.objects.select_related('user').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Roadmaps.STATUSES
        return context

class AdminRoadmapDetailView(LoginRequiredMixin, DetailView):
    model = Roadmaps
    template_name = 'admin_interface/roadmaps/detail.html'
    context_object_name = 'roadmap'

    def get_queryset(self):
        if not self.request.user.role in ['MANAGER', 'ADMIN']:
            return Roadmaps.objects.none()
        return Roadmaps.objects.select_related('user').prefetch_related('ai_configs')

@method_decorator(require_POST, name='dispatch')
class RegenerateRoadmapView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.role in ['MANAGER', 'ADMIN']:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        try:
            roadmap = Roadmaps.objects.get(pk=pk)
            ai_service = AIService()
            preparation_service = AIDataPreparationService()

            data = preparation_service.prepare_complete_generation_data(
                temp_responses=request.session.get('temp_responses', {}),
                user=roadmap.user
            )
            result = ai_service.send_prompt(data['prompt'])

            roadmap.content = result
            roadmap.status = 'COMPLETED'
            roadmap.version += 1
            roadmap.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(require_POST, name='dispatch')
class ArchiveRoadmapView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.role in ['MANAGER', 'ADMIN']:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        try:
            roadmap = Roadmaps.objects.get(pk=pk)
            roadmap.status = 'ARCHIVED'
            roadmap.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
class GlobalAIConfigurationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Récupère la configuration globale de l'IA"""
        config = AIConfiguration.objects.first()
        if not config:
            config = AIConfiguration.objects.create()
        serializer = AIConfigurationSerializer(config)
        return Response(serializer.data)

    def post(self, request):
        """Met à jour la configuration globale de l'IA"""
        config = AIConfiguration.objects.first()
        serializer = AIConfigurationSerializer(config, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)