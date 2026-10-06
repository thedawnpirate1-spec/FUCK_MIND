from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('KanMind Profile', {'fields': ('color',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'color')
