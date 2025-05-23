# users/views.py

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import User, Role, UserRole, Program, Client
from .serializers import UserCreateSerializer, RoleSerializer, UserSerializer, ProgramCreateSerializer, ProgramsSerializer, CustomUserDetailsSerializer, NewClientSerializer
from dj_rest_auth.views import UserDetailsView

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
    def get(self, request):
        clients = Client.objects.filter(new_client=True)
        serializer = NewClientSerializer(clients, many=True)
        return Response(serializer.data)

