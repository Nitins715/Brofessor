from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "id", "is_staff", "is_active")
    search_fields = ("username", "email", "id")
    readonly_fields = ("id", "date_joined", "last_login")
