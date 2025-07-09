from django.db import models

class Survey(models.Model):
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    title = models.CharField(max_length=200, verbose_name='설문 제목')
    description = models.TextField(blank=True, verbose_name='설문 설명')
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='생성자')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '설문조사'
        verbose_name_plural = '설문조사'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Question(models.Model):
    class QuestionType(models.TextChoices):
        TEXT = 'TEXT', '주관식'
        SINGLE_CHOICE = 'SINGLE_CHOICE', '단일 선택'
        MULTIPLE_CHOICE = 'MULTIPLE_CHOICE', '다중 선택'

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions', verbose_name='설문조사')
    question_text = models.TextField(verbose_name='질문 내용')
    question_type = models.CharField(max_length=20, choices=QuestionType.choices, verbose_name='질문 유형')
    choices = models.JSONField(default=list, blank=True, verbose_name='선택지 (JSON 배열)') # 단일/다중 선택용

    class Meta:
        verbose_name = '질문'
        verbose_name_plural = '질문'

    def __str__(self):
        return f'{self.survey.title} - {self.question_text[:30]}...'

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='질문')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, verbose_name='응답 교인')
    answer_text = models.TextField(blank=True, verbose_name='주관식 응답')
    selected_choices = models.JSONField(default=list, blank=True, verbose_name='선택된 선택지 (JSON 배열)')
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name='응답 시각')

    class Meta:
        verbose_name = '응답'
        verbose_name_plural = '응답'
        unique_together = ('question', 'member') # 한 교인은 한 질문에 한 번만 응답 가능

    def __str__(self):
        return f'{self.member.name} - {self.question.question_text[:20]}...'