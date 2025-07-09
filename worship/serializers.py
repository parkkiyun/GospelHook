from rest_framework import serializers
from .models import WorshipRecord

class WorshipRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorshipRecord
        fields = '__all__'
