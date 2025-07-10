from rest_framework import serializers
from .models import Survey, Question, Answer
from members.serializers import MemberSerializer
from users.serializers import UserSerializer


class QuestionSerializer(serializers.ModelSerializer):
    """질문 Serializer"""
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    answer_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'question_type_display',
            'choices', 'answer_count'
        ]
        read_only_fields = ['survey']
    
    def get_answer_count(self, obj):
        """답변 수 반환"""
        return obj.answers.count()


class QuestionCreateSerializer(serializers.ModelSerializer):
    """질문 생성용 Serializer"""
    
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'choices']
    
    def validate_question_text(self, value):
        """질문 텍스트 유효성 검사"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("질문 내용은 5자 이상이어야 합니다.")
        return value.strip()
    
    def validate_choices(self, value):
        """선택지 유효성 검사"""
        question_type = self.initial_data.get('question_type')
        if question_type in ['SINGLE_CHOICE', 'MULTIPLE_CHOICE']:
            if not value or len(value) < 2:
                raise serializers.ValidationError("선택형 질문은 최소 2개 이상의 선택지가 필요합니다.")
        return value


class AnswerSerializer(serializers.ModelSerializer):
    """답변 Serializer"""
    member_detail = MemberSerializer(source='member', read_only=True)
    question_detail = QuestionSerializer(source='question', read_only=True)
    
    class Meta:
        model = Answer
        fields = [
            'id', 'question', 'question_detail', 'member', 'member_detail',
            'answer_text', 'selected_choices', 'answered_at'
        ]
        read_only_fields = ['member', 'answered_at']


class AnswerCreateSerializer(serializers.ModelSerializer):
    """답변 생성용 Serializer"""
    
    class Meta:
        model = Answer
        fields = ['question', 'answer_text', 'selected_choices']
    
    def validate(self, data):
        """답변 유효성 검사"""
        question = data.get('question')
        answer_text = data.get('answer_text')
        selected_choices = data.get('selected_choices', [])
        
        if question.question_type == 'TEXT':
            if not answer_text or len(answer_text.strip()) < 1:
                raise serializers.ValidationError("주관식 답변은 필수입니다.")
        elif question.question_type in ['SINGLE_CHOICE', 'MULTIPLE_CHOICE']:
            if not selected_choices:
                raise serializers.ValidationError("선택지를 선택해주세요.")
            
            # 선택지 유효성 검사
            valid_choices = question.choices or []
            for choice in selected_choices:
                if choice not in valid_choices:
                    raise serializers.ValidationError(f"유효하지 않은 선택지입니다: {choice}")
            
            # 단일 선택 검사
            if question.question_type == 'SINGLE_CHOICE' and len(selected_choices) > 1:
                raise serializers.ValidationError("단일 선택 질문은 하나의 선택지만 선택할 수 있습니다.")
        
        return data
    
    def create(self, validated_data):
        """답변 생성"""
        user = self.context['request'].user
        question = validated_data['question']
        
        # 사용자의 교회 멤버 정보 가져오기
        try:
            church_user = user.church_users.get(church_id=question.survey.church_id)
            member = church_user.member
        except:
            raise serializers.ValidationError("교회 멤버 정보를 찾을 수 없습니다.")
        
        # 중복 답변 확인
        if Answer.objects.filter(question=question, member=member).exists():
            raise serializers.ValidationError("이미 답변한 질문입니다.")
        
        validated_data['member'] = member
        return super().create(validated_data)


class SurveyListSerializer(serializers.ModelSerializer):
    """설문조사 목록용 Serializer"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    question_count = serializers.SerializerMethodField()
    response_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    is_responded = serializers.SerializerMethodField()
    
    class Meta:
        model = Survey
        fields = [
            'id', 'title', 'start_date', 'end_date', 'created_by_name',
            'question_count', 'response_count', 'is_active', 'is_responded', 'created_at'
        ]
    
    def get_question_count(self, obj):
        """질문 수 반환"""
        return obj.questions.count()
    
    def get_response_count(self, obj):
        """응답 수 반환"""
        return Answer.objects.filter(question__survey=obj).values('member').distinct().count()
    
    def get_is_active(self, obj):
        """활성 상태 반환"""
        from datetime import date
        today = date.today()
        return obj.start_date <= today <= obj.end_date
    
    def get_is_responded(self, obj):
        """현재 사용자 응답 여부 반환"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                church_id = self.context.get('church_id')
                church_user = request.user.church_users.get(church_id=church_id)
                member = church_user.member
                return Answer.objects.filter(question__survey=obj, member=member).exists()
            except:
                pass
        return False


class SurveyDetailSerializer(serializers.ModelSerializer):
    """설문조사 상세용 Serializer"""
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    response_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    is_responded = serializers.SerializerMethodField()
    
    class Meta:
        model = Survey
        fields = [
            'id', 'church', 'title', 'description', 'start_date', 'end_date',
            'created_by', 'created_by_detail', 'questions', 'question_count',
            'response_count', 'is_active', 'is_responded', 'created_at', 'updated_at'
        ]
        read_only_fields = ['church', 'created_by', 'created_at', 'updated_at']
    
    def get_question_count(self, obj):
        """질문 수 반환"""
        return obj.questions.count()
    
    def get_response_count(self, obj):
        """응답 수 반환"""
        return Answer.objects.filter(question__survey=obj).values('member').distinct().count()
    
    def get_is_active(self, obj):
        """활성 상태 반환"""
        from datetime import date
        today = date.today()
        return obj.start_date <= today <= obj.end_date
    
    def get_is_responded(self, obj):
        """현재 사용자 응답 여부 반환"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                church_id = self.context.get('church_id')
                church_user = request.user.church_users.get(church_id=church_id)
                member = church_user.member
                return Answer.objects.filter(question__survey=obj, member=member).exists()
            except:
                pass
        return False


