from dj_rest_auth.views import LoginView
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import UserCreateView, RoleListView, UserListView, UsersByRoleView, ProgramCreateView, ProgramListView, CustomUserDetailsView, NewClientListView, ScheduleConsultationView, TrainerConsultationDetails , ConsultationScheduleDetails, ClientListView, ClientDetailsView, WeeklyWorkoutDetailsView, SaveWeeklyWorkoutUpdatesView, ClientListByDateView, MarkClientAttendanceView, ClientListByMonthView, ProgramListwithTypeView, TrainerScheduleView, TrainerAvailabilityView, CountryListView, LeadCreateView, LeadsListView, LeadsView, LeadsUpdate, UsersRoleView, SalesClientListView, AssignTrainerDietitianView, followupStatusUpdateView, TrainerScheduleHourlyView, fetchFollowupsView, groupProgramListView, groupProgramView, NewLeadView, GraphLeadView, GraphRevenueView, NewClientListDietitianView, DietitianConsultationDetailsView, DietConsultationScheduleDetails, DietitianClientListView, WeeklyDietDetailsView, SaveWeeklyDietUpdatesView, ActiveClientDietitianView, ConsultationDietitianView, UpcomingConsultDietView, MissedConsultDietView, DietConsultationDetails, DietGraphView, BiweeklyDetailsView, BiweeklyDataUpdateView, CountBiweeklyUpdationView, DietClientMeetingsView, DietFirstConsultationDetails, DietMeetingUpdationsView, MeetingDetailsView, RemidersListView, UpdateMeetingView, DietOnlyMeetingUpdationsView, FetchMeetingDetailsView, TDCMeetingUpdateView, WeeklyMeetingView, UpdateWeeklyMeeting, WeeklyMeetingByWeekNoView, WeeklyMeetingDetailsView, MeasurementListView, MeasurementDataUpdateView, MeasurementDetailsView, MeasurementProgressView, DietChartListView, DietChartUpdateView

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),

    path('fetchCountry/', CountryListView.as_view(), name='country-list'),

    path('userDetails/', CustomUserDetailsView.as_view(), name='rest_user_details'),
    path('userCreate', UserCreateView.as_view(), name='user-create'),
    path('userList', UserListView.as_view(), name='user-list'),
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('byrole/<int:role_id>/', UsersByRoleView.as_view(), name='user-role'),
    path('getRole', UsersRoleView.as_view(), name='user-role-name'),

    path('programCreate', ProgramCreateView.as_view(), name='program-create'),
    path('ProgramList', ProgramListView.as_view(), name='program-list'),
    path('group-programs', groupProgramListView.as_view(), name='group-program-list'),
    path('single-group-programs/<int:program_id>', groupProgramView.as_view(), name='single-group-program'),

    path('newclientList', NewClientListView.as_view(), name='newclient-list'),
    path('newclientListDietitian', NewClientListDietitianView.as_view(), name='newclient-list-dietitian'),
    path('clientList', ClientListView.as_view(), name='client-list'),
    path('dietitianclientList', DietitianClientListView.as_view(), name='dietitian-client-list'),
    path('clientDetails/<int:client_id>/', ClientDetailsView.as_view(), name='client-details'),
    path('clientListbyDate/<str:attendance_date>/', ClientListByDateView.as_view(), name='client-list-by-date'),
    path('clientListbyMonth/<int:client_id>/<int:year>/<int:month>/', ClientListByMonthView.as_view(), name='client-list-by-month'),
    path('markClientAttendance/', MarkClientAttendanceView.as_view(), name='mark-client-attendance'),

    path('weekworkoutDetails/<int:client_id>/', WeeklyWorkoutDetailsView.as_view(), name='weekly-workout-details'),
    path('workout/update/<int:client_id>/<int:week_table_id>', SaveWeeklyWorkoutUpdatesView.as_view(), name='weekly-workout-updates'),


    path('scheduleconsulation', ScheduleConsultationView.as_view(), name='schedule-consultation'),
    path('trainerconsulation_details', TrainerConsultationDetails.as_view(), name='trainer_consulation_details'),
    path('consulationscheduleList', ConsultationScheduleDetails.as_view(), name='consulation-schedule-list'),
    path('dietconsulationscheduleList', DietConsultationScheduleDetails.as_view(), name='diet-consulation-schedule-list'),

    path('programListTrainer/<str:program_type>/', ProgramListwithTypeView.as_view(), name='program-list-type'),
    # path('availabilityTrainer/<int:trainer_id>/', TrainerScheduleView.as_view(), name='availability-trainer'),
    path('availabilityTrainer', TrainerScheduleView.as_view(), name='availability-trainer'),
    path('trainerHourlySchedule', TrainerScheduleHourlyView.as_view(), name='availability-trainer'),
    path('timingTrainer/<int:trainer_id>/', TrainerAvailabilityView.as_view(), name='timing-trainer'),

    path('leadCreate', LeadCreateView.as_view(), name='lead-create'),
    path('leadsList', LeadsListView.as_view(), name='lead-list'),
    path('fetchLead/<int:lead_id>', LeadsView.as_view(), name='lead-view'),
    path('leadUpdate/<int:lead_id>', LeadsUpdate.as_view(), name='lead-update'),
    path('salesclientList', SalesClientListView.as_view(), name='sales-client-list'),
    path('assignTrainerDietitian', AssignTrainerDietitianView.as_view(), name='assign-trainer-dietitian'),
    path('followupStatusUpdate', followupStatusUpdateView.as_view(), name='followup-status-update'),
    path('fetchFollowups/<int:client_id>', fetchFollowupsView.as_view(), name='fetch-followup'),

    path('fetchNewleads/<str:month>/<int:year>/', NewLeadView.as_view(), name='new-lead-count'),
    path('fetchleadsgraph/<str:month>/<int:year>/', GraphLeadView.as_view(), name='grpah-lead-count'),
    path('fetchrevenuegraph/<int:year>/', GraphRevenueView.as_view(), name='grpah-revenue-count'),

    path('dietitianconsulation_details', DietitianConsultationDetailsView.as_view(), name='dietitian-consulation-details'),
    path('weekdietDetails/<int:client_id>/', WeeklyDietDetailsView.as_view(), name='weekly-diet-details'),
    path('diet_chart/update/<int:client_id>', SaveWeeklyDietUpdatesView.as_view(), name='weekly-diet-updates'),
    path('fetchActiveClientsDietitian/', ActiveClientDietitianView.as_view(), name='diet-active-clients'),
    path('fetchConsultationDietitian/', ConsultationDietitianView.as_view(), name='diet-consulattion-clients'),
    path('dietupcomingconsulationscheduleList', UpcomingConsultDietView.as_view(), name='upcoming-consulattion-clients'),
    path('dietmissedconsulationscheduleList', MissedConsultDietView.as_view(), name='missed-consulattion-clients'),
    path('dietconsulationDetails/<int:client_id>', DietConsultationDetails.as_view(), name='diet-consulattion-details'),
    path('diet_chart_graph/<int:client_id>/', DietGraphView.as_view(), name='diet-graph-view'),
    path('measurementList/<int:client_id>/', MeasurementListView.as_view(), name='measurement-list-view'),
    path('measureData/update', MeasurementDataUpdateView.as_view(), name='measurement-update-view'),
    path('measurementDetails/<int:meeting_id>/', MeasurementDetailsView.as_view(), name='measurement-details-view'),
    path('measureProgressData/<int:client_id>/', MeasurementProgressView.as_view(), name='measurement-progress-view'),
    path('fetchupsomingbiweeklyUpdation/', CountBiweeklyUpdationView.as_view(), name='biweekly-upcoming-clients'),

    path('dietclientMeetingList/<int:client_id>', DietClientMeetingsView.as_view(), name='diet-client-meeting'),
    path('dietfirstconsulationdetails/<int:client_id>', DietFirstConsultationDetails.as_view(), name='diet-first-consultaion'),
    path('dietMeetingUpdations', DietMeetingUpdationsView.as_view(), name='diet-meeting-updations'),
    path('getMeetingDetails/<int:meeting_id>', MeetingDetailsView.as_view(), name='meeting-details'),
    path('fetchReminders/', RemidersListView.as_view(), name='reminder-list'),
    path('updateMeeting/<str:update>/<int:meeting_id>', UpdateMeetingView.as_view(), name='update-meeting'),
    path('dietOnlyMeetingUpdations', DietOnlyMeetingUpdationsView.as_view(), name='diet-meeting'),
    path('fetchMeetingDetails/<int:meeting_id>', FetchMeetingDetailsView.as_view(), name='meeting-details'),
    path('TDCMeetingUpdations', TDCMeetingUpdateView.as_view(), name='tdc-meeting-update'),
    path('weeklyMeetingList/<int:client_id>', WeeklyMeetingView.as_view(), name='week-meeting-list'),
    # path('weeklyMeetingList/<int:client_id>', WeeklyMeetingView.as_view(), name='week-meeting-list'),
    path('updateWeeklydata', UpdateWeeklyMeeting.as_view(), name='update-week-meeting'),
    path('weeklyMeetingDetails/<int:meeting_id>', WeeklyMeetingDetailsView.as_view(), name='week-meeting-details'),
    path('weeklyMeetingByWeekNo', WeeklyMeetingByWeekNoView.as_view(), name='weekly-meeting-by-weekno'),
    path('dietchartList/<int:client_id>/', DietChartListView.as_view(), name='diet-chart-list'),
    path('dietChart/update', DietChartUpdateView.as_view(), name='diet-chart-update'),

    
]

# 👇 This enables serving media files (like PDFs) in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)