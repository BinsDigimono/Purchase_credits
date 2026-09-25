from django.contrib import admin
from django.db.models import Q

from .models import Message, Thread


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "body", "is_ai", "created_at", "read_at")


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "professor", "updated_at")
    inlines = [MessageInline]

    def get_queryset(self, request):
        threads = super().get_queryset(request)
        if request.user.is_superuser:
            return threads
        return threads.filter(Q(student=request.user) | Q(professor=request.user))

    def has_add_permission(self, request):
        return False
