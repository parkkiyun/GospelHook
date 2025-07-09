from rest_framework import serializers
from .models import CareLog

class CareLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareLog
        fields = '__all__'
