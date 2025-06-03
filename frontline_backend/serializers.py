# users/serializers.py

from rest_framework import serializers
from django.db.models import Count
from .models import User, UserRole, Role, Program, Client, ProgramClient, ConsulationSchedules, TrainerConsultationDetails
from dj_rest_auth.serializers import UserDetailsSerializer
from django.utils.timezone import localtime
from .constants import ROLE_PREFIXES 

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

        # Generate user_id
        existing_count = UserRole.objects.filter(role=role).count()

        # Step 5: Generate user_id
        prefix = ROLE_PREFIXES.get(role.rolename.lower(), 'XX')
        serial_number = str(existing_count).zfill(2)  # e.g., 00, 01, 02...
        user.user_id = f"FF{prefix}{serial_number}"
        user.save()

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
        fields = ['id', 'name', 'email', 'phone', 'roles', 'user_id']

    def get_roles(self, obj):
        user_roles = UserRole.objects.filter(user=obj).select_related('role')
        return UserRoleSerializer(user_roles, many=True).data

class CustomUserDetailsSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'roles']

    def get_roles(self, obj):
        user_roles = UserRole.objects.filter(user=obj).select_related('role')
        return UserRoleSerializer(user_roles, many=True).data
    
class ProgramCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = '__all__'

    # Optional: Validate that the trainers are users with proper roles if needed
    def validate_group_trainer_level1(self, value):
        if value and not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Invalid group_trainer_level1 user.")
        return value

    def validate_group_trainer_level2(self, value):
        if value and not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Invalid group_trainer_level2 user.")
        return value
    

class ProgramsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = ['id', 'name', 'program_type']

class ProgramClientSerializer(serializers.ModelSerializer):
    program = ProgramsSerializer()

    class Meta:
        model = ProgramClient
        fields = ['program', 'preferred_time', 'preferred_group_time', 'status']

class NewClientSerializer(serializers.ModelSerializer):
    programs = ProgramClientSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'new_client', 'client_id', 
                  'diet_first_consultation', 'trainer_first_consultation', 'programs']
        
    def get_programs(self, obj):
        user = self.context['request'].user  # logged-in user
        # Filter only programs where trainer is the logged-in user
        program_clients = obj.programs.filter(trainer=user)
        return ProgramClientSerializer(program_clients, many=True).data

class ConsultationScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsulationSchedules
        fields = '__all__'

class TrainerConsultationDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerConsultationDetails
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    programs = ProgramClientSerializer(many=True, read_only=True)
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'status', 'programs', 'client_id', 'workout_start_date']
    def get_programs(self, obj):
        user = self.context['request'].user  # logged-in user
        # Filter only programs where trainer is the logged-in user
        program_clients = obj.programs.filter(trainer=user)
        return ProgramClientSerializer(program_clients, many=True).data

class ConsultationScheduleWithClientSerializer(serializers.ModelSerializer):
    client = ClientSerializer()  # nested serializer
    completed_consultations = serializers.SerializerMethodField()
    last_consultation_datetime = serializers.SerializerMethodField()
    last_consultation_user_id = serializers.SerializerMethodField()

    class Meta:
        model = ConsulationSchedules
        fields = ['id', 'client', 'user', 'no_of_consultation', 'completed_consultations', 'datetime', 'type', 'status', 'created_at', 'last_consultation_datetime', 'last_consultation_user_id']

    def get_completed_consultations(self, obj):
        return max(obj.no_of_consultation - 1, 0)
    
    def get_last_consultation_datetime(self, obj):
        last = ConsulationSchedules.objects.filter(
            client=obj.client,
            user=obj.user
        ).order_by('-datetime').first()

        if last and last.datetime:
            # Convert to local time before formatting
            local_dt = localtime(last.datetime)
            return local_dt.strftime('%d-%m-%Y %H:%M')

        return None

    def get_last_consultation_user_id(self, obj):
        last = ConsulationSchedules.objects.filter(
            client=obj.client,
            user=obj.user,
        ).exclude(id=obj.id).order_by('-datetime').first()
        return last.user.id if last else obj.user.id 

                        


