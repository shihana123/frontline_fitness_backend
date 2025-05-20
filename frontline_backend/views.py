# users/views.py

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import User, Role
from .serializers import UserCreateSerializer, RoleSerializer, UserSerializer

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

