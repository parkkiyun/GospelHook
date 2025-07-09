from rest_framework import serializers
from .models import EducationProgram, EducationRegistration

class EducationProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationProgram
        fields = '__all__'

class EducationRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationRegistration
        fields = '__all__'