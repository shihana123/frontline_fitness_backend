# users/views.py

from rest_framework import generics
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import User, Role, UserRole, Program, Client, ConsulationSchedules, ProgramClient, WeeklyWorkoutUpdates
from .serializers import UserCreateSerializer, RoleSerializer, UserSerializer, ProgramCreateSerializer, ProgramsSerializer, CustomUserDetailsSerializer, NewClientSerializer, ConsultationScheduleSerializer, TrainerConsultationDataSerializer, ConsultationScheduleWithClientSerializer, ClientSerializer, WeeklyWorkoutSerializer
from dj_rest_auth.views import UserDetailsView
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
import calendar

class CustomUserDetailsView(UserDetailsView):
    serializer_class = CustomUserDetailsSerializer

class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

class RoleListView(APIView):
    def get(self, request):
        roles = Role.objects.filter(status=True)  # optional filter
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
class UserListView(APIView):
    def get(self, request):
        # users = User.objects.filter(status=True)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UsersByRoleView(APIView):
    def get(self, request, role_id):
        user_roles = UserRole.objects.filter(role__id=role_id).select_related('user', 'role')
        users = [user_role.user for user_role in user_roles]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class ProgramCreateView(APIView):
    def post(self, request):
        serializer = ProgramCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Program created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProgramListView(APIView):
    def get(self, request):
        # users = User.objects.filter(status=True)
        programs = Program.objects.all()
        serializer = ProgramsSerializer(programs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class NewClientListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user.id
        clients = Client.objects.filter(new_client=True, programs__trainer_id = user).distinct()
        serializer = NewClientSerializer(clients, many=True)
        return Response(serializer.data)
    

class ScheduleConsultationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id  # Attach logged-in user automatically

        serializer = ConsultationScheduleSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            client_id = serializer.validated_data['client'].id  # Extract client from validated data
            user_id = request.user.id
            client = Client.objects.get(id=client_id)
            client.trainer_first_consultation = 2

            
            no_of_consultation = serializer.validated_data.get('no_of_consultation')
            no_of_consultation = serializer.validated_data.get('no_of_consultation')

            if no_of_consultation == 2:
                client.new_client = False
                client.trainer_first_consultation = 1

                

            workout_start_date = request.data.get('workout_start_date')
            if workout_start_date:
                client.workout_start_date = workout_start_date
            client.save()

            if workout_start_date and no_of_consultation == 2:
                program_client = ProgramClient.objects.filter(client=client, status="active").last()
                if program_client and program_client.workout_days:
                    no_of_days = len(program_client.workout_days)
                else:
                    no_of_days = 0

                workout_start_date = datetime.strptime(workout_start_date, "%Y-%m-%d").date()
                start_weekday = workout_start_date.weekday()  # Monday=0, Sunday=6
                days_until_saturday = (calendar.SATURDAY - start_weekday) % 7
                week_end_date = workout_start_date + timedelta(days=days_until_saturday)

                WeeklyWorkoutUpdates.objects.create(
                    client = client,
                    trainer_id = request.user,
                    week_no = 1,
                    no_of_days = no_of_days,
                    week_start_date = workout_start_date,
                    week_end_date = week_end_date,
                    status = False
                )

            # Update latest ConsulationSchedules row's status to True (1)
            previous_consultation = ConsulationSchedules.objects.filter(
                client=client,
                user=request.user,
                status=False  # assuming you're only interested in those not already marked True
            ).order_by('-datetime')[1:2].first()

            if previous_consultation:
                previous_consultation.status = True
                previous_consultation.save()

            # client.save()
            return Response({'message': 'Consultation scheduled successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TrainerConsultationDetails(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id  # Attach logged-in user automatically

        serializer = TrainerConsultationDataSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            client_id = serializer.validated_data['client'].id  # Extract client from validated data
            client = Client.objects.get(id=client_id)
            client.trainer_first_consultation = 3
            client.save()

            return Response({'message': 'Consultation Data saved successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConsultationScheduleDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        consultations = ConsulationSchedules.objects.filter(
            Q(user=request.user),
            Q(status=False),
            Q(client__trainer_first_consultation=3) | Q(client__trainer_first_consultation=1)
        ).select_related('client')
        serializer = ConsultationScheduleWithClientSerializer(consultations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ClientListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user.id
        clients = Client.objects.filter(new_client=False, programs__trainer_id = user).distinct()
        serializer =ClientSerializer(clients, many=True)
        return Response(serializer.data)
    
class ClientDetailsView(APIView):
    def get(self, request, client_id):
        clients = Client.objects.filter(id=client_id)
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)

class WeeklyWorkoutDetailsView(APIView):
    def get(self, request, client_id):
        client = Client.objects.get(id=client_id)
        weekly_updates = WeeklyWorkoutUpdates.objects.filter(client=client).order_by('-week_no')
        serializer = WeeklyWorkoutSerializer(weekly_updates, many=True)
        return Response(serializer.data)