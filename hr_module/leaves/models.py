from django.db import models
from employees.models import Employee

class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    
    LEAVE_TYPES = [
        ('Sick', 'Sick Leave'),
        ('Annual', 'Annual Leave'),
        ('Unpaid', 'Unpaid Leave'),
        ('Other', 'Other'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES, default='Annual')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    attachment = models.FileField(upload_to='leave_attachments/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_status = LeaveRequest.objects.get(pk=self.pk).status
            
        super().save(*args, **kwargs)
        
        # Automation: Update Attendance Logs if approved
        if self.status == 'Approved' and old_status != 'Approved':
            from attendance.models import AttendanceLog
            import datetime
            
            curr_date = self.start_date
            while curr_date <= self.end_date:
                # Update or create attendance log for this day
                log, created = AttendanceLog.objects.get_or_create(
                    employee=self.employee,
                    date=curr_date
                )
                log.status = 'Leave'
                # Clear any penalties for this day
                log.late_minutes = 0
                log.overtime_hours = 0
                log.save()
                
                curr_date += datetime.timedelta(days=1)

    def __str__(self):
        return f"{self.employee.full_name} - {self.start_date} to {self.end_date} ({self.status})"
