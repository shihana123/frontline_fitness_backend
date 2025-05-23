from django.db import models
from .constants import GENDER_CHOICES, STATUS_CHOICES, CLIENT_STATUS_CHOICES
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
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
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.name


class Client(models.Model):
    name = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=CLIENT_STATUS_CHOICES)
    new_client = models.BooleanField(default=True)
    diet_first_consultation = models.BooleanField(default=False)
    trainer_first_consultation = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

class ProgramClient(models.Model):
 
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='programs')
    program = models.ForeignKey('Program', on_delete=models.CASCADE, related_name='program_clients')
    preferred_time = models.CharField(max_length=100, blank=True, null=True)
    preferred_group_time = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.client.name} - {self.program.name}"