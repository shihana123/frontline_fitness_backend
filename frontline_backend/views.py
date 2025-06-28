# users/views.py

from rest_framework import generics
from django.db.models import Q, OuterRef, Subquery, Exists
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .models import User, Role, UserRole, Program, Client, ConsulationSchedules, ProgramClient, WeeklyWorkoutUpdates, WeeklyWorkoutwithDaysUpdates, ClienAttendanceUpdates, Country, Leads, LeadsFollowup
from .serializers import UserCreateSerializer, RoleSerializer, UserSerializer, ProgramCreateSerializer, ProgramsSerializer, CustomUserDetailsSerializer, NewClientSerializer, ConsultationScheduleSerializer, TrainerConsultationDataSerializer, ConsultationScheduleWithClientSerializer, ClientSerializer, WeeklyWorkoutSerializer, ProgramClientDaysSerializer, CountrySerializer, LeadCreateSerializer, LeadsSerializer, GroupProgramSerializer, DietitianConsultationDataSerializer
from dj_rest_auth.views import UserDetailsView
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta, date, time
import calendar
from calendar import monthrange
from django.shortcuts import get_object_or_404
import re
from django.utils import timezone
from django.utils.dateparse import parse_time
from django.utils.timezone import now

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
        elif type == 'dietitian':
            if serializer.is_valid():
                serializer.save()
                client_id = serializer.validated_data['client'].id  # Extract client from validated data
                user_id = request.user.id
                client = Client.objects.get(id=client_id)
                client.diet_first_consultation = 2
                
                no_of_consultation = serializer.validated_data.get('no_of_consultation')
                if no_of_consultation == 2:
                    client.new_client = False
                    client.diet_first_consultation = 1

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
    
class DietitianConsultationDetails(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id  # Attach logged-in user automatically

        serializer = DietitianConsultationDataSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            client_id = serializer.validated_data['client'].id  # Extract client from validated data
            client = Client.objects.get(id=client_id)
            client.diet_first_consultation = 3
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

class DietConsultationScheduleDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        consultations = ConsulationSchedules.objects.filter(
            Q(user=request.user),
            Q(status=False),
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
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user.id
        clients = Client.objects.filter(new_client=False, programs__dietitian_id = user).distinct()
        serializer =ClientSerializer(clients, many=True)
        return Response(serializer.data)

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
        client.amount = amount
        client.save()

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