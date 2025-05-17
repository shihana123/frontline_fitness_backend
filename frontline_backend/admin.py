from django.contrib import admin
from .models import Role
from .models import User
from .models import UserRole

admin.site.register(Role)
admin.site.register(User)
admin.site.register(UserRole)
# Register your models here.
