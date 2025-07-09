from rest_framework import serializers
from .models import Announcement, PushLog

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'

class PushLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushLog
        fields = '__all__'