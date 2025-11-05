from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'password',
        ]
        read_only_fields = [
            'id',
            'role_display',
            'date_joined',
            'last_login',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }
