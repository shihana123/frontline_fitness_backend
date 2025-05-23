from dj_rest_auth.views import LoginView
from django.urls import path
from .views import UserCreateView, RoleListView, UserListView, UsersByRoleView, ProgramCreateView, ProgramListView, CustomUserDetailsView, NewClientListView

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),

    path('userDetails/', CustomUserDetailsView.as_view(), name='rest_user_details'),
    path('userCreate', UserCreateView.as_view(), name='user-create'),
    path('userList', UserListView.as_view(), name='user-list'),
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('byrole/<int:role_id>/', UsersByRoleView.as_view(), name='user-role'),

    path('programCreate', ProgramCreateView.as_view(), name='program-create'),
    path('ProgramList', ProgramListView.as_view(), name='program-list'),

    path('clientList', NewClientListView.as_view(), name='client-list'),

]