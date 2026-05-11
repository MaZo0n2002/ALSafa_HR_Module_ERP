from django.db import models
from django.conf import settings

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Position(models.Model):
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')

    def __str__(self):
        return f"{self.title} - {self.department.name}"

class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile', null=True, blank=True)
    branch = models.ForeignKey('accounts.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    employee_code = models.CharField(max_length=20, unique=True, blank=True, help_text="Unique employee identifier (auto-generated)")
    full_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, blank=True) # Keeping for backwards compatibility
    last_name = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    job_title = models.CharField(max_length=100, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fixed monthly base salary")
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('On Leave', 'On Leave'),
        ('Resigned', 'Resigned'),
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    join_date = models.DateField(null=True, blank=True)
    hire_date = models.DateField() # Original field
    is_active = models.BooleanField(default=True)
    zkteco_id = models.IntegerField(null=True, blank=True, help_text="User ID mapped from ZKTime biometric device")
    bank_number = models.CharField(max_length=50, blank=True, null=True, help_text="IBAN or Bank Account Number")
    requires_attendance_tracking = models.BooleanField(default=True, help_text="Uncheck if this employee is exempt from fingerprint/scanner attendance tracking")

    def save(self, *args, **kwargs):
        branch_code = self.branch.code if self.branch else '00'
        expected_prefix = f"SLS-{branch_code}-"
        
        if not self.employee_code or not self.employee_code.startswith(expected_prefix):
            # Find the highest code for THIS branch
            last_employee = Employee.objects.filter(employee_code__startswith=expected_prefix).order_by('employee_code').last()
            if last_employee:
                try:
                    parts = last_employee.employee_code.split('-')
                    next_num = int(parts[-1]) + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            
            # Ensure uniqueness
            while Employee.objects.filter(employee_code=f"{expected_prefix}{next_num:04d}").exists():
                next_num += 1
                
            self.employee_code = f"{expected_prefix}{next_num:04d}"
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.employee_code}] {self.full_name}"

# Signals to propagate settings change
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver

@receiver(post_init, sender=Employee)
def remember_tracking_status(sender, instance, **kwargs):
    instance._old_tracking_status = instance.requires_attendance_tracking

@receiver(post_save, sender=Employee)
def propagate_tracking_change(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_old_tracking_status'):
        if instance.requires_attendance_tracking != instance._old_tracking_status:
            from attendance.models import AttendanceLog
            from payroll.models import Payslip
            import datetime
            
            today = datetime.date.today()
            # Update all logs for the CURRENT month to match new reality
            logs = instance.attendance_logs.filter(date__month=today.month, date__year=today.year)
            
            for log in logs:
                # Re-trigger the save() logic in AttendanceLog which handles the exempt vs tracked status
                log.save()
            
            # Also re-trigger payslip calculation if it exists
            payslip = Payslip.objects.filter(employee=instance, month=today.month, year=today.year).first()
            if payslip:
                payslip.save()
