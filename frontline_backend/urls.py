from dj_rest_auth.views import LoginView
from django.urls import path
from .views import UserCreateView, RoleListView, UserListView, UsersByRoleView, ProgramCreateView, ProgramListView, CustomUserDetailsView, NewClientListView, ScheduleConsultationView, TrainerConsultationDetails , ConsultationScheduleDetails, ClientListView, ClientDetailsView, WeeklyWorkoutDetailsView, SaveWeeklyWorkoutUpdatesView, ClientListByDateView, MarkClientAttendanceView, ClientListByMonthView, ProgramListwithTypeView

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
    path('clientListbyDate/<str:attendance_date>/', ClientListByDateView.as_view(), name='client-list-by-date'),
    path('clientListbyMonth/<int:client_id>/<int:year>/<int:month>/', ClientListByMonthView.as_view(), name='client-list-by-month'),
    path('markClientAttendance/', MarkClientAttendanceView.as_view(), name='mark-client-attendance'),

    path('weekworkoutDetails/<int:client_id>/', WeeklyWorkoutDetailsView.as_view(), name='weekly-workout-details'),
    path('workout/update/<int:client_id>/<int:week_table_id>', SaveWeeklyWorkoutUpdatesView.as_view(), name='weekly-workout-updates'),


    path('scheduleconsulation', ScheduleConsultationView.as_view(), name='schedule-consultation'),
    path('trainerconsulation_details', TrainerConsultationDetails.as_view(), name='trainer_consulation_details'),
    path('consulationscheduleList', ConsultationScheduleDetails.as_view(), name='consulation-schedule-list'),

    path('programListTrainer/<str:program_type>/', ProgramListwithTypeView.as_view(), name='program-list-type'),
    
]