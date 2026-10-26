from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Contact, Task, Board, Comment, Subtask


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('KanMind Profile', {'fields': ('color',)}),
    )
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff', 'color'
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'color', 'created_at')
    search_fields = ('name', 'email', 'phone')


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'created_at')
    search_fields = ('title',)
    filter_horizontal = ('members',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'board', 'status', 'priority', 'category',
        'due_date', 'created_by', 'created_at'
    )
    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'author', 'created_at')
    search_fields = ('content',)


@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'title', 'is_completed')
    list_filter = ('is_completed',)
