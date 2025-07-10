from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, ChurchUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    """사용자 등록 시리얼라이저"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password_confirm')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """사용자 로그인 시리얼라이저"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('아이디 또는 비밀번호가 올바르지 않습니다.')
            if not user.is_active:
                raise serializers.ValidationError('비활성화된 계정입니다.')
            attrs['user'] = user
        return attrs


class ChurchUserSerializer(serializers.ModelSerializer):
    """교회 사용자 시리얼라이저"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    church_name = serializers.CharField(source='church.name', read_only=True)
    
    class Meta:
        model = ChurchUser
        fields = (
            'id', 'user_email', 'church_name', 'role', 'name', 
            'phone', 'position', 'is_active', 'joined_at'
        )
        read_only_fields = ('joined_at',)


class UserSerializer(serializers.ModelSerializer):
    """기본 사용자 시리얼라이저"""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'is_verified', 'created_at')
        read_only_fields = ('id', 'is_verified', 'created_at')


class UserProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 시리얼라이저"""
    church_profiles = ChurchUserSerializer(source='church_users', many=True, read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'is_verified', 
            'last_login', 'created_at', 'church_profiles'
        )
        read_only_fields = ('id', 'email', 'is_verified', 'last_login', 'created_at')


class PasswordChangeSerializer(serializers.Serializer):
    """비밀번호 변경 시리얼라이저"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('현재 비밀번호가 올바르지 않습니다.')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('새 비밀번호가 일치하지 않습니다.')
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
