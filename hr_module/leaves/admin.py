from django.contrib import admin
from .models import LeaveRequest

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'applied_on')
    list_filter = ('status', 'leave_type', 'applied_on')
    search_fields = ('employee__full_name', 'employee__employee_code', 'reason')
    actions = ['approve_leaves', 'reject_leaves']

    def approve_leaves(self, request, queryset):
        for leave in queryset:
            leave.status = 'Approved'
            leave.save()
            # Update employee status
            emp = leave.employee
            emp.status = 'On Leave'
            emp.save()
        self.message_user(request, "Selected leave requests approved.")
    approve_leaves.short_description = "Approve selected leaves"

    def reject_leaves(self, request, queryset):
        queryset.update(status='Rejected')
        self.message_user(request, "Selected leave requests rejected.")
    reject_leaves.short_description = "Reject selected leaves"
