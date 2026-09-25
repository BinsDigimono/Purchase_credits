from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

EXTRA_FIELDS = ("学内情報", {"fields": ("role", "display_name", "student_number", "department")})


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "display_name", "role", "department", "is_staff")
    list_filter = ("role", "is_staff")
    search_fields = ("username", "display_name", "student_number")
    fieldsets = UserAdmin.fieldsets + (EXTRA_FIELDS,)
    add_fieldsets = UserAdmin.add_fieldsets + (EXTRA_FIELDS,)
