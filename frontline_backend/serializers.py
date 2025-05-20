# users/serializers.py

from rest_framework import serializers
from .models import User, UserRole, Role

class UserCreateSerializer(serializers.ModelSerializer):
    role_id = serializers.IntegerField(write_only=True)  # coming from frontend

    class Meta:
        model = User
        fields = [
            'name', 'phone', 'email', 'password', 'resume', 'address', 'state', 'country',
            'pincode', 'age', 'gender', 'joining_date', 'available_time',
            'available_days', 'contract', 'status', 'language', 'role_id'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        role_id = validated_data.pop('role_id')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)

        # Assign role
        role = Role.objects.get(id=role_id)
        UserRole.objects.create(user=user, role=role)

        return user

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'rolename']
class UserRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer()  # Nest role inside

    class Meta:
        model = UserRole
        fields = ['role']

class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'roles']

    def get_roles(self, obj):
        roles = UserRole.objects.filter(user=obj)
        return UserRoleSerializer(roles, many=True).data

