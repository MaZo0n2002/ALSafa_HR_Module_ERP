from django.contrib import admin
from .models import Department, Position, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'department')
    list_filter = ('department',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_code', 'full_name', 'department', 'basic_salary', 'status', 'is_active')
    list_filter = ('department', 'status', 'is_active')
    search_fields = ('employee_code', 'full_name')
    autocomplete_fields = ['user'] # Better UI for user selection
