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
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=CLIENT_STATUS_CHOICES)
    new_client = models.BooleanField(default=True)
    workout_start_date = models.DateField(null=True, blank=True)
    diet_first_consultation = models.IntegerField(default=False)
    trainer_first_consultation = models.IntegerField(default=False)
    

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
    status = models.CharField(max_length=10, default='New Lead', null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, default=100)
    program_type = models.CharField(max_length=50, null=True, blank=True)
    program_name = models.CharField(max_length=255)
    preferred_days = models.JSONField(null=True, blank=True)
    preferred_time = models.JSONField(null=True, blank=True)
    lead_date = models.DateField(null=True)
    follow_up_date = models.DateField(null=True)
    notes = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.email

class LeadsFollowup(models.Model):
    lead = models.ForeignKey(Leads, on_delete=models.CASCADE)
    sales = models.ForeignKey(User, on_delete=models.CASCADE)
    follow_up_date = models.DateField(null=True)
    status = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.follow_up_date or self.status



    


