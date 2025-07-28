# users/views.py

from rest_framework import generics
from django.db import models
from django.db.models import Q, OuterRef, Subquery, Exists, Case, When, Value, IntegerField, BooleanField, F
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import User, Role, UserRole, Program, Client, ConsulationSchedules, ProgramClient, WeeklyWorkoutUpdates, WeeklyWorkoutwithDaysUpdates, ClienAttendanceUpdates, Country, Leads, LeadsFollowup, weeklydietupdates, MonthlyDietConsultationDetails, DietitianConsultationDetails, BiweeklyUpdations, ClientSubscription, MeetingsTDC, Measurementsclients, MeetingTDCDetails, WeeklyMeeting, SubscriptionPause, ClientPauseLimit, ClientPause, DietchartClient, TrainerMeetingTDCDetails, ReschedulesSessions, MainProgram
from .serializers import UserCreateSerializer, RoleSerializer, UserSerializer, ProgramCreateSerializer, ProgramsSerializer, CustomUserDetailsSerializer, NewClientSerializer, ConsultationScheduleSerializer, TrainerConsultationDataSerializer, ConsultationScheduleWithClientSerializer, ClientSerializer, WeeklyWorkoutSerializer, ProgramClientDaysSerializer, CountrySerializer, LeadCreateSerializer, LeadsSerializer, GroupProgramSerializer, DietitianConsultationDataSerializer, WeeklyDietSerializer, WeeklyDietUpdateSerializer, BiweeklyUpdationsSerializer, MeetingsTDCSerializer, DietitianConsultationDetailsSerializer, MeasurementsclientsSerializer, MeetingTDCDetailsSerializer, WeeklyMeetingSerializer, MeetingTDCDetailswithDietSerializer, ClientWithDietchartSerializer, ClientPauseLimitSerializer, ClientPauseSerializer,TrainerMeetingTDCDetailsSerializer, ReschedulesSessionsSerializer, MainProgramsSerializer, MainProgramCreateSerializer
from dj_rest_auth.views import UserDetailsView
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta, date, time
import calendar
from calendar import monthrange, month_name
from django.shortcuts import get_object_or_404
import re
from django.utils import timezone
from django.utils.dateparse import parse_time
from django.utils.timezone import now
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models.functions import ExtractMonth
from django.core.exceptions import ObjectDoesNotExist
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

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
        # users = User.objects.all()
        # user_roles = UserRole.objects.filter(role__id=1).select_related('user', 'role')
        # users = [user_role.user for user_role in user_roles]

        users = User.objects.exclude(
            Q(id__in=UserRole.objects.filter(role__rolename__iexact='admin').values_list('user_id', flat=True)) |
            Q(is_superuser=True)
        )
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

class MainProgramCreateView(APIView):
    def post(self, request):
        serializer = MainProgramCreateSerializer(data=request.data)
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

