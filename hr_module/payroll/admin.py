from django.contrib import admin
from .models import SystemConfiguration, Loan, Earning, Deduction, Payslip

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'working_days_per_month', 'overtime_rate_per_hour', 'late_deduction_rate_per_minute', 'insurance_percentage', 'tax_percentage')

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'total_amount', 'monthly_installment', 'remaining_balance', 'start_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('employee__full_name', 'employee__employee_code')

@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ('employee', 'type', 'amount', 'date')
    list_filter = ('type', 'date')
    search_fields = ('employee__full_name', 'employee__employee_code')

@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'type', 'amount', 'date')
    list_filter = ('type', 'date')
    search_fields = ('employee__full_name', 'employee__employee_code')

@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'total_earnings', 'total_deductions', 'net_salary', 'status')
    list_filter = ('status', 'year', 'month')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_code')
    readonly_fields = ('total_earnings', 'total_deductions', 'net_salary')
