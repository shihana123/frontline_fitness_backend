from django.contrib import admin
from .models import Role, User, UserRole, Program, Client, ProgramClient, SubscriptionPause


admin.site.register(Role)
admin.site.register(User)
admin.site.register(UserRole)
admin.site.register(Program)
admin.site.register(Client)
admin.site.register(ProgramClient)
admin.site.register(SubscriptionPause)
# Register your models here.
