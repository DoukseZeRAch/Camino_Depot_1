# apps/question_handling/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Questions
from django.utils import timezone

class QuestionAnalyticsService:
    """Service dédié aux statistiques des questions"""
    
    @staticmethod
    def get_questions_stats(category=None):
        """Récupère les statistiques des questions"""
        query = Questions.objects.all()
        if category:
            query = query.filter(category=category)

        return {
            'total': query.count(),
            'active': query.filter(is_active=True).count(),
            'by_type': {
                'TEXT': query.filter(type='TEXT').count(),
                'MULTIPLE_CHOICE': query.filter(type='MULTIPLE_CHOICE').count(),
                'TABLE': query.filter(type='TABLE').count()
            },
            'by_category': query.values('category').annotate(
                count=Count('id')
            )
        }

class QuestionOrderService:
    """Service dédié à la gestion de l'ordre des questions"""
    
    @staticmethod
    @transaction.atomic
    def validate_order(orders: dict):
        """Valide que les ordres sont cohérents"""
        used_orders = set()
        for order in orders.values():
            if order in used_orders:
                raise ValidationError(f"L'ordre {order} est dupliqué")
            used_orders.add(order)

    @staticmethod
    @transaction.atomic
    def reorder_questions(category: str, orders: dict):
        """
        Réorganise les questions d'une catégorie
        Compatible avec la vue existante
        """
        try:
            QuestionOrderService.validate_order(orders)
            questions = Questions.objects.filter(category=category)
            
            # Mise à jour des ordres
            for question_id, order in orders.items():
                questions.filter(id=question_id).update(
                    order_num=order,
                    updated_at=timezone.now()
                )
            
            return True
        except Exception as e:
            raise ValidationError(f"Erreur lors de la réorganisation: {str(e)}")

# Modification minimale de la vue existante pour intégrer les services
# apps/question_handling/views.py (ajouts uniquement)

from .services import QuestionAnalyticsService, QuestionOrderService

class QuestionsViewSet(viewsets.ModelViewSet):  # Extension de la classe existante
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Ajoute un endpoint pour les statistiques"""
        category = request.query_params.get('category')
        stats = QuestionAnalyticsService.get_questions_stats(category)
        return Response(stats)

    def reorder(self, request):  # Override de la méthode existante
        try:
            category = request.query_params.get('category')
            orders = request.data
            
            if not category:
                return Response(
                    {'error': 'Category is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            QuestionOrderService.reorder_questions(category, orders)
            return Response({'status': 'success'})
            
        except ValidationError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )