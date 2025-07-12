from django.db import models
from .constants import GENDER_CHOICES, STATUS_CHOICES, CLIENT_STATUS_CHOICES
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, null=False)
    phone = models.CharField(max_length=15, null=False)
    email = models.EmailField(unique=True, null=False)
    password = models.CharField(max_length=128, null=False)
    resume = models.FileField(upload_to='resumes/', null=True)
    address = models.TextField(null=True)
    state = models.CharField(max_length=50, null=True)
    country = models.CharField(max_length=50, null=False)  # Allow null
    pincode = models.CharField(max_length=10, null=True)
    age = models.PositiveIntegerField(null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    joining_date = models.DateField(null=True)
    available_time = models.JSONField(null=True)
    available_days = models.JSONField(null=True)  # e.g., ['mon', 'tue']
    contract = models.FileField(upload_to='contracts/', null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', null=True)
    language = models.JSONField(null=True)  # e.g., ['en', 'hi']

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone']

    def __str__(self):
        return self.name or self.email
    
class Role(models.Model):
    rolename = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.rolename
    
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'role')  # Prevent duplicate assignments

    def __str__(self):
        return f"{self.user.name} - {self.role.rolename}"


class Program(models.Model):
    name = models.CharField(max_length=255)
    program_type = models.JSONField(null=True, blank=True)
    personal_select_days = models.JSONField(null=True, blank=True)

    group_select_days_level1 = models.JSONField(null=True, blank=True)
    group_select_time_level1 = models.JSONField(null=True, blank=True)
    group_capacity_level1 = models.PositiveIntegerField(null=True, blank=True)
    group_trainer_level1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_trainer_1_programs')
    
    group_select_days_level2 = models.JSONField(null=True, blank=True)
    group_select_time_level2 = models.JSONField(null=True, blank=True)
    group_capacity_level2 = models.PositiveIntegerField(null=True, blank=True)
    group_trainer_level2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_trainer_2_programs')

    group_select_days_level3 = models.JSONField(null=True, blank=True)
    group_select_time_level3 = models.JSONField(null=True, blank=True)
    group_capacity_level3 = models.PositiveIntegerField(null=True, blank=True)
    group_trainer_level3 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_trainer_3_programs')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.name


class Client(models.Model):
    client_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    sales = models.ForeignKey('User', on_delete=models.CASCADE, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=CLIENT_STATUS_CHOICES)
    new_client = models.BooleanField(default=True)
    workout_start_date = models.DateField(null=True, blank=True)
    diet_first_consultation = models.IntegerField(default=False)
    trainer_first_consultation = models.IntegerField(default=False)
    role_assigned_on = models.DateField(null=True, blank=True)
    program_months = models.IntegerField(default=3)
    program_start_date = models.DateField(null=True, blank=True)
    program_end_date = models.DateField(null=True, blank=True)
    amount = models.CharField(max_length=20,null=True, blank=True)
    paused = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)
    

    def __str__(self):
        return self.name
    

class ProgramClient(models.Model):
 
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='programs')
    program = models.ForeignKey('Program', on_delete=models.CASCADE, related_name='program_clients')
    program_type = models.CharField(max_length=100, blank=True, null=True)
    preferred_time = models.JSONField(blank=True, null=True)
    preferred_group_time = models.CharField(max_length=100, blank=True, null=True)
    workout_days = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trainer_program_clients'
    )
    dietitian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dietitian_program_clients'
    )

    def __str__(self):
        return f"{self.client.name} - {self.program.name}"

