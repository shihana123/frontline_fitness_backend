from dj_rest_auth.views import LoginView
from django.urls import path
from .views import UserCreateView, RoleListView, UserListView

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('userCreate', UserCreateView.as_view(), name='user-create'),
    path('userList', UserListView.as_view(), name='user-list'),
    path('roles/', RoleListView.as_view(), name='role-list'),
]