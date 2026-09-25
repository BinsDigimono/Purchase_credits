from django.contrib import admin

from .models import Order, OrderItem, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "professor", "price", "stock", "is_active")
    list_editable = ("price", "stock", "is_active")
    list_filter = ("is_active", "department")
    search_fields = ("code", "name")

    def get_queryset(self, request):
        subjects = super().get_queryset(request)
        if request.user.is_superuser:
            return subjects
        return subjects.filter(professor=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.professor_id:
            obj.professor = request.user
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("subject_name", "price", "buyer", "sold_at")
    search_fields = ("subject_name",)

    def get_queryset(self, request):
        items = super().get_queryset(request)
        if request.user.is_superuser:
            return items
        return items.filter(subject__professor=request.user)

    def buyer(self, obj):
        return obj.order.user

    def sold_at(self, obj):
        return obj.order.created_at

    def has_add_permission(self, request):
        return False


admin.site.register(Order)