class ConsulationSchedules(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    no_of_consultation = models.IntegerField()
    datetime = models.DateTimeField()
    type = models.CharField(max_length=50)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation for {self.client.name} with {self.user.username} on {self.datetime}"

class TrainerConsultationDetails(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    no_of_consultation = models.IntegerField()
    current_acitivity_level = models.CharField(max_length=100, blank=True, null=True)
    current_workouts = models.CharField(max_length=100, blank=True, null=True)
    physical_limitations = models.CharField(max_length=100, blank=True, null=True)
    equipment_owned = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation Details of trainer  for {self.client.name} with {self.user.username} on {self.created_at}"
    
class WeeklyWorkoutUpdates(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    trainer_id = models.ForeignKey(User, on_delete=models.CASCADE)
    week_no = models.IntegerField(default=1, blank=True)
    no_of_days = models.IntegerField(default=1, blank=True)
    week_no_of_days = models.IntegerField(default=1, blank=True)
    week_start_date = models.DateField(null=True)
    week_end_date = models.DateField(null=True)
    week_workout_dates = models.JSONField(null=True, blank=True)
    week_workout_days = models.JSONField(null=True, blank=True)
    status = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Weekly updates of  {self.client.name}  on {self.created_at}"
    
class WeeklyWorkoutwithDaysUpdates(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    trainer_id = models.ForeignKey(User, on_delete=models.CASCADE)
    weekly_updates_id = models.ForeignKey(WeeklyWorkoutUpdates, on_delete=models.CASCADE, default=1, related_name='daily_workouts')
    week_no = models.IntegerField(default=1, blank=True)
    day_no = models.IntegerField(default=1, blank=True)
    workout_date = models.DateField(null=True)
    workout_type = models.CharField(max_length=100, null=True, blank=True)
    workout_sets = models.IntegerField(default=1, blank=True)
    workout_reps = models.IntegerField(default=1, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Weekly updates of  {self.client.name}  on {self.created_at}"
    
class ClienAttendanceUpdates(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    trainer_id = models.ForeignKey(User, on_delete=models.CASCADE)
    workout_date = models.DateField(null=True)
    status = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attendance of   {self.client.name}  marked on {self.created_at}"
    
class Country(models.Model):
    country_code = models.CharField(max_length=100, null=False)
    country_name = models.CharField(max_length=100, null=False)
    def __str__(self):
        return self.country_name or self.country_code


class Leads(models.Model):
    name = models.CharField(max_length=100, null=False)
    source = models.CharField(max_length=100, null=False)
    sales_id = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, null=False)
    email = models.EmailField(unique=True, null=False)
    status = models.CharField(max_length=255, default='New Lead', null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, default=100)
    program_type = models.CharField(max_length=50, null=True, blank=True)
    program_name = models.CharField(max_length=255)
    preferred_days = models.JSONField(null=True, blank=True)
    preferred_time = models.JSONField(null=True, blank=True)
    lead_date = models.DateField(null=True)
    follow_up_date = models.DateField(null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name or self.email

class LeadsFollowup(models.Model):
    lead = models.ForeignKey(Leads, on_delete=models.CASCADE)
    sales = models.ForeignKey(User, on_delete=models.CASCADE)
    follow_up_date = models.DateField(null=True)
    status = models.BooleanField(default=0)
    lead_status = models.CharField(max_length=255, null=True)
    notes = models.CharField(max_length=255, null=True)
    activity_type = models.CharField(max_length=25, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.follow_up_date or self.status

class DietitianConsultationDetails(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    no_of_consultation = models.IntegerField()
    diet_preferences = models.CharField(max_length=100, blank=True, null=True)
    current_eating_pattern = models.CharField(max_length=100, blank=True, null=True)
    appetite_level = models.CharField(max_length=100, blank=True, null=True)
    no_of_meals_per_day = models.CharField(max_length=100, blank=True, null=True)
    cook_at_home_out = models.CharField(max_length=100, blank=True, null=True)
    food_allergies = models.CharField(max_length=100, blank=True, null=True)
    diet_before = models.CharField(max_length=100, blank=True, null=True)
    snacking_habits = models.CharField(max_length=100, blank=True, null=True)
    nutrient_deficiencies = models.CharField(max_length=100, blank=True, null=True)
    sleeping_duration = models.CharField(max_length=100, blank=True, null=True)
    water_intake_per_day = models.CharField(max_length=100, blank=True, null=True)
    working_schedule = models.CharField(max_length=100, blank=True, null=True)
    sleep_quality = models.CharField(max_length=100, blank=True, null=True)
    stress = models.CharField(max_length=100, blank=True, null=True)
    hobbies = models.CharField(max_length=100, blank=True, null=True)
    screen_time = models.CharField(max_length=100, blank=True, null=True)
    pre_existing_conditions = models.CharField(max_length=100, blank=True, null=True)
    past_surgeries = models.CharField(max_length=100, blank=True, null=True)
    medication = models.CharField(max_length=100, blank=True, null=True)
    menstrual_history = models.CharField(max_length=100, blank=True, null=True)
    pregnancy_history = models.CharField(max_length=100, blank=True, null=True)
    breast_feeding = models.CharField(max_length=100, blank=True, null=True)
    supplements = models.CharField(max_length=100, blank=True, null=True)
    medical_tests = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.user

class weeklydietupdates(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    dietitian_id = models.ForeignKey(User, on_delete=models.CASCADE)
    week_no = models.IntegerField(default=1, blank=True)
    diet_chart = models.FileField(upload_to='diet_chart/', null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.client

class MonthlyDietConsultationDetails(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    dietitian_id = models.ForeignKey(User, on_delete=models.CASCADE)
    consult_schedule = models.ForeignKey(ConsulationSchedules, on_delete=models.CASCADE, default=1,)
    month = models.IntegerField(default=1, blank=True)
    consult_date = models.DateField(null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    notes = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.client

class BiweeklyUpdations(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    dietitian_id = models.ForeignKey(User, on_delete=models.CASCADE)
    week_no = models.IntegerField(default=1, blank=True)
    notes = models.CharField(max_length=255, null=True)
    status = models.BooleanField(default=0, blank=True)
    update_date = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.client

class ClientSubscription(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    program_months = models.IntegerField(default=3)
    program_start_date = models.DateField(null=True, blank=True)
    program_end_date = models.DateField(null=True, blank=True)
    amount = models.CharField(max_length=20,null=True, blank=True)
    subscription_type = models.CharField(max_length=120, default='new') # new/renewal
    subscription_id = models.CharField(max_length=20, null=True, unique=True)
    program_type = models.CharField(max_length=70, null=True, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.client
    
class MeetingsTDC(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='meetings_as_trainer')
    dietitian = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='meetings_as_dietitian')
    meeting_type = models.CharField(max_length=120, default='day_1')#day_1, dietchart, dietition_only, TDC, Renewal
    day_no = models.IntegerField(default=1)
    status = models.BooleanField(default=False)
    meeting_date = models.DateField(null=True, blank=True)
    actual_meeting_date = models.DateField(null=True, blank=True)
    need_meeting = models.IntegerField(default=1)
    measurements = models.BooleanField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.client

class MeetingTDCDetails(models.Model):
    meetingtdc = models.ForeignKey(MeetingsTDC, on_delete=models.CASCADE)
    notes = models.CharField(max_length=255, null=True, blank=True)
    change_dietplan = models.BooleanField(default=0)
    uploaded = models.BooleanField(default=0)
    diet_paln = models.CharField(max_length=255, null=True, blank=True)
    diet_plan_uploaded_at = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.meetingtdc

class Measurementsclients(models.Model):
    meetingtdc = models.ForeignKey(MeetingsTDC, on_delete=models.CASCADE)
    chest = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    right_arm = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    left_arm = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    waist = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    hip = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    left_thigh = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    right_thigh = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    right_calf = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    left_calf = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    updated_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.meetingtdc

class WeeklyMeeting(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, default=1)
    dietitian_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    height = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    notes = models.CharField(max_length=255, null=True)
    week_no = models.IntegerField(default=1)
    meeting_date = models.DateField(null=True, blank=True)
    entered_date = models.DateField(null=True, blank=True)
    status = models.BooleanField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.client
    
class ClientPause(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, default=1)
    subscription_id = models.CharField(max_length=120, null=True)
    type = models.CharField(max_length=120, null=True, default='Paused') #Paused, Activated
    paused_at = models.DateTimeField(null=True, blank=True)
    paused_from = models.DateField(null=True, blank=True)
    paused_to = models.DateField(null=True, blank=True)
    no_of_days = models.IntegerField(null=True, default=1)
    notes = models.CharField(max_length=255, null=True, blank=True)
    program_pause_reactivate_on = models.DateField(null=True, blank=True)
    program_end_date = models.DateField(null=True, blank=True)
    program_end_date_changed = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.client

class ClientPauseLimit(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, default=1)
    subscription_months = models.IntegerField(null=True, default=1)
    no_of_days_available = models.IntegerField(null=True, default=0)
    no_of_pauses_available = models.IntegerField(null=True, default=0)
    no_of_paused_days = models.IntegerField(null=True, default=0)
    no_of_pauses_taken = models.IntegerField(null=True, default=0)
    no_of_pause_days_rem = models.IntegerField(null=True, default=0)
    no_of_pause_rem = models.IntegerField(null=True, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.client

class SubscriptionPause(models.Model):
    subscription_months = models.IntegerField(null=True, default=1)
    no_of_pauses = models.IntegerField(null=True, default=0)
    no_of_days = models.IntegerField(null=True, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return 'subscription pause count added'
    
class DietchartClient(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, default=1)
    uploaded = models.BooleanField(default=0)
    diet_plan = models.FileField(upload_to='diet_chart/', null=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    diet_plan_uploaded_at = models.DateField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    







    


