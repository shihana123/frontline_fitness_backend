# users/views.py

from rest_framework import generics
from django.db.models import Q, OuterRef, Subquery, Exists
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import User, Role, UserRole, Program, Client, ConsulationSchedules, ProgramClient, WeeklyWorkoutUpdates, WeeklyWorkoutwithDaysUpdates, ClienAttendanceUpdates, Country, Leads, LeadsFollowup
from .serializers import UserCreateSerializer, RoleSerializer, UserSerializer, ProgramCreateSerializer, ProgramsSerializer, CustomUserDetailsSerializer, NewClientSerializer, ConsultationScheduleSerializer, TrainerConsultationDataSerializer, ConsultationScheduleWithClientSerializer, ClientSerializer, WeeklyWorkoutSerializer, ProgramClientDaysSerializer, CountrySerializer, LeadCreateSerializer, LeadsSerializer
from dj_rest_auth.views import UserDetailsView
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta, date
import calendar
from calendar import monthrange

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

                week_range = [workout_start_date + timedelta(days=i) for i in range((week_end_date - workout_start_date).days + 1)]
                current_week_days = [day.strftime('%A').lower() for day in week_range]

                week_no_of_days = 0
                week_workout_days = []
                week_workout_dates = []
                if program_client and program_client.workout_days:
                    client_days = [day.lower() for day in program_client.workout_days]
                    # Count how many of client's workout days fall in this week range
                    # week_no_of_days = sum(1 for day in current_week_days if day in client_days)

                    for date, day_name in zip(week_range, current_week_days):
                        if day_name in client_days:
                            week_no_of_days += 1
                            week_workout_days.append(day_name)
                            week_workout_dates.append(date.strftime('%Y-%m-%d'))

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
        date_str = attendance_date  # expected format: 'YYYY-MM-DD'
        if not date_str:
            return Response({'error': 'Date is required'}, status=400)

        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            weekday = selected_date.strftime('%A').lower()  # e.g. 'tuesday'

            attendance_subquery = ClienAttendanceUpdates.objects.filter(
                client=OuterRef('client'),
                workout_date=selected_date,
                trainer_id=request.user
            )

            # Filter ProgramClient for:
            # - Active programs
            # - Client's workout started
            # - Workout includes this weekday
            # - Trainer is the current user
            program_clients = ProgramClient.objects.filter(
                status='active',
                client__workout_start_date__lte=selected_date,
                workout_days__icontains=weekday,
                trainer=request.user
            ).annotate(
                has_attendance=Exists(attendance_subquery)
            ).select_related('client', 'program', 'trainer', 'dietitian')

            serializer = ProgramClientDaysSerializer(program_clients, many=True)
            return Response(serializer.data)

        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)
        
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
    
class TrainerScheduleView(APIView):
    def get(self, request, trainer_id):
        program_clients = ProgramClient.objects.filter(trainer_id=trainer_id, status="active")
        # Initialize empty schedule
        schedule = {
            'sunday': [],
            'monday': [],
            'tuesday': [],
            'wednesday': [],
            'thursday': [],
            'friday': [],
            'saturday': []
        }
        for pc in program_clients:
            days = pc.workout_days or []         # e.g., ['monday', 'wednesday']
            time_slots = pc.preferred_time or [] # e.g., [["10:30", "11:30"]]
            program_name = pc.program.name if pc.program else "Program"

            for day in days:
                for slot in time_slots:
                    if slot and len(slot) == 2:
                        schedule[day.lower()].append({
                            "start": slot[0],
                            "end": slot[1],
                            "program": program_name
                        })

        return Response(schedule)
    
class CountryListView(APIView):
    def get(self, request):
        # users = User.objects.filter(status=True)
        countries = Country.objects.all()
        serializer = CountrySerializer(countries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class LeadCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LeadCreateSerializer(data=request.data, context={'request': request})
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
        leads = Leads.objects.filter(sales_id = user).distinct()
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
    
    
    


        