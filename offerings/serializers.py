from rest_framework import serializers
from .models import Offering

class OfferingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offering
        fields = '__all__'
