from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Contact


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('KanMind Profile', {'fields': ('color',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'color')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'color', 'created_at')
    search_fields = ('name', 'email', 'phone')
