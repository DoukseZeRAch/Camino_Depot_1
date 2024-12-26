# apps/response_management/analytics.py
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import csv
from io import StringIO
from .models import Responses, ResponsesBackup

class ResponseAnalytics:
    """Service d'analytics pour les réponses, s'intègre avec le modèle existant"""
    
    @staticmethod
    def get_aggregated_stats(user_id=None, date_range=None):
        """Statistiques agrégées des réponses"""
        query = Responses.objects.all()
        
        if user_id:
            query = query.filter(user_id=user_id)
            
        if date_range:
            start_date, end_date = date_range
            query = query.filter(created_at__range=(start_date, end_date))
            
        total_responses = query.count()
        if total_responses == 0:
            return {
                'total_responses': 0,
                'completion_rate': 0,
                'validity_rate': 0
            }
            
        stats = {
            'total_responses': total_responses,
            'completion_rate': (
                query.filter(is_complete=True).count() / total_responses * 100
            ),
            'validity_rate': (
                query.filter(is_valid=True).count() / total_responses * 100
            ),
            'by_question_type': list(
                query.values('question__type')
                .annotate(count=Count('id'))
                .order_by('question__type')
            ),
            'response_history': list(
                query.values('created_at__date')
                .annotate(count=Count('id'))
                .order_by('-created_at__date')[:30]
            )
        }
        
        return stats

    @staticmethod
    def export_responses(queryset, fields):
        """Export des réponses en CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        # En-têtes personnalisés
        headers = {
            'id': 'ID',
            'created_at': 'Date de création',
            'updated_at': 'Dernière modification',
            'question__text': 'Question',
            'content': 'Réponse',
            'is_valid': 'Validé',
            'is_complete': 'Complété'
        }
        
        writer.writerow([headers.get(field, field) for field in fields])
        
        # Données
        for response in queryset:
            row = []
            for field in fields:
                if field == 'content':
                    # Formater le contenu JSON pour le CSV
                    content = response.content or {}
                    if response.question and response.question.type == 'MULTIPLE_CHOICE':
                        value = ', '.join(content.get('selected', []))
                    elif response.question and response.question.type == 'TEXT':
                        value = content.get('text', '')
                    else:
                        value = str(content)
                    row.append(value)
                elif '__' in field:
                    # Gestion des champs reliés
                    obj = response
                    for part in field.split('__'):
                        obj = getattr(obj, part, '')
                    row.append(str(obj))
                else:
                    row.append(str(getattr(response, field, '')))
            writer.writerow(row)
        
        return output.getvalue()

# Extension du ViewSet existant dans views.py
# À ajouter dans la classe ResponsesViewSet

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques agrégées des réponses"""
        user_id = request.query_params.get('user_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        date_range = None
        if start_date and end_date:
            try:
                date_range = (
                    timezone.datetime.strptime(start_date, '%Y-%m-%d'),
                    timezone.datetime.strptime(end_date, '%Y-%m-%d')
                )
            except ValueError:
                return Response(
                    {'error': 'Format de date invalide'}, 
                    status=400
                )
        
        stats = ResponseAnalytics.get_aggregated_stats(user_id, date_range)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export des réponses en CSV"""
        allowed_fields = {
            'id', 'created_at', 'updated_at', 'question__text',
            'content', 'is_valid', 'is_complete'
        }
        
        requested_fields = request.query_params.getlist('fields', [])
        export_fields = [f for f in requested_fields if f in allowed_fields] or [
            'created_at', 'question__text', 'content', 'is_valid'
        ]
        
        queryset = self.get_queryset()
        csv_content = ResponseAnalytics.export_responses(queryset, export_fields)
        
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="responses_export.csv"'
        return response