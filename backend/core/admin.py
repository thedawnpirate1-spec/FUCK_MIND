from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Task, Board, Comment


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('KanMind Profile', {'fields': ('color',)}),
    )
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff', 'color'
    )


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'created_at')
    search_fields = ('title',)
    filter_horizontal = ('members',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'board', 'status', 'priority',
        'due_date', 'created_by', 'created_at'
    )
    list_filter = ('status', 'priority')
    search_fields = ('title', 'description')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'author', 'created_at')
    search_fields = ('content',)