class NewClientListDietitianView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user.id
        clients = Client.objects.filter(new_client=True, programs__dietitian_id = user).distinct()
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
        type = serializer.validated_data.get('type')
        
        
        if type == 'trainer':
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

                    week_range = [workout_start_date + timedelta(days=i) for i in range((week_end_date - workout_start_date).days + 1)]
                    current_week_days = [day.strftime('%A').lower() for day in week_range]

                    week_no_of_days = 0
                    week_workout_days = []
                    week_workout_dates = []
                    if program_client and program_client.workout_days:
                        client_days = [day.lower() for day in program_client.workout_days]
                        # Count how many of client's workout days fall in this week range
                        # week_no_of_days = sum(1 for day in current_week_days if day in client_days)

                        for week_date, day_name in zip(week_range, current_week_days):
                            if day_name in client_days:
                                week_no_of_days += 1
                                week_workout_days.append(day_name)
                                week_workout_dates.append(week_date.strftime('%Y-%m-%d'))

                    WeeklyWorkoutUpdates.objects.create(
                        client = client,
                        trainer_id = request.user,
                        week_no = 1,
                        no_of_days = no_of_days,
                        week_no_of_days = week_no_of_days,
                        week_start_date = workout_start_date,
                        week_end_date = week_end_date,
                        week_workout_days = week_workout_days,
                        week_workout_dates = week_workout_dates,
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
        elif type == 'dietitian':
            # if serializer.is_valid():
            #     serializer.save()
                client_id = serializer.validated_data['client'].id  # Extract client from validated data
                user_id = request.user.id
                client = Client.objects.get(id=client_id)
                client.diet_first_consultation = 2
                
                no_of_consultation = serializer.validated_data.get('no_of_consultation')
                if no_of_consultation == 2:
                    client.new_client = False
                    client.diet_first_consultation = 1

                if no_of_consultation >= 2:
                    previous_consultation = ConsulationSchedules.objects.filter(
                        client=client,
                        user=request.user,
                        status=False  # assuming you're only interested in those not already marked True
                    ).order_by('-datetime')[1:2].first()

                    if previous_consultation:
                        previous_consultation.status = True
                        previous_consultation.save()

                    # Insert into MonthlyDietConsultationDetails
                    consult_date = serializer.validated_data.get('datetime')
                    height = request.data.get('height', 0)
                    weight = request.data.get('weight', 0)
                    bmi = request.data.get('bmi', 0)
                    notes = request.data.get('notes', '')

                    MonthlyDietConsultationDetails.objects.create(
                        client=client,
                        dietitian_id=request.user,
                        month=datetime.now().month,
                        consult_date=previous_consultation.datetime.date(),
                        height=height,
                        weight=weight,
                        bmi=bmi,
                        notes=notes,
                        consult_schedule=previous_consultation.id
                    )

                client.save()
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
    
class DietitianConsultationDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id

        user = request.user
        try:
            program_client = ProgramClient.objects.get(client=data['client'])
        except ProgramClient.DoesNotExist:
            return Response({'error': 'ProgramClient not found'}, status=status.HTTP_404_NOT_FOUND)

        trainer = program_client.trainer
        dietitian = program_client.dietitian
        program_type = program_client.program_type

        is_trainer = user == trainer
        is_dietitian = user == dietitian

        # Determine role-specific serializer
        if is_dietitian:
            serializer = DietitianConsultationDataSerializer(data=data)
        elif is_trainer:
            serializer = TrainerConsultationDataSerializer(data=data)
        else:
            return Response({'error': 'You are not assigned as trainer or dietitian for this client.'}, status=status.HTTP_403_FORBIDDEN)

        if serializer.is_valid():
            serializer.save()
            client_id = serializer.validated_data['client'].id
            client = Client.objects.get(id=client_id)

            if is_dietitian:
                client.diet_first_consultation = 1
            elif is_trainer:
                client.trainer_first_consultation = 1

            client.new_client = False
            client.save()

            try:
                subscription = ClientSubscription.objects.filter(client=client, subscription_type='new').latest('id')
            except ClientSubscription.DoesNotExist:
                return Response({'error': 'No subscription found'}, status=status.HTTP_404_NOT_FOUND)

            program_months = subscription.program_months
            start_date = date.today() + timedelta(days=1)
            end_date = start_date + timedelta(days=program_months * 30)
            subscription.program_start_date = start_date
            subscription.program_end_date = end_date
            subscription.save()

            try:
                program_client = ProgramClient.objects.get(client=client)
            except ProgramClient.DoesNotExist:
                return Response({'error': 'ProgramClient not found'}, status=status.HTTP_404_NOT_FOUND)

            trainer = program_client.trainer
            dietitian = program_client.dietitian
            program_type = program_client.program_type

            # If MeetingsTDC already exists, update status fields only
            existing_meetings = MeetingsTDC.objects.filter(client=client, trainer=trainer, dietitian=dietitian)

            if existing_meetings.exists():
                if is_trainer:
                    existing_meetings.update(trainer_status=True)
                    MeetingsTDC.objects.filter(
                        client=client,
                        trainer=trainer,
                        dietitian=dietitian,
                        day_no=1,
                        dietitian_status=True
                    ).update(status=True)

                elif is_dietitian:
                    existing_meetings.update(dietitian_status=True)
                    MeetingsTDC.objects.filter(
                        client=client,
                        trainer=trainer,
                        dietitian=dietitian,
                        day_no=1,
                        trainer_status=True
                    ).update(status=True)

                return Response({'message': 'Meeting status updated successfully (no new meetings created).'}, status=status.HTTP_200_OK)

            # Proceed to create new meetings
            if program_type == 'Personal Training':
                base_days = [1, 3, 10]
                next_day = 25
                while next_day <= (program_months * 30):
                    base_days.append(next_day)
                    next_day += 15
                meeting_days = base_days
            else:  # Group
                base_days = [1, 10, 24]
                next_day = 54
                while next_day <= (program_months * 30):
                    base_days.append(next_day)
                    next_day += 30
                meeting_days = base_days

            for i, day in enumerate(meeting_days):
                meeting_date = start_date + timedelta(days=day - 1)
                meeting_type = self.get_meeting_type(day, i, len(meeting_days))

                measurements = False
                if meeting_type in ['Renewal', 'dietchart']:
                    measurements = True
                elif program_type == 'Group' and meeting_type == 'TDC':
                    measurements = True
                elif program_type == 'Personal Training' and meeting_type == 'TDC' and (i % 2 == 0):
                    measurements = True

                meeting = MeetingsTDC.objects.create(
                    client=client,
                    trainer=trainer,
                    dietitian=dietitian,
                    meeting_type=meeting_type,
                    day_no=day,
                    status=(day == 1),
                    trainer_status=(request.user == 'trainer' and day == 1),
                    dietitian_status=(request.user == 'dietitian' and day == 1),
                    meeting_date=meeting_date,
                    actual_meeting_date=None,
                    measurements=measurements
                )

                if request.user == trainer:
                    TrainerMeetingTDCDetails.objects.create(
                        meetingtdc=meeting,
                        need_data=(True if (program_type == 'Group' or (program_type == 'Personal Training' and i % 2 == 0)) else False)
                    )

                if measurements:
                    Measurementsclients.objects.create(meetingtdc=meeting)

            def get_saturdays(start_date, end_date):
                saturdays = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() == 5:
                        saturdays.append(current_date)
                    current_date += timedelta(days=1)
                return saturdays

            saturdays = get_saturdays(start_date, end_date)

            for week_no, sat_date in enumerate(saturdays, start=1):
                WeeklyMeeting.objects.create(
                    client=client,
                    dietitian_id=dietitian,
                    height=0,
                    weight=0,
                    bmi=0,
                    notes=None,
                    week_no=week_no,
                    meeting_date=sat_date,
                    entered_date=None
                )

            return Response({'message': 'Consultation Data saved successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_meeting_type(self, day, index, total):
        if day == 1:
            return 'day_1'
        elif day == 3:
            return 'dietchart'
        elif day == 10:
            return 'dietition_only'
        elif index == total - 1:
            return 'Renewal'
        else:
            return 'TDC'


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

class DietConsultationScheduleDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        consultations = ConsulationSchedules.objects.filter(
            Q(user=request.user),
            Q(status=False),
            Q(no_of_consultation=1),
            Q(client__diet_first_consultation=3) | Q(client__diet_first_consultation=1)
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
    
class DietitianClientListView(APIView):
    # permission_classes = [IsAuthenticated]
    # def get(self, request):
    #     user = request.user.id
    #     clients = Client.objects.filter(new_client=False, programs__dietitian_id = user).distinct()
    #     serializer =ClientSerializer(clients, many=True)
    #     return Response(serializer.data)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user.id
        clients = Client.objects.filter(new_client=False, programs__dietitian_id=user).distinct()

        client_data = []

        for client in clients:
            pause_info = {
                'pause_available': False,
                'pause_days_remaining': 0,
                'pauses_remaining': 0
            }

            # Get latest subscription
            latest_subscription = ClientSubscription.objects.filter(client=client).order_by('-id').first()
            if latest_subscription and latest_subscription.program_type == 'Personal Training':
                sub_months = latest_subscription.program_months

                # Get rule from SubscriptionPause
                try:
                    rule = SubscriptionPause.objects.get(subscription_months=sub_months)
                except SubscriptionPause.DoesNotExist:
                    rule = None

                if rule:
                    # Check if this client already has a pause record
                    try:
                        pause_limit = ClientPauseLimit.objects.get(client=client)
                        pause_info['pause_available'] = pause_limit.no_of_pause_rem > 0
                        pause_info['pause_days_remaining'] = pause_limit.no_of_pause_days_rem
                        pause_info['pauses_remaining'] = pause_limit.no_of_pause_rem
                    except ClientPauseLimit.DoesNotExist:
                        # No pause taken yet, so all pause days are available
                        pause_info['pause_available'] = True
                        pause_info['pause_days_remaining'] = rule.no_of_days
                        pause_info['pauses_remaining'] = rule.no_of_pauses

            serialized = ClientSerializer(client).data
            serialized['pause_info'] = pause_info
            client_data.append(serialized)

        return Response(client_data)

class SalesClientListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user.id
        clients = Client.objects.filter(sales = user).distinct()
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

class SaveWeeklyWorkoutUpdatesView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, client_id, week_table_id):
        trainer_id = request.user.id
        # data = request.data.get('data')

        if not trainer_id:
            return Response({'error': 'trainer_id is missing'}, status=400)
        try:
            client = Client.objects.get(id=client_id)
            trainer = request.user
            weekly_update = WeeklyWorkoutUpdates.objects.get(id=week_table_id)
        except (Client.DoesNotExist, User.DoesNotExist, WeeklyWorkoutUpdates.DoesNotExist):
            return Response({'error': 'Invalid client, trainer, or weekly_update ID.'}, status=status.HTTP_400_BAD_REQUEST)
        
        for item in request.data:
            workout_type = item.get('workout_type')
            sets = item.get('sets') or 0
            reps = item.get('reps') or 0
            week_no = item.get('week_no') or 1
            day_no = int(item.get('day') or 1)
            workout_date = item.get('date')

            if not workout_type:
                continue

            WeeklyWorkoutwithDaysUpdates.objects.create(
                client=client,
                trainer_id=trainer,
                weekly_updates_id=weekly_update,
                week_no=week_no,
                day_no=day_no,
                workout_date=workout_date,
                workout_type=workout_type,
                workout_sets=sets,
                workout_reps=reps
            )

        weekly_update.status = True
        weekly_update.save()

        # Step 2: Prepare next week's data
        if client.workout_start_date:
            program_client = ProgramClient.objects.filter(client=client, status="active").last()

            if program_client and program_client.workout_days:
                client_days = [day.lower() for day in program_client.workout_days]
                no_of_days = len(client_days)
            else:
                no_of_days = 0
                client_days = []

            # Next week's start date is one day after current week_end_date
            current_week_end = weekly_update.week_end_date
            next_week_start = current_week_end + timedelta(days=1)

            # Calculate end of next week (Saturday)
            start_weekday = next_week_start.weekday()
            days_until_saturday = (calendar.SATURDAY - start_weekday) % 7
            next_week_end = next_week_start + timedelta(days=days_until_saturday)

            # Date range for next week
            next_week_range = [next_week_start + timedelta(days=i) for i in range((next_week_end - next_week_start).days + 1)]
            next_week_day_names = [d.strftime('%A').lower() for d in next_week_range]

            # Filter workout days
            week_no_of_days = 0
            week_workout_days = []
            week_workout_dates = []

            for date, day_name in zip(next_week_range, next_week_day_names):
                if day_name in client_days:
                    week_no_of_days += 1
                    week_workout_days.append(day_name)
                    week_workout_dates.append(date.strftime('%Y-%m-%d'))

            # Step 3: Create next WeeklyWorkoutUpdates record
            WeeklyWorkoutUpdates.objects.create(
                client=client,
                trainer_id=request.user,
                week_no=weekly_update.week_no + 1,
                no_of_days=no_of_days,
                week_no_of_days=week_no_of_days,
                week_start_date=next_week_start,
                week_end_date=next_week_end,
                week_workout_days=week_workout_days,
                week_workout_dates=week_workout_dates,
                status=False
            )

        return Response({'success': 'Workout updates saved successfully.'}, status=status.HTTP_201_CREATED)

class ClientListByDateView(APIView):
    permission_classes = [IsAuthenticated]  # ensure only logged-in users can access

    def get(self, request, attendance_date):
        if not attendance_date:
            return Response({'error': 'Date is required'}, status=400)

        try:
            selected_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            weekday = selected_date.strftime('%A').lower()

            # Subquery: Check for active subscription during selected date
            latest_subs = ClientSubscription.objects.filter(
                client=OuterRef('client'),
                program_start_date__lte=selected_date,
                program_end_date__gte=selected_date
            ).order_by('-id')

            # Subquery: Check if attendance exists
            attendance_subquery = ClienAttendanceUpdates.objects.filter(
                client=OuterRef('client'),
                workout_date=selected_date,
                trainer_id=request.user
            )

            # Subquery: Check if session is rescheduled
            reschedule_subquery = ReschedulesSessions.objects.filter(
                client=OuterRef('client'),
                session_date=selected_date,
                trainer=request.user
            )

            # Get program clients filtered with all conditions
            program_clients = ProgramClient.objects.annotate(
                has_valid_subscription=Exists(latest_subs),
                has_attendance=Exists(attendance_subquery),
                has_reschedule=Exists(reschedule_subquery)
            ).filter(
                status='active',
                trainer=request.user,
                workout_days__icontains=weekday,
                has_valid_subscription=True
            ).select_related('client', 'program', 'trainer', 'dietitian')

            serializer = ProgramClientDaysSerializer(program_clients, many=True)

            # Optional: Fetch full reschedule details per client
            reschedules = ReschedulesSessions.objects.filter(
                session_date=selected_date,
                trainer=request.user,
                client__in=[pc.client.id for pc in program_clients]
            )

            from .serializers import ReschedulesSessionsSerializer  # create if needed
            reschedule_data = ReschedulesSessionsSerializer(reschedules, many=True).data

            return Response({
                'clients': serializer.data,
                'reschedules': reschedule_data
            })

        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        
class MarkClientAttendanceView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        client_id = request.data.get('client_id')
        workout_date = request.data.get('workout_date')

        if not client_id or not workout_date:
            return Response({"error": "Client ID and date required"}, status=400)
        try:
            client = Client.objects.get(id=client_id)
            workout_date_obj = datetime.strptime(workout_date, '%Y-%m-%d').date()

            attendance_exists = ClienAttendanceUpdates.objects.filter(
                client=client,
                workout_date=workout_date_obj
            ).exists()

            if attendance_exists:
                return Response({"message": "Attendance already marked"}, status=200)
            ClienAttendanceUpdates.objects.create(
                client=client,
                trainer_id=request.user,
                workout_date=workout_date_obj
            )
            return Response({"message": "Attendance marked successfully"}, status=201)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

class ClientListByMonthView(APIView):
    def get(self, request, client_id, year, month):
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=404)
        workout_start_date = client.workout_start_date
        if not workout_start_date:
            return Response({'error': 'Client has no workout_start_date'}, status=400)

        # Get active program
        program_client = ProgramClient.objects.filter(client=client, status="active").last()
        if not program_client:
            return Response({'error': 'No active program found'}, status=404)

        workout_days = program_client.workout_days or []
        # Normalize to lowercase
        workout_days = [day.lower() for day in workout_days]

        num_days = monthrange(int(year), int(month))[1]
        workout_dates = []

        for day in range(1, num_days + 1):
            current_date = date(int(year), int(month), day)
            if current_date >= workout_start_date:
                if current_date.strftime('%A').lower() in workout_days:
                    # Check if attendance is marked
                    attendance = ClienAttendanceUpdates.objects.filter(client=client, workout_date=current_date).first()
                    
                    workout_dates.append({
                        'date': current_date,
                        'attended': bool(attendance),
                        'attendance_data': {
                            'id': attendance.id,
                            'trainer_id': attendance.trainer_id.id,
                            'status': attendance.status,
                            'created_at': attendance.created_at,
                        } if attendance else None
                    })
        
        return Response({
            'program': {
                'id': program_client.program.id,
                'name': program_client.program.name,
                'type': program_client.program_type,
                'preferred_time': program_client.preferred_time,
            },
            'workout_dates': workout_dates
        })
    
class ProgramListwithTypeView(APIView):
    def get(self, request, program_type):
        if program_type:
            programs = Program.objects.filter(program_type__contains=[program_type])
        else:
            programs = Program.objects.all()

        serializer = ProgramsSerializer(programs, many=True)
        return Response(serializer.data)

class TrainerAvailabilityView(APIView):
    def get(self, request, trainer_id):
        trainer = User.objects.filter(id=trainer_id).first()
        if not trainer:
            return Response({"detail": "Trainer not found."}, status=404)

        return Response({
            "available_days": trainer.available_days,
            "available_time": trainer.available_time
        })

def time_overlap(selected_start, selected_end, booked_start, booked_end):
    return selected_start < booked_end and selected_end > booked_start
 
class TrainerScheduleView(APIView):
    def post(self, request):
        selected_start = parse_time(request.data.get('start_time'))
        selected_end = parse_time(request.data.get('end_time'))

        days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        result = []
        
        trainer_role_id = 3  # or Role.objects.get(rolename='Trainer').id if you prefer dynamic

        trainers = User.objects.filter(
            userrole__role_id=trainer_role_id
        ).distinct()

        for trainer in trainers:
            trainer_data = {
                'trainer_id': trainer.id,
                'trainer_name': trainer.name,
                'availability': {}
            }
            for day in days_of_week:
                # Default to available
                status = {'available': True, 'program_name': None}

                program_clients = ProgramClient.objects.filter(trainer=trainer)
                for pc in program_clients:
                    workout_days = [d.capitalize() for d in (pc.workout_days or [])]
                    if day in workout_days:
                        preferred_times = pc.preferred_time or []
                        for time_range in preferred_times:
                            booked_start = parse_time(time_range[0])
                            booked_end = parse_time(time_range[1])
                            if time_overlap(selected_start, selected_end, booked_start, booked_end):
                                status = {
                                    'available': False,
                                    'program_name': pc.program.name,
                                    'program_time': f"{booked_start.strftime('%H:%M')} - {booked_end.strftime('%H:%M')}"
                                }
                                break

                trainer_data['availability'][day] = status
            result.append(trainer_data)
        return Response(result)

class TrainerScheduleHourlyView(APIView):
    def get(self, request):
        trainers = User.objects.filter(userrole__role__rolename='Trainer').distinct()
        result = []

        for trainer in trainers:
            program_blocks = []
            program_clients = ProgramClient.objects.filter(trainer=trainer)

            for pc in program_clients:
                # Get workout days
                workout_days = [day.capitalize() for day in (pc.workout_days or [])]

                # Go through preferred_time list
                for time_range in pc.preferred_time or []:
                    start = parse_time(time_range[0])
                    end = parse_time(time_range[1])

                    if start and end:
                        start_hour = start.hour
                        end_hour = end.hour
                        if end.minute > 0:
                            end_hour += 1  # Round up if there are minutes

                        program_blocks.append({
                            'start_hour': start_hour,
                            'end_hour': end_hour,
                            'program_name': pc.program.name,
                            'program_days': workout_days
                        })

            result.append({
                'trainer_id': trainer.id,
                'trainer_name': trainer.name,
                'program_blocks': program_blocks
            })

        return Response(result)
    
class CountryListView(APIView):
    def get(self, request):
        # users = User.objects.filter(status=True)
        countries = Country.objects.all()
        serializer = CountrySerializer(countries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class LeadCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()

        # if 'lead_date' not in data or not data['lead_date']:
        data['lead_date'] = timezone.now().date()

        serializer = LeadCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            lead = serializer.save()

            # Automatically create follow-up entry
            LeadsFollowup.objects.create(
                lead_id=lead.id,
                sales_id=request.user.id,
                follow_up_date=lead.follow_up_date,  # or use timezone.now().date() if dynamic
                status=False  # default follow-up status
            )

            return Response({
                "message": "Lead and follow-up created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeadsListView(APIView):
    
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # users = User.objects.filter(status=True)
        user = request.user.id
        leads = Leads.objects.filter(sales_id=user)\
                             .exclude(status='Converted')\
                             .order_by('-created_at')  # DESC order = LIFO
        serializer = LeadsSerializer(leads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LeadsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, lead_id):
        # users = User.objects.filter(status=True)
        user = request.user.id
        leads = Leads.objects.filter(sales_id = user, id=lead_id).distinct()
        serializer = LeadsSerializer(leads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class LeadsUpdate(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, lead_id):
        lead = get_object_or_404(Leads, id=lead_id, sales_id=request.user.id)
        old_followup_date = lead.follow_up_date
        serializer = LeadCreateSerializer(lead, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            
            # if request.data.get('status') != 'Converted':
            #     # ✅ Update old follow-up row
            #     LeadsFollowup.objects.create(
            #         lead_id=lead.id,
            #         sales_id=request.user.id,
            #         follow_up_date=lead.follow_up_date,  # or use timezone.now().date() if dynamic
            #         notes = lead.notes,
            #         status=False  # default follow-up status
            #     )
            # ✅ If lead status is converted, create Client & ProgramClient
            if request.data.get('status') == 'Converted':
                # Generate new client_id like FFCL001
                last_client = Client.objects.order_by('-id').first()
                if last_client and last_client.client_id:
                    # extract numeric part using regex (e.g., from "FCL004" or "FFCL004")
                    match = re.search(r'\d+', last_client.client_id)
                    if match:
                        last_number = int(match.group())
                        new_client_id = f"FFCL{last_number + 1:03d}"
                    else:
                        # fallback if no number found
                        new_client_id = "FFCL001"
                else:
                    new_client_id = "FFCL001"
                
                # ✅ Create Client
                client = Client.objects.create(
                    client_id=new_client_id,
                    name=lead.name,
                    source=lead.source,
                    email=lead.email,
                    phone=lead.phone,
                    status='Converted',  # assuming default
                    sales=request.user
                )
                # ✅ Create ProgramClient
                ProgramClient.objects.create(
                    client=client,
                    program_id=lead.program_name,  # assuming this is ID in POST
                    program_type=lead.program_type,
                    preferred_time=lead.preferred_time,
                    workout_days=lead.preferred_days,
                    status='active',  # adjust as needed
                )

                return Response({
                    "message": "Lead and follow-up updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "message": "Lead and follow-up updated successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UsersRoleView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        roles = UserRole.objects.filter(user=user).select_related('role')

        # Return role names
        role_names = [ur.role.rolename for ur in roles]

        return Response({'roles': role_names}, status=200)

class AssignTrainerDietitianView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client_id = request.data.get('client_id')
        trainer_id = request.data.get('trainer_id')
        dietitian_id = request.data.get('dietitian_id')
        program_months = request.data.get('program_month')
        amount = request.data.get('amount')
        program_start_date = request.data.get('program_start_date')
        program_end_date = request.data.get('program_end_date')

        if not client_id:
            return Response({'error': 'Client ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(id=client_id)  # or client_id=client_id if you're matching via `client_id` field
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get the latest or most relevant ProgramClient entry for the client
        try:
            program_client = ProgramClient.objects.filter(client=client).latest('id')
        except ProgramClient.DoesNotExist:
            return Response({'error': 'No program found for this client'}, status=status.HTTP_404_NOT_FOUND)

        # Update trainer and dietitian in ProgramClient
        if trainer_id:
            try:
                trainer = User.objects.get(id=trainer_id)
                program_client.trainer = trainer
            except User.DoesNotExist:
                return Response({'error': 'Trainer not found'}, status=status.HTTP_404_NOT_FOUND)

        if dietitian_id:
            try:
                dietitian = User.objects.get(id=dietitian_id)
                program_client.dietitian = dietitian
            except User.DoesNotExist:
                return Response({'error': 'Dietitian not found'}, status=status.HTTP_404_NOT_FOUND)

        program_client.save()

        # Also update client.role_assigned_on
        client.role_assigned_on = timezone.now().date()
        client.program_months = program_months
        client.program_start_date = program_start_date
        client.program_end_date = program_end_date
        client.amount = amount
        client.save()


        try:
            program = Program.objects.get(id=request.data.get('program_id'))
        except Program.DoesNotExist:
            return Response({'error': 'Program not found'}, status=status.HTTP_404_NOT_FOUND)

        # Count current subscriptions
        count = ClientSubscription.objects.count() + 1  # +1 for the next one
        subscription_id = f"CLN{str(count).zfill(3)}"  # Pads with zeros (e.g., CLN001)


        ClientSubscription.objects.create(
            client=client,
            program=program,
            program_months=program_months,
            program_start_date=program_start_date,
            program_end_date=program_end_date,
            amount=amount,
            subscription_type='new',
            subscription_id=subscription_id  # ✅ Set the new formatted ID
        )
        return Response({'message': 'Trainer & Dietitian assigned successfully'}, status=status.HTTP_200_OK)
        
class followupStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        followup_id = request.data.get('followup_id')
        notes = request.data.get('notes')
        lead_status = request.data.get('lead_status')
        activity_type = request.data.get('activity_type')
        followup_date = request.data.get('followup_date')
        try:
            followup = LeadsFollowup.objects.get(id=followup_id)
            lead = followup.lead

            # Update Lead status
            lead.status = lead_status
            lead.save()


            # Update current followup
            followup.status = 1
            followup.lead_status = lead_status
            followup.notes = notes
            followup.save()

            if lead_status == 'Converted':
                lead = get_object_or_404(Leads, id=lead.id)
                last_client = Client.objects.order_by('-id').first()
                if last_client and last_client.client_id:
                    # extract numeric part using regex (e.g., from "FCL004" or "FFCL004")
                    match = re.search(r'\d+', last_client.client_id)
                    if match:
                        last_number = int(match.group())
                        new_client_id = f"FFCL{last_number + 1:03d}"
                    else:
                        # fallback if no number found
                        new_client_id = "FFCL001"
                else:
                    new_client_id = "FFCL001"
                # ✅ Create Client
                client = Client.objects.create(
                    client_id=new_client_id,
                    name=lead.name,
                    source=lead.source,
                    email=lead.email,
                    phone=lead.phone,
                    status='Converted',  # assuming default
                    sales=request.user
                )

                lead.client = client
                lead.save()

                # ✅ Create ProgramClient
                ProgramClient.objects.create(
                    client=client,
                    program_id=lead.program_name,  # assuming this is ID in POST
                    program_type=lead.program_type,
                    preferred_time=lead.preferred_time,
                    workout_days=lead.preferred_days,
                    status='active',  # adjust as needed
                )
                return Response({
                    "message": "Lead converted successfully",
                }, status=status.HTTP_201_CREATED)
            
            if lead_status != 'Converted':
                LeadsFollowup.objects.create(
                    lead=lead,
                    sales=request.user,
                    follow_up_date=followup_date,  # or set next date if needed
                    status=0,
                    lead_status=None,
                    notes=None,
                    activity_type=activity_type
                )
                return Response({'message': 'Followup updated successfully'}, status=status.HTTP_200_OK)

        except LeadsFollowup.DoesNotExist:
            return Response({'error': 'Followup not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class fetchFollowupsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, client_id):
        # users = User.objects.filter(status=True)
        user = request.user.id
        leads = Leads.objects.filter(sales_id = user, client_id=client_id).distinct()
        serializer = LeadsSerializer(leads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class groupProgramListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        programs = Program.objects.filter(program_type__icontains='Group')
        serializer = GroupProgramSerializer(programs, many=True)
        return Response(serializer.data)
    
class groupProgramView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, program_id):
        programs = Program.objects.filter(program_type__icontains='Group', id=program_id)
        serializer = GroupProgramSerializer(programs, many=True)
        return Response(serializer.data)
    
class NewLeadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, month, year):
        user = request.user

        try:
            # ✅ Correct method
            month_number = list(calendar.month_name).index(month)
        except ValueError:
            return Response({'error': 'Invalid month name'}, status=400)

        if month_number == 0:
            return Response({'error': 'Invalid month name'}, status=400)

        leads_count = Leads.objects.filter(
            sales_id=user,
            lead_date__year=int(year),
            lead_date__month=month_number,
        ).count()

        converted_count = Leads.objects.filter(
            sales_id=user,
            lead_date__year=int(year),
            lead_date__month=month_number,
            status='Converted'
        ).count()

        followup_count = LeadsFollowup.objects.filter(
            sales=user,
            follow_up_date__year=int(year),
            follow_up_date__month=month_number,
            status=False  # status = 0
        ).count()

        clients = Client.objects.filter(
            sales=user,
            created_at__year=int(year),
            created_at__month=month_number
        )

        # Convert and sum amounts safely
        monthly_revenue = 0
        for client in clients:
            try:
                if client.amount:
                    monthly_revenue += float(client.amount)
            except ValueError:
                pass  # Ignore invalid amount strings

        return Response({
            "leads_count": leads_count,
            "converted_count": converted_count,
            "followup_count": followup_count,
            "monthly_revenue": monthly_revenue,
            "month": month,
            "year": year
        })
    
class GraphLeadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, month, year):
        user = request.user

        try:
            month_number = list(calendar.month_name).index(month)
        except ValueError:
            return Response({'error': 'Invalid month name'}, status=400)

        if month_number == 0:
            return Response({'error': 'Invalid month name'}, status=400)

        # Total days in month
        total_days = calendar.monthrange(int(year), month_number)[1]

        # Initialize count map for each day
        daily_count = {str(day): 0 for day in range(1, total_days + 1)}

        leads = Leads.objects.filter(
            sales_id=user,
            lead_date__year=int(year),
            lead_date__month=month_number
        )

        for lead in leads:
            day = str(lead.lead_date.day)
            daily_count[day] += 1

        return Response({
            "days": list(daily_count.keys()),
            "counts": list(daily_count.values()),
            "month": month,
            "year": year
        })
    
class GraphRevenueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year):
        user = request.user

        monthly_revenue = [0] * 12  # Index 0 = Jan, 11 = Dec

        clients = Client.objects.filter(
            sales=user,
            created_at__year=year
        )

        for client in clients:
            try:
                if client.amount:
                    month_index = client.created_at.month - 1  # 1-12 → 0-11
                    monthly_revenue[month_index] += float(client.amount)
            except (ValueError, AttributeError):
                continue

        month_names = list(calendar.month_abbr)[1:]  # ['Jan', ..., 'Dec']

        return Response({
            "months": month_names,
            "revenue": monthly_revenue,
            "year": year
        })
    
class WeeklyDietDetailsView(APIView):
    def get(self, request, client_id):
        client = Client.objects.get(id=client_id)
        weekly_updates = weeklydietupdates.objects.filter(client=client).order_by('-week_no')
        serializer = WeeklyDietSerializer(weekly_updates, many=True)
        return Response(serializer.data)
    
class SaveWeeklyDietUpdatesView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # <-- Add this line

    def post(self, request, client_id):
        dietitian_id = request.user.id
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        data['client'] = client.id
        data['dietitian_id'] = request.user.id

        serializer = WeeklyDietUpdateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActiveClientDietitianView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        # Get distinct client IDs where the logged-in user is the dietitian
        client_ids = ProgramClient.objects.filter(
            dietitian=user,
            status='active',  # optional: only active programs
        ).values_list('client_id', flat=True).distinct()

        # Get the number of unique clients
        count = Client.objects.filter(id__in=client_ids, new_client=0).count()

        return Response({'active_client_count': count})
    
class ConsultationDietitianView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        now = timezone.now()
        next_week = now + timedelta(days=7)

        # 1. Upcoming in the next 7 days
        upcoming = ConsulationSchedules.objects.filter(
            user=user,
            type='dietitian',
            status=False,
            datetime__range=[now, next_week]
        ).count()

        # 2. Due (missed) consultations
        due = ConsulationSchedules.objects.filter(
            user=user,
            type='dietitian',
            status=False,
            datetime__lt=now
        ).count()

        return Response({
            'upcoming_consultations': upcoming,
            'due_consultations': due
        })
    
class UpcomingConsultDietView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        next_two_weeks = now + timedelta(days=14)

        consultations = ConsulationSchedules.objects.filter(
            Q(user=request.user),
            Q(status=False),
            Q(datetime__range=(now, next_two_weeks)),  # upcoming in next 2 weeks
            Q(client__diet_first_consultation=3) | Q(client__diet_first_consultation=1)
        ).select_related('client')

        serializer = ConsultationScheduleWithClientSerializer(consultations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class MissedConsultDietView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()

        due_consultations = ConsulationSchedules.objects.filter(
            Q(user=request.user),
            Q(status=False),
            Q(datetime__lt=now),  # past datetime
            Q(client__diet_first_consultation=3) | Q(client__diet_first_consultation=1)
        ).select_related('client')

        serializer = ConsultationScheduleWithClientSerializer(due_consultations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DietConsultationDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, client_id):
        user = request.user

        # Filter only completed (status=True) dietitian consultations for the given client
        consultations = ConsulationSchedules.objects.filter(
            user=user,
            type='dietitian',
            client_id=client_id  # 👈 Filter by client
        )
        data = []
        for consultation in consultations:
            client = consultation.client

            diet_details = DietitianConsultationDetails.objects.filter(client=client, user=user).first()
            monthly_details = MonthlyDietConsultationDetails.objects.filter(client=client, dietitian_id=user, consult_schedule=consultation).first()

            data.append({
                "consultation_id": consultation.id,
                "datetime": consultation.datetime,
                "no_of_consultation": consultation.no_of_consultation,
                "client_name": client.name,
                "status": consultation.status,
                "dietitian_consultation_details": {
                    "diet_preferences": diet_details.diet_preferences if diet_details else None,
                    "current_eating_pattern": diet_details.current_eating_pattern if diet_details else None,
                    "appetite_level": diet_details.appetite_level if diet_details else None,
                    "no_of_meals_per_day": diet_details.no_of_meals_per_day if diet_details else None,
                    "cook_at_home_out": diet_details.cook_at_home_out if diet_details else None,
                    "food_allergies": diet_details.food_allergies if diet_details else None,
                    "diet_before": diet_details.diet_before if diet_details else None,
                    "snacking_habits": diet_details.snacking_habits if diet_details else None,
                    "nutrient_deficiencies": diet_details.nutrient_deficiencies if diet_details else None,
                    "sleeping_duration": diet_details.sleeping_duration if diet_details else None,
                    "water_intake_per_day": diet_details.water_intake_per_day if diet_details else None,
                    "working_schedule": diet_details.working_schedule if diet_details else None,
                    "sleep_quality": diet_details.sleep_quality if diet_details else None,
                    "stress": diet_details.stress if diet_details else None,
                    "hobbies": diet_details.hobbies if diet_details else None,
                    "screen_time": diet_details.screen_time if diet_details else None,
                    "pre_existing_conditions": diet_details.pre_existing_conditions if diet_details else None,
                    "past_surgeries": diet_details.past_surgeries if diet_details else None,
                    "medication": diet_details.medication if diet_details else None,
                    "menstrual_history": diet_details.menstrual_history if diet_details else None,
                    "pregnancy_history": diet_details.pregnancy_history if diet_details else None,
                    "breast_feeding": diet_details.breast_feeding if diet_details else None,
                    "supplements": diet_details.supplements if diet_details else None,
                    "medical_tests": diet_details.medical_tests if diet_details else None,
                    # Add more fields as needed
                },
                "monthly_diet_consultation_details": {
                    "height": monthly_details.height if monthly_details else None,
                    "weight": monthly_details.weight if monthly_details else None,
                    "bmi": monthly_details.bmi if monthly_details else None,
                    "notes": monthly_details.notes if monthly_details else None,
                    "consult_date": monthly_details.consult_date if monthly_details else consultation.datetime.date()
                }
            })
        return Response(data)
        # You can now combine or join related data like DietitianConsultationDetails & MonthlyDietConsultationDetails
        # For now just sending the filtered list
        # serializer = ConsultationScheduleWithClientSerializer(consultations, many=True)
        # return Response(serializer.data, status=status.HTTP_200_OK)

class DietGraphView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        from .models import MonthlyDietConsultationDetails  # your model path here

        data = (
            MonthlyDietConsultationDetails.objects
            .filter(client_id=client_id)
            .annotate(month_num=ExtractMonth('consult_date'))  # avoid conflict with 'month' field
            .order_by('consult_date')
        )

        # prepare graph data
        months = []
        weight = []
        bmi = []
        height = []

        for entry in data:
            months.append(month_name[entry.month_num])
            weight.append(float(entry.weight))
            bmi.append(float(entry.bmi))
            height.append(float(entry.height))

        return Response({
            "months": months,
            "weight": weight,
            "bmi": bmi,
            "height": height
        })

class BiweeklyDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        user = request.user
        updates = BiweeklyUpdations.objects.filter(client_id=client_id, dietitian_id=user).order_by('-update_date')

        serializer = BiweeklyUpdationsSerializer(updates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class BiweeklyDataUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, client_id):
        week_no = int(request.data.get('week_no'))
        notes = request.data.get('notes')
        status = request.data.get('status') == 'true'
        biweekly_id = request.data.get('biweekly_id')  # for updating existing row if week_no > 1
        client = Client.objects.get(id=client_id)
        dietitian = request.user

        if week_no == 1:
             # Insert initial row
            first_row = BiweeklyUpdations.objects.create(
                client=client,
                dietitian_id=dietitian,
                week_no=week_no,
                notes=notes,
                status=status,
                update_date=date.today()
            )

            # Insert follow-up row
            BiweeklyUpdations.objects.create(
                client=client,
                dietitian_id=dietitian,
                week_no=week_no + 1,
                notes=None,
                status=False,
                update_date=date.today() + timedelta(weeks=2)
            )
        else:
            # Update current row
            current_row = BiweeklyUpdations.objects.get(id=biweekly_id)
            current_row.notes = notes
            current_row.status = True
            current_row.save()

            # Insert new follow-up row
            BiweeklyUpdations.objects.create(
                client=client,
                dietitian_id=dietitian,
                week_no=week_no + 1,
                notes=None,
                status=False,
                update_date=current_row.update_date + timedelta(weeks=2)
            )

        return Response({"message": "Biweekly data processed successfully"})
    
class CountBiweeklyUpdationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()
        two_weeks_later = today + timedelta(days=14)

        count = BiweeklyUpdations.objects.filter(
            dietitian_id=user,
            update_date__range=(today, two_weeks_later),
            status = 0
        ).count()

        return Response({"upcoming_biweekly_count": count}, status=status.HTTP_200_OK)
    
class DietClientMeetingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        user = request.user

        meetings = MeetingsTDC.objects.filter(client_id=client_id, dietitian=user).annotate(
            pending_first=Case(
                When(status=False, then=Value(0)),
                When(status=True, then=Value(1)),
                output_field=IntegerField()
            )
        ).order_by('pending_first', 'meeting_date')

        serializer = MeetingsTDCSerializer(meetings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TrainerClientMeetingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        user = request.user

        meetings = MeetingsTDC.objects.filter(client_id=client_id, trainer=user, meeting_for='both').annotate(
            pending_first=Case(
                When(trainer_status=False, then=Value(0)),
                When(trainer_status=True, then=Value(1)),
                output_field=IntegerField()
            )
        ).order_by('pending_first', 'meeting_date')

        serializer = MeetingsTDCSerializer(meetings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DietFirstConsultationDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        user = request.user

        try:
            consultation = DietitianConsultationDetails.objects.get(client_id=client_id, user=user)
        except DietitianConsultationDetails.DoesNotExist:
            return Response({'error': 'No consultation data found for this client.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DietitianConsultationDetailsSerializer(consultation)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DietMeetingUpdationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        meeting_id = data.get('meeting_id')

        try:
            meeting = MeetingsTDC.objects.get(id=meeting_id)
        except MeetingsTDC.DoesNotExist:
            return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # ✅ Update meeting status to 1
        meeting.status = True
        meeting.actual_meeting_date = date.today()
        meeting.save()

        # Update Measurements entry
        try:
            measurement = Measurementsclients.objects.get(meetingtdc=meeting)
            measurement.chest = data.get('chest', 0)
            measurement.right_arm = data.get('right_arm', 0)
            measurement.left_arm = data.get('left_arm', 0)
            measurement.waist = data.get('waist', 0)
            measurement.hip = data.get('hip', 0)
            measurement.left_thigh = data.get('left_thigh', 0)
            measurement.right_thigh = data.get('right_thigh', 0)
            measurement.right_calf = data.get('right_calf', 0)
            measurement.left_calf = data.get('left_calf', 0)
            measurement.updated_date = date.today()
            measurement.save()
        except Measurementsclients.DoesNotExist:
            return Response({'error': 'Measurements entry not found for this meeting.'}, status=status.HTTP_404_NOT_FOUND)

        # Create MeetingTDCDetails entry if `diet_chart` is provided
        diet_chart = data.get('diet_chart')
        if diet_chart:
            MeetingTDCDetails.objects.create(
                meetingtdc=meeting,
                diet_paln=diet_chart,
                uploaded=True,
                change_dietplan=True,
                notes=data.get('notes'),
                diet_plan_uploaded_at=date.today()
            )

        return Response({'message': 'Measurements and diet chart updated successfully.'}, status=status.HTTP_201_CREATED)
    
class MeetingDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, meeting_id):
        try:
            meeting = MeetingsTDC.objects.get(id=meeting_id)
        except MeetingsTDC.DoesNotExist:
            return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize meeting
        meeting_data = MeetingsTDCSerializer(meeting).data

        # Serialize measurements
        try:
            measurement = Measurementsclients.objects.get(meetingtdc=meeting)
            measurement_data = MeasurementsclientsSerializer(measurement).data
        except Measurementsclients.DoesNotExist:
            measurement_data = {}

        # Serialize dietitian meeting details
        try:
            details = MeetingTDCDetails.objects.get(meetingtdc=meeting)
            details_data = MeetingTDCDetailsSerializer(details).data
        except MeetingTDCDetails.DoesNotExist:
            details_data = {}

        # Serialize trainer meeting details
        try:
            trainer_details = TrainerMeetingTDCDetails.objects.get(meetingtdc=meeting)
            trainer_details_data = TrainerMeetingTDCDetailsSerializer(trainer_details).data
        except TrainerMeetingTDCDetails.DoesNotExist:
            trainer_details_data = {}

        return Response({
            'meeting': meeting_data,
            'measurements': measurement_data,
            'diet_details': details_data,
            'trainer_details': trainer_details_data
        }, status=status.HTTP_200_OK)


class RemidersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        two_days_ahead = today + timedelta(days=2)

        # === 1. MeetingsTDC ===
        base_tdc_qs = MeetingsTDC.objects.filter(
            dietitian=user,
            status=False,
        ).filter(
            Q(need_meeting=1) | Q(need_meeting=2)
        ).exclude(meeting_type='day_1')

        tdc_upcoming = base_tdc_qs.filter(meeting_date__range=(today, two_days_ahead))
        tdc_expired = base_tdc_qs.filter(meeting_date__lt=today)

        # === 2. Weekly Meetings (Weekly is on Saturday, reminder is on Friday) ===
        weekly_qs = WeeklyMeeting.objects.filter(dietitian_id=user, status=False)
        weekly_upcoming = weekly_qs.filter(meeting_date=today + timedelta(days=1))  # Friday reminder for Saturday
        weekly_expired = weekly_qs.filter(meeting_date__lt=today)

        # === 3. Measurements Clients (based on related meetingtdc)
        measurement_upcoming = Measurementsclients.objects.filter(
            meetingtdc__in=tdc_upcoming
        )
        measurement_expired = Measurementsclients.objects.filter(
            meetingtdc__in=tdc_expired
        )

        # Grouping helpers
        def group_tdc(queryset):
            data = {}
            for meeting in queryset:
                mtype = meeting.meeting_type
                if mtype not in data:
                    data[mtype] = []
                data[mtype].append({
                    'id': meeting.id,
                    'client': meeting.client.name,
                    'meeting_date': meeting.meeting_date,
                    'status': meeting.status,
                    'day_no': meeting.day_no,
                    'need_meeting': meeting.need_meeting,
                    'meeting_model': 'TDC'
                })
            return data

        def group_weekly(queryset):
            key = 'Weekly'
            return {
                key: [
                    {
                        'id': meeting.id,
                        'client': meeting.client.name,
                        'meeting_date': meeting.meeting_date,
                        'status': meeting.status,
                        'week_no': meeting.week_no,
                        'meeting_model': 'Weekly'
                    } for meeting in queryset
                ]
            }

        def group_measurements(queryset):
            key = 'Measurements'
            return {
                key: [
                    {
                        'id': m.id,
                        'client': m.meetingtdc.client.name,
                        'meeting_id': m.meetingtdc.id,
                        'meeting_date': m.meetingtdc.meeting_date,
                        'status': m.meetingtdc.status,
                        'updated_date': m.updated_date,
                        'meeting_model': 'Measurements'
                    } for m in queryset
                ]
            }

        # Final response
        return Response({
            'upcoming': {
                **group_tdc(tdc_upcoming),
                **group_weekly(weekly_upcoming),
                **group_measurements(measurement_upcoming)
            },
            'expired': {
                **group_tdc(tdc_expired),
                **group_weekly(weekly_expired),
                **group_measurements(measurement_expired)
            }
        })
    
class UpdateMeetingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, update, meeting_id):
        try:
            meeting = MeetingsTDC.objects.get(id=meeting_id)

            # Update need_meeting field
            if update == "yes":
                meeting.need_meeting = 2
            else:
                meeting.need_meeting = 0
                meeting.status = 1
            meeting.save()

            # Add a record to MeetingTDCDetails
            if update == "no":
                MeetingTDCDetails.objects.create(
                    meetingtdc=meeting,
                    notes="no need of meeting",
                    change_dietplan=False,
                    uploaded=False,
                    diet_plan_uploaded_at=timezone.now().date()
                )

            return Response({"message": "Meeting updated successfully."})

        except MeetingsTDC.DoesNotExist:
            return Response({"error": "Meeting not found."}, status=404)

class DietOnlyMeetingUpdationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        meeting_id = request.data.get('meeting_id')
        diet_chart = request.FILES.get('diet_chart')  # file if uploaded

        try:
            meeting = MeetingsTDC.objects.get(id=meeting_id)
        except MeetingsTDC.DoesNotExist:
            return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

        # 1. Update MeetingsTDC
        meeting.status = True
        meeting.actual_meeting_date = timezone.now().date()
        meeting.save()

        # 2. Create MeetingTDCDetails row
        meeting_details = MeetingTDCDetails.objects.create(
            meetingtdc=meeting,
            notes=request.data.get('notes'),
            change_dietplan=True,
            uploaded=bool(diet_chart),
            diet_paln=diet_chart.name if diet_chart else '',
            diet_plan_uploaded_at=timezone.now().date() if diet_chart else None
        )

        # 3. Save file if needed
        if diet_chart:
            meeting_details.diet_paln = diet_chart
            meeting_details.save()

        return Response({'message': 'Meeting updated successfully'}, status=status.HTTP_200_OK)
    
class FetchMeetingDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, meeting_id):
        try:
            meeting = MeetingsTDC.objects.get(id=meeting_id)
        except MeetingsTDC.DoesNotExist:
            return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the base meeting
        meeting_data = MeetingsTDCSerializer(meeting).data

        # Serialize MeetingTDCDetails if needed (if you use it elsewhere)
        meeting_details = MeetingTDCDetails.objects.filter(meetingtdc=meeting)
        meeting_details_data = MeetingTDCDetailsSerializer(meeting_details, many=True).data

        # Fetch TrainerMeetingTDCDetails for this meeting
        try:
            trainer_details = TrainerMeetingTDCDetails.objects.get(meetingtdc=meeting)
            from .serializers import TrainerMeetingTDCDetailsSerializer  # Import serializer if not already
            trainer_details_data = TrainerMeetingTDCDetailsSerializer(trainer_details).data
        except TrainerMeetingTDCDetails.DoesNotExist:
            trainer_details_data = None

        return Response({
            'meeting': meeting_data,
            'meeting_details': meeting_details_data,
            'trainer_details': trainer_details_data,
        }, status=status.HTTP_200_OK)

class TDCMeetingUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        meeting_id = request.data.get('meeting_id')
        notes = request.data.get('notes')
        show_diet_chart = request.data.get('showDietChart')
        diet_chart = request.FILES.get('diet_chart')

        try:
            meeting = MeetingsTDC.objects.get(id=meeting_id)

            # Update MeetingsTDC
            meeting.status = True
            meeting.actual_meeting_date = date.today()
            meeting.save()

            # Determine logic for MeetingTDCDetails
            change_dietplan = False
            uploaded = False
            diet_plan_uploaded_at = None
            diet_paln = None

            if show_diet_chart == 'true' or show_diet_chart is True:
                change_dietplan = True
                if diet_chart:
                    uploaded = True
                    diet_paln = diet_chart.name
                    diet_plan_uploaded_at = date.today()

            # Create MeetingTDCDetails row
            MeetingTDCDetails.objects.create(
                meetingtdc=meeting,
                notes=notes,
                change_dietplan=change_dietplan,
                uploaded=uploaded,
                diet_paln=diet_paln,
                diet_plan_uploaded_at=diet_plan_uploaded_at
            )

            return Response({'message': 'Meeting updated successfully'}, status=status.HTTP_200_OK)

        except MeetingsTDC.DoesNotExist:
            return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
class WeeklyMeetingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        user = request.user  # Logged-in user
        meetings = WeeklyMeeting.objects.filter(client_id=client_id, dietitian_id=user).order_by('week_no')

        serializer = WeeklyMeetingSerializer(meetings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UpdateWeeklyMeeting(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        meeting_id = request.data.get('meeting_id')
        try:
            weekly_meeting = WeeklyMeeting.objects.get(id=meeting_id)
        except WeeklyMeeting.DoesNotExist:
            return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)

        weekly_meeting.height = request.data.get('height', 0)
        weekly_meeting.weight = request.data.get('weight', 0)
        weekly_meeting.bmi = request.data.get('bmi', 0)
        weekly_meeting.notes = request.data.get('notes', '')
        weekly_meeting.status = True
        weekly_meeting.entered_date = date.today()
        weekly_meeting.save()

        return Response({'message': 'Weekly meeting updated successfully'}, status=status.HTTP_200_OK)
    
class WeeklyMeetingDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, meeting_id):
        try:
            meeting = WeeklyMeeting.objects.get(id=meeting_id, dietitian_id=request.user)
            serializer = WeeklyMeetingSerializer(meeting)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WeeklyMeeting.DoesNotExist:
            return Response({"error": "Meeting not found"}, status=status.HTTP_404_NOT_FOUND)
        
class WeeklyMeetingByWeekNoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client_id = request.GET.get('client_id')
        week_no = request.GET.get('week_no')

        try:
            meeting = WeeklyMeeting.objects.get(client_id=client_id, week_no=week_no, dietitian_id=request.user.id)
            serializer = WeeklyMeetingSerializer(meeting)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WeeklyMeeting.DoesNotExist:
            return Response({'error': 'Previous meeting not found'}, status=status.HTTP_404_NOT_FOUND)
        
class MeasurementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        user = request.user

        measurements = Measurementsclients.objects.filter(
            meetingtdc__client_id=client_id,
            meetingtdc__dietitian=user
        ).annotate(
            is_pending=Case(
                When(updated_date__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('-is_pending', 'meetingtdc__meeting_date')  # pending (null) first, then by date

        data = [
            {
                'measurement_id': m.id,
                'meeting_id': m.meetingtdc.id,
                'meeting_date': m.meetingtdc.meeting_date,
                'updated_date': m.updated_date,
                'chest': m.chest,
                'right_arm': m.right_arm,
                'left_arm': m.left_arm,
                'waist': m.waist,
                'hip': m.hip,
                'left_thigh': m.left_thigh,
                'right_thigh': m.right_thigh,
                'right_calf': m.right_calf,
                'left_calf': m.left_calf,
            }
            for m in measurements
        ]

        return Response(data, status=status.HTTP_200_OK)
    
class MeasurementDataUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        meeting_id = data.get('meeting_id')

        # Update Measurements entry
        try:
            measurement = Measurementsclients.objects.get(id=meeting_id)
            measurement.chest = data.get('chest', 0)
            measurement.right_arm = data.get('right_arm', 0)
            measurement.left_arm = data.get('left_arm', 0)
            measurement.waist = data.get('waist', 0)
            measurement.hip = data.get('hip', 0)
            measurement.left_thigh = data.get('left_thigh', 0)
            measurement.right_thigh = data.get('right_thigh', 0)
            measurement.right_calf = data.get('right_calf', 0)
            measurement.left_calf = data.get('left_calf', 0)
            measurement.updated_date = date.today()
            measurement.save()
        except Measurementsclients.DoesNotExist:
            return Response({'error': 'Measurements entry not found for this meeting.'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'message': 'Measurements and diet chart updated successfully.'}, status=status.HTTP_201_CREATED)

class MeasurementDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, meeting_id):
        try:
            measurement = Measurementsclients.objects.get(id=meeting_id)
        except Measurementsclients.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MeasurementsclientsSerializer(measurement)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MeasurementProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        # Get meetings with measurements=True for the logged-in dietitian and specific client
        meetings = MeetingsTDC.objects.filter(
            client_id=client_id,
            dietitian=request.user,
            measurements=True
        ).order_by('meeting_date')

        data = []
        for meeting in meetings:
            try:
                measure = Measurementsclients.objects.get(meetingtdc=meeting)
                data.append({
                    'meeting_date': meeting.meeting_date,
                    'chest': measure.chest,
                    'right_arm': measure.right_arm,
                    'left_arm': measure.left_arm,
                    'waist': measure.waist,
                    'hip': measure.hip,
                    'left_thigh': measure.left_thigh,
                    'right_thigh': measure.right_thigh,
                    'right_calf': measure.right_calf,
                    'left_calf': measure.left_calf,
                })
            except Measurementsclients.DoesNotExist:
                continue

        return Response(data, status=status.HTTP_200_OK)

class DietChartListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        meeting_details = MeetingTDCDetails.objects.filter(meetingtdc__client_id=client_id)
        serializer = MeetingTDCDetailswithDietSerializer(meeting_details, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DietChartUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        dietchart_id = request.data.get('dietchart_id')
        notes = request.data.get('notes')
        diet_chart_file = request.FILES.get('diet_chart')

        if not dietchart_id:
            return Response({'error': 'dietchart_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            meeting_detail = MeetingTDCDetails.objects.get(id=dietchart_id)
        except ObjectDoesNotExist:
            return Response({'error': 'MeetingTDCDetails not found'}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Update fields
        if notes:
            meeting_detail.notes = notes

        if diet_chart_file:
            meeting_detail.diet_paln = diet_chart_file
            meeting_detail.uploaded = True
            meeting_detail.diet_plan_uploaded_at = date.today()

        meeting_detail.save()

        return Response({'message': 'Diet chart updated successfully'}, status=status.HTTP_200_OK)
    
class PauseClientDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get latest subscription
        latest_subscription = ClientSubscription.objects.filter(client=client).order_by('-id').first()
        if not latest_subscription:
            return Response({'error': 'No subscription found for this client'}, status=status.HTTP_404_NOT_FOUND)

        if latest_subscription.program_type != 'Personal Training':
            return Response({'error': 'Pause only available for Personal Training clients'}, status=status.HTTP_400_BAD_REQUEST)

        sub_months = latest_subscription.program_months

        # Get pause policy
        try:
            pause_policy = SubscriptionPause.objects.get(subscription_months=sub_months)
        except SubscriptionPause.DoesNotExist:
            return Response({'error': 'No pause policy defined for this subscription length'}, status=status.HTTP_404_NOT_FOUND)

        # Get pause usage data (if exists)
        try:
            pause_record = ClientPauseLimit.objects.get(client=client)
            pause_data = {
                'total_days_allowed': pause_policy.no_of_days,
                'total_pauses_allowed': pause_policy.no_of_pauses,
                'days_used': pause_record.no_of_paused_days,
                'pauses_used': pause_record.no_of_pauses_taken,
                'days_remaining': pause_record.no_of_pause_days_rem,
                'pauses_remaining': pause_record.no_of_pause_rem,
            }
        except ClientPauseLimit.DoesNotExist:
            # No pause taken yet
            pause_data = {
                'total_days_allowed': pause_policy.no_of_days,
                'total_pauses_allowed': pause_policy.no_of_pauses,
                'days_used': 0,
                'pauses_used': 0,
                'days_remaining': pause_policy.no_of_days,
                'pauses_remaining': pause_policy.no_of_pauses,
            }

        return Response({
            'client_id': client.id,
            'client_name': client.name,
            'pause_summary': pause_data
        })
    
class PauseClientView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client_id = request.data.get('client_id')
        pause_days = int(request.data.get('pause_days', 0))
        pause_from = request.data.get('pause_from')
        notes = request.data.get('notes', '')

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        latest_subscription = ClientSubscription.objects.filter(client=client).order_by('-id').first()
        if not latest_subscription:
            return Response({'error': 'No subscription found'}, status=status.HTTP_404_NOT_FOUND)

        subscription_id = latest_subscription.subscription_id
        program_months = latest_subscription.program_months

        try:
            pause_policy = SubscriptionPause.objects.get(subscription_months=program_months)
        except SubscriptionPause.DoesNotExist:
            return Response({'error': 'Pause policy not found for this subscription'}, status=status.HTTP_404_NOT_FOUND)

        # Dates
        paused_from_date = datetime.strptime(pause_from, "%Y-%m-%d").date() if pause_from else datetime.today().date()
        paused_to_date = paused_from_date + timedelta(days=pause_days)
        program_end_date = latest_subscription.program_end_date
        if not program_end_date:
            return Response({'error': 'Subscription missing end date'}, status=status.HTTP_400_BAD_REQUEST)

        program_end_date_changed = program_end_date + timedelta(days=pause_days)
        program_pause_reactivate_on = paused_to_date + timedelta(days=1)

        # Save ClientPause with updated fields
        ClientPause.objects.create(
            client=client,
            subscription_id=subscription_id,
            type='Paused',
            paused_at=datetime.now(),
            paused_from=paused_from_date,
            paused_to=paused_to_date,
            no_of_days=pause_days,
            notes=notes,
            program_end_date=program_end_date,
            program_end_date_changed=program_end_date_changed,
            program_pause_reactivate_on=program_pause_reactivate_on
        )

        # Handle pause limit
        pause_limit, created = ClientPauseLimit.objects.get_or_create(client=client, defaults={
            'subscription_months': program_months,
            'no_of_days_available': pause_policy.no_of_days,
            'no_of_pauses_available': pause_policy.no_of_pauses,
            'no_of_paused_days': pause_days,
            'no_of_pauses_taken': 1,
            'no_of_pause_days_rem': pause_policy.no_of_days - pause_days,
            'no_of_pause_rem': pause_policy.no_of_pauses - 1
        })

        if not created:
            if pause_limit.no_of_pause_rem <= 0 or pause_limit.no_of_pause_days_rem < pause_days:
                return Response({'error': 'No more pause days or counts left'}, status=status.HTTP_400_BAD_REQUEST)

            pause_limit.no_of_paused_days += pause_days
            pause_limit.no_of_pauses_taken += 1
            pause_limit.no_of_pause_days_rem -= pause_days
            pause_limit.no_of_pause_rem -= 1
            pause_limit.save()

        # Update client
        client.paused = True
        client.program_end_date = program_end_date_changed
        client.save()

        # Update MeetingsTDC
        MeetingsTDC.objects.filter(client=client, status=False).update(
            meeting_date=models.F('meeting_date') + timedelta(days=pause_days),
            dietitian_id=request.user.id
        )

        # Remove existing weekly meetings
        WeeklyMeeting.objects.filter(client=client, status=False).delete()

        # Generate Saturdays between resume and new program end
        def get_saturdays(start_date, end_date):
            saturdays = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() == 5:  # Saturday
                    saturdays.append(current_date)
                current_date += timedelta(days=1)
            return saturdays

        saturdays = get_saturdays(program_pause_reactivate_on, program_end_date_changed)

        # Create new weekly meetings
        for week_no, sat_date in enumerate(saturdays, start=1):
            WeeklyMeeting.objects.create(
                client=client,
                dietitian_id=request.user,
                week_no=week_no,
                meeting_date=sat_date,
                status=False
            )

        return Response({'message': 'Client paused successfully.'}, status=status.HTTP_200_OK)

class PauseClientListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user.id
        clients = Client.objects.filter(new_client=False, programs__dietitian_id=user, paused=True).distinct()

        client_data = []

        for client in clients:
            pause_info = {
                'pause_available': False,
                'pause_days_remaining': 0,
                'pauses_remaining': 0
            }

            # Get latest subscription
            latest_subscription = ClientSubscription.objects.filter(client=client).order_by('-id').first()
            if latest_subscription and latest_subscription.program_type == 'Personal Training':
                sub_months = latest_subscription.program_months

                # Get rule from SubscriptionPause
                try:
                    rule = SubscriptionPause.objects.get(subscription_months=sub_months)
                except SubscriptionPause.DoesNotExist:
                    rule = None

                if rule:
                    # Check if this client already has a pause record
                    try:
                        pause_limit = ClientPauseLimit.objects.get(client=client)
                        pause_info['pause_available'] = pause_limit.no_of_pause_rem > 0
                        pause_info['pause_days_remaining'] = pause_limit.no_of_pause_days_rem
                        pause_info['pauses_remaining'] = pause_limit.no_of_pause_rem
                    except ClientPauseLimit.DoesNotExist:
                        # No pause taken yet, so all pause days are available
                        pause_info['pause_available'] = True
                        pause_info['pause_days_remaining'] = rule.no_of_days
                        pause_info['pauses_remaining'] = rule.no_of_pauses

            serialized = ClientSerializer(client).data
            serialized['pause_info'] = pause_info
            client_data.append(serialized)

        return Response(client_data)
    
class VMCClientListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clients = Client.objects.filter(
            Q(source__iexact='VMC') | Q(source__iexact='Vijayalalakshmi Medical Centre')
        )
        serializer = ClientWithDietchartSerializer(clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class VMCDietchartUpload(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client_id = request.data.get('client_id')
        notes = request.data.get('notes')
        diet_plan_file = request.FILES.get('diet_plan')
        user = request.user

        # Validate client
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        saved_path = None
        if diet_plan_file:
            ext = os.path.splitext(diet_plan_file.name)[1]
            now_str = datetime.now().strftime('%Y%m%d_%H%M')
            new_filename = f"{client.client_id}_{now_str}{ext}"
            file_path = f'diet_chart/{new_filename}'
            saved_path = default_storage.save(file_path, ContentFile(diet_plan_file.read()))

        # Save the data
        DietchartClient.objects.create(
            client=client,
            uploaded=True,
            diet_plan=saved_path,
            notes=notes,
            diet_plan_uploaded_at=date.today(),
            user=user
        )

        return Response({'message': 'Diet chart uploaded successfully'}, status=status.HTTP_200_OK)

class FetchActiveClients(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, month, year):
        try:
            # Convert month name (e.g., "July") to number (7)
            month_number = list(calendar.month_name).index(month.capitalize())
            year = int(year)
        except (ValueError, IndexError):
            return Response({'error': 'Invalid month or year'}, status=400)

        # Filter clients where program_start_date is in the given month/year
        active_clients = Client.objects.filter(
            Q(source__icontains="vmc") | Q(source__icontains="vijayalalakshmi medical centre"),
            created_at__month=month_number,
            created_at__year=year
        )

        count = active_clients.count()

        return Response({
            'active_client_count': count
        })

class FetchActiveClientsGraphView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, month, year):
        # Convert month name (e.g., "July") to month number (e.g., 7)
        try:
            month_number = datetime.strptime(month, '%B').month
        except ValueError:
            return Response({"error": "Invalid month name"}, status=400)

        try:
            year = int(year)
        except ValueError:
            return Response({"error": "Invalid year"}, status=400)

        # Calculate first and last day of the month
        first_day = datetime(year, month_number, 1).date()
        last_day = datetime(year, month_number, monthrange(year, month_number)[1]).date()

        # Filter clients where source is VMC (case-insensitive) and created_at is in this month
        clients = Client.objects.filter(
            source__iexact='VMC',
            created_at__date__range=(first_day, last_day)
        )

        # Prepare daily count
        day_counts = {}
        for day in range(1, last_day.day + 1):
            date_obj = datetime(year, month_number, day).date()
            count = clients.filter(created_at__date=date_obj).count()
            day_counts[str(day)] = count

        # Prepare lists for frontend
        days = list(day_counts.keys())
        counts = list(day_counts.values())

        return Response({
            "days": days,
            "counts": counts
        })

class FetchActiveClientsYearlyGraphView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year):
        try:
            year = int(year)
        except ValueError:
            return Response({"error": "Invalid year"}, status=400)

        # Month names for labels
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        # Count active clients per month
        counts = []
        for month in range(1, 13):
            month_clients = Client.objects.filter(
                created_at__year=year,
                created_at__month=month,
                status__iexact='Converted',
                source__iexact='VMC'  # case-insensitive match
            ).count()
            counts.append(month_clients)

        return Response({
            "months": months,
            "counts": counts
        })

class SalesPauseClientListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user.id
        clients = Client.objects.filter(new_client=False, sales_id=user, paused=True).distinct()
        client_data = []

        for client in clients:
            pause_info = None
            latest_pause = None

            latest_subscription = ClientSubscription.objects.filter(client=client).order_by('-id').first()
            if latest_subscription and latest_subscription.program_type == 'Personal Training':
                sub_months = latest_subscription.program_months

                try:
                    rule = SubscriptionPause.objects.get(subscription_months=sub_months)
                except SubscriptionPause.DoesNotExist:
                    rule = None

                try:
                    pause_limit = ClientPauseLimit.objects.get(client=client)
                    pause_info = ClientPauseLimitSerializer(pause_limit).data
                except ClientPauseLimit.DoesNotExist:
                    if rule:
                        pause_info = {
                            "client": client.id,
                            "subscription_months": sub_months,
                            "no_of_days_available": rule.no_of_days,
                            "no_of_pauses_available": rule.no_of_pauses,
                            "no_of_paused_days": 0,
                            "no_of_pauses_taken": 0,
                            "no_of_pause_days_rem": rule.no_of_days,
                            "no_of_pause_rem": rule.no_of_pauses,
                            "created_at": None,
                            "updated_at": None
                        }

            # 👇 Get last ClientPause record
            last_pause = ClientPause.objects.filter(client=client).order_by('-id').first()
            if last_pause:
                latest_pause = ClientPauseSerializer(last_pause).data

            serialized_client = ClientSerializer(client).data
            serialized_client['pause_info'] = pause_info
            serialized_client['latest_pause_record'] = latest_pause

            client_data.append(serialized_client)

        return Response(client_data)


class ActivatePauseClientView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client_id = request.data.get('client_id')
        notes = request.data.get('notes')
        user = request.user

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get latest pause
        latest_pause = ClientPause.objects.filter(client=client).order_by('-id').first()
        if not latest_pause:
            return Response({'error': 'No previous pause found'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate pause days from paused_from to today
        paused_from = latest_pause.paused_from
        today = date.today()
        no_of_days_paused = (today - paused_from).days if paused_from else 0

        # Update program end date
        program_end_date = latest_pause.program_end_date
        program_end_date_changed = program_end_date - timedelta(days=no_of_days_paused)

        # Reactivation row
        ClientPause.objects.create(
            client=client,
            user=user,
            subscription_id=latest_pause.subscription_id,
            type='Activated',
            paused_at=datetime.now(),
            paused_from=None,
            paused_to=None,
            no_of_days=no_of_days_paused,
            notes=notes,
            program_end_date=program_end_date,
            program_end_date_changed=program_end_date_changed,
            program_pause_reactivate_on=today + timedelta(days=1)
        )

        # Update pause limit
        try:
            pause_limit = ClientPauseLimit.objects.get(client=client)
            pause_limit.no_of_paused_days += no_of_days_paused
            pause_limit.no_of_pause_days_rem -= no_of_days_paused
            pause_limit.save()
        except ClientPauseLimit.DoesNotExist:
            pass  # Optional: Log or handle no pause record

        # Update MeetingsTDC
        MeetingsTDC.objects.filter(client=client, status=False).update(
            meeting_date=F('meeting_date') - timedelta(days=no_of_days_paused),
            dietitian_id=user.id
        )

        # Remove existing weekly meetings
        WeeklyMeeting.objects.filter(client=client, status=False).delete()

        # Generate new weekly meetings
        start_date = today + timedelta(days=1)
        end_date = program_end_date_changed

        def get_saturdays(start_date, end_date):
            saturdays = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() == 5:
                    saturdays.append(current_date)
                current_date += timedelta(days=1)
            return saturdays

        saturdays = get_saturdays(start_date, end_date)

        for week_no, sat_date in enumerate(saturdays, start=1):
            WeeklyMeeting.objects.create(
                client=client,
                dietitian_id=user,
                week_no=week_no,
                meeting_date=sat_date,
                status=False
            )

        # Mark client as not paused
        client.paused = False
        client.save()

        return Response({'message': 'Client activated successfully.'}, status=status.HTTP_200_OK)

class TrainerMeetingsUpdationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        meeting_id = request.data.get('meeting_id')
        if not meeting_id:
            return Response({'error': 'Meeting ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            meeting = MeetingsTDC.objects.get(id=meeting_id)
        except MeetingsTDC.DoesNotExist:
            return Response({'error': 'MeetingTDC not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get or create TrainerMeetingTDCDetails
        trainer_details, _ = TrainerMeetingTDCDetails.objects.get_or_create(meetingtdc=meeting)

        # Update the trainer details
        for field in [
            'half_sit_up', 'modified_push_ups', 'plank_hold', 'wall_sqaut_hold',
            'shoulder_flexibility', 'sit_and_reach', 'hamstring_flexibility', 'quadriceps_flexibility',
            'rounded_shoulder', 'kyphosis', 'lordosis', 'scoliosis', 'bow_leg', 'knock_knees',
            'winging_of_scapula', 'flat_foot', 'notes'
        ]:
            if field in request.data:
                setattr(trainer_details, field, request.data.get(field))

        trainer_details.status = True
        trainer_details.save()

        # Update the MeetingsTDC table
        meeting.trainer_status = True
        meeting.trainer_actual_meeting_date = now().date()

        if meeting.trainer_status and meeting.dietitian_status:
            meeting.status = True

        meeting.save()

        return Response({'message': 'Trainer meeting details updated successfully.'}, status=status.HTTP_200_OK)
    
class RescheduleSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            client_id = request.data.get('client_id')
            session_date = request.data.get('session_date')
            cancelled_by = request.data.get('cancelled_by')
            reschedule = request.data.get('reschedule')
            reschedule_to = request.data.get('reschedule_to')
            notes = request.data.get('notes')

            if not client_id or not session_date:
                return Response({'error': 'Client ID and Session Date are required.'}, status=status.HTTP_400_BAD_REQUEST)

            client = Client.objects.get(id=client_id)

            reschedule_session = ReschedulesSessions.objects.create(
                client=client,
                trainer=request.user,
                session_date=session_date,
                cancelled_by=cancelled_by,
                reschedule=reschedule,
                reschedule_to=reschedule_to if reschedule else None,
                notes=notes
            )

            return Response({'message': 'Session rescheduled successfully'}, status=status.HTTP_201_CREATED)

        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MainProgramListView(APIView):
    def get(self, request):
        # users = User.objects.filter(status=True)
        programs = MainProgram.objects.filter(is_deleted=0)
        serializer = MainProgramsSerializer(programs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteMainProgramView(APIView):
    def post(self, request, pk):
        try:
            program = MainProgram.objects.get(id=pk)
            program.is_deleted = True
            program.save()
            return Response({'message': 'Program deleted'}, status=status.HTTP_200_OK)
        except MainProgram.DoesNotExist:
            return Response({'error': 'Program not found'}, status=status.HTTP_404_NOT_FOUND)

class DetailsMainProgramView(APIView):
     def get(self, request, pk):
        programs = MainProgram.objects.filter(id=pk)
        serializer = MainProgramsSerializer(programs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateMainProgramView(APIView):
    def post(self, request, pk):
        try:
            program = MainProgram.objects.get(id=pk)
        except MainProgram.DoesNotExist:
            return Response({'error': 'Program not found'}, status=404)

        program.name = request.data.get('name', program.name)
        program.status = request.data.get('status', program.status)
        program.save()

        serializer = MainProgramsSerializer(program)
        return Response(serializer.data, status=200)
