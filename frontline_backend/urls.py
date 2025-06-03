from dj_rest_auth.views import LoginView
from django.urls import path
from .views import UserCreateView, RoleListView, UserListView, UsersByRoleView, ProgramCreateView, ProgramListView, CustomUserDetailsView, NewClientListView, ScheduleConsultationView, TrainerConsultationDetails , ConsultationScheduleDetails, ClientListView, ClientDetailsView

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),

    path('userDetails/', CustomUserDetailsView.as_view(), name='rest_user_details'),
    path('userCreate', UserCreateView.as_view(), name='user-create'),
    path('userList', UserListView.as_view(), name='user-list'),
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('byrole/<int:role_id>/', UsersByRoleView.as_view(), name='user-role'),

    path('programCreate', ProgramCreateView.as_view(), name='program-create'),
    path('ProgramList', ProgramListView.as_view(), name='program-list'),

    path('newclientList', NewClientListView.as_view(), name='newclient-list'),
    path('clientList', ClientListView.as_view(), name='client-list'),
    path('clientDetails/<int:client_id>/', ClientDetailsView.as_view(), name='client-details'),


    path('scheduleconsulation', ScheduleConsultationView.as_view(), name='schedule-consultation'),
    path('trainerconsulation_details', TrainerConsultationDetails.as_view(), name='trainer_consulation_details'),
    path('consulationscheduleList', ConsultationScheduleDetails.as_view(), name='consulation-schedule-list'),
]