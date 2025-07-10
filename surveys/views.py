from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.db import transaction
from datetime import date, timedelta
from .models import Survey, Question, Answer
from .serializers import (
    SurveyListSerializer,
    SurveyDetailSerializer,
    SurveyCreateSerializer,
    SurveyUpdateSerializer,
    SurveyResponseSerializer,
    QuestionSerializer,
    QuestionCreateSerializer,
    AnswerSerializer,
    AnswerCreateSerializer
)
from church_core.unified_permissions import UnifiedPermission


class SurveyViewSet(viewsets.ModelViewSet):
    """설문조사 관리 API ViewSet"""
    resource_name = 'survey'
    queryset = Survey.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['start_date', 'end_date', 'created_by']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """교회별 설문조사 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id).select_related(
            'church', 'created_by'
        ).prefetch_related('questions')

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'list':
            return SurveyListSerializer
        elif self.action == 'create':
            return SurveyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SurveyUpdateSerializer
        elif self.action == 'respond':
            return SurveyResponseSerializer
        return SurveyDetailSerializer

    def get_serializer_context(self):
        """시리얼라이저 컨텍스트에 church_id 추가"""
        context = super().get_serializer_context()
        context['church_id'] = self.kwargs.get('church_id')
        return context

    def perform_create(self, serializer):
        """설문조사 생성 시 교회 정보 자동 설정"""
        church_id = self.kwargs.get('church_id')
        serializer.save(church_id=church_id, created_by=self.request.user)

    # create, update, destroy는 UnifiedPermission에서 처리합니다.

    @action(detail=False, methods=['get'])
    def active(self, request, church_id=None):
        """활성 설문조사 목록"""
        today = date.today()
        queryset = self.get_queryset().filter(
            start_date__lte=today,
            end_date__gte=today
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request, church_id=None):
        """예정된 설문조사 목록"""
        today = date.today()
        queryset = self.get_queryset().filter(start_date__gt=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completed(self, request, church_id=None):
        """완료된 설문조사 목록"""
        today = date.today()
        queryset = self.get_queryset().filter(end_date__lt=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None, church_id=None):
        """설문조사 응답"""
        survey = self.get_object()
        
        # 설문조사 활성 상태 확인
        today = date.today()
        if not (survey.start_date <= today <= survey.end_date):
            return Response(
                {"detail": "설문조사가 활성 상태가 아닙니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 사용자의 교회 멤버 정보 가져오기
        try:
            church_user = request.user.church_users.get(church_id=church_id)
            member = church_user.member
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 이미 응답했는지 확인
        if Answer.objects.filter(question__survey=survey, member=member).exists():
            return Response(
                {"detail": "이미 응답한 설문조사입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            answers_data = serializer.validated_data['answers']
            
            # 트랜잭션으로 모든 답변 저장
            with transaction.atomic():
                for answer_data in answers_data:
                    question = Question.objects.get(id=answer_data['question_id'])
                    
                    # 질문이 해당 설문조사에 속하는지 확인
                    if question.survey != survey:
                        return Response(
                            {"detail": "질문이 해당 설문조사에 속하지 않습니다."}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    Answer.objects.create(
                        question=question,
                        member=member,
                        answer_text=answer_data.get('answer_text', ''),
                        selected_choices=answer_data.get('selected_choices', [])
                    )
            
            return Response({"detail": "설문조사 응답이 완료되었습니다."})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None, church_id=None):
        """설문조사 결과 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        survey = self.get_object()
        questions = survey.questions.all()
        
        results = []
        for question in questions:
            question_result = {
                'question_id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'total_responses': question.answers.count()
            }
            
            if question.question_type == 'TEXT':
                # 주관식 답변 목록
                answers = question.answers.values_list('answer_text', flat=True)
                question_result['answers'] = list(answers)
            else:
                # 객관식 선택지별 통계
                choice_stats = {}
                for choice in question.choices or []:
                    choice_stats[choice] = 0
                
                for answer in question.answers.all():
                    for choice in answer.selected_choices or []:
                        if choice in choice_stats:
                            choice_stats[choice] += 1
                
                question_result['choice_statistics'] = choice_stats
            
            results.append(question_result)
        
        return Response({
            'survey': SurveyDetailSerializer(survey, context={'request': request}).data,
            'total_responses': Answer.objects.filter(question__survey=survey).values('member').distinct().count(),
            'question_results': results
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """설문조사 통계 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        queryset = self.get_queryset()
        today = date.today()
        
        # 기본 통계
        total_surveys = queryset.count()
        active_surveys = queryset.filter(start_date__lte=today, end_date__gte=today).count()
        upcoming_surveys = queryset.filter(start_date__gt=today).count()
        completed_surveys = queryset.filter(end_date__lt=today).count()
        
        # 응답 통계
        total_responses = Answer.objects.filter(
            question__survey__church_id=church_id
        ).values('member').distinct().count()
        
        # 월별 설문조사 생성 수
        monthly_surveys = queryset.filter(
            created_at__year=today.year
        ).extra(
            select={'month': 'EXTRACT(month FROM created_at)'}
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        return Response({
            'total_surveys': total_surveys,
            'active_surveys': active_surveys,
            'upcoming_surveys': upcoming_surveys,
            'completed_surveys': completed_surveys,
            'total_responses': total_responses,
            'monthly_surveys': list(monthly_surveys)
        })

    @action(detail=True, methods=['get'])
    def my_response(self, request, pk=None, church_id=None):
        """내 응답 조회"""
        survey = self.get_object()
        
        # 사용자의 교회 멤버 정보 가져오기
        try:
            church_user = request.user.church_users.get(church_id=church_id)
            member = church_user.member
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 응답 조회
        answers = Answer.objects.filter(question__survey=survey, member=member)
        if not answers.exists():
            return Response(
                {"detail": "응답하지 않은 설문조사입니다."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AnswerSerializer(answers, many=True)
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    """질문 관리 API ViewSet"""
    resource_name = 'question'
    queryset = Question.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['survey', 'question_type']
    search_fields = ['question_text']
    ordering_fields = ['id']
    ordering = ['id']

    def get_queryset(self):
        """교회별 질문 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(survey__church_id=church_id).select_related('survey')

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'create':
            return QuestionCreateSerializer
        return QuestionSerializer

    def perform_create(self, serializer):
        """질문 생성 시 설문조사 정보 자동 설정"""
        survey_id = self.kwargs.get('survey_id')
        serializer.save(survey_id=survey_id)

    # create, update, destroy는 UnifiedPermission에서 처리합니다.


class AnswerViewSet(viewsets.ModelViewSet):
    """답변 관리 API ViewSet"""
    resource_name = 'answer'
    queryset = Answer.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['question', 'member']
    search_fields = ['answer_text']
    ordering_fields = ['answered_at']
    ordering = ['-answered_at']

    def get_queryset(self):
        """교회별 답변 필터링"""
        church_id = self.kwargs.get('church_id')
        queryset = self.queryset.filter(question__survey__church_id=church_id).select_related(
            'question', 'question__survey', 'member'
        )
        
        # UnifiedPermission이 객체 수준 권한을 처리하므로, 수동 필터링 제거
        return queryset

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'create':
            return AnswerCreateSerializer
        return AnswerSerializer

    def perform_create(self, serializer):
        """답변 생성 시 멤버 정보 자동 설정"""
        church_id = self.kwargs.get('church_id')
        try:
            church_user = self.request.user.church_users.get(church_id=church_id)
            member = church_user.member
            serializer.save(member=member)
        except:
            raise serializers.ValidationError("교회 멤버 정보를 찾을 수 없습니다.")

    # update, destroy는 UnifiedPermission에서 객체 소유권 등을 확인하여 처리합니다.

    @action(detail=False, methods=['get'])
    def my_answers(self, request, church_id=None):
        """내 답변 목록"""
        try:
            church_user = request.user.church_users.get(church_id=church_id)
            member = church_user.member
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(member=member)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
