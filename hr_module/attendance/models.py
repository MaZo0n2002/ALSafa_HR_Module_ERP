from decimal import Decimal
import datetime
from django.db import models
from employees.models import Employee


class Shift(models.Model):
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_minutes = models.IntegerField(default=15, help_text="Allowed late minutes before penalty")

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class AttendanceLog(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Half-day', 'Half-day'),
        ('Leave', 'Approved Leave'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_logs')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Absent')
    late_minutes = models.IntegerField(default=0, help_text="Calculated automatically")
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Calculated automatically")

    class Meta:
        unique_together = ('employee', 'date')

    def save(self, *args, **kwargs):
        # We need to import locally to avoid circular import if config was moved, 
        # but since config is in payroll, let's fetch it:
        from payroll.models import SystemConfiguration
        config = SystemConfiguration.get_config(self.employee.branch)

        # Logic for employees who REQUIRE tracking
        if self.employee.requires_attendance_tracking:
            # Late logic
            if self.check_in:
                shift_start = config.shift_start_time
                in_dt = datetime.datetime.combine(self.date, self.check_in)
                start_dt = datetime.datetime.combine(self.date, shift_start)
                
                diff = (in_dt - start_dt).total_seconds() / 60.0
                self.late_minutes = max(0, int(diff))
                
                # Apply Grace Period
                if self.late_minutes > config.grace_period_minutes:
                    self.status = 'Late'
                else:
                    self.status = 'Present'
            else:
                self.status = 'Absent'
                self.late_minutes = 0
            
            # Overtime logic
            if self.check_out:
                shift_end = config.shift_end_time
                out_dt = datetime.datetime.combine(self.date, self.check_out)
                end_dt = datetime.datetime.combine(self.date, shift_end)
                
                diff = (out_dt - end_dt).total_seconds() / 60.0
                overtime_mins = max(0, int(diff))
                self.overtime_hours = Decimal(overtime_mins / 60.0).quantize(Decimal('0.00'))
        else:
            # EXEMPT staff: Always Present in the logs for record
            self.status = 'Present'
            self.late_minutes = 0
            self.overtime_hours = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.status}"
