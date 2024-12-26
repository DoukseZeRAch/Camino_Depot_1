# backend/apps/question_handling/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action  
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from .models import Questions
from .serializers import QuestionSerializer

class QuestionsViewSet(viewsets.ModelViewSet):
   queryset = Questions.objects.all()
   serializer_class = QuestionSerializer
   permission_classes = [IsAuthenticated]

   def get_queryset(self):
       if self.request.user.role in ['MANAGER', 'ADMIN']:
           return Questions.objects.all()
       return Questions.objects.filter(is_active=True)

   def create(self, request, *args, **kwargs):
       # Ajouter l'utilisateur qui crée la question
       request.data['created_by'] = request.user.id
       return super().create(request, *args, **kwargs)

   @action(detail=False, methods=['post'])
   def reorder(self, request):
       try:
           orders = request.data
           for question_id, order in orders.items():
               Questions.objects.filter(id=question_id).update(order_num=order)
           return Response(status=status.HTTP_200_OK)
       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
       
   @action(detail=True, methods=['patch'])
   def toggle_active(self, request, pk=None):
        question = self.get_object()
        question.is_active = not question.is_active
        question.save()
        return Response({'is_active': question.is_active})

   @action(detail=False, methods=['get'])
   def by_category(self, request):
        category = request.query_params.get('category')
        questions = self.get_queryset().filter(category=category)
        serializer = self.get_serializer(questions, many=True)
        return Response(serializer.data)

   @action(detail=True, methods=['post'])
   def duplicate(self, request, pk=None):
        question = self.get_object()
        question.pk = None
        question.text = f"{question.text} (Copy)"
        question.order_num = Questions.objects.count() + 1
        question.save()
        serializer = self.get_serializer(question)
        return Response(serializer.data)
   @action(detail=True, methods=['get'])
   def detail(self, request, pk=None):
    question = self.get_object()
    return render(request, 'admin_interface/questions/detail.html', {
        'question': question
    })
   @action(detail=True, methods=['get'])
   def preview(self, request, pk=None):
        """
        API pour prévisualiser une question.
        """
        question = self.get_object()
        serializer = self.get_serializer(question)
        return Response(serializer.data)

# Create your views here.