class SurveyCreateSerializer(serializers.ModelSerializer):
    """설문조사 생성용 Serializer"""
    
    class Meta:
        model = Survey
        fields = ['title', 'description', 'start_date', 'end_date']
    
    def validate_title(self, value):
        """제목 유효성 검사"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 2자 이상이어야 합니다.")
        return value.strip()
    
    def validate_description(self, value):
        """설명 유효성 검사"""
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("설명은 5자 이상이어야 합니다.")
        return value.strip() if value else value
    
    def validate(self, data):
        """교차 유효성 검사"""
        from datetime import date
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError("시작일은 종료일보다 이전이어야 합니다.")
            
            if end_date < date.today():
                raise serializers.ValidationError("종료일은 오늘 이후여야 합니다.")
        
        return data
    
    def create(self, validated_data):
        """설문조사 생성"""
        user = self.context['request'].user
        church_id = self.context.get('church_id')
        
        validated_data['church_id'] = church_id
        validated_data['created_by'] = user
        
        return super().create(validated_data)


class SurveyUpdateSerializer(serializers.ModelSerializer):
    """설문조사 수정용 Serializer"""
    
    class Meta:
        model = Survey
        fields = ['title', 'description', 'start_date', 'end_date']
    
    def validate_title(self, value):
        """제목 유효성 검사"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 2자 이상이어야 합니다.")
        return value.strip()
    
    def validate_description(self, value):
        """설명 유효성 검사"""
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("설명은 5자 이상이어야 합니다.")
        return value.strip() if value else value
    
    def validate(self, data):
        """교차 유효성 검사"""
        from datetime import date
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError("시작일은 종료일보다 이전이어야 합니다.")
        
        return data


class SurveyResponseSerializer(serializers.Serializer):
    """설문조사 응답용 Serializer"""
    answers = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    def validate_answers(self, value):
        """답변 유효성 검사"""
        if not value:
            raise serializers.ValidationError("답변이 필요합니다.")
        
        for answer_data in value:
            question_id = answer_data.get('question_id')
            answer_text = answer_data.get('answer_text')
            selected_choices = answer_data.get('selected_choices', [])
            
            if not question_id:
                raise serializers.ValidationError("질문 ID가 필요합니다.")
            
            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                raise serializers.ValidationError(f"질문을 찾을 수 없습니다: {question_id}")
            
            if question.question_type == 'TEXT':
                if not answer_text or len(answer_text.strip()) < 1:
                    raise serializers.ValidationError("주관식 답변은 필수입니다.")
            elif question.question_type in ['SINGLE_CHOICE', 'MULTIPLE_CHOICE']:
                if not selected_choices:
                    raise serializers.ValidationError("선택지를 선택해주세요.")
                
                # 선택지 유효성 검사
                valid_choices = question.choices or []
                for choice in selected_choices:
                    if choice not in valid_choices:
                        raise serializers.ValidationError(f"유효하지 않은 선택지입니다: {choice}")
                
                # 단일 선택 검사
                if question.question_type == 'SINGLE_CHOICE' and len(selected_choices) > 1:
                    raise serializers.ValidationError("단일 선택 질문은 하나의 선택지만 선택할 수 있습니다.")
        
        return value
