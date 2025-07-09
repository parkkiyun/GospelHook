from rest_framework import serializers
from .models import Bulletin

class BulletinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bulletin
        fields = '__all__'
